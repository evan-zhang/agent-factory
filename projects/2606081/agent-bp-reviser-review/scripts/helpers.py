#!/usr/bin/env python3
"""
BP 修订辅助函数
提供目标匹配、证据处理、补丁生成、API 调用、会话记忆等辅助功能
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime, timedelta
import json
import os
import urllib.request
import urllib.parse

# ─── 配置 ────────────────────────────────────────────────────────
BP_API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api"
BP_APP_KEY = os.environ.get("XGJK_API_KEY", "TsFhRR7OywNULeHPqudePf85STc4EpHI")
BP_PERIOD_ID = os.environ.get("BP_PERIOD_ID", "1994002024299085826")
BP_GROUP_ID_PRODUCT = os.environ.get("BP_GROUP_ID_PRODUCT", "1994002335135023106")

# ─── 会话规则记忆（全局，单次运行周期内保持）────────────────
_session_memory: Dict[str, Dict[str, Any]] = {}

def remember_corrected_rule(rule_id: str, correction: Dict[str, Any]) -> None:
    """记录被纠正的规则到会话记忆"""
    _session_memory[rule_id] = {
        "correction": correction,
        "timestamp": datetime.now().isoformat(),
        "applied": False
    }

def get_session_memory() -> Dict[str, Dict[str, Any]]:
    """获取当前会话记忆"""
    return dict(_session_memory)

def clear_session_memory() -> None:
    """清空会话记忆（新会话时调用）"""
    _session_memory.clear()

def apply_session_memory(revision_output=None, target_standard=None) -> List[str]:
    """应用会话记忆，返回本次触发的记忆规则列表

    revision_output 和 target_standard 保留用于将来集成；
    目前直接从全局 _session_memory 读取。
    """
    triggered = []
    for rule_id, mem in _session_memory.items():
        if not mem.get("applied", False):
            mem["applied"] = True
            triggered.append(rule_id)
    return triggered

# ─── BP API 调用 ─────────────────────────────────────────────────

def _bp_api_call(path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """调用 BP 系统 Open API

    Args:
        path: API 路径，如 /bp/group/searchByName
        params: URL 查询参数

    Returns:
        解析后的 JSON 响应字典
    """
    url = f"{BP_API_BASE}{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"

    req = urllib.request.Request(url, headers={"appKey": BP_APP_KEY})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        return {"resultCode": 0, "resultMsg": str(e), "data": None}


def search_tasks_by_name(name: str, period_id: str = BP_PERIOD_ID) -> List[Dict[str, Any]]:
    """按名称模糊搜索任务（2.11）

    用于 Step 0 目标定位的 keyword 搜索。

    Returns:
        匹配的任务列表，每个元素含 id/name/type
    """
    resp = _bp_api_call("/bp/task/v2/searchByName", {
        "periodId": period_id,
        "name": name
    })
    if resp.get("resultCode") == 1 and resp.get("data"):
        return resp["data"]
    return []


def get_task_tree(group_id: str) -> List[Dict[str, Any]]:
    """获取分组下的完整任务树（2.4 getSimpleTree）

    Returns:
        递归树结构，节点含 id/name/type/children
    """
    resp = _bp_api_call("/bp/task/v2/getSimpleTree", {"groupId": group_id})
    if resp.get("resultCode") == 1 and resp.get("data"):
        return resp["data"]
    return []


def get_goal_detail(goal_id: str) -> Optional[Dict[str, Any]]:
    """获取目标详情（2.5 getGoalDetail）"""
    resp = _bp_api_call(f"/bp/goal/{goal_id}/detail")
    if resp.get("resultCode") == 1 and resp.get("data"):
        return resp["data"]
    return None


def search_groups_by_name(name: str) -> List[Dict[str, Any]]:
    """按名称模糊搜索分组（2.12）"""
    resp = _bp_api_call("/bp/group/searchByName", {
        "periodId": BP_PERIOD_ID,
        "name": name
    })
    if resp.get("resultCode") == 1 and resp.get("data"):
        return resp["data"]
    return []


def _walk_tree_for_match(nodes: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """递归遍历任务树，匹配包含 keyword 的节点"""
    results = []
    for node in nodes:
        name = node.get("name", "")
        if keyword in name:
            results.append({
                "target_id": node["id"],
                "target_name": name,
                "target_type": node.get("type", ""),
                "match_reason": f"名称匹配: {keyword}",
                "confidence": 0.8 if name == keyword else 0.5
            })
        children = node.get("children", [])
        if children:
            results.extend(_walk_tree_for_match(children, keyword))
    return results


def search_product_aliases(keywords: List[str], period_id: str = BP_PERIOD_ID,
                          group_id: str = "") -> List[Dict[str, Any]]:
    """搜索产品别名和目标

    优先策略：
    1. 模糊搜索任务（2.11 searchByName）
    2. 回退到分组搜索（2.12 searchByName），再遍历任务树（2.4 getSimpleTree）
    3. 去重合并结果

    该函数是「搜索策略分层」原则（RR-09）和「产品别名搜索」原则（ER-03）的实现。
    """
    seen_ids = set()
    results = []

    for keyword in keywords:
        if not keyword or len(keyword) < 2:
            continue

        # 策略 1：直接模糊搜索任务
        tasks = search_tasks_by_name(keyword, period_id)
        for t in tasks:
            tid = str(t.get("id", ""))
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                results.append({
                    "target_id": tid,
                    "target_name": t.get("name", ""),
                    "target_type": t.get("type", ""),
                    "match_reason": f"任务名称模糊匹配: {keyword}",
                    "confidence": 0.85,
                    "source": "searchByName"
                })

        # 策略 2：搜索分组，遍历其任务树
        if not group_id:
            groups = search_groups_by_name(keyword)
            for g in groups:
                gid = str(g.get("id", ""))
                if gid:
                    tree = get_task_tree(gid)
                    tree_results = _walk_tree_for_match(tree, keyword)
                    for tr in tree_results:
                        tid = tr["target_id"]
                        if tid not in seen_ids:
                            seen_ids.add(tid)
                            tr["source"] = "group_tree"
                            tr["group_name"] = g.get("name", "")
                            results.append(tr)

    return results


# ─── 证据相关 ───────────────────────────────────────────────────

def _parse_evidence_time(t: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(t)
    except:
        return None


def calculate_evidence_confidence(evidence_bundle, target_standard) -> float:
    """计算证据置信度"""

    score = 0.0

    # 责任人匹配度（40%）
    if evidence_bundle.responsibility_chain and \
       target_standard.owner in evidence_bundle.responsibility_chain:
        score += 0.4

    # 时间相关性（30%）
    if evidence_bundle.evidence_time:
        try:
            evidence_time = datetime.fromisoformat(evidence_bundle.evidence_time)
            target_end = datetime.fromisoformat(target_standard.period.get("end", "2026-12-31"))
            days_diff = abs((target_end - evidence_time).days)

            if days_diff <= 7:
                score += 0.3
            elif days_diff <= 30:
                score += 0.2
            elif days_diff <= 90:
                score += 0.1
        except:
            pass

    # 内容完整性（20%）
    if evidence_bundle.evidence_content and \
       evidence_bundle.evidence_content.get("summary"):
        score += 0.2

    # 来源可靠性（10%）
    reliable_sources = ["weekly_report", "monthly_report", "goal_report"]
    if evidence_bundle.evidence_type in reliable_sources:
        score += 0.1

    return min(score, 1.0)


def detect_major_defects(evidence_content: Dict[str, Any]) -> List[str]:
    """检测重大缺陷"""

    defects = []
    summary = evidence_content.get("summary", "")

    if "不一致" in summary or "矛盾" in summary:
        defects.append("data_inconsistency")
    if "错误" in summary or "异常" in summary:
        defects.append("obvious_error")
    if "冲突" in summary:
        defects.append("logical_contradiction")

    return defects


def calculate_time_distance(target_standard, evidence_time: str) -> int:
    """计算时间距离"""

    try:
        evidence_dt = datetime.fromisoformat(evidence_time)
        target_end = datetime.fromisoformat(target_standard.period.get("end", "2026-12-31"))
        return abs((target_end - evidence_dt).days)
    except:
        return 999


def in_responsibility_chain(evidence_bundle, target_standard) -> bool:
    """检查证据是否在目标责任链中"""

    if not evidence_bundle.responsibility_chain:
        return False
    return any(
        role in target_standard.responsibility_chain
        for role in evidence_bundle.responsibility_chain
    )


# ─── 写回与一致性 ───────────────────────────────────────────────

def generate_writeback_patch(revision_output, target_standard) -> Dict[str, Any]:
    """生成写回补丁"""

    patch = {
        "text_updates": [],
        "color_updates": [],
        "evidence_updates": []
    }

    if revision_output.revision_action == "rewrite":
        patch["text_updates"].append({
            "target": revision_output.target_code,
            "field": "target_description",
            "old_value": None,
            "new_value": revision_output.revision_reason
        })

        if revision_output.target_color:
            patch["color_updates"].append({
                "target": revision_output.target_code,
                "old_color": None,
                "new_color": revision_output.target_color
            })

        for evidence_id in revision_output.evidence_bundle_ref:
            patch["evidence_updates"].append({
                "evidence_id": evidence_id,
                "action": "add",
                "details": {"status": "verified"}
            })

    return patch


def run_consistency_check(revision_output, target_standard, evidence_bundles=None) -> Dict[str, Any]:
    """运行一致性校验"""

    issues = []
    patch = revision_output.writeback_patch

    if patch.get("color_updates"):
        color_update = patch["color_updates"][0]
        new_color = color_update.get("new_color")

        if new_color == "black" and len(revision_output.evidence_bundle_ref) > 0:
            issues.append("黑灯状态不应有有效证据")

        if new_color == "green":
            has_primary = False
            if evidence_bundles:
                has_primary = any(
                    b.evidence_level == "primary" and
                    b.evidence_id in revision_output.evidence_bundle_ref
                    for b in evidence_bundles
                )
            if not has_primary:
                issues.append("绿灯状态需要主要证据")

    for update in patch.get("text_updates", []):
        if update.get("target") != revision_output.target_code:
            issues.append(f"检测到跨目标文字写回: {update.get('target')}")
            break

    for update in patch.get("color_updates", []):
        if update.get("target") != revision_output.target_code:
            issues.append(f"检测到跨目标色块写回: {update.get('target')}")
            break

    return {"passed": len(issues) == 0, "issues": issues}


def merge_patches(patch1: Dict[str, Any], patch2: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个补丁"""
    return {
        "text_updates": patch1.get("text_updates", []) + patch2.get("text_updates", []),
        "color_updates": patch1.get("color_updates", []) + patch2.get("color_updates", []),
        "evidence_updates": patch1.get("evidence_updates", []) + patch2.get("evidence_updates", [])
    }


