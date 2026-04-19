"""
main.py
=======
BP评分系统 CLI 主入口。

子命令：
  run     -- 拉取BP树、AI评分、生成报告
  adjust  -- 人工调整指定BP分值（联动更新下级）
  confirm -- 锁定报告，触发奖金系数审查，写入跨组织缓存
  cache   -- 缓存管理（目前支持 clear）

环境变量：
  BP_APP_KEY      BP系统认证key
  SCORER_MODEL    LLM模型名（默认 gpt-4o）
  SCORER_API_KEY  LLM API key
  SCORER_API_BASE LLM API base（默认 https://api.openai.com/v1）
  BP_BASE_URL     BP系统base URL
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# 路径设置：确保 scripts/ 下的模块可被 import
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
CONFIG_DIR = WORKSPACE_DIR / "config"
OUTPUT_DIR = WORKSPACE_DIR / "output"

sys.path.insert(0, str(SCRIPT_DIR))

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def load_weights() -> dict:
    """加载 config/scoring_weights.yaml。"""
    weights_path = CONFIG_DIR / "scoring_weights.yaml"
    if not weights_path.exists():
        logger.warning("权重配置文件不存在，使用默认值: %s", weights_path)
        return {
            "peer_scoring": {
                "strategic_alignment": 0.40,
                "measurability": 0.20,
                "measure_coverage": 0.20,
                "impact_scope": 0.20,
            },
            "pool_distribution": {
                "target_accuracy": 0.45,
                "outcome_contribution": 0.35,
                "measure_completeness": 0.20,
            },
            "system": {
                "confidence_threshold": 0.70,
                "min_bp_score": 1.0,
                "min_undertaker_score": 0.5,
                "max_batch_size": 10,
                "llm_retry_count": 3,
            },
        }
    with open(weights_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_output_dir() -> str:
    """确保 output 目录存在，返回其路径字符串。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_DIR)


def get_report_output_path(org_name: str) -> str:
    """根据组织名和当前日期生成报告路径。"""
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{org_name}-{date_str}-report.md"
    return str(OUTPUT_DIR / filename)


