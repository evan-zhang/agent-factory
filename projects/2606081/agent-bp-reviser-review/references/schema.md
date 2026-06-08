# 完整 JSON Schema 定义

## TargetStandard（目标标准包）

```json
{
  "type": "object",
  "description": "BP 目标的标准定义，包含目标的所有元数据和规则",
  "required": [
    "target_code",
    "target_name",
    "layer",
    "bp_type",
    "period",
    "measurements",
    "source",
    "scope",
    "effective_from",
    "version",
    "conflict_policy",
    "owner",
    "responsibility_chain",
    "evidence_hint",
    "status_rule",
    "writeback_rule"
  ],
  "properties": {
    "target_code": {
      "type": "string",
      "description": "目标唯一编码",
      "pattern": "^[A-Z0-9_-]+$",
      "example": "ORG_2026_Q1_REG_001"
    },
    "target_name": {
      "type": "string",
      "description": "目标名称",
      "example": "完成3个新品种注册"
    },
    "layer": {
      "type": "string",
      "enum": ["goal", "result", "initiative"],
      "description": "目标层级：goal(目标), result(结果), initiative(举措)"
    },
    "bp_type": {
      "type": "string",
      "enum": ["organization", "personal"],
      "description": "BP 类型：organization(组织), personal(个人)"
    },
    "period": {
      "type": "object",
      "description": "周期",
      "properties": {
        "start": {"type": "string", "format": "date"},
        "end": {"type": "string", "format": "date"}
      }
    },
    "measurements": {
      "type": "array",
      "description": "指标列表",
      "items": {
        "type": "object",
        "properties": {
          "metric": {"type": "string"},
          "target": {"type": "number"},
          "current": {"type": "number"}
        }
      }
    },
    "source": {
      "type": "string",
      "description": "来源系统",
      "example": "BP_Management_System"
    },
    "scope": {
      "type": "string",
      "description": "适用范围",
      "example": "全公司"
    },
    "effective_from": {
      "type": "string",
      "format": "date",
      "description": "生效日期"
    },
    "version": {
      "type": "string",
      "description": "版本号",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "example": "1.0.0"
    },
    "conflict_policy": {
      "type": "string",
      "enum": ["block", "prefer_explicit", "prefer_latest", "fallback_to_hold"],
      "description": "冲突策略：block(阻断), prefer_explicit(优先显式), prefer_latest(优先最新), fallback_to_hold(回退到暂停)"
    },
    "owner": {
      "type": "string",
      "description": "责任人",
      "example": "张三"
    },
    "responsibility_chain": {
      "type": "array",
      "description": "责任链（从上到下）",
      "items": {"type": "string"},
      "example": ["公司", "研发部", "张三"]
    },
    "evidence_hint": {
      "type": "array",
      "description": "证据提示",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "source": {"type": "string"},
          "keywords": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "status_rule": {
      "type": "object",
      "description": "状态规则",
      "properties": {
        "green_threshold": {"type": "number"},
        "yellow_threshold": {"type": "number"},
        "red_threshold": {"type": "number"}
      }
    },
    "writeback_rule": {
      "type": "object",
      "description": "写回规则",
      "properties": {
        "sync_color": {"type": "boolean"},
        "sync_evidence": {"type": "boolean"},
        "allow_cross_target": {"type": "boolean"}
      }
    }
  }
}
```

---

## EvidenceBundle（证据包）

```json
{
  "type": "object",
  "description": "目标相关的证据集合",
  "required": [
    "target_code",
    "target_name",
    "target_scope_match",
    "evidence_id",
    "evidence_type",
    "evidence_level",
    "evidence_source",
    "evidence_time",
    "evidence_content",
    "evidence_confidence"
  ],
  "properties": {
    "target_code": {
      "type": "string",
      "description": "目标编码"
    },
    "target_name": {
      "type": "string",
      "description": "目标名称"
    },
    "target_scope_match": {
      "type": "boolean",
      "description": "目标范围匹配"
    },
    "evidence_id": {
      "type": "string",
      "description": "证据唯一ID",
      "pattern": "^(ev_|EVI_)[0-9]+$"
    },
    "evidence_type": {
      "type": "string",
      "enum": ["goal_report", "result_report", "initiative_report", "system_record", "document_record", "manual_confirmation"],
      "description": "证据类型"
    },
    "evidence_level": {
      "type": "string",
      "enum": ["primary", "secondary", "background", "insufficient"],
      "description": "证据层级：primary(主要), secondary(次要), background(背景), insufficient(不足)"
    },
    "evidence_source": {
      "type": "string",
      "description": "证据来源",
      "example": "周报-2026-W23"
    },
    "evidence_time": {
      "type": "string",
      "format": "date-time",
      "description": "证据时间"
    },
    "evidence_content": {
      "type": "object",
      "description": "证据内容",
      "properties": {
        "summary": {"type": "string"},
        "details": {"type": "object"},
        "attachments": {"type": "array", "items": {"type": "string"}}
      }
    },
    "evidence_confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "证据置信度（0-1）"
    },
    "trace_path": {
      "type": "array",
      "description": "追溯路径",
      "items": {"type": "string"}
    },
    "responsibility_chain": {
      "type": "array",
      "description": "证据责任链",
      "items": {"type": "string"}
    },
    "match_reason": {
      "type": "string",
      "description": "匹配原因"
    },
    "exclude_reason": {
      "type": "string",
      "description": "排除原因（如果被排除）"
    },
    "scope_note": {
      "type": "string",
      "description": "范围备注"
    },
    "role_hint": {
      "type": "string",
      "description": "角色提示"
    },
    "writeback_hint": {
      "type": "string",
      "description": "写回提示"
    },
    "risk_flag": {
      "type": "boolean",
      "description": "风险标志",
      "default": false
    }
  }
}
```

