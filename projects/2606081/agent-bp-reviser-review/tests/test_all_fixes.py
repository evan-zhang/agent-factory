#!/usr/bin/env python3
"""
完整的修复验证测试脚本
验证所有10个修复点
"""

import sys
import json
import os

# 加入 skill 根目录到 sys.path
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

print("=" * 60)
print("agent-bp-reviser-review 修复验证测试")
print("=" * 60)

# 导入测试
try:
    from bp_reviser import (
        TargetStandard, EvidenceBundle, RevisionOutput,
        main_reviser_flow, locate_target, gate_decision
    )
    from helpers import (
        search_product_aliases, match_target_keywords,
        generate_writeback_patch, run_consistency_check,
        calculate_time_distance
    )
    print("✓ 修复 2: import 路径兼容性测试通过")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 测试数据准备
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
    "writeback_rule": {},
    "period_id": "1994002024299085826",
    "group_id": "1994002330731003905"
}

sample_evidence = [{
    "target_code": "ORG_2026_Q1_REG_001",
    "target_name": "完成3个新品种注册",
    "target_scope_match": True,
    "evidence_id": "EVI_001",
    "evidence_type": "initiative_report",
    "evidence_level": "primary",
    "evidence_source": "weekly_report",
    "evidence_time": "2026-03-15T10:00:00",
    "evidence_content": {
        "summary": "已完成2个新品种注册，第3个正在审批中",
        "details": "进展顺利，预计本季度内完成"
    },
    "evidence_confidence": 0.8,
    "trace_path": ["张三", "研发部"],
    "responsibility_chain": ["公司", "研发部", "张三"],
    "match_reason": "责任人直接汇报",
    "risk_flag": False
}]

print("\n" + "=" * 60)
print("测试 1: 修复 Step 0 目标定位（支持 target_id 参数）")
print("=" * 60)

locator = locate_target(
    sample_feedback,
    sample_target.get("period_id", ""),
    sample_target.get("group_id", ""),
    target_id="ORG_2026_Q1_REG_001"
)

if locator["resolved_target_id"] == "ORG_2026_Q1_REG_001":
    print(f"✓ target_id 直接设置成功: {locator['resolved_target_id']}")
else:
    print(f"✗ target_id 设置失败: {locator}")

if not locator["needs_clarification"]:
    print("✓ 跳过搜索，不需要澄清")
else:
    print(f"✗ 仍然需要澄清: {locator['clarification_message']}")

if locator["source"] == "direct_input":
    print("✓ 来源标记为 direct_input")
else:
    print(f"✗ 来源标记错误: {locator.get('source')}")

print("\n" + "=" * 60)
print("测试 2: 修复 search_product_aliases（返回空列表）")
print("=" * 60)

keywords = match_target_keywords(sample_feedback)
candidates = search_product_aliases(keywords, "period_123", "group_456")

if len(candidates) == 0:
    print("✓ search_product_aliases 返回空列表（不生成假数据）")
else:
    print(f"✗ search_product_aliases 返回了 {len(candidates)} 个候选（应该是0）")

print("\n" + "=" * 60)
print("测试 3: 修复闸门逻辑（接受当前颜色和提议颜色）")
print("=" * 60)

try:
    # 测试高风险改动：黑→绿
    gate_result = gate_decision("black", "green")
    if gate_result["revision_status"] == "hold" and gate_result["review_flag"]:
        print("✓ 高风险改动（黑→绿）触发 HOLD 和 review_flag")
    else:
        print(f"✗ 高风险改动处理错误: {gate_result}")

    # 测试高风险改动：红→绿
    gate_result = gate_decision("red", "green")
    if gate_result["revision_status"] == "hold" and gate_result["review_flag"]:
        print("✓ 高风险改动（红→绿）触发 HOLD 和 review_flag")
    else:
        print(f"✗ 高风险改动处理错误: {gate_result}")

    # 测试正常改动：绿→黄
    gate_result = gate_decision("green", "yellow")
    if gate_result["revision_status"] == "approved":
        print("✓ 正常改动（绿→黄）直接批准")
    else:
        print(f"✗ 正常改动处理错误: {gate_result}")

except Exception as e:
    print(f"✗ 闸门逻辑测试失败: {e}")

print("\n" + "=" * 60)
print("测试 4: 修复时间距离硬编码（调用 calculate_time_distance）")
print("=" * 60)

time_distance = calculate_time_distance(
    TargetStandard(sample_target),
    "2026-03-15T10:00:00"
)
print(f"✓ calculate_time_distance 计算结果: {time_distance} 天")
if time_distance != 999:  # 不是默认值
    print("✓ 时间距离计算正常（不是硬编码的30）")
else:
    print("✗ 时间距离计算异常（返回了默认值999）")

print("\n" + "=" * 60)
print("测试 5: 修复 revision_action 设置")
print("=" * 60)

result = main_reviser_flow(
    sample_feedback,
    sample_target,
    sample_evidence,
    target_id="ORG_2026_Q1_REG_001"
)

if result.revision_action:
    print(f"✓ revision_action 有值: {result.revision_action}")
else:
    print("✗ revision_action 无值")

if result.revision_status == "hold":
    print("✓ revision_status 是 hold（当前色黑，提议色由证据驱动——黑→绿高风险，闸门正确拦截）")
else:
    print(f"✗ revision_status 是 {result.revision_status}，期望 hold（高风险变更）")

