# 测试：修订闸门决策

## 测试目标

验证修订闸门的决策逻辑，包括风险评估、证据闭环检查、标准冲突检测

## 测试用例 1：高风险改动（黑→绿）

### 输入

当前灯色：`black`
目标灯色：`green`
修订动作：`rewrite`

### 预期输出

```json
{
  "revision_status": "hold",
  "review_flag": true,
  "gate_decision": "高风险改动（黑→绿），需要人工复核"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('black', 'rewrite_green')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `hold`，触发复核标志

---

## 测试用例 2：高风险改动（红→绿）

### 输入

当前灯色：`red`
目标灯色：`green`
修订动作：`rewrite`

### 预期输出

```json
{
  "revision_status": "hold",
  "review_flag": true,
  "gate_decision": "高风险改动（红→绿），需要人工复核"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('red', 'rewrite_green')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `hold`，触发复核标志

---

## 测试用例 3：证据未闭环（黑灯）

### 输入

当前灯色：`black`
目标灯色：`yellow`
修订动作：`rewrite`

### 预期输出

```json
{
  "revision_status": "needs_more_evidence",
  "review_flag": false,
  "gate_decision": "证据未闭环"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('black', 'rewrite')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `needs_more_evidence`

---

## 测试用例 4：正常改动（黄→绿）

### 输入

当前灯色：`yellow`
目标灯色：`green`
修订动作：`rewrite`
主要证据：存在

### 预期输出

```json
{
  "revision_status": "approved",
  "review_flag": false,
  "gate_decision": "批准修订"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('yellow', 'rewrite')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `approved`

---

## 测试用例 5：保持不变（keep）

### 输入

当前灯色：`green`
目标灯色：`green`
修订动作：`keep`

### 预期输出

```json
{
  "revision_status": "approved",
  "review_flag": false,
  "gate_decision": "批准修订"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('green', 'keep')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `approved`

---

## 测试用例 6：标记待处理（证据不足）

### 输入

当前灯色：`unknown`
目标灯色：`pending`
修订动作：`mark_pending`

### 预期输出

```json
{
  "revision_status": "hold",
  "review_flag": false,
  "gate_decision": "证据不足，标记为待处理"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('unknown', 'mark_pending')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `hold`

---

## 测试用例 7：回退操作（revert）

### 输入

当前灯色：`green`
目标灯色：`yellow`
修订动作：`revert`

### 预期输出

```json
{
  "revision_status": "approved",
  "review_flag": false,
  "gate_decision": "批准修订（回退操作）"
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import gate_decision
import json

result = gate_decision('green', 'revert')
print(json.dumps(result, ensure_ascii=False))
"
```

### 预期结果

✓ 修订状态为 `approved`

---

## 测试用例 8：用户反馈降级处理

### 输入

用户反馈：
```
把「完成3个新品种注册」改成绿色
```

### 预期输出

```json
{
  "hypothesis": "把「完成3个新品种注册」改成绿色",
  "status": "pending_verification",
  "search_tasks": [
    {
      "task_type": "search_evidence",
      "keywords": ["完成3个新品种注册"],
      "priority": "high"
    }
  ]
}
```

### 执行命令

```bash
python3 -c "
from scripts.bp_reviser import downgrade_user_feedback
from scripts.helpers import match_target_keywords
import json

feedback = '把「完成3个新品种注册」改成绿色'
result = downgrade_user_feedback(feedback)
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

### 预期结果

✓ 用户反馈被降级为假设，生成证据检索任务

---

## 测试总结

| 测试用例 | 场景 | 当前灯色 | 目标灯色 | 预期状态 | 复核标志 | 用户故事 |
|----------|------|----------|----------|----------|----------|----------|
| 用例1 | 黑→绿 | black | green | hold | ✓ | US-05, US-11 |
| 用例2 | 红→绿 | red | green | hold | ✓ | US-05, US-11 |
| 用例3 | 证据未闭环 | black | yellow | needs_more_evidence | ✗ | US-02, US-13 |
| 用例4 | 黄→绿 | yellow | green | approved | ✗ | 正常流程 |
| 用例5 | 保持不变 | green | green | approved | ✗ | 正常流程 |
| 用例6 | 标记待处理 | unknown | pending | hold | ✗ | US-06 |
| 用例7 | 回退操作 | green | yellow | approved | ✗ | 正常流程 |
| 用例8 | 用户反馈降级 | N/A | N/A | pending_verification | ✗ | US-05, US-11 |

---

## 关键验证点

1. ✓ **高风险改动触发复核**：黑→绿、红→绿必须触发 `review_flag=True`
2. ✓ **证据未闭环**：黑灯状态必须返回 `needs_more_evidence`
3. ✓ **用户反馈降级**：用户反馈不能直接作为修改指令
4. ✓ **正常流程通过**：低风险改动直接批准
5. ✓ **保持不变操作**：`keep` 动作不需要复核

---

## 执行所有测试

> ✅ 本规格已有可执行版本：`tests/test_revision_gating.py`（unittest，8 个用例）

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/test_revision_gating.py
python3 tests/run_all.py
```
