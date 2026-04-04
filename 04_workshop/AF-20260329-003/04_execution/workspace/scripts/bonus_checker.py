"""
bonus_checker.py
================
奖金系数合理性评价模块。

在 `confirm` 命令执行时自动触发：
1. 调用 API 4.17 获取关键岗位奖金系数建议
2. 与 AI 评分结果做纵向对比（排名差异）
3. 读取跨组织缓存，做横向同岗位对标
4. 输出评价章节（追加到 confirmed.md 末尾）
5. 将结果写入跨组织缓存

参见 GRV 第十一节。
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

from bp_fetcher import batch_get_key_position_markdown

logger = logging.getLogger(__name__)

# 跨组织缓存文件路径（相对于 output 目录）
CROSS_ORG_CACHE_FILENAME = ".cross_org_cache.json"


# ---------------------------------------------------------------------------
# 缓存读写
# ---------------------------------------------------------------------------

def load_cross_org_cache(output_dir: str) -> dict:
    """
    加载跨组织对标缓存文件。

    :param output_dir: output 目录路径
    :return: 缓存 dict，格式见 GRV 11.5
    """
    cache_path = os.path.join(output_dir, CROSS_ORG_CACHE_FILENAME)
    if not os.path.exists(cache_path):
        return {"version": 1, "last_updated": None, "orgs": {}}
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cross_org_cache(output_dir: str, cache: dict) -> None:
    """
    保存跨组织对标缓存文件。

    :param output_dir: output 目录路径
    :param cache: 缓存 dict
    """
    cache["last_updated"] = datetime.now().isoformat()
    cache_path = os.path.join(output_dir, CROSS_ORG_CACHE_FILENAME)
    os.makedirs(output_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    logger.info("跨组织缓存已更新: %s", cache_path)


def update_cross_org_cache(
    output_dir: str,
    org_name: str,
    persons: list[dict],
) -> None:
    """
    将当前组织的个人评分结果写入跨组织缓存。

    :param output_dir: output 目录路径
    :param org_name: 组织名称
    :param persons: 个人数据列表，每项含 emp_id, name, title, ai_score, ai_score_pct, human_bonus_coef
    """
    cache = load_cross_org_cache(output_dir)
    cache["orgs"][org_name] = {
        "confirmed_at": datetime.now().isoformat(),
        "persons": persons,
    }
    save_cross_org_cache(output_dir, cache)


# ---------------------------------------------------------------------------
# API 4.17 响应解析
# ---------------------------------------------------------------------------

def _parse_bonus_coef_from_markdown(md_text: str) -> Optional[float]:
    """
    从 API 4.17 返回的 Markdown 文本中提取个人层奖金系数建议（月）。

    :param md_text: Markdown 格式文本
    :return: 奖金系数（float），解析失败返回 None
    """
    # 尝试常见格式："个人系数建议：1.2" 或 "personal_coef: 1.2"
    patterns = [
        r"个人系数建议[：:]\s*([\d.]+)",
        r"奖金系数.*?个人[：:]\s*([\d.]+)",
        r"personal_coef[：:]\s*([\d.]+)",
        r"个人奖金系数[：:]\s*([\d.]+)",
    ]
    for pat in patterns:
        m = re.search(pat, md_text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    # 兜底：提取第一个浮点数（作为系数）
    nums = re.findall(r"\b(\d+\.\d+)\b", md_text)
    if nums:
        try:
            return float(nums[0])
        except ValueError:
            pass
    return None


def _parse_title_from_markdown(md_text: str) -> str:
    """
    从 API 4.17 返回的 Markdown 文本中提取岗位 title。

    :param md_text: Markdown 文本
    :return: 岗位 title，或 "未知岗位"
    """
    patterns = [
        r"岗位[：:]\s*(.+)",
        r"title[：:]\s*(.+)",
        r"职位[：:]\s*(.+)",
    ]
    for pat in patterns:
        m = re.search(pat, md_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "未知岗位"


# ---------------------------------------------------------------------------
# 评价逻辑
# ---------------------------------------------------------------------------

def _rank_persons(persons_data: list[dict], score_key: str) -> list[dict]:
    """
    按指定 key 对人员列表降序排名，返回带 rank 字段的副本。

    :param persons_data: 人员数据列表
    :param score_key: 排名依据字段名
    :return: 带 rank 字段的列表（1-based）
    """
    sorted_list = sorted(persons_data, key=lambda x: x.get(score_key, 0.0), reverse=True)
    for i, p in enumerate(sorted_list):
        p = dict(p)
        p[f"rank_{score_key}"] = i + 1
        sorted_list[i] = p
    return sorted_list


def evaluate_bonus_consistency(
    persons_with_ai_scores: list[dict],
    bonus_data: dict[str, str],
    confidence_threshold: float = 0.60,
) -> list[dict]:
    """
    对每位员工进行纵向评价（AI评分 vs 人工系数建议）。

    :param persons_with_ai_scores: 个人节点列表，每项含 id, name, score, confidence
    :param bonus_data: {groupId: markdown_text}（API 4.17 返回）
    :param confidence_threshold: 无法比较的置信度阈值
    :return: 评价结果列表
    """
    total_ai = sum(p.get("score", 0.0) for p in persons_with_ai_scores)

    # 提取人工系数
    enriched = []
    for person in persons_with_ai_scores:
        group_id = person.get("personal_group_id", "")
        md_text = bonus_data.get(group_id, "")
        coef = _parse_bonus_coef_from_markdown(md_text) if md_text else None
        title = _parse_title_from_markdown(md_text) if md_text else "未知岗位"
        ai_score_pct = (person.get("score", 0.0) / total_ai * 100) if total_ai > 0 else 0.0

        enriched.append({
            **person,
            "title": title,
            "human_bonus_coef": coef,
            "ai_score_pct": round(ai_score_pct, 2),
        })

    # 计算排名
    ai_ranked = {p.get("id"): i + 1 for i, p in enumerate(
        sorted(enriched, key=lambda x: x.get("score", 0.0), reverse=True)
    )}
    human_ranked = {p.get("id"): i + 1 for i, p in enumerate(
        sorted(
            [p for p in enriched if p.get("human_bonus_coef") is not None],
            key=lambda x: x.get("human_bonus_coef", 0.0), reverse=True
        )
    )}

    # 人工系数总和（用于归一化占比）
    human_total = sum(p.get("human_bonus_coef", 0.0) for p in enriched if p.get("human_bonus_coef"))

    results = []
    for person in enriched:
        pid = person.get("id")
        confidence = person.get("confidence", 1.0)
        coef = person.get("human_bonus_coef")
        ai_rank = ai_ranked.get(pid, 0)
        human_rank = human_ranked.get(pid)

        # 无法比较的情况
        if confidence < confidence_threshold or coef is None:
            verdict = "❓ 无法比较"
            note = "AI置信度过低" if confidence < confidence_threshold else "无人工系数数据"
        else:
            # 计算排名差和分值差
            rank_diff = abs(ai_rank - human_rank) if human_rank else 0
            ai_pct = person.get("ai_score_pct", 0.0)
            human_pct = (coef / human_total * 100) if human_total > 0 else 0.0
            diff_pct = abs(ai_pct - human_pct)

            if rank_diff >= 2 and diff_pct >= 15:
                if human_rank < ai_rank:
                    verdict = "⚠️ 偏高"
                    note = f"人工系数排名第{human_rank}，AI评分排名第{ai_rank}，差异显著（{rank_diff}位差，分值差{diff_pct:.0f}%）"
                else:
                    verdict = "⚠️ 偏低"
                    note = f"人工系数排名第{human_rank}，AI评分排名第{ai_rank}，差异显著（{rank_diff}位差，分值差{diff_pct:.0f}%）"
            else:
                verdict = "✅ 合理"
                note = "排名一致，差异在合理范围内"

        results.append({
            **person,
            "human_bonus_coef": coef,
            "ai_rank": ai_rank,
            "human_rank": human_rank,
            "verdict": verdict,
            "verdict_note": note,
        })

    return results


# ---------------------------------------------------------------------------
# 横向同岗位对标
# ---------------------------------------------------------------------------

def cross_org_benchmark(
    org_name: str,
    current_persons: list[dict],
    cache: dict,
) -> dict[str, list[dict]]:
    """
    从缓存中提取与当前组织相同岗位的人员，进行横向对标。

    :param org_name: 当前组织名称（用于排除自身数据）
    :param current_persons: 当前组织的人员评价结果列表（含 title 字段）
    :param cache: 跨组织缓存 dict
    :return: {title: [person_dicts]}，按岗位分组的同岗位人员列表
    """
    # 收集当前组织的岗位集合
    current_titles = {p.get("title") for p in current_persons if p.get("title") and p.get("title") != "未知岗位"}

    if not current_titles:
        return {}

    # 从缓存中收集其他组织的同岗位人员
    title_groups: dict[str, list[dict]] = {t: [] for t in current_titles}

    # 先加入当前组织成员（标注来源）
    for person in current_persons:
        title = person.get("title", "未知岗位")
        if title in title_groups:
            title_groups[title].append({**person, "org": org_name})

    # 从缓存中加入其他组织
    for cached_org, org_data in cache.get("orgs", {}).items():
        if cached_org == org_name:
            continue
        for p in org_data.get("persons", []):
            ptitle = p.get("title", "未知岗位")
            if ptitle in title_groups:
                title_groups[ptitle].append({**p, "org": cached_org})

    # 过滤掉只有当前组织的 title（无法横向对标）
    return {t: persons for t, persons in title_groups.items() if len(persons) > 1}


# ---------------------------------------------------------------------------
# Markdown 报告生成
# ---------------------------------------------------------------------------

def generate_bonus_section(
    org_name: str,
    evaluation_results: list[dict],
    benchmark_data: dict[str, list[dict]],
) -> str:
    """
    生成奖金系数合理性审查的 Markdown 章节文本。

    :param org_name: 组织名称
    :param evaluation_results: 纵向评价结果列表
    :param benchmark_data: 横向对标数据 {title: [persons]}
    :return: Markdown 字符串（追加到 confirmed.md 末尾）
    """
    lines = [
        "---",
        "",
        "## 奖金系数合理性审查",
        "",
        "> 以下对比基于 API 4.17 系统奖金系数建议（人工设定）与本次 AI 评分结果。",
        "> 评价结论仅供参考，最终激励决策由管理者判断。",
        "",
        "### 纵向对比（AI评分 vs 人工系数建议）",
        "",
        "| 姓名 | 岗位 | AI评分 | AI排名 | 人工系数建议 | 人工排名 | 评价 | 说明 |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for r in evaluation_results:
        name = r.get("name", "?")
        title = r.get("title", "未知")
        ai_score = r.get("score", 0.0)
        ai_pct = r.get("ai_score_pct", 0.0)
        ai_rank = r.get("ai_rank", "?")
        coef = r.get("human_bonus_coef")
        human_rank = r.get("human_rank", "?")
        verdict = r.get("verdict", "?")
        note = r.get("verdict_note", "")

        coef_str = f"{coef}月" if coef is not None else "无数据"
        human_rank_str = f"#{human_rank}" if human_rank else "—"

        lines.append(
            f"| {name} | {title} | {ai_score:.1f}分({ai_pct:.1f}%) | "
            f"#{ai_rank} | {coef_str} | {human_rank_str} | {verdict} | {note} |"
        )

    lines.append("")

    if benchmark_data:
        lines.append("### 同岗位横向对标")
        lines.append("")

        for title, persons in benchmark_data.items():
            orgs_count = len({p.get("org") for p in persons})
            lines.append(f"#### 岗位：{title}（共 {len(persons)} 人，来自 {orgs_count} 个组织）")
            lines.append("")
            lines.append("| 姓名 | 所属组织 | AI评分占比 | 人工系数建议 | 差异评价 |")
            lines.append("|---|---|---|---|---|")

            ai_scores = [p.get("ai_score_pct", p.get("ai_score", 0.0)) for p in persons]
            coefs = [p.get("human_bonus_coef") for p in persons if p.get("human_bonus_coef")]
            ai_mean = sum(ai_scores) / len(ai_scores) if ai_scores else 0.0
            coef_mean = sum(coefs) / len(coefs) if coefs else None

            for p in persons:
                p_name = p.get("name", "?")
                p_org = p.get("org", "?")
                p_ai = p.get("ai_score_pct", p.get("ai_score", 0.0))
                p_coef = p.get("human_bonus_coef")
                p_coef_str = f"{p_coef}月" if p_coef is not None else "无数据"
                p_verdict = p.get("verdict", "—")
                lines.append(f"| {p_name} | {p_org} | {p_ai:.1f}% | {p_coef_str} | {p_verdict} |")

            lines.append("")
            coef_mean_str = f"{coef_mean:.2f}月" if coef_mean is not None else "无数据"
            lines.append(
                f"> 📊 同岗位AI评分均值：{ai_mean:.1f}%，人工系数均值：{coef_mean_str}"
            )
            lines.append("")
    else:
        lines.append(
            "> `[跨组织数据不足，跳过横向对标]`"
            "（首次运行或缓存为空，待其他组织完成评分后自动补充）"
        )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主入口（供 main.py confirm 调用）
# ---------------------------------------------------------------------------

def run_bonus_check(
    org_name: str,
    persons: list[dict],
    output_dir: str,
    confidence_threshold: float = 0.60,
) -> str:
    """
    执行完整的奖金系数合理性评价流程，返回 Markdown 章节文本。

    :param org_name: 组织名称
    :param persons: 个人节点列表（含 id, name, score, confidence, personal_group_id）
    :param output_dir: output 目录路径
    :param confidence_threshold: 无法比较的置信度下限
    :return: Markdown 章节文本
    """
    # 批量调用 API 4.17
    group_ids = [p.get("personal_group_id") for p in persons if p.get("personal_group_id")]
    bonus_data = {}
    if group_ids:
        try:
            bonus_data = batch_get_key_position_markdown(group_ids)
        except Exception as e:
            logger.error("API 4.17 调用失败: %s", e)
            bonus_data = {}

    # 纵向评价
    evaluation_results = evaluate_bonus_consistency(persons, bonus_data, confidence_threshold)

    # 读取跨组织缓存，横向对标
    cache = load_cross_org_cache(output_dir)
    benchmark_data = cross_org_benchmark(org_name, evaluation_results, cache)

    # 生成报告章节
    section = generate_bonus_section(org_name, evaluation_results, benchmark_data)

    # 更新跨组织缓存（写入当前组织数据）
    cache_persons = [
        {
            "emp_id": r.get("id", ""),
            "name": r.get("name", ""),
            "title": r.get("title", "未知岗位"),
            "ai_score": r.get("score", 0.0),
            "ai_score_pct": r.get("ai_score_pct", 0.0),
            "human_bonus_coef": r.get("human_bonus_coef"),
        }
        for r in evaluation_results
    ]
    update_cross_org_cache(output_dir, org_name, cache_persons)

    return section