# ─── 输出 ────────────────────────────────────────────────────────

def create_three_segment_output() -> str:
    """创建三段式输出（无证据时）"""
    return """## 现状

当前目标无有效证据。

## 用户补充

请提供以下信息：
- 目标责任人
- 目标进展情况
- 相关支持材料

## 整改计划

- [ ] 收集目标证据
- [ ] 验证责任人汇报
- [ ] 更新目标状态
"""


def generate_validation_report(revision_output, target_standard) -> str:
    """生成验证报告"""
    report_lines = [
        "# 修订验证报告",
        "",
        f"## 目标: {revision_output.target_name}",
        f"目标编码: {revision_output.target_code}",
        "",
        "### 应用标准",
        f"- 版本: {revision_output.standard_applied}",
        f"- 责任人: {target_standard.owner}",
        "",
        "### 修订结果",
        f"- 状态: {revision_output.revision_status}",
        f"- 动作: {revision_output.revision_action}",
        f"- 原因: {revision_output.revision_reason}",
        "",
        "### 证据情况",
        f"- 证据数量: {len(revision_output.evidence_bundle_ref)}",
        f"- 证据引用: {', '.join(revision_output.evidence_bundle_ref)}",
        "",
        "### 一致性检查",
    ]
    check = revision_output.consistency_check
    report_lines.append("✓ 通过" if check.get("passed") else "✗ 失败")
    if not check.get("passed"):
        for issue in check.get("issues", []):
            report_lines.append(f"  - {issue}")

    report_lines.extend([
        "",
        "### 追踪信息",
        f"- 追踪ID: {revision_output.trace_id}",
        f"- 置信度: {revision_output.confidence_after_revision:.2f}",
        f"- 复核标志: {revision_output.review_flag}",
    ])
    return "\n".join(report_lines)


