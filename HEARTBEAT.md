# HEARTBEAT.md

## 每次心跳检查（每 2 分钟）

### Step 1：检查 Sub-Agent 状态
运行 `subagents list`，检查是否有 Sub-Agent 正在执行。

- 如果有：列出任务名称和当前状态，发送给用户。
- 如果全部空闲：进入 Step 2。

### Step 2：检查运行时数据（外在验证）

**检查 `_runtime/experience/corrections.md`**
- 最后更新时间是什么时候？
- 如果超过 7 天没有新记录，说明 Orchestrator 可能没有在做自我反省

**检查 `_runtime/experience/patterns.md`**
- 最后更新时间是什么时候？
- 如果超过 14 天没有新记录，说明可能没有沉淀经验

### Step 3：报告异常

如果发现异常，发送给用户：
```
⚠️ 经验沉淀异常：
- corrections.md 最后更新：[时间]
- patterns.md 最后更新：[时间]
建议：请 Orchestrator 检查是否需要补充记录。
```

### Step 4：正常时回复
如果全部正常：回复 HEARTBEAT_OK，不打扰用户。
