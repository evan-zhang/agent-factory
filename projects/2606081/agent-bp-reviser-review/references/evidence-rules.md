# 证据规则

## ER-01: 法务证据≠注册进展

**规则**：法务/投资/泛背景材料不能自动作为注册进展证据。

**说明**：
- 法务文档属于 `background` 层级
- 投资材料属于 `background` 层级
- 注册进展需要责任人直接汇报

**层级判定**：`background`

**用户故事**：US-01, US-10, US-15

---

## ER-02: 先查证据再修改

**规则**：不能先修改后补证据，必须先检索证据再决定修订。

**说明**：
- 用户反馈触发证据检索
- 检索结果决定修订动作
- 无足够证据则 `hold` 或 `needs_more_evidence`

**修订动作**：`hold`, `needs_more_evidence`, `block`

**用户故事**：US-02, US-13, US-14

---

## ER-03: 产品别名搜索

**规则**：必须用产品别名补充搜索，防止漏检。

**说明**：
- 目标可能用产品别名提及
- 别名列表必须维护
- 搜索时同时使用正式名和别名

**搜索策略**：
```python
search_keywords = [target_name] + product_aliases
```

**用户故事**：US-07

---

## ER-04: 跳过部门找具体人

**规则**：证据搜索必须下沉到具体责任人，不能只看部门层面。

**说明**：
- 部门汇报不等于具体责任人汇报
- 必须定位到 `owner_chain` 中的具体人
- 跨部门协作时定位到协作责任人

**责任链回溯**：
```python
def trace_responsibility(target_standard):
    chain = target_standard.responsibility_chain
    # 下沉到最后一级责任人
    concrete_owner = chain[-1]
    return concrete_owner
```

**用户故事**：US-08

---

## ER-05: 证据责任人定位

**规则**：证据必须归属于目标责任链中的责任人。

**说明**：
- 证据的 `responsibility_chain` 必须与目标的 `owner_chain` 匹配
- 不属于责任链的证据只能作为 `secondary` 或 `background`
- 无责任人的证据标记为 `insufficient`

**匹配检查**：
```python
def check_responsibility_match(evidence, target_standard):
    return any(role in target_standard.responsibility_chain 
               for role in evidence.responsibility_chain)
```

**用户故事**：US-01, US-10, US-15

---

## ER-06: 证据时间维度

**规则**：证据必须考虑时间维度，过期证据不能自动生效。

**说明**：
- 证据有 `evidence_time` 字段
- 过期证据标记风险
- 时间距离影响判灯

**时间计算**：
```python
def calculate_time_distance(target_standard, evidence_time):
    target_end = target_standard.period.end
    distance = (target_end - evidence_time).days
    return distance
```

**用户故事**：US-09, US-17

---

## ER-07: 重大缺陷过滤

**规则**：资料有重大缺陷时，证据不能自动生效。

**说明**：
- 缺陷类型：数据不一致、逻辑矛盾、明显错误
- 重大缺陷证据标记 `risk_flag=True`
- 触发人工复核

**缺陷检测**：
```python
def detect_major_defects(evidence_content):
    defects = []
    # 检测数据不一致
    if has_inconsistency(evidence_content):
        defects.append("data_inconsistency")
    # 检测逻辑矛盾
    if has_contradiction(evidence_content):
        defects.append("logical_contradiction")
    # 检测明显错误
    if has_obvious_error(evidence_content):
        defects.append("obvious_error")
    return defects
```

**用户故事**：US-09, US-17

---

## ER-08: 证据层级强制区分

**规则**：必须严格区分 primary / secondary / background / insufficient。

**层级定义**：

| 层级 | 定义 | 示例 |
|------|------|------|
| `primary` | 目标责任人的直接汇报 | 周报、月报中的目标进展 |
| `secondary` | 间接相关的佐证材料 | 协作方的佐证邮件 |
| `background` | 泛背景材料 | 法务文档、投资材料 |
| `insufficient` | 证据不足 | 无责任人、无时间、无内容 |

**分层算法**：
```python
def classify_evidence(evidence, target_standard):
    # Primary: 目标责任人直接汇报
    if is_direct_responsible(evidence, target_standard):
        return "primary"
    
    # Secondary: 间接相关但有责任人
    if is_indirectly_related(evidence, target_standard):
        return "secondary"
    
    # Background: 泛背景材料
    if is_background_material(evidence):
        return "background"
    
    # Insufficient: 其他
    return "insufficient"
```

---

## ER-09: 汇报类型覆盖

**规则**：证据搜索必须覆盖所有汇报类型。

**汇报类型**：
- 单周报
- 双周报
- 月报
- 专项汇报

**搜索策略**：
```python
def search_all_report_types(target_code, period):
    report_types = [
        "weekly_report",
        "biweekly_report",
        "monthly_report",
        "special_report"
    ]
    for report_type in report_types:
        search_reports(target_code, period, report_type)
```

---

## ER-10: 证据置信度计算

**规则**：每个证据必须计算 `evidence_confidence`（0-1）。

**置信度因素**：
- 责任人匹配度（40%）
- 时间相关性（30%）
- 内容完整性（20%）
- 来源可靠性（10%）

**计算公式**：
```python
def calculate_confidence(evidence, target_standard):
    score = 0.0
    
    # 责任人匹配度（40%）
    if is_responsible_match(evidence, target_standard):
        score += 0.4
    
    # 时间相关性（30%）
    time_relevance = calculate_time_relevance(evidence, target_standard)
    score += time_relevance * 0.3
    
    # 内容完整性（20%）
    if is_content_complete(evidence):
        score += 0.2
    
    # 来源可靠性（10%）
    source_reliability = get_source_reliability(evidence.evidence_source)
    score += source_reliability * 0.1
    
    return min(score, 1.0)
```

---

## ER-11: 证据排除规则

**规则**：不属于目标责任链的证据必须排除。

**排除原因**：
- `exclude_reason: "not_in_responsibility_chain"`: 不在责任链中
- `exclude_reason: "out_of_scope"`: 超出目标范围
- `exclude_reason: "time_mismatch"`: 时间不匹配
- `exclude_reason: "content_irrelevant"`: 内容不相关

**排除处理**：
```python
def should_exclude_evidence(evidence, target_standard):
    # 检查责任链
    if not in_responsibility_chain(evidence, target_standard):
        return True, "not_in_responsibility_chain"
    
    # 检查范围
    if not in_scope(evidence, target_standard):
        return True, "out_of_scope"
    
    # 检查时间
    if not time_match(evidence, target_standard):
        return True, "time_mismatch"
    
    # 检查内容
    if not content_relevant(evidence, target_standard):
        return True, "content_irrelevant"
    
    return False, None
```

---

## ER-12: 证据范围备注

**规则**：证据必须包含 `scope_note` 说明适用范围。

**备注内容**：
- 目标适用范围
- 时间适用范围
- 责任人适用范围

**备注格式**：
```json
{
  "scope_note": "适用于 2026 Q1 的组织目标，责任人：张三，覆盖范围：注册进展"
}
```
