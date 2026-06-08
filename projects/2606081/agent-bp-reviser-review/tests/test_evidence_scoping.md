# 测试：证据范围界定

## 测试目标

验证证据的责任链匹配、层级分类和排除规则

## 测试用例 1：主要证据（primary）识别

### 输入

证据：
```json
{
  "evidence_id": "ev_001",
  "evidence_type": "goal_report",
  "evidence_source": "周报-2026-W23-张三",
  "evidence_content": {
    "summary": "本周完成了2个新品种的注册申报"
  },
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

目标标准：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### 预期输出

```json
{
  "evidence_level": "primary",
  "match_reason": "目标责任人直接汇报"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import EvidenceBundle, TargetStandard
import json

evidence_data = {
    'evidence_id': 'ev_001',
    'evidence_type': 'goal_report',
    'evidence_source': '周报-2026-W23-张三',
    'evidence_content': {'summary': '本周完成了2个新品种的注册申报'},
    'responsibility_chain': ['公司', '研发部', '张三']
}

target_data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'owner': '张三',
    'responsibility_chain': ['公司', '研发部', '张三'],
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'layer': 'goal',
    'bp_type': 'organization',
    'evidence_hint': [],
    'status_rule': {},
    'writeback_rule': {}
}

evidence = EvidenceBundle(evidence_data)
target = TargetStandard(target_data)

level = evidence.classify(target)
print(json.dumps({'evidence_level': level}, ensure_ascii=False))
"
```

### 预期结果

✓ 证据层级为 `primary`

---

## 测试用例 2：次要证据（secondary）识别

### 输入

证据：
```json
{
  "evidence_id": "ev_002",
  "evidence_type": "result_report",
  "evidence_source": "协作邮件-李四",
  "evidence_content": {
    "summary": "协作方确认支持注册进展"
  },
  "responsibility_chain": ["公司", "市场部", "李四"]
}
```

目标标准：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### 预期输出

```json
{
  "evidence_level": "secondary",
  "match_reason": "间接相关，但在责任链中"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import EvidenceBundle, TargetStandard
import json

evidence_data = {
    'evidence_id': 'ev_002',
    'evidence_type': 'result_report',
    'evidence_source': '协作邮件-李四',
    'evidence_content': {'summary': '协作方确认支持注册进展'},
    'responsibility_chain': ['公司', '市场部', '李四']
}

target_data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'owner': '张三',
    'responsibility_chain': ['公司', '研发部', '张三'],
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'layer': 'goal',
    'bp_type': 'organization',
    'evidence_hint': [],
    'status_rule': {},
    'writeback_rule': {}
}

evidence = EvidenceBundle(evidence_data)
target = TargetStandard(target_data)

level = evidence.classify(target)
print(json.dumps({'evidence_level': level}, ensure_ascii=False))
"
```

### 预期结果

✓ 证据层级为 `secondary`

---

## 测试用例 3：背景证据（background）识别

### 输入

证据：
```json
{
  "evidence_id": "ev_003",
  "evidence_type": "document_record",
  "evidence_source": "法务文档-注册指南",
  "evidence_content": {
    "summary": "法务部门提供的注册指南文档"
  },
  "responsibility_chain": ["公司", "法务部"]
}
```

目标标准：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### 预期输出

```json
{
  "evidence_level": "background",
  "match_reason": "泛背景材料，不能作为进展证据"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import EvidenceBundle, TargetStandard
import json

evidence_data = {
    'evidence_id': 'ev_003',
    'evidence_type': 'document_record',
    'evidence_source': '法务文档-注册指南',
    'evidence_content': {'summary': '法务部门提供的注册指南文档'},
    'responsibility_chain': ['公司', '法务部']
}

target_data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'owner': '张三',
    'responsibility_chain': ['公司', '研发部', '张三'],
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'layer': 'goal',
    'bp_type': 'organization',
    'evidence_hint': [],
    'status_rule': {},
    'writeback_rule': {}
}

evidence = EvidenceBundle(evidence_data)
target = TargetStandard(target_data)

level = evidence.classify(target)
print(json.dumps({'evidence_level': level}, ensure_ascii=False))
"
```

### 预期结果

✓ 证据层级为 `background`

---

## 测试用例 4：证据不足（insufficient）识别

### 输入

证据：
```json
{
  "evidence_id": "ev_004",
  "evidence_type": "manual_confirmation",
  "evidence_source": "口头确认",
  "evidence_content": {
    "summary": "有人说进展顺利"
  },
  "responsibility_chain": []
}
```

目标标准：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### 预期输出

```json
{
  "evidence_level": "insufficient",
  "exclude_reason": "无责任人，无具体来源"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import EvidenceBundle, TargetStandard
import json

evidence_data = {
    'evidence_id': 'ev_004',
    'evidence_type': 'manual_confirmation',
    'evidence_source': '口头确认',
    'evidence_content': {'summary': '有人说进展顺利'},
    'responsibility_chain': []
}

target_data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'owner': '张三',
    'responsibility_chain': ['公司', '研发部', '张三'],
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'layer': 'goal',
    'bp_type': 'organization',
    'evidence_hint': [],
    'status_rule': {},
    'writeback_rule': {}
}

evidence = EvidenceBundle(evidence_data)
target = TargetStandard(target_data)

level = evidence.classify(target)
print(json.dumps({'evidence_level': level}, ensure_ascii=False))
"
```

### 预期结果

✓ 证据层级为 `insufficient`

---

## 测试用例 5：法务证据≠注册进展

### 输入

证据：
```json
{
  "evidence_id": "ev_005",
  "evidence_type": "document_record",
  "evidence_source": "法务文档-投资协议",
  "evidence_content": {
    "summary": "法务部门提供的投资协议文档"
  },
  "responsibility_chain": ["公司", "法务部"]
}
```

目标标准：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### 预期输出

```json
{
  "evidence_level": "background",
  "exclude_reason": "法务证据≠注册进展",
  "match_reason": "泛背景材料，不能作为注册进展证据"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import EvidenceBundle, TargetStandard
import json

evidence_data = {
    'evidence_id': 'ev_005',
    'evidence_type': 'document_record',
    'evidence_source': '法务文档-投资协议',
    'evidence_content': {'summary': '法务部门提供的投资协议文档'},
    'responsibility_chain': ['公司', '法务部']
}

target_data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'owner': '张三',
    'responsibility_chain': ['公司', '研发部', '张三'],
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'layer': 'goal',
    'bp_type': 'organization',
    'evidence_hint': [],
    'status_rule': {},
    'writeback_rule': {}
}

evidence = EvidenceBundle(evidence_data)
target = TargetStandard(target_data)

level = evidence.classify(target)
print(json.dumps({'evidence_level': level}, ensure_ascii=False))
"
```

### 预期结果

✓ 证据层级为 `background`，法务文档不能作为注册进展证据

---

## 测试总结

| 测试用例 | 证据类型 | 责任链 | 预期层级 | 用户故事 |
|----------|----------|--------|----------|----------|
| 用例1 | goal_report | 责任人张三 | primary | US-01, US-10 |
| 用例2 | result_report | 协作方李四 | secondary | US-01 |
| 用例3 | document_record | 法务部 | background | US-01 |
| 用例4 | manual_confirmation | 无责任人 | insufficient | US-01 |
| 用例5 | document_record | 法务部（投资） | background | US-01, US-10, US-15 |

---

## 执行所有测试

> ✅ 本规格已有可执行版本：`tests/test_evidence_scoping.py`（unittest，7 个用例）

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/test_evidence_scoping.py
python3 tests/run_all.py
```
