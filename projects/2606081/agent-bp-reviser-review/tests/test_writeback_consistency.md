# 测试：写回一致性校验

## 测试目标

验证写回补丁的一致性校验，包括文字/色块/证据栏同步、跨目标检查等

## 测试用例 1：绿灯 + 主要证据一致性通过

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "target_color": "green",
  "evidence_bundle_ref": ["ev_001"],
  "writeback_patch": {
    "text_updates": [
      {
        "field": "target_status",
        "old_value": "black",
        "new_value": "green"
      }
    ],
    "color_updates": [
      {
        "target": "ORG_2026_Q1_REG_001",
        "old_color": "black",
        "new_color": "green"
      }
    ],
    "evidence_updates": [
      {
        "evidence_id": "ev_001",
        "action": "add",
        "details": {"level": "primary"}
      }
    ]
  }
}
```

证据：
```json
{
  "ev_001": {
    "evidence_level": "primary"
  }
}
```

### 预期输出

```json
{
  "passed": true,
  "issues": []
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput, TargetStandard
from scripts.helpers import run_consistency_check
import json

# 创建修订输出
output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.target_color = 'green'
output.evidence_bundle_ref = ['ev_001']
output.writeback_patch = {
    'text_updates': [
        {'field': 'target_status', 'old_value': 'black', 'new_value': 'green'}
    ],
    'color_updates': [
        {'target': 'ORG_2026_Q1_REG_001', 'old_color': 'black', 'new_color': 'green'}
    ],
    'evidence_updates': [
        {'evidence_id': 'ev_001', 'action': 'add', 'details': {'level': 'primary'}}
    ]
}

# 创建目标标准（简化）
target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

# 运行一致性校验
result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✓ 一致性检查通过

---

## 测试用例 2：黑灯 + 有效证据不一致

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "target_color": "black",
  "evidence_bundle_ref": ["ev_001", "ev_002"],
  "writeback_patch": {
    "color_updates": [
      {
        "target": "ORG_2026_Q1_REG_001",
        "old_color": "green",
        "new_color": "black"
      }
    ]
  }
}
```

### 预期输出

```json
{
  "passed": false,
  "issues": [
    "黑灯状态不应有有效证据"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.target_color = 'black'
output.evidence_bundle_ref = ['ev_001', 'ev_002']
output.writeback_patch = {
    'color_updates': [
        {'target': 'ORG_2026_Q1_REG_001', 'old_color': 'green', 'new_color': 'black'}
    ]
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✗ 一致性检查失败：黑灯状态不应有有效证据

---

## 测试用例 3：绿灯 + 无主要证据不一致

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "target_color": "green",
  "evidence_bundle_ref": ["ev_003"],
  "writeback_patch": {
    "color_updates": [
      {
        "target": "ORG_2026_Q1_REG_001",
        "old_color": "yellow",
        "new_color": "green"
      }
    ]
  }
}
```

证据：
```json
{
  "ev_003": {
    "evidence_level": "background"
  }
}
```

### 预期输出

```json
{
  "passed": false,
  "issues": [
    "绿灯状态需要主要证据"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.target_color = 'green'
output.evidence_bundle_ref = ['ev_003']
output.writeback_patch = {
    'color_updates': [
        {'target': 'ORG_2026_Q1_REG_001', 'old_color': 'yellow', 'new_color': 'green'}
    ]
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✗ 一致性检查失败：绿灯状态需要主要证据

---

## 测试用例 4：跨目标文字写回检测

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "evidence_bundle_ref": ["ev_001"],
  "writeback_patch": {
    "text_updates": [
      {
        "target": "ORG_2026_Q1_REG_002",
        "field": "target_status",
        "old_value": "black",
        "new_value": "green"
      }
    ]
  }
}
```

### 预期输出

```json
{
  "passed": false,
  "issues": [
    "检测到跨目标文字写回: ORG_2026_Q1_REG_002"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.evidence_bundle_ref = ['ev_001']
output.writeback_patch = {
    'text_updates': [
        {'target': 'ORG_2026_Q1_REG_002', 'field': 'target_status', 'old_value': 'black', 'new_value': 'green'}
    ]
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✗ 一致性检查失败：检测到跨目标文字写回

---

## 测试用例 5：跨目标色块写回检测

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "evidence_bundle_ref": ["ev_001"],
  "writeback_patch": {
    "color_updates": [
      {
        "target": "ORG_2026_Q1_REG_003",
        "old_color": "black",
        "new_color": "green"
      }
    ]
  }
}
```

### 预期输出

```json
{
  "passed": false,
  "issues": [
    "检测到跨目标色块写回: ORG_2026_Q1_REG_003"
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.evidence_bundle_ref = ['ev_001']
output.writeback_patch = {
    'color_updates': [
        {'target': 'ORG_2026_Q1_REG_003', 'old_color': 'black', 'new_color': 'green'}
    ]
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✗ 一致性检查失败：检测到跨目标色块写回

---

## 测试用例 6：文字/色块/证据栏三者同步

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "rewrite",
  "target_color": "yellow",
  "evidence_bundle_ref": ["ev_001", "ev_002"],
  "writeback_patch": {
    "text_updates": [
      {
        "field": "target_status",
        "old_value": "green",
        "new_value": "yellow"
      }
    ],
    "color_updates": [
      {
        "target": "ORG_2026_Q1_REG_001",
        "old_color": "green",
        "new_color": "yellow"
      }
    ],
    "evidence_updates": [
      {
        "evidence_id": "ev_001",
        "action": "add",
        "details": {"level": "secondary"}
      },
      {
        "evidence_id": "ev_002",
        "action": "add",
        "details": {"level": "secondary"}
      }
    ]
  }
}
```

### 预期输出

```json
{
  "passed": true,
  "issues": []
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'rewrite'
output.target_color = 'yellow'
output.evidence_bundle_ref = ['ev_001', 'ev_002']
output.writeback_patch = {
    'text_updates': [
        {'field': 'target_status', 'old_value': 'green', 'new_value': 'yellow'}
    ],
    'color_updates': [
        {'target': 'ORG_2026_Q1_REG_001', 'old_color': 'green', 'new_color': 'yellow'}
    ],
    'evidence_updates': [
        {'evidence_id': 'ev_001', 'action': 'add', 'details': {'level': 'secondary'}},
        {'evidence_id': 'ev_002', 'action': 'add', 'details': {'level': 'secondary'}}
    ]
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✓ 一致性检查通过：黄灯 + 次要证据，三者同步

---

## 测试用例 7：无更新的一致性

### 输入

修订输出：
```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_action": "keep",
  "evidence_bundle_ref": [],
  "writeback_patch": {
    "text_updates": [],
    "color_updates": [],
    "evidence_updates": []
  }
}
```

### 预期输出

```json
{
  "passed": true,
  "issues": []
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import RevisionOutput
from scripts.helpers import run_consistency_check
import json

output = RevisionOutput()
output.target_code = 'ORG_2026_Q1_REG_001'
output.revision_action = 'keep'
output.evidence_bundle_ref = []
output.writeback_patch = {
    'text_updates': [],
    'color_updates': [],
    'evidence_updates': []
}

target_standard = type('obj', (object,), {
    'target_code': 'ORG_2026_Q1_REG_001'
})

result = run_consistency_check(output, target_standard)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✓ 一致性检查通过：无更新操作

---

## 测试总结

| 测试用例 | 场景 | 灯色 | 证据 | 跨目标 | 预期结果 | 用户故事 |
|----------|------|------|------|--------|----------|----------|
| 用例1 | 绿灯+主要证据 | green | primary | ✗ | ✓ 通过 | US-03 |
| 用例2 | 黑灯+有效证据 | black | 有证据 | ✗ | ✗ 失败 | US-03 |
| 用例3 | 绿灯+无主要证据 | green | background | ✗ | ✗ 失败 | US-03 |
| 用例4 | 跨目标文字 | N/A | N/A | ✓ | ✗ 失败 | US-04 |
| 用例5 | 跨目标色块 | N/A | N/A | ✓ | ✗ 失败 | US-04 |
| 用例6 | 三者同步 | yellow | secondary | ✗ | ✓ 通过 | US-03 |
| 用例7 | 无更新 | N/A | N/A | ✗ | ✓ 通过 | 正常流程 |

---

## 关键验证点

1. ✓ **文字/色块/证据栏同步**：三者必须同时更新
2. ✓ **灯色与证据一致性**：
   - 黑灯不应有有效证据
   - 绿灯需要有主要证据
3. ✓ **跨目标检测**：
   - 跨目标文字写回被阻断
   - 跨目标色块写回被阻断
4. ✓ **无更新操作**：保持不变的一致性

---

## 执行所有测试

> ✅ 本规格已有可执行版本：`tests/test_writeback_consistency.py`（unittest，6 个用例）

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/test_writeback_consistency.py
python3 tests/run_all.py
```