---

## RevisionOutput（修订输出）

```json
{
  "type": "object",
  "description": "修订操作的结果输出",
  "required": [
    "target_code",
    "target_name",
    "standard_applied",
    "revision_status",
    "revision_action",
    "revision_reason",
    "requires_recompute",
    "consistency_check",
    "writeback_patch"
  ],
  "properties": {
    "target_code": {
      "type": "string",
      "description": "目标编码"
    },
    "target_name": {
      "type": "string",
      "description": "目标名称"
    },
    "standard_applied": {
      "type": "string",
      "description": "应用的标准版本"
    },
    "revision_status": {
      "type": "string",
      "enum": ["approved", "blocked", "hold", "needs_more_evidence"],
      "description": "修订状态：approved(批准), blocked(阻断), hold(暂停), needs_more_evidence(需要更多证据)"
    },
    "revision_action": {
      "type": "string",
      "enum": ["rewrite", "keep", "revert", "mark_pending"],
      "description": "修订动作：rewrite(重写), keep(保持), revert(回退), mark_pending(标记待处理)"
    },
    "revision_reason": {
      "type": "string",
      "description": "修订原因"
    },
    "blocked_reason": {
      "type": "string",
      "description": "阻断原因（如果被阻断）"
    },
    "target_color": {
      "type": "string",
      "description": "提议的新灯色",
      "enum": ["black", "red", "yellow", "green"]
    },
    "requires_recompute": {
      "type": "boolean",
      "description": "是否需要重新计算",
      "default": false
    },
    "evidence_bundle_ref": {
      "type": "array",
      "description": "证据包引用",
      "items": {"type": "string"}
    },
    "consistency_check": {
      "type": "object",
      "description": "一致性检查结果",
      "properties": {
        "passed": {
          "type": "boolean",
          "description": "是否通过"
        },
        "issues": {
          "type": "array",
          "description": "问题列表",
          "items": {"type": "string"}
        }
      }
    },
    "writeback_patch": {
      "type": "object",
      "description": "写回补丁",
      "properties": {
        "text_updates": {
          "type": "array",
          "description": "文字更新",
          "items": {
            "type": "object",
            "properties": {
              "field": {"type": "string"},
              "old_value": {},
              "new_value": {}
            }
          }
        },
        "color_updates": {
          "type": "array",
          "description": "色块更新",
          "items": {
            "type": "object",
            "properties": {
              "target": {"type": "string"},
              "old_color": {"type": "string"},
              "new_color": {"type": "string"}
            }
          }
        },
        "evidence_updates": {
          "type": "array",
          "description": "证据更新",
          "items": {
            "type": "object",
            "properties": {
              "evidence_id": {"type": "string"},
              "action": {"type": "string", "enum": ["add", "remove", "update"]},
              "details": {"type": "object"}
            }
          }
        }
      }
    },
    "review_flag": {
      "type": "boolean",
      "description": "是否需要人工复核",
      "default": false
    },
    "recompute_scope": {
      "type": "string",
      "description": "重新计算范围"
    },
    "trace_id": {
      "type": "string",
      "description": "追踪ID"
    },
    "confidence_after_revision": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "修订后置信度"
    },
    "user_note": {
      "type": "string",
      "description": "用户备注"
    },
    "gate_decision": {
      "type": "string",
      "description": "闸门决策说明"
    },
    "principle_violations": {
      "type": "array",
      "description": "违反的核心原则（US-11）",
      "items": {"type": "string"}
    },
    "three_segment_output": {
      "type": "string",
      "description": "三段式输出（无证据时用）"
    },
    "session_memory_triggered": {
      "type": "array",
      "description": "本次触发的会话记忆规则",
      "items": {"type": "string"}
    },
    "checkpoint_id": {
      "type": "string",
      "description": "检查点 ID（支持任务暂停/重做）"
    }
  }
}
```

