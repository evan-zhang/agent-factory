# 已加载 confirm-protocol.md

## 确认单标准格式

确认单必须包含以下六个字段：

1. **背景**：为什么要做这个任务（What/Why）
2. **执行步骤**：将要执行哪些具体操作（How，具体到命令/配置项）
3. **风险点**：可能出现的问题及影响
4. **推荐方案**：如有多种做法，给出推荐及理由
5. **推荐理由**：为什么推荐这个方案
6. **需确认问题**：明确列出需要用户回答的问题

---

## 确认结果类型

| 结果 | 含义 | 后续动作 |
|---|---|---|
| APPROVED | 确认通过 | 继续执行 |
| REJECTED | 确认不通过 | 重新规划，回到 PLAN |
| CHANGE_REQUESTED | 要求修改 | 修改后重新提交确认 |
| DEFERRED | 暂缓 | 暂停执行，等待时机 |

---

## 多轮确认规则

- state.json 维护 `confirmCount` 字段，初始为 0
- 每次用户提交确认（APPROVED/REJECTED/CHANGE_REQUESTED），`confirmCount += 1`
- `confirmCount ≥ 3` 时，输出 JSON 介入提示：
  ```json
  {"type": "INTERVENTION_REQUIRED", "reason": "多轮未达成一致", "instanceId": "...", "confirmCount": 3}
  ```
- 介入选项：
  - 再给三轮（继续等待用户明确决策）
  - 带缺陷往下走（由主编排做出最终决定并记录）
- 主编排介入时填写 DECISIONS.md 介入记录表（分歧点/选项A/选项B/用户选择/缺陷清单）
