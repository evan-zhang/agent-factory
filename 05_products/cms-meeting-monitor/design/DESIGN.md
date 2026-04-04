# DESIGN - cms-meeting-monitor

## 1) 目标
- 从 CMS AI慧记 持续拉取会议内容，支持实时监控和后台静默两种模式。
- 不做 AI 分析——分析由主 Agent 调用 LLM 处理。

## 2) 边界（不做什么）
- 不做会议内容分析/摘要。
- 不替代 CMS AI慧记 的主服务。
- 不存储会议内容（只负责拉取和推送）。

## 3) 核心流程

### Caption 模式（实时推送）
1. Cron Job 每 60 秒触发（agentTurn）
2. `monitor.py tick` 拉取最新片段
3. 有新内容 → `notifier.py` 构建消息 → `message.send` 推送到当前会话
4. 无新内容 → 不发消息

### Silent 模式（后台拉取）
1. Cron Job 每 60 秒触发（systemEvent）
2. `monitor.py tick` 拉取最新片段
3. 有新内容 → 更新状态消息的 reaction 作为心跳
4. 不主动发消息打扰用户

## 4) Cron 触发设计
- Caption 模式：`payload.kind = "agentTurn"`，由 agent 决定是否调用 message.send
- Silent 模式：`payload.kind = "systemEvent"`，固定通知文本通过 announce 投递

## 5) 依赖
- 环境变量：`XG_BIZ_API_KEY`
- 脚本：`monitor.py`（拉取）、`notifier.py`（通知构建）
