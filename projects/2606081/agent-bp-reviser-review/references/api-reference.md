# API Reference

## 输入接口

### TargetInput

用户提供的原始输入。

```json
{
  "raw_feedback": "用户的自然语言反馈",
  "period_id": "周期标识（可选）",
  "group_id": "集团标识（可选）",
  "user_context": {
    "user_id": "用户ID",
    "role": "用户角色",
    "permissions": ["权限列表"]
  }
}
```

### TargetStandardInput

标准注入输入。

```json
{
  "target_code": "目标编码",
  "target_name": "目标名称",
  "layer": "goal|result|initiative",
  "bp_type": "organization|personal",
  "period": "周期",
  "measurements": ["指标列表"],
  "source": "来源系统",
  "scope": "适用范围",
  "effective_from": "生效日期",
  "version": "版本号",
  "conflict_policy": "block|prefer_explicit|prefer_latest|fallback_to_hold",
  "owner": "责任人",
  "responsibility_chain": ["责任链"],
  "evidence_hint": ["证据提示"],
  "status_rule": "状态规则",
  "writeback_rule": "写回规则"
}
```

## 输出接口

### TargetLocatorOutput

Step 0 的输出。

```json
{
  "raw_feedback": "原始反馈",
  "period_id": "周期ID",
  "group_id": "集团ID",
  "candidate_targets": [
    {
      "target_id": "目标ID",
      "target_name": "目标名称",
      "match_reason": "匹配原因",
      "confidence": 0.95
    }
  ],
  "resolved_target_id": "锁定目标ID（唯一匹配时）",
  "needs_clarification": true,
  "clarification_message": "需要用户确认的消息"
}
```

### RevisionOutput

修订最终输出。

```json
{
  "target_code": "目标编码",
  "target_name": "目标名称",
  "standard_applied": "应用的标准版本",
  "revision_status": "approved|blocked|hold|needs_more_evidence",
  "revision_action": "rewrite|keep|revert|mark_pending",
  "revision_reason": "修订原因",
  "blocked_reason": "阻断原因（如果被阻断）",
  "target_color": "black|red|yellow|green",
  "requires_recompute": false,
  "evidence_bundle_ref": ["证据引用"],
  "consistency_check": {
    "passed": true,
    "issues": []
  },
  "writeback_patch": {
    "text_updates": [
      {
        "field": "字段名",
        "old_value": "旧值",
        "new_value": "新值"
      }
    ],
    "color_updates": [
      {
        "target": "目标",
        "old_color": "旧颜色",
        "new_color": "新颜色"
      }
    ],
    "evidence_updates": [
      {
        "evidence_id": "证据ID",
        "action": "add|remove|update",
        "details": {}
      }
    ]
  },
  "review_flag": false,
  "recompute_scope": "重新计算范围",
  "trace_id": "追踪ID",
  "confidence_after_revision": 0.9,
  "user_note": "用户备注",
  "gate_decision": "闸门决策说明",
  "principle_violations": ["违反的核心原则"],
  "three_segment_output": "三段式输出（无证据时）",
  "session_memory_triggered": ["已纠正规则ID"],
  "checkpoint_id": "检查点ID"
}
```

## 中间输出

### EvidenceBundleOutput

Step 4 的输出。

```json
{
  "target_code": "目标编码",
  "target_name": "目标名称",
  "target_scope_match": true,
  "evidence_items": [
    {
      "evidence_id": "证据ID",
      "evidence_type": "goal_report|result_report|initiative_report|system_record|document_record|manual_confirmation",
      "evidence_level": "primary|secondary|background|insufficient",
      "evidence_source": "证据来源",
      "evidence_time": "证据时间",
      "evidence_content": "证据内容",
      "evidence_confidence": 0.85,
      "trace_path": ["追溯路径"],
      "responsibility_chain": ["责任链"],
      "match_reason": "匹配原因",
      "exclude_reason": "排除原因（如果被排除）",
      "scope_note": "范围备注",
      "role_hint": "角色提示",
      "writeback_hint": "写回提示",
      "risk_flag": false
    }
  ],
  "summary": {
    "total_count": 10,
    "primary_count": 5,
    "secondary_count": 3,
    "background_count": 2,
    "insufficient_count": 0,
    "overall_confidence": 0.82
  }
}
```

## 错误输出

### ErrorResponse

错误响应格式。

```json
{
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "error_details": {
    "step": "出错的步骤",
    "input": "导致错误的输入",
    "suggested_action": "建议的操作"
  },
  "timestamp": "2026-06-06T10:00:00Z"
}
```

## 常见错误码

- `TARGET_NOT_FOUND`: 目标未找到
- `STANDARD_INVALID`: 标准无效或不完整
- `EVIDENCE_INSUFFICIENT`: 证据不足
- `CONFLICT_DETECTED`: 标准冲突
- `CROSS_TARGET_WRITEBACK`: 跨目标写回尝试（被阻断）
- `CONSISTENCY_CHECK_FAILED`: 一致性校验失败
- `GATE_BLOCKED`: 修订闸门阻断
- `PERMISSION_DENIED`: 权限不足