---

## TargetLocator（目标定位器）

```json
{
  "type": "object",
  "description": "在标准注入之前用于定位目标",
  "required": [
    "raw_feedback",
    "period_id",
    "group_id",
    "candidate_targets"
  ],
  "properties": {
    "raw_feedback": {
      "type": "string",
      "description": "用户原始反馈"
    },
    "period_id": {
      "type": "string",
      "description": "周期ID"
    },
    "group_id": {
      "type": "string",
      "description": "集团ID"
    },
    "candidate_targets": {
      "type": "array",
      "description": "候选目标列表",
      "items": {
        "type": "object",
        "properties": {
          "target_id": {
            "type": "string",
            "description": "目标ID"
          },
          "target_name": {
            "type": "string",
            "description": "目标名称"
          },
          "match_reason": {
            "type": "string",
            "description": "匹配原因"
          },
          "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "匹配置信度"
          }
        }
      }
    },
    "resolved_target_id": {
      "type": "string",
      "description": "锁定目标ID（唯一匹配时）"
    },
    "needs_clarification": {
      "type": "boolean",
      "description": "是否需要用户确认"
    },
    "clarification_message": {
      "type": "string",
      "description": "需要用户确认的消息"
    }
  }
}
```

---

## 枚举定义

### LayerEnum（目标层级）

```python
from enum import StrEnum

class LayerEnum(StrEnum):
    GOAL = "goal"          # 目标
    RESULT = "result"      # 结果
    INITIATIVE = "initiative"  # 举措
```

### BPTypeEnum（BP 类型）

```python
class BPTypeEnum(StrEnum):
    ORGANIZATION = "organization"  # 组织
    PERSONAL = "personal"         # 个人
```

### EvidenceTypeEnum（证据类型）

```python
class EvidenceTypeEnum(StrEnum):
    GOAL_REPORT = "goal_report"              # 目标报告
    RESULT_REPORT = "result_report"          # 结果报告
    INITIATIVE_REPORT = "initiative_report"  # 举措报告
    SYSTEM_RECORD = "system_record"          # 系统记录
    DOCUMENT_RECORD = "document_record"      # 文档记录
    MANUAL_CONFIRMATION = "manual_confirmation"  # 人工确认
```

### EvidenceLevelEnum（证据层级）

```python
class EvidenceLevelEnum(StrEnum):
    PRIMARY = "primary"           # 主要证据
    SECONDARY = "secondary"        # 次要证据
    BACKGROUND = "background"     # 背景证据
    INSUFFICIENT = "insufficient"  # 证据不足
```

### RevisionStatusEnum（修订状态）

```python
class RevisionStatusEnum(StrEnum):
    APPROVED = "approved"                    # 批准
    BLOCKED = "blocked"                       # 阻断
    HOLD = "hold"                            # 暂停
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"  # 需要更多证据
```

### RevisionActionEnum（修订动作）

```python
class RevisionActionEnum(StrEnum):
    REWRITE = "rewrite"          # 重写
    KEEP = "keep"               # 保持
    REVERT = "revert"           # 回退
    MARK_PENDING = "mark_pending"  # 标记待处理
```

### ConflictPolicyEnum（冲突策略）

```python
class ConflictPolicyEnum(StrEnum):
    BLOCK = "block"                          # 阻断
    PREFER_EXPLICIT = "prefer_explicit"      # 优先显式
    PREFER_LATEST = "prefer_latest"          # 优先最新
    FALLBACK_TO_HOLD = "fallback_to_hold"   # 回退到暂停
```

---

## 约束说明

### 唯一性约束

- `target_code` 在系统中必须唯一
- `evidence_id` 在证据库中必须唯一
- `trace_id` 在修订历史中必须唯一

### 版本约束

- `version` 必须符合语义化版本规范（Semantic Versioning）
- `effective_from` 必须早于或等于当前日期

### 置信度约束

- `evidence_confidence` 范围：[0.0, 1.0]
- `confidence_after_revision` 范围：[0.0, 1.0]
- 置信度低于 0.5 的证据自动标记为 `insufficient`

### 责任链约束

- `responsibility_chain` 长度至少为 1
- `owner` 必须是 `responsibility_chain` 的最后一个元素
- 证据的 `responsibility_chain` 必须与目标的 `owner_chain` 匹配才能作为 `primary` 证据

### 时间约束

- `evidence_time` 不能晚于当前时间
- 目标的 `period.end` 用于计算时间距离
- 证据时间距离超过 90 天自动降低证据层级

### 证据数量约束

- 一个目标至少需要 1 个 `primary` 证据才能判灯
- 证据包中的 `primary` 证据数量建议不超过 20 个
- `background` 证据数量不限，但不自动参与判灯
