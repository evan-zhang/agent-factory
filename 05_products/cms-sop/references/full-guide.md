# 已加载 full-guide.md
<!-- guide-token: FULL-2026-Q1 | 版本标识，读取后写入 LOG.md 作可审计链路 -->

## 执行路径说明

Full 模式由主 Agent 调度子 Agent 执行，子 Agent spawn 时注入：

```python
task = f"""你是 SOP Full 模式的执行子 Agent。
【必读文件】：
1. read {instance_path}/state.json
2. read {instance_path}/TASK.md
3. read {skill_dir}/references/full-guide.md
4. read {skill_dir}/references/shared/state-machine.md
5. read {skill_dir}/references/shared/confirm-protocol.md
【当前任务】：{task_description}
【实例路径】：{instance_path}
【执行规则】：
- 所有操作结果必须写入对应文件（LOG.md/RESULT.md等）
- 不通过自由文本向主 Agent 传递结果
- 每次状态变更调用 update_state.py
- 需要用户确认时写入 DECISIONS.md 并停止执行，等待主 Agent 轮询
【禁止】：
- 直接输出最终结论（必须写文件）
- 修改 SKILL.md 或 references/ 下的文件
- spawn 二级子 Agent
"""
spawn_subagent(task)
```

---

## 七件套文件说明

### TASK.md（四件套之一）
- 元数据头：`mode: full`
- 继承声明区（升级时填写，正常创建留空）
- 任务目标、背景、范围、成功标准、执行计划

### LOG.md（四件套之二）
- 元数据头：`mode: full`
- 执行日志表（含 [ARTIFACT] 标记格式）
- 阶段摘要、阻塞记录

### RESULT.md（四件套之三）
- 元数据头：`mode: full`
- 完成情况、成功标准验收、变更清单、交付物索引

### HANDOVER.md（四件套之四）
- 交接信息、当前状态、待办事项

### PLAN.md（Full 新增）
- 执行步骤表（步骤/操作/负责方/预计耗时/依赖）
- 里程碑表（里程碑/目标时间/验收方式）
- 资源需求（人员/工具/外部依赖）
- 风险预案表（风险/概率/影响/预案）
- 回滚方案

### DECISIONS.md（Full 新增）
- 决策记录表（轮次/时间/决策主题/用户结论/用户意见/后续动作）
- 主编排介入记录表（3轮未达成一致时填写）

### ARTIFACTS.md（Full 新增）
- 自动收集产物表（从 LOG.md [ARTIFACT] 标记汇总）
- 手动补充产物表
- 交付确认

---

## 子 Agent 注入规范

1. 注入任务描述（task_description）
2. 注入实例路径和 skill 路径
3. 子 Agent 结果只写文件，不通过自由文本传递
4. 主 Agent 执行后只读 `state.json` 和 `RESULT.md`/`DECISIONS.md`

---

## 多轮确认机制

- 每次确认写入 DECISIONS.md 决策记录表
- state.json 维护 `confirmCount`
- `confirmCount ≥ 3` 时输出 JSON 介入提示，格式：
  ```json
  {"type": "INTERVENTION_REQUIRED", "reason": "多轮未达成一致", "instanceId": "...", "confirmCount": 3}
  ```
- 主编排介入：填写 DECISIONS.md 介入记录表，决定是"再给三轮"还是"带缺陷往下走"

---

## ARTIFACTS 自动收集规范

LOG.md 中产生交付物的行加 `[ARTIFACT]` 标记：

```markdown
| 时间 | EXECUTE | 发布 cms-sop v1.0.0 到 ClawHub [ARTIFACT] | OK | slug=cms-sop |
```

归档时扫描 LOG.md 所有含 `[ARTIFACT]` 的行，写入 ARTIFACTS.md 自动收集表。
