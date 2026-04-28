# HEARTBEAT.md

## 每次心跳检查（每 30 分钟）

### Step 1：检查 Sub-Agent 状态

运行 `subagents list`，检查是否有 Sub-Agent 正在执行。

- 如果有异常（卡死超10分钟）：报告给用户。
- 如果全部空闲或正常运行：回复 HEARTBEAT_OK，不打扰用户。