# ─── 关键词提取 ──────────────────────────────────────────────────

def match_target_keywords(raw_feedback: str) -> List[str]:
    """从用户反馈中提取关键词"""
    keywords = []

    quoted_pattern = r'「([^」]+)」|\"([^\"]+)\"'
    matches = re.findall(quoted_pattern, raw_feedback)
    for match in matches:
        text = match[0] if match[0] else match[1]
        keywords.append(text)

    words = raw_feedback.split()
    keywords.extend([w for w in words if len(w) >= 2])

    return keywords


# ─── 检查点（Checkpoint）—— 支持任务暂停/重做 (US-12) ──────────
_checkpoints: Dict[str, Dict[str, Any]] = {}

def save_checkpoint(target_id: str, step: int, state: Dict[str, Any]) -> str:
    """保存任务检查点

    Args:
        target_id: 目标 ID
        step: 当前完成的步骤编号
        state: 当前状态数据

    Returns:
        检查点 ID
    """
    cpid = f"cp_{target_id}_{datetime.now().strftime('%H%M%S')}"
    _checkpoints[cpid] = {
        "target_id": target_id,
        "step": step,
        "state": state,
        "timestamp": datetime.now().isoformat(),
        "status": "saved"
    }
    return cpid


def get_checkpoint(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """获取检查点"""
    return _checkpoints.get(checkpoint_id)


def resume_checkpoint(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """恢复检查点

    Returns:
        检查点状态（成功恢复后标记为 resumed）
    """
    cp = _checkpoints.get(checkpoint_id)
    if cp and cp.get("status") == "saved":
        cp["status"] = "resumed"
        cp["resumed_at"] = datetime.now().isoformat()
        return cp["state"]
    return None


def pause_task(task_id: str, checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """暂停任务并保存快照"""
    cp_id = save_checkpoint(task_id, checkpoint_data.get("step", 0), checkpoint_data)
    return {"task_id": task_id, "status": "paused", "checkpoint_id": cp_id}


def resume_task(task_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """恢复暂停的任务"""
    state = resume_checkpoint(checkpoint_id)
    if state:
        return {"task_id": task_id, "status": "resumed", "state": state}
    return None


# ─── 批量拆分 ────────────────────────────────────────────────────

def split_batch_input(raw_feedback: str, separator: str = "。") -> List[str]:
    """将包含多个目标的用户反馈拆分为独立条目

    Args:
        raw_feedback: 用户原始反馈（可能包含多个目标）
        separator: 拆分分隔符，默认句号

    Returns:
        拆分后的独立反馈列表（去空、去重复、前后 trim）

    这是 US-04「批量多目标拆分」和 RR-06「批量多目标拆分」的实现。
    """
    parts = [p.strip() for p in raw_feedback.split(separator) if p.strip()]
    seen = []
    result = []
    for p in parts:
        if p not in seen and len(p) >= 2:
            seen.append(p)
            result.append(p)
    return result


# ─── 核心原则检查（US-11 三条原则的硬约束）─────────────────────

def check_core_principles(output, raw_feedback: str, evidence_bundles: List[Any]) -> List[str]:
    """检查三条核心原则是否被违反

    原则 1：用户反馈降级为线索（不能直接作为修改指令）
    原则 2：证据检索必须下沉到具体责任人
    原则 3：找到证据后必须写入证据栏

    Returns:
        违反的原则 ID 列表
    """
    violations = []

    # 原则 1: 反馈降级 — 检查 output.user_note 是否标记为 hypothesis
    if output.user_note and "hypothesis:" not in str(output.user_note):
        violations.append("PRINCIPLE_1: 用户反馈未降级为 hypothesis")

    # 原则 2: 责任人下沉 — 检查 evidence 的责任链是否包含具体人名
    if evidence_bundles:
        for eb in evidence_bundles:
            if eb.responsibility_chain and len(eb.responsibility_chain) < 2:
                violations.append("PRINCIPLE_2: 证据责任链未下沉到具体责任人")

    # 原则 3: 证据写入栏 — 检查 writeback_patch 是否包含 evidence_updates
    if output.revision_action == "rewrite":
        patch = output.writeback_patch
        if not patch.get("evidence_updates"):
            violations.append("PRINCIPLE_3: 修订后证据未写入证据栏")

    return violations


if __name__ == "__main__":
    print("测试辅助函数...")
    feedback = "把「完成3个新品种注册」改成绿色"
    keywords = match_target_keywords(feedback)
    print(f"关键词: {keywords}")
    print(create_three_segment_output())