# ---------------------------------------------------------------------------
# run 子命令
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> None:
    """
    run 命令：拉取BP树 → AI评分 → 生成报告。

    流程：
    1. 用 bp_fetcher 按组织名搜索 groupId
    2. 获取指定周期 periodId
    3. 获取 BP 简单树列表
    4. 为每个 BP 获取完整详情
    5. 用 scorer 进行同级 BP 权重评分
    6. 用 report 生成 Markdown 报告
    7. 保存评分树 JSON 缓存
    """
    from bp_fetcher import (
        search_by_name,
        get_all_periods,
        get_simple_tree,
        get_goal_and_key_result,
        get_undertakers_from_bp,
    )
    from scorer import batch_score_peer_bps, score_undertakers
    from adjuster import build_original_ratios_session
    from report import generate_report, save_score_tree

    org_name = args.org
    period_name = args.period
    weights = load_weights()
    output_dir = ensure_output_dir()
    confidence_threshold = weights.get("system", {}).get("confidence_threshold", 0.70)
    max_batch_size = weights.get("system", {}).get("max_batch_size", 10)
    retry_count = weights.get("system", {}).get("llm_retry_count", 3)
    peer_weights = weights.get("peer_scoring", {})
    pool_weights = weights.get("pool_distribution", {})

    logger.info("开始评分流程: 组织=%s 周期=%s", org_name, period_name)

    # Step 1: 搜索组织
    logger.info("搜索组织: %s", org_name)
    orgs = search_by_name(org_name)
    if not orgs:
        logger.error("未找到组织: %s", org_name)
        sys.exit(1)
    if len(orgs) > 1:
        logger.error("找到多个同名组织，请确认：%s", [o.get("name") for o in orgs])
        sys.exit(1)
    group_id = orgs[0]["groupId"]
    logger.info("组织 groupId: %s", group_id)

    # Step 2: 获取周期
    logger.info("获取BP周期列表...")
    periods = get_all_periods(group_id)
    period = next((p for p in periods if p.get("name") == period_name), None)
    if period is None:
        available = [p.get("name") for p in periods]
        logger.error("未找到周期 '%s'，可用周期: %s", period_name, available)
        sys.exit(1)
    period_id = period["periodId"]
    logger.info("周期 periodId: %s", period_id)

    # Step 3: 获取BP简单树（一级列表）
    logger.info("获取BP列表...")
    simple_tree = get_simple_tree(group_id, period_id)
    if not simple_tree:
        logger.warning("组织 %s 在周期 %s 下没有BP", org_name, period_name)
        simple_tree = []

    # Step 4: 获取每个BP的完整详情
    logger.info("获取 %d 个BP详情...", len(simple_tree))
    bp_details = []
    for node in simple_tree:
        bp_id = node.get("bpId") or node.get("id", "")
        detail = get_goal_and_key_result(bp_id, period_id)
        if detail:
            bp_details.append(detail)
        else:
            logger.warning("获取BP详情失败: %s", bp_id)

    if not bp_details:
        logger.error("无法获取任何BP详情，终止")
        sys.exit(1)

    # Step 5: 同级BP权重评分
    logger.info("AI评分中（共%d个BP）...", len(bp_details))
    score_result = batch_score_peer_bps(
        org_name=org_name,
        period_name=period_name,
        bp_list=bp_details,
        parent_bp=None,
        weights=peer_weights,
        batch_size=max_batch_size,
        retry_count=retry_count,
    )

    # 构造评分树节点
    score_map = {}
    if score_result:
        for s in score_result.get("scores", []):
            score_map[s["bp_id"]] = s

    score_tree = []
    for bp in bp_details:
        bp_id = bp.get("bpId", "")
        s = score_map.get(bp_id, {})
        node = {
            "id": bp_id,
            "name": bp.get("objective", "（无标题）"),
            "type": "bp",
            "score": s.get("score", 0.0),
            "score_source": "ai_original" if s else "ai_failed",
            "adjusted_from": None,
            "adjust_reason": None,
            "confidence": s.get("confidence"),
            "reason": s.get("reason", ""),
            "tags": [],
            "children": [],
            "parent_ratio": s.get("score", 0.0) / 100.0 if s else 0.0,
            "org_path": org_name,
            "source_bp_ids": [bp_id],
        }

        # 处理承接方
        undertakers_info = get_undertakers_from_bp(bp)
        if undertakers_info:
            # 聚合所有承接方部门名称
            undertaker_names = []
            for item in undertakers_info:
                for dept in item.get("undertakers", []):
                    name = dept.get("name", "")
                    if name and name not in undertaker_names:
                        undertaker_names.append(name)

            if undertaker_names:
                # 为每个承接方创建子节点（简化：无需再次评分，展示为下级）
                for uname in undertaker_names:
                    child = {
                        "id": f"{bp_id}-{uname}",
                        "name": uname,
                        "type": "bp",
                        "score": round(node["score"] / len(undertaker_names), 1),
                        "score_source": "cascade_updated",
                        "adjusted_from": None,
                        "adjust_reason": None,
                        "confidence": None,
                        "reason": f"承接《{bp.get('objective', '')}》",
                        "tags": [],
                        "children": [],
                        "parent_ratio": 1.0 / len(undertaker_names),
                        "org_path": f"{org_name} → {uname}",
                        "source_bp_ids": [bp_id],
                    }
                    node["children"].append(child)
        else:
            node["tags"].append("无承接")
            node["score_source"] = "no_undertaker" if not s else node["score_source"]

        score_tree.append(node)

    # 构建原始比例 session
    original_ratios_session = build_original_ratios_session(score_tree)

    # Step 6: 生成报告
    report_path = get_report_output_path(org_name)
    logger.info("生成报告: %s", report_path)
    actual_path = generate_report(
        org_name=org_name,
        period_name=period_name,
        score_tree=score_tree,
        confidence_threshold=confidence_threshold,
        output_dir=output_dir,
    )

    # Step 7: 保存评分树缓存
    tree_data = {
        "org_name": org_name,
        "period_name": period_name,
        "period_id": period_id,
        "group_id": group_id,
        "score_tree": score_tree,
        "original_ratios_session": original_ratios_session,
        "generated_at": datetime.now().isoformat(),
    }
    save_score_tree(actual_path, tree_data)

    print(f"\n✅ 评分完成！报告已生成：{actual_path}")
    print(f"   下一步：python3 scripts/main.py confirm --report {actual_path}")


