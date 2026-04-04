# HEARTBEAT.md

运行 sessions_list，检查是否有 Sub-Agent 正在执行。
如果有：列出任务名称和当前状态，发送给用户。
如果全部空闲且无异常：回复 HEARTBEAT_OK，不打扰用户。
