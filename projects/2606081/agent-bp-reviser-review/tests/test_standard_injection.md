# 测试：标准注入

## 测试目标

验证 `TargetStandard` 注入和校验功能

## 测试用例 1：标准完整字段注入

### 输入

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "goal",
  "bp_type": "organization",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "measurements": [
    {
      "metric": "注册数量",
      "target": 3,
      "current": 1
    }
  ],
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
```

### 预期输出

```json
{
  "valid": true,
  "errors": []
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import TargetStandard
import json

data = json.loads(open('examples/target_standard_sample.json').read())
standard = TargetStandard(data)
is_valid, errors = standard.validate()
print(json.dumps({'valid': is_valid, 'errors': errors}, ensure_ascii=False))
"
```

### 预期结果

✓ 通过校验

---

## 测试用例 2：缺少必填字段

### 输入

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "goal",
  "bp_type": "organization",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  }
}
```

### 预期输出

```json
{
  "valid": false,
  "errors": [
    "缺少必填字段: source",
    "缺少必填字段: version",
    "缺少必填字段: owner"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import TargetStandard
import json

data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'layer': 'goal',
    'bp_type': 'organization',
    'period': {'start': '2026-01-01', 'end': '2026-03-31'}
}
standard = TargetStandard(data)
is_valid, errors = standard.validate()
print(json.dumps({'valid': is_valid, 'errors': errors}, ensure_ascii=False))
"
```

### 预期结果

✗ 校验失败，返回缺失字段列表

---

## 测试用例 3：无效的 layer 值

### 输入

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "invalid_layer",
  "bp_type": "organization",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "source": "BP_System",
  "effective_from": "2026-01-01",
  "version": "1.0.0",
  "owner": "张三",
  "responsibility_chain": ["张三"]
}
```

### 预期输出

```json
{
  "valid": false,
  "errors": [
    "无效的 layer: invalid_layer"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import TargetStandard, LayerEnum
import json

data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'layer': 'invalid_layer',
    'bp_type': 'organization',
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'owner': '张三',
    'responsibility_chain': ['张三']
}
standard = TargetStandard(data)
is_valid, errors = standard.validate()
print(json.dumps({'valid': is_valid, 'errors': errors}, ensure_ascii=False))
"
```

### 预期结果

✗ 校验失败，返回无效 layer 错误

---

## 测试用例 4：空责任链

### 输入

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "goal",
  "bp_type": "organization",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "source": "BP_System",
  "effective_from": "2026-01-01",
  "version": "1.0.0",
  "owner": "张三",
  "responsibility_chain": []
}
```

### 预期输出

```json
{
  "valid": false,
  "errors": [
    "责任链不能为空"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import TargetStandard
import json

data = {
    'target_code': 'ORG_2026_Q1_REG_001',
    'target_name': '完成3个新品种注册',
    'layer': 'goal',
    'bp_type': 'organization',
    'period': {'start': '2026-01-01', 'end': '2026-03-31'},
    'source': 'BP_System',
    'effective_from': '2026-01-01',
    'version': '1.0.0',
    'owner': '张三',
    'responsibility_chain': []
}
standard = TargetStandard(data)
is_valid, errors = standard.validate()
print(json.dumps({'valid': is_valid, 'errors': errors}, ensure_ascii=False))
"
```

### 预期结果

✗ 校验失败，责任链不能为空

---

## 测试用例 5：版本格式验证

### 输入

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "goal",
  "bp_type": "organization",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "source": "BP_System",
  "effective_from": "2026-01-01",
  "version": "invalid_version",
  "owner": "张三",
  "responsibility_chain": ["张三"]
}
```

### 预期输出

```json
{
  "valid": true,
  "errors": []
}
```

### 说明

当前实现中 `version` 字段只检查存在性，不验证格式。如果需要格式验证，需要在 `validate()` 方法中添加版本格式检查。

---

## 测试总结

| 测试用例 | 描述 | 预期结果 | 实际结果 |
|----------|------|----------|----------|
| 用例1 | 完整标准注入 | ✓ 通过 | 待执行 |
| 用例2 | 缺少必填字段 | ✗ 失败 | 待执行 |
| 用例3 | 无效 layer 值 | ✗ 失败 | 待执行 |
| 用例4 | 空责任链 | ✗ 失败 | 待执行 |
| 用例5 | 版本格式验证 | ✓ 通过（当前不验证格式） | 待执行 |

---

## 执行所有测试

> ✅ 本规格已有可执行版本：`tests/test_standard_injection.py`（unittest，7 个用例）

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/test_standard_injection.py      # 单独运行本套
python3 tests/run_all.py                       # 运行全部 unittest 套件
```

**注意（P1 修复后预期变更）**：
- 用例2 缺失字段会列出全部缺失项（含 scope/effective_from/conflict_policy/status_rule/writeback_rule 等 16 字段校验）
- 新增校验：`bp_type` 枚举、`conflict_policy` 枚举、`owner` 必须等于 `responsibility_chain` 末尾元素
