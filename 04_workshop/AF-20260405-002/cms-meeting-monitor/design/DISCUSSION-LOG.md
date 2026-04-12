# DISCUSSION LOG - cms-meeting-monitor

## 2026-04-02 08:00~08:42 (Asia/Shanghai)
- 触发背景：cms-meeting-monitor 开发讨论，确定两种监控模式的 cron 触发机制
- 用户诉求：会议内容监控需要两种模式——字幕模式（实时推送）和静默模式（后台拉取）
- 关键讨论：
  - 字幕模式：Cron Job 每 60 秒拉取，有新内容时推送最新片段到当前会话
  - 静默模式：Cron Job 每 60 秒拉取，不主动发消息，有新内容时更新 reaction 作为心跳
- 关键决策：
  - **Caption 模式** → 方案 A（agentTurn + message.send，有新内容才发）
  - **静默模式** → 方案 B（systemEvent + announce，固定通知文本）
- 执行状态：
  - `monitor.py` — start/status/stop/tick 四个命令 ✅
  - `notifier.py` — 通知消息构建 ✅
  - SKILL.md cron 触发逻辑待更新（目前只在讨论中确认，未写入文档）
- 待办：
  - 将 caption/silent 两种模式的 cron 触发逻辑写入 SKILL.md
  - Validator 检查通过后正式发布