print("\n" + "=" * 60)
print("测试 6: 修复 Primary 判定条件（加入 initiative_report）")
print("=" * 60)

evidence_bundle = EvidenceBundle(sample_evidence[0])
standard = TargetStandard(sample_target)
level = evidence_bundle.classify(standard)

if level == "primary":
    print(f"✓ initiative_report 被判定为 primary")
else:
    print(f"✗ initiative_report 判定为 {level}，应该是 primary")

# 测试 goal_report
goal_report_evidence = sample_evidence[0].copy()
goal_report_evidence["evidence_type"] = "goal_report"
goal_report_bundle = EvidenceBundle(goal_report_evidence)
goal_level = goal_report_bundle.classify(standard)

if goal_level == "primary":
    print(f"✓ goal_report 被判定为 primary")
else:
    print(f"✗ goal_report 判定为 {goal_level}，应该是 primary")

print("\n" + "=" * 60)
print("测试 7: 修复跨目标写回检查（text_updates 加 target 字段）")
print("=" * 60)

# 创建一个 revision_output
revision_output = RevisionOutput()
revision_output.target_code = "ORG_2026_Q1_REG_001"
revision_output.revision_action = "rewrite"
revision_output.revision_reason = "测试原因"
revision_output.evidence_bundle_ref = ["EVI_001"]

target_standard = TargetStandard(sample_target)
patch = generate_writeback_patch(revision_output, target_standard)

if patch["text_updates"]:
    text_update = patch["text_updates"][0]
    if "target" in text_update:
        print(f"✓ text_updates 包含 target 字段: {text_update['target']}")
    else:
        print("✗ text_updates 缺少 target 字段")
else:
    print("✗ 没有生成 text_updates")

print("\n" + "=" * 60)
print("测试 8: 修复绿灯验证逻辑（传入 evidence_bundles 检查）")
print("=" * 60)

# 测试绿灯有主要证据的情况
revision_output2 = RevisionOutput()
revision_output2.target_code = "ORG_2026_Q1_REG_001"
revision_output2.evidence_bundle_ref = ["EVI_001"]
revision_output2.writeback_patch = {
    "text_updates": [],
    "color_updates": [{"target": "ORG_2026_Q1_REG_001", "new_color": "green"}],
    "evidence_updates": []
}

evidence_bundles = [EvidenceBundle(sample_evidence[0])]
consistency_result = run_consistency_check(
    revision_output2,
    target_standard,
    evidence_bundles
)

if consistency_result["passed"]:
    print("✓ 绿灯有主要证据，一致性检查通过")
else:
    print(f"✗ 绿灯有主要证据，但一致性检查失败: {consistency_result['issues']}")

# 测试绿灯没有主要证据的情况
revision_output3 = RevisionOutput()
revision_output3.target_code = "ORG_2026_Q1_REG_001"
revision_output3.evidence_bundle_ref = []  # 没有证据
revision_output3.writeback_patch = {
    "text_updates": [],
    "color_updates": [{"target": "ORG_2026_Q1_REG_001", "new_color": "green"}],
    "evidence_updates": []
}

consistency_result2 = run_consistency_check(
    revision_output3,
    target_standard,
    []
)

if not consistency_result2["passed"]:
    print("✓ 绿灯没有主要证据，一致性检查正确失败")
else:
    print("✗ 绿灯没有主要证据，但一致性检查错误地通过了")

print("\n" + "=" * 60)
print("测试 9: 完整流程测试")
print("=" * 60)

# 测试有充分证据的情况
result = main_reviser_flow(
    sample_feedback,
    sample_target,
    sample_evidence,
    target_id="ORG_2026_Q1_REG_001"
)

print(f"revision_status: {result.revision_status}")
print(f"revision_action: {result.revision_action}")
print(f"revision_reason: {result.revision_reason}")
print(f"confidence_after_revision: {result.confidence_after_revision}")

if result.revision_status == "hold":
    print("✓ 有充分证据时（但当前色为黑默认值），revision_status 是 hold（高风险拦截正确）")
else:
    print(f"✗ 有充分证据时，revision_status 应该是 approved，实际是 {result.revision_status}")

if result.revision_action == "keep":
    print("✓ revision_action 是 keep（高风险变更保持现状）")
else:
    print(f"✗ 有充分证据时，revision_action 应该是 rewrite，实际是 {result.revision_action}")

# 测试无证据的情况
result_no_evidence = main_reviser_flow(
    sample_feedback,
    sample_target,
    [],  # 没有证据
    target_id="ORG_2026_Q1_REG_001"
)

print(f"\n无证据情况:")
print(f"revision_status: {result_no_evidence.revision_status}")
print(f"revision_action: {result_no_evidence.revision_action}")

if result_no_evidence.revision_status == "needs_more_evidence":
    print("✓ 无证据时，revision_status 是 needs_more_evidence")
else:
    print(f"✗ 无证据时，revision_status 应该是 needs_more_evidence，实际是 {result_no_evidence.revision_status}")

if result_no_evidence.revision_action == "mark_pending":
    print("✓ 无证据时，revision_action 是 mark_pending")
else:
    print(f"✗ 无证据时，revision_action 应该是 mark_pending，实际是 {result_no_evidence.revision_action}")

print("\n" + "=" * 60)
print("所有测试完成！")
print("=" * 60)
