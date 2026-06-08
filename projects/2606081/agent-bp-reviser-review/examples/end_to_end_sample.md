# agent-bp-reviser-review 端到端示例

## 场景：用户要求修改目标状态

### 用户反馈

```
把「完成3个新品种注册」改成绿色
```

### Step 0: 目标定位

系统提取关键词：`["完成3个新品种注册"]`

搜索目标树，找到唯一匹配：
- 目标编码：`ORG_2026_Q1_REG_001`
- 目标名称：`完成3个新品种注册`
- 责任人：张三

**定位结果**：锁定目标 `ORG_2026_Q1_REG_001`

---

### Step 1: 标准注入

注入 `TargetStandard`：

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
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"],
  "version": "1.0.0",
  "conflict_policy": "prefer_latest"
}
```

**校验结果**：✓ 标准有效

---

### Step 2: 降级用户反馈

用户反馈降级为假设：

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

---

### Step 3: 责任链检索

按责任链搜索证据：

- 责任人：张三
- 搜索范围：周报、双周报、月报、专项汇报
- 搜索关键词：注册、进展、品种

**检索结果**：
- 找到周报 `2026-W23-张三`
- 包含目标进展信息

---

### Step 4: 证据语义分层

检索到的证据分层：

| 证据ID | 类型 | 层级 | 置信度 | 责任链匹配 |
|--------|------|------|--------|------------|
| ev_001 | goal_report | primary | 0.85 | ✓ (张三) |

**证据详情**：

```json
{
  "evidence_id": "ev_001",
  "evidence_type": "goal_report",
  "evidence_level": "primary",
  "evidence_source": "周报-2026-W23-张三",
  "evidence_content": {
    "summary": "本周完成了2个新品种的注册申报，预计Q1能完成目标"
  },
  "evidence_confidence": 0.85,
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

---

### Step 5: 独立判灯/判定

**双维度判断**：

1. **时间维度**：
   - 目标结束：2026-03-31
   - 证据时间：2026-06-10
   - 时间距离：约70天（中等）

2. **缺陷维度**：
   - 证据内容完整：✓
   - 责任链匹配：✓
   - 无重大缺陷：✓

**判灯结果**：

```json
{
  "color": "green",
  "reason": "时间临近，无重大缺陷，证据充分"
}
```

---

### Step 6: 修订闸门

**风险评估**：
- 当前灯色：假设为黑色
- 目标灯色：绿色
- 风险等级：高（黑→绿）

**闸门决策**：

```json
{
  "revision_status": "hold",
  "review_flag": true,
  "gate_decision": "高风险改动（黑→绿），需要人工复核"
}
```

---

### 人工复核（假设通过）

复核结果：✓ 批准修订

---

### Step 7: 写回联动

生成写回补丁：

```json
{
  "text_updates": [
    {
      "field": "target_status",
      "old_value": "black",
      "new_value": "green"
    },
    {
      "field": "target_description",
      "old_value": "无进展",
      "new_value": "已完成2/3，进展良好"
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
      "details": {
        "status": "verified",
        "level": "primary"
      }
    }
  ]
}
```

---

### Step 8: 一致性校验

**检查项目**：

1. ✓ 文字与灯色同步（green → green）
2. ✓ 色块与灯色同步（black → green）
3. ✓ 证据栏与证据包一致（ev_001 已添加）
4. ✓ 结论与证据一致（绿灯 + 主要证据）
5. ✓ 无跨目标写回

**校验结果**：

```json
{
  "passed": true,
  "issues": []
}
```

---

### 最终修订输出

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "standard_applied": "1.0.0",
  "revision_status": "approved",
  "revision_action": "rewrite",
  "revision_reason": "基于责任人周报证据（ev_001），目标进展良好，判灯为绿色",
  "evidence_bundle_ref": ["ev_001"],
  "consistency_check": {
    "passed": true,
    "issues": []
  },
  "writeback_patch": { /* 见Step 7 */ },
  "review_flag": false,
  "trace_id": "trace_20260606100000",
  "confidence_after_revision": 0.85,
  "gate_decision": "批准修订"
}
```

---

## 输出效果

### BP 系统界面更新

- 目标：`完成3个新品种注册`
- 状态：🟢 绿色
- 描述：`已完成2/3，进展良好`
- 证据：`周报-2026-W23-张三` ✓

### 追踪信息

- 追踪ID：`trace_20260606100000`
- 标准版本：`1.0.0`
- 修订时间：`2026-06-06 10:00:00`
- 置信度：`0.85`

---

## 关键要点

1. ✓ **单目标原则**：只处理一个目标
2. ✓ **标准先行**：先注入 TargetStandard
3. ✓ **用户反馈降级**：反馈作为线索，不直接执行
4. ✓ **责任链回溯**：证据来自责任人张三
5. ✓ **证据分层**：主要证据 primary，置信度 0.85
6. ✓ **独立判灯**：基于双维度判断
7. ✓ **闸门决策**：高风险改动触发复核
8. ✓ **写回联动**：文字、色块、证据栏同步
9. ✓ **一致性校验**：全部通过
10. ✓ **版本可追溯**：完整追踪信息

---

## 用户故事覆盖

- ✓ US-01: 法务证据≠注册进展，证据责任人定位（ev_001 来自张三周报）
- ✓ US-02: 先查证据再修改（Step 3→Step 5→Step 6）
- ✓ US-03: 判灯独立运行，灯色/文字/色块同步（Step 5 + Step 8）
- ✓ US-05: 用户反馈降级为线索（Step 2）
- ✓ US-09: 判灯双维度（时间+缺陷）（Step 5）
- ✓ US-11: 用户反馈不能直接当指令（Step 2 + Step 6）