# ---------------------------------------------------------------------------
# adjust 子命令
# ---------------------------------------------------------------------------

def cmd_adjust(args: argparse.Namespace) -> None:
    """
    adjust 命令：人工调整指定BP分值，联动更新下级。
    """
    from adjuster import adjust_bp_score, validate_tree_score_conservation
    from report import load_score_tree_from_report, save_score_tree, generate_report

    report_path = args.report
    bp_id = args.bp_id
    new_score = args.score
    reason = args.reason
    weights = load_weights()
    confidence_threshold = weights.get("system", {}).get("confidence_threshold", 0.70)
    output_dir = ensure_output_dir()

    if not os.path.exists(report_path):
        logger.error("报告文件不存在: %s", report_path)
        sys.exit(1)

    # 加载评分树缓存
    tree_data = load_score_tree_from_report(report_path)
    if tree_data is None:
        logger.error("找不到评分树缓存（*-tree.json），无法执行调整")
        sys.exit(1)

    score_tree = tree_data.get("score_tree", [])
    original_ratios_session = tree_data.get("original_ratios_session", {})
    org_name = tree_data.get("org_name", "未知组织")
    period_name = tree_data.get("period_name", "未知周期")

    logger.info("调整 BP %s → %s 分，原因：%s", bp_id, new_score, reason)

    # 执行调整
    updated_tree, found = adjust_bp_score(
        score_tree=score_tree,
        bp_id=bp_id,
        new_score=new_score,
        reason=reason,
        original_ratios_session=original_ratios_session,
        parent_id="root",
    )

    if not found:
        logger.error("未找到 BP ID: %s，请检查报告中的 BP ID", bp_id)
        sys.exit(1)

    # 验证分值守恒
    valid, errors = validate_tree_score_conservation(updated_tree, expected_total=100.0)
    if not valid:
        logger.warning("分值守恒验证失败（可能有浮点误差）: %s", errors)

    # 保存更新后的评分树
    tree_data["score_tree"] = updated_tree
    save_score_tree(report_path, tree_data)

    # 重新生成报告（覆盖原文件）
    generate_report(
        org_name=org_name,
        period_name=period_name,
        score_tree=updated_tree,
        confidence_threshold=confidence_threshold,
        output_dir=output_dir,
        version="v1（待人工确认，含手动调整）",
    )

    print(f"\n✅ 调整完成！BP {bp_id} 分值已更新为 {new_score} 分")
    print(f"   报告已重新生成：{report_path}")
    print(f"   如需继续调整，重复运行 adjust 命令；完成后运行 confirm 锁定")


# ---------------------------------------------------------------------------
# confirm 子命令
# ---------------------------------------------------------------------------

def cmd_confirm(args: argparse.Namespace) -> None:
    """
    confirm 命令：锁定报告 → 触发奖金系数审查 → 写入跨组织缓存。
    """
    from report import load_score_tree_from_report, generate_confirmed_report, collect_persons
    from bonus_checker import run_bonus_check

    report_path = args.report
    weights = load_weights()
    output_dir = ensure_output_dir()

    if not os.path.exists(report_path):
        logger.error("报告文件不存在: %s", report_path)
        sys.exit(1)

    confirmed_path = report_path.replace("-report.md", "-confirmed.md")
    if os.path.exists(confirmed_path):
        logger.warning("已存在确认版本：%s，将覆盖", confirmed_path)

    # 加载评分树
    tree_data = load_score_tree_from_report(report_path)
    if tree_data is None:
        logger.warning("找不到评分树缓存，将仅锁定报告（无奖金系数审查）")
        bonus_section = ""
        org_name = "未知组织"
    else:
        org_name = tree_data.get("org_name", "未知组织")
        score_tree = tree_data.get("score_tree", [])

        # 收集个人层节点
        persons = collect_persons(score_tree)

        if persons:
            logger.info("触发奖金系数合理性审查（%d 人）...", len(persons))
            try:
                bonus_section = run_bonus_check(
                    org_name=org_name,
                    persons=persons,
                    output_dir=output_dir,
                )
            except Exception as e:
                logger.error("奖金系数审查失败（不影响确认流程）: %s", e)
                bonus_section = ""
        else:
            logger.info("无个人层数据，跳过奖金系数审查")
            bonus_section = ""

    # 生成 confirmed.md
    confirmed_path = generate_confirmed_report(report_path, bonus_section=bonus_section)

    print(f"\n✅ 报告已确认并锁定：{confirmed_path}")
    print(f"   跨组织缓存已更新：{output_dir}/.cross_org_cache.json")
    print("   ⚠️  此文件为最终确认版本，不可再修改。如需更新，请重新运行 run 命令。")


