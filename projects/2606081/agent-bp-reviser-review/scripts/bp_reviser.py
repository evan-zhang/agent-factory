#!/usr/bin/env python3
"""
BP 目标修订主要处理流程
单目标证据驱动复核修订控制器
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# 兼容两种运行方式
try:
    from .helpers import (
        match_target_keywords,
        search_product_aliases,
        calculate_evidence_confidence,
        generate_writeback_patch,
        run_consistency_check,
        generate_validation_report,
        calculate_time_distance,
        create_three_segment_output,
        save_checkpoint,
        get_checkpoint,
        resume_checkpoint,
        pause_task,
        resume_task,
        split_batch_input,
        remember_corrected_rule,
        get_session_memory,
        apply_session_memory,
        clear_session_memory,
        check_core_principles,
        search_tasks_by_name,
        get_task_tree,
        get_goal_detail,
        detect_major_defects,
        in_responsibility_chain,
    )
except ImportError:
    from helpers import (
        match_target_keywords,
        search_product_aliases,
        calculate_evidence_confidence,
        generate_writeback_patch,
        run_consistency_check,
        generate_validation_report,
        calculate_time_distance,
        create_three_segment_output,
        save_checkpoint,
        get_checkpoint,
        resume_checkpoint,
        pause_task,
        resume_task,
        split_batch_input,
        remember_corrected_rule,
        get_session_memory,
        apply_session_memory,
        clear_session_memory,
        check_core_principles,
        search_tasks_by_name,
        get_task_tree,
        get_goal_detail,
        detect_major_defects,
        in_responsibility_chain,
    )


class LayerEnum(str, Enum):
    GOAL = "goal"
    RESULT = "result"
    INITIATIVE = "initiative"


class BPTypeEnum(str, Enum):
    ORGANIZATION = "organization"
    PERSONAL = "personal"


class EvidenceLevelEnum(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKGROUND = "background"
    INSUFFICIENT = "insufficient"


class RevisionStatusEnum(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    HOLD = "hold"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


class RevisionActionEnum(str, Enum):
    REWRITE = "rewrite"
    KEEP = "keep"
    REVERT = "revert"
    MARK_PENDING = "mark_pending"


class TargetStandard:
    """目标标准包"""

    def __init__(self, data: Dict[str, Any]):
        self.target_code = data.get("target_code")
        self.target_name = data.get("target_name")
        self.layer = data.get("layer")
        self.bp_type = data.get("bp_type")
        self.period = data.get("period", {})
        self.measurements = data.get("measurements", [])
        self.source = data.get("source")
        self.scope = data.get("scope")
        self.effective_from = data.get("effective_from")
        self.version = data.get("version")
        self.conflict_policy = data.get("conflict_policy")
        self.owner = data.get("owner")
        self.responsibility_chain = data.get("responsibility_chain", [])
        self.evidence_hint = data.get("evidence_hint", [])
        self.status_rule = data.get("status_rule", {})
        self.writeback_rule = data.get("writeback_rule", {})

    def validate(self) -> tuple[bool, List[str]]:
        """校验标准完整性（schema 全部 16 个必填字段）"""
        errors = []
        required_fields = [
            "target_code", "target_name", "layer", "bp_type",
            "period", "measurements", "source", "scope",
            "effective_from", "version", "conflict_policy", "owner",
            "responsibility_chain", "evidence_hint", "status_rule",
            "writeback_rule"
        ]
        # 允许空列表/空字典的字段（有默认值但属于结构定义）
        allow_empty = {"measurements", "evidence_hint", "status_rule", "writeback_rule"}
        for field in required_fields:
            val = getattr(self, field, None)
            if val is None:
                errors.append(f"缺少必填字段: {field}")
            elif isinstance(val, (list, dict)) and len(val) == 0 and field not in allow_empty:
                errors.append(f"缺少必填字段: {field}")
        if self.layer not in [e.value for e in LayerEnum]:
            errors.append(f"无效的 layer: {self.layer}")
        if self.bp_type not in [e.value for e in BPTypeEnum]:
            errors.append(f"无效的 bp_type: {self.bp_type}")
        valid_conflict_policies = ["block", "prefer_explicit", "prefer_latest", "fallback_to_hold"]
        if self.conflict_policy and self.conflict_policy not in valid_conflict_policies:
            errors.append(f"无效的 conflict_policy: {self.conflict_policy}")
        if len(self.responsibility_chain) == 0:
            errors.append("责任链不能为空")
        if self.owner and self.responsibility_chain and self.owner != self.responsibility_chain[-1]:
            errors.append(f"owner ({self.owner}) 必须是 responsibility_chain 的末尾元素 ({self.responsibility_chain[-1]})")
        return len(errors) == 0, errors


class EvidenceBundle:
    """证据包"""

    def __init__(self, data: Dict[str, Any]):
        self.target_code = data.get("target_code")
        self.target_name = data.get("target_name")
        self.target_scope_match = data.get("target_scope_match", False)
        self.evidence_id = data.get("evidence_id")
        self.evidence_type = data.get("evidence_type")
        self.evidence_level = data.get("evidence_level")
        self.evidence_source = data.get("evidence_source")
        self.evidence_time = data.get("evidence_time")
        self.evidence_content = data.get("evidence_content", {})
        self.evidence_confidence = data.get("evidence_confidence", 0.0)
        self.trace_path = data.get("trace_path", [])
        self.responsibility_chain = data.get("responsibility_chain", [])
        self.match_reason = data.get("match_reason")
        self.exclude_reason = data.get("exclude_reason")
        self.scope_note = data.get("scope_note")
        self.role_hint = data.get("role_hint")
        self.writeback_hint = data.get("writeback_hint")
        self.risk_flag = data.get("risk_flag", False)

        # B5: 证据时间不能晚于当前时间
        if self.evidence_time:
            try:
                from datetime import datetime as _dt
                if _dt.fromisoformat(self.evidence_time) > _dt.now():
                    self.exclude_reason = f"证据时间晚于当前时间: {self.evidence_time}"
                    self.evidence_level = "insufficient"
            except (ValueError, TypeError):
                pass

    def classify(self, target_standard: 'TargetStandard') -> str:
        """证据层级分类

        判定顺序：责任链匹配 → primary → background → secondary → insufficient
        同时调用 detect_major_defects 自动标记 risk_flag（ER-07）
        """
        # 自动检测重大缺陷（ER-07）
        if not self.risk_flag and self.evidence_content:
            defects = detect_major_defects(self.evidence_content)
            if defects:
                self.risk_flag = True

        # 检查责任链匹配（使用 helpers.in_responsibility_chain）
        if not in_responsibility_chain(self, target_standard):
            return EvidenceLevelEnum.INSUFFICIENT

        # Primary: 目标责任人直接汇报
        if self.responsibility_chain and \
           self.responsibility_chain[-1] == target_standard.owner:
            if self.evidence_type in ["goal_report", "result_report", "initiative_report"]:
                return EvidenceLevelEnum.PRIMARY

        # Background: 法务/投融资/泛背景材料
        if self.evidence_type in ["document_record"]:
            return EvidenceLevelEnum.BACKGROUND

        # Secondary: 有责任链但非责任人直接汇报
        if self.responsibility_chain:
            return EvidenceLevelEnum.SECONDARY

        # Insufficient: 兜底
        return EvidenceLevelEnum.INSUFFICIENT


class RevisionOutput:
    """修订输出"""

    def __init__(self):
        self.target_code: Optional[str] = None
        self.target_name: Optional[str] = None
        self.standard_applied: Optional[str] = None
        self.revision_status: Optional[str] = None
        self.revision_action: Optional[str] = None
        self.revision_reason: Optional[str] = None
        self.blocked_reason: Optional[str] = None
        self.target_color: Optional[str] = None
        self.requires_recompute: bool = False
        self.evidence_bundle_ref: List[str] = []
        self.consistency_check: Dict[str, Any] = {"passed": False, "issues": []}
        self.writeback_patch: Dict[str, Any] = {
            "text_updates": [],
            "color_updates": [],
            "evidence_updates": []
        }
        self.review_flag: bool = False
        self.recompute_scope: Optional[str] = None
        self.trace_id: Optional[str] = None
        self.confidence_after_revision: float = 0.0
        self.user_note: Optional[str] = None
        self.gate_decision: Optional[str] = None
        self.principle_violations: List[str] = []
        self.three_segment_output: Optional[str] = None
        self.session_memory_triggered: List[str] = []
        self.checkpoint_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target_code": self.target_code,
            "target_name": self.target_name,
            "standard_applied": self.standard_applied,
            "revision_status": str(self.revision_status) if self.revision_status else None,
            "revision_action": str(self.revision_action) if self.revision_action else None,
            "revision_reason": self.revision_reason,
            "blocked_reason": self.blocked_reason,
            "target_color": self.target_color,
            "requires_recompute": self.requires_recompute,
            "evidence_bundle_ref": self.evidence_bundle_ref,
            "consistency_check": self.consistency_check,
            "writeback_patch": self.writeback_patch,
            "review_flag": self.review_flag,
            "recompute_scope": self.recompute_scope,
            "trace_id": self.trace_id,
            "confidence_after_revision": round(self.confidence_after_revision, 4),
            "user_note": self.user_note,
            "gate_decision": self.gate_decision,
            "principle_violations": self.principle_violations,
            "three_segment_output": self.three_segment_output,
            "session_memory_triggered": self.session_memory_triggered,
            "checkpoint_id": self.checkpoint_id,
        }

    def set_three_segment_if_needed(self, primary_count: int):
        """无主要证据时设置三段式输出，有证据时清除"""
        if primary_count == 0:
            self.three_segment_output = create_three_segment_output()
        else:
            self.three_segment_output = None


def locate_target(raw_feedback: str, period_id: str, group_id: str,
                  target_id: Optional[str] = None) -> Dict[str, Any]:
    """Step 0: 目标定位

    使用 BP API 的 searchByName（2.11）和 getSimpleTree（2.4）进行关键词搜索，
    支持通过 target_id 直接跳过搜索。

    Returns:
        目标定位结果字典
    """
    if target_id:
        return {
            "raw_feedback": raw_feedback,
            "period_id": period_id,
            "group_id": group_id,
            "candidate_targets": [],
            "resolved_target_id": target_id,
            "needs_clarification": False,
            "clarification_message": None,
            "source": "direct_input"
        }

    keywords = match_target_keywords(raw_feedback)
    candidates = search_product_aliases(keywords, period_id, group_id)

    locator = {
        "raw_feedback": raw_feedback,
        "period_id": period_id,
        "group_id": group_id,
        "candidate_targets": candidates,
        "resolved_target_id": None,
        "needs_clarification": False,
        "clarification_message": None,
        "source": "keyword_search"
    }

    if len(candidates) == 0:
        locator["clarification_message"] = "未找到匹配目标，请提供更多信息或直接指定 target_id"
        locator["needs_clarification"] = True
    elif len(candidates) == 1:
        locator["resolved_target_id"] = candidates[0]["target_id"]
    else:
        locator["clarification_message"] = f"找到 {len(candidates)} 个候选目标，请确认"
        locator["needs_clarification"] = True

    return locator


def inject_standard(target_input: Dict[str, Any]) -> TargetStandard:
    """Step 1: 接收目标与标准注入

    包含冲突策略执行（GR-02 / B3）：
    - block: 阻断修订
    - prefer_explicit: 要求用户提供显式值
    - prefer_latest: 使用最新版本（默认行为）
    - fallback_to_hold: 冲突时回退到 hold
    """
    standard = TargetStandard(target_input)
    is_valid, errors = standard.validate()
    if not is_valid:
        raise ValueError(f"标准无效: {', '.join(errors)}")

    # 冲突策略处理（B3）
    conflict_policy = standard.conflict_policy
    existing_version = target_input.get("_existing_version")
    if existing_version and existing_version != standard.version:
        if conflict_policy == "block":
            raise ValueError(f"版本冲突（block策略）: 现有={existing_version}, 注入={standard.version}")
        # prefer_latest / prefer_explicit / fallback_to_hold: 继续使用注入版本

    return standard


def downgrade_user_feedback(raw_feedback: str) -> Dict[str, Any]:
    """Step 2: 降级用户反馈"""
    return {
        "hypothesis": raw_feedback,
        "status": "pending_verification",
        "search_tasks": [
            {
                "task_type": "search_evidence",
                "keywords": match_target_keywords(raw_feedback),
                "priority": "high"
            }
        ]
    }


def search_responsibility_chain(target_standard: TargetStandard) -> List[Dict[str, Any]]:
    """Step 3: 责任链检索"""
    chain = target_standard.responsibility_chain
    concrete_owner = chain[-1] if chain else None
    evidence_search_tasks = []
    for report_type in ["weekly", "biweekly", "monthly", "special"]:
        evidence_search_tasks.append({
            "owner": concrete_owner,
            "report_type": report_type,
            "target_code": target_standard.target_code,
            "period": target_standard.period
        })
    return evidence_search_tasks


def classify_evidence(evidence_items: List[Dict],
                      target_standard: TargetStandard) -> List[EvidenceBundle]:
    """Step 4: 证据语义分层"""
    bundles = []
    for item in evidence_items:
        bundle = EvidenceBundle(item)
        bundle.evidence_level = bundle.classify(target_standard)
        bundle.evidence_confidence = calculate_evidence_confidence(bundle, target_standard)
        bundles.append(bundle)
    return bundles


def determine_light_color(target_standard: TargetStandard,
                          evidence_bundles: List[EvidenceBundle]) -> Dict[str, Any]:
    """Step 5: 独立判灯/判定"""
    primary_evidence = [b for b in evidence_bundles
                        if b.evidence_level == EvidenceLevelEnum.PRIMARY]

    if len(primary_evidence) == 0:
        return {"color": "black", "reason": "无有效证据"}

    time_distance = 999
    if primary_evidence:
        latest_evidence = max(primary_evidence, key=lambda e: e.evidence_time or "")
        if latest_evidence.evidence_time:
            time_distance = calculate_time_distance(target_standard,
                                                     latest_evidence.evidence_time)

    has_major_defects = any(b.risk_flag for b in primary_evidence)

    if time_distance < 30 and not has_major_defects:
        return {"color": "green", "reason": "时间临近，无重大缺陷"}
    elif time_distance < 90 and not has_major_defects:
        return {"color": "yellow", "reason": "时间中等或无重大缺陷"}
    else:
        return {"color": "red", "reason": "时间较远或存在重大缺陷"}


def gate_decision(current_color: str, proposed_color: str) -> Dict[str, Any]:
    """Step 6: 修订闸门

    Args:
        current_color: 系统当前灯色
        proposed_color: 提议的新灯色（来自 determine_light_color）

    Returns:
        闸门决策结果
    """
    # 高风险改动检查（黑→绿、红→绿）
    if current_color in ["black", "red"] and proposed_color == "green":
        return {
            "revision_status": RevisionStatusEnum.HOLD,
            "review_flag": True,
            "gate_decision": f"高风险改动（{current_color}→绿），需要人工复核"
        }

    # 当前色与提议色相同 → 正常批准
    if current_color == proposed_color:
        return {
            "revision_status": RevisionStatusEnum.APPROVED,
            "review_flag": False,
            "gate_decision": "批准修订"
        }

    # 其他普通改动，非高风险
    return {
        "revision_status": RevisionStatusEnum.APPROVED,
        "review_flag": False,
        "gate_decision": f"批准修订 ({current_color}→{proposed_color})"
    }


def apply_writeback_patch(revision_output: RevisionOutput,
                          target_standard: TargetStandard) -> None:
    """Step 7: 调用 helpers 生成写回补丁并写入 output"""
    patch = generate_writeback_patch(revision_output, target_standard)
    revision_output.writeback_patch = patch


def run_flow_consistency_check(revision_output: RevisionOutput,
                               target_standard: TargetStandard,
                               evidence_bundles: List[EvidenceBundle]) -> None:
    """Step 8: 调用 helpers 做一致性校验并阻断不合规输出"""
    result = run_consistency_check(revision_output, target_standard, evidence_bundles)
    revision_output.consistency_check = result
    if not result["passed"]:
        revision_output.revision_status = RevisionStatusEnum.BLOCKED
        revision_output.blocked_reason = f"一致性校验失败: {', '.join(result['issues'])}"


def run_session_memory_step(revision_output: RevisionOutput) -> None:
    """Step 9: 应用会话规则记忆"""
    triggered = apply_session_memory(revision_output, None)
    revision_output.session_memory_triggered = triggered
    if triggered:
        note = f"本次应用了 {len(triggered)} 条已纠正规则"
        if revision_output.user_note:
            revision_output.user_note += f" | {note}"
        else:
            revision_output.user_note = note


def run_principle_check(revision_output: RevisionOutput,
                        raw_feedback: str,
                        evidence_bundles: List[EvidenceBundle]) -> None:
    """编码核心原则为硬约束（US-11 三条原则）"""
    violations = check_core_principles(revision_output, raw_feedback, evidence_bundles)
    revision_output.principle_violations = violations
    if violations:
        if revision_output.revision_status in [
            RevisionStatusEnum.APPROVED, RevisionStatusEnum.HOLD
        ]:
            revision_output.revision_status = RevisionStatusEnum.BLOCKED
            revision_output.blocked_reason = f"违反核心原则: {'; '.join(violations)}"


def main_reviser_flow(raw_feedback: str,
                      target_input: Dict[str, Any],
                      evidence_items: List[Dict],
                      target_id: Optional[str] = None,
                      current_color: str = "black") -> RevisionOutput:
    """主要修订流程

    Args:
        raw_feedback: 用户原始反馈
        target_input: 目标标准输入
        evidence_items: 证据项列表
        target_id: 可选，跳过 keyword 搜索直接锁定目标
        current_color: 系统当前灯色（default="black"）

    Returns:
        修订输出结果
    """
    output = RevisionOutput()

    # Step 0: 目标定位
    locator = locate_target(
        raw_feedback,
        target_input.get("period_id", ""),
        target_input.get("group_id", ""),
        target_id=target_id
    )
    if locator["needs_clarification"]:
        output.revision_status = RevisionStatusEnum.BLOCKED
        output.blocked_reason = locator["clarification_message"]
        return output

    # Step 1: 标准注入
    target_standard = inject_standard(target_input)
    output.target_code = target_standard.target_code
    output.target_name = target_standard.target_name
    output.standard_applied = target_standard.version

    # Step 2: 降级用户反馈
    feedback_task = downgrade_user_feedback(raw_feedback)
    output.user_note = f"hypothesis: {feedback_task['hypothesis']}"

    # Step 3: 责任链检索
    search_tasks = search_responsibility_chain(target_standard)
    if search_tasks:
        report_types = [t["report_type"] for t in search_tasks]
        output.recompute_scope = f"责任链搜索: {','.join(report_types)}"

    # Step 4: 证据分层
    evidence_bundles = classify_evidence(evidence_items, target_standard)
    output.evidence_bundle_ref = [b.evidence_id for b in evidence_bundles]

    # Step 5: 判灯
    primary_count = len([b for b in evidence_bundles
                         if b.evidence_level == EvidenceLevelEnum.PRIMARY])
    light_result = determine_light_color(target_standard, evidence_bundles)
    proposed_color = light_result["color"]
    output.target_color = proposed_color

    # 无主要证据 → 三段式输出 (US-06)
    output.set_three_segment_if_needed(primary_count)

    # Step 6: 闸门决策
    gate_result = gate_decision(current_color, proposed_color)
    output.revision_status = gate_result["revision_status"]
    output.review_flag = gate_result["review_flag"]
    output.gate_decision = gate_result["gate_decision"]

    # 设置 revision_action
    if output.revision_status == RevisionStatusEnum.APPROVED:
        if primary_evidence := [b for b in evidence_bundles
                                if b.evidence_level == EvidenceLevelEnum.PRIMARY]:
            output.revision_action = RevisionActionEnum.REWRITE
            output.revision_reason = light_result["reason"]
        else:
            output.revision_action = RevisionActionEnum.MARK_PENDING
            output.revision_reason = "等待证据补充"
    elif output.revision_status == RevisionStatusEnum.NEEDS_MORE_EVIDENCE:
        output.revision_action = RevisionActionEnum.MARK_PENDING
        output.revision_reason = "需要更多证据"
    elif output.revision_status == RevisionStatusEnum.HOLD:
        output.revision_action = RevisionActionEnum.KEEP
        output.revision_reason = "高风险改动，保持当前状态"
    elif output.revision_status == RevisionStatusEnum.BLOCKED:
        output.revision_action = RevisionActionEnum.REVERT
        output.revision_reason = "修订被阻断"

    # Step 7: 写回联动
    if output.revision_status == RevisionStatusEnum.APPROVED:
        apply_writeback_patch(output, target_standard)
        run_flow_consistency_check(output, target_standard, evidence_bundles)

    # Step 8（后置）: 核心原则检查 (US-11)
    run_principle_check(output, raw_feedback, evidence_bundles)

    # Step 9: 会话规则记忆
    run_session_memory_step(output)

    # 保存检查点
    output.checkpoint_id = save_checkpoint(
        target_standard.target_code, 9,
        {"revision_status": str(output.revision_status),
         "proposed_color": proposed_color,
         "current_color": current_color}
    )

    # 追踪ID & 置信度
    output.trace_id = f"trace_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if primary_evidence := [b for b in evidence_bundles
                            if b.evidence_level == EvidenceLevelEnum.PRIMARY]:
        avg_confidence = sum(b.evidence_confidence for b in primary_evidence) / len(primary_evidence)
        output.confidence_after_revision = avg_confidence

    return output


if __name__ == "__main__":
    sample_feedback = "把「完成3个新品种注册」改成绿色"
    sample_target = {
        "target_code": "ORG_2026_Q1_REG_001",
        "target_name": "完成3个新品种注册",
        "layer": "goal",
        "bp_type": "organization",
        "period": {"start": "2026-01-01", "end": "2026-03-31"},
        "source": "BP_System",
        "scope": "全公司",
        "effective_from": "2026-01-01",
        "version": "1.0.0",
        "conflict_policy": "prefer_latest",
        "owner": "张三",
        "responsibility_chain": ["公司", "研发部", "张三"],
        "evidence_hint": [],
        "status_rule": {},
        "writeback_rule": {}
    }
    sample_evidence = []
    result = main_reviser_flow(sample_feedback, sample_target, sample_evidence)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
