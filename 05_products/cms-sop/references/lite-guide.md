# 已加载 lite-guide.md
<!-- guide-token: LITE-2026-Q1 | 版本标识，读取后写入 LOG.md 作可审计链路 -->

## 五步执行流程

```
TARGET → PLAN → CHECKLIST → EXECUTE → ARCHIVE
```

**TARGET（目标）**：明确任务目标，记录到 TASK.md，stage 设为 TARGET
**PLAN（计划）**：制定执行步骤，识别风险，stage 设为 PLAN
**CHECKLIST（确认）**：生成确认单，请求用户确认，checklistConfirmed=true 后才可执行
**EXECUTE（执行）**：按计划执行，实时写 LOG.md，stage 设为 EXECUTE
**ARCHIVE（归档）**：填写 RESULT.md，stage 设为 ARCHIVE，status 设为 DONE

---

## 四件套文件说明

### TASK.md
- 元数据头：`mode: lite`，实例 ID、标题、负责人、创建时间
- 任务目标、背景、范围、成功标准
- 执行计划（步骤/操作/预计耗时/风险点）
- 决策记录表（追加制）

### LOG.md
- 元数据头：`mode: lite`
- 执行日志表（时间/阶段/操作/结果/备注）
- 阶段摘要表（阶段/完成时间/摘要/遗留问题）
- 阻塞记录表（时间/原因/解除时间/方式）

### RESULT.md
- 元数据头：`mode: lite`
- 完成情况、成功标准验收、变更清单
- 交付物索引、遗留问题、经验总结
- 用户确认区（结果/时间/意见）

### HANDOVER.md
- 交接信息（交出方/接入方/时间/原因）
- 当前状态、待办事项表、注意事项

---

## 确认单门禁规则

CHECKLIST 阶段必须生成标准确认单，包含：
- **背景**：任务目的
- **执行步骤**：具体操作序列
- **风险点**：可能的问题
- **推荐方案**：如有多种做法，给出推荐及理由
- **需确认问题**：明确列出

用户确认结果写入 RESULT.md 确认区：
- `APPROVED`：通过，继续执行
- `REJECTED`：不通过，重新规划
- `CHANGE_REQUESTED`：修改后重新确认
- `DEFERRED`：暂缓

**门禁**：checklistConfirmed=false 时，update_state.py 拒绝进入 RUNNING。

---

## 升级触发条件

执行中发现以下任一情况，立即调用 `scripts/upgrade.py`：
1. 预计耗时超过 20 分钟
2. 涉及 ≥ 2 个系统
3. 需要多轮人工确认
4. 需要发布/重启等高影响操作

升级后原 Lite 实例 status 设为 UPGRADED，Full 实例新建。
