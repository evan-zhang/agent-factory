#!/usr/bin/env python3
"""
验证修复效果的测试脚本
"""

import sys
import json
import os

# 加入 skill 根目录到 sys.path
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# 导入测试
try:
    from bp_reviser import (
        TargetStandard, EvidenceBundle, RevisionOutput,
        main_reviser_flow, locate_target
    )
    from helpers import (
        search_product_aliases, match_target_keywords
    )
    print("✓ 导入测试通过")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 测试 1: 传入 target_id 时能跳过搜索直接走主流程
print("\n测试 1: 传入 target_id 跳过搜索")
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

# 模拟一个主要证据
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

result = main_reviser_flow(
    sample_feedback,
    sample_target,
    sample_evidence,
    target_id="ORG_2026_Q1_REG_001"
)

print(f"revision_status: {result.revision_status}")
print(f"revision_action: {result.revision_action}")
print(f"blocked_reason: {result.blocked_reason}")

# 验证要求 2: 输出 revision_status 不是 blocked（当有充分证据时）
if result.revision_status != "blocked":
    print("✓ revision_status 不是 blocked（测试通过）")
else:
    print(f"✗ revision_status 是 blocked: {result.blocked_reason}")

# 验证要求 3: revision_action 有值
if result.revision_action:
    print(f"✓ revision_action 有值: {result.revision_action}")
else:
    print("✗ revision_action 无值")

# 测试 2: locate_target 支持直接传入 target_id
print("\n测试 2: locate_target 支持 target_id 参数")
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

# 测试 3: search_product_aliases 返回空列表
print("\n测试 3: search_product_aliases 返回空列表（不是假数据）")

keywords = match_target_keywords(sample_feedback)
candidates = search_product_aliases(keywords, "period_123", "group_456")

if len(candidates) == 0:
    print("✓ search_product_aliases 返回空列表")
else:
    print(f"✗ search_product_aliases 返回了 {len(candidates)} 个候选")

# 测试 4: Primary 判定包含 initiative_report
print("\n测试 4: Primary 判定包含 initiative_report")
evidence_bundle = EvidenceBundle(sample_evidence[0])
standard = TargetStandard(sample_target)
level = evidence_bundle.classify(standard)

if level == "primary":
    print(f"✓ initiative_report 被判定为 primary")
else:
    print(f"✗ initiative_report 判定为 {level}，应该是 primary")

print("\n所有测试完成！")