# ---------------------------------------------------------------------------
# cache 子命令
# ---------------------------------------------------------------------------

def cmd_cache(args: argparse.Namespace) -> None:
    """
    cache 命令：缓存管理。
    目前支持：clear（清除跨组织缓存）
    """
    action = args.cache_action

    if action == "clear":
        cache_path = OUTPUT_DIR / ".cross_org_cache.json"
        if cache_path.exists():
            cache_path.unlink()
            print(f"✅ 跨组织缓存已清除：{cache_path}")
        else:
            print(f"⚠️  跨组织缓存文件不存在，无需清除：{cache_path}")
    else:
        logger.error("未知的 cache 操作: %s（目前仅支持 clear）", action)
        sys.exit(1)


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="BP评分系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 scripts/main.py run --org "产品中心" --period "2026Q1"
  python3 scripts/main.py adjust --report output/产品中心-20260329-report.md --bp-id BP-001 --score 70 --reason "战略优先级调整"
  python3 scripts/main.py confirm --report output/产品中心-20260329-report.md
  python3 scripts/main.py cache clear
""",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ---- run ----
    run_parser = subparsers.add_parser("run", help="拉取BP树、AI评分、生成报告")
    run_parser.add_argument("--org", required=True, metavar="ORG_NAME", help="组织名称，如 '产品中心'")
    run_parser.add_argument("--period", required=True, metavar="PERIOD", help="BP周期名称，如 '2026Q1'")
    run_parser.set_defaults(func=cmd_run)

    # ---- adjust ----
    adj_parser = subparsers.add_parser("adjust", help="人工调整指定BP分值（联动更新下级）")
    adj_parser.add_argument("--report", required=True, metavar="REPORT_PATH", help="报告文件路径（*-report.md）")
    adj_parser.add_argument("--bp-id", required=True, metavar="BP_ID", help="要调整的BP ID，如 'BP-001'")
    adj_parser.add_argument("--score", required=True, type=float, metavar="SCORE", help="新的分值（浮点数）")
    adj_parser.add_argument("--reason", required=True, metavar="REASON", help="调整理由")
    adj_parser.set_defaults(func=cmd_adjust)

    # ---- confirm ----
    conf_parser = subparsers.add_parser("confirm", help="锁定报告，触发奖金系数审查，写入跨组织缓存")
    conf_parser.add_argument("--report", required=True, metavar="REPORT_PATH", help="报告文件路径（*-report.md）")
    conf_parser.set_defaults(func=cmd_confirm)

    # ---- cache ----
    cache_parser = subparsers.add_parser("cache", help="缓存管理")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_action", metavar="ACTION")
    cache_subparsers.required = True
    cache_subparsers.add_parser("clear", help="清除跨组织缓存（output/.cross_org_cache.json）")
    cache_parser.set_defaults(func=cmd_cache)

    return parser


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main() -> None:
    # 环境变量检查（警告，不强制退出）
    if not os.environ.get("BP_APP_KEY"):
        logger.warning("环境变量 BP_APP_KEY 未设置，BP系统API调用可能失败")
    if not os.environ.get("SCORER_API_KEY"):
        logger.warning("环境变量 SCORER_API_KEY 未设置，AI评分功能将不可用")

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
