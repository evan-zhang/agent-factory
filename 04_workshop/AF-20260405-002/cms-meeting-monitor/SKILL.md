---
name: cms-meeting-monitor
description: 从 CMS AI慧记 拉取会议内容，支持字幕模式和静默模式两种监控方式。字幕模式实时推送新片段；静默模式后台拉取，有新内容时通知。不做 AI 分析——分析由主 Agent 调用 LLM 处理。
metadata:
  requires:
    env: [XG_BIZ_API_KEY]
  version: v1.0.1
tools_provided:
  - name: monitor
    category: exec
    risk_level: medium
    permission: read
    description: 会议内容监控器，支持字幕模式和静默模式拉取
    status: active
  - name: notifier
    category: exec
    risk_level: medium
    permission: write
    description: 会议内容通知器，有新内容时推送给用户
    status: active
---

## API 文档

> ⚠️ **重要提示**：本 Skill 调用玄关开放平台 AI慧记 API，权威文档是玄关开放平台官方文档。
>
> **官方文档链接**：https://github.com/xgjk/dev-guide/tree/main/02.产品业务AI文档/AI慧记
>
> 本 Skill 的代码实现与官方文档完全一致。如需查看完整的 AI慧记 API 规范，请直接访问上述官方文档。

---

# CMS AI慧记 — 会议监控

**版本**: 1.0.0

**定位**：主 Agent 的监控工具，负责持续拉取会议内容 + 通知用户。不做分析，分析由主 Agent 调用 LLM 处理。

---

## 两种监控模式

### 🅰️ 字幕模式（实时推送）
- Cron Job 每 60 秒拉取一次
- 有新内容时，推送最新片段到当前会话
- 用户可以看到实时滚动的字幕感内容
- 用户可随时选中某段文字让主 Agent 处理

### 🅱️ 静默模式（后台拉取）
- Cron Job 每 60 秒拉取一次
- **不主动发消息打扰用户**
- 有新内容时，更新一条状态消息的 reaction 作为心跳
- 用户主动说"到现在聊了什么"时，主 Agent 才响应

---

## 启动监控

```
用户：帮我接入会议
  ↓
主 Agent：
  好的！请选择模式：
  🅰️ 字幕模式 — 实时推送新片段
  🅱️ 静默模式 — 后台拉取，有事才说
  
  用户选了 🅱️
    ↓
主 Agent：好的，静默监控已开启。你说"到现在"我就给你小结。
  💤 监控中
    
[后台 Cron Job 每60秒拉取，不打扰用户]

用户：到现在聊了什么？
    ↓
主 Agent：[读取 transcript.txt + LLM 总结]
    
    【30分钟小结】
    已确认：Q2目标1.2亿，华东区为重点
    讨论中：团队分工
    
    要继续还是有其他需求？
```

---

## 命令路由

| 用户意图 | 调用的脚本 |
|---------|-----------|
| 接入会议（选择模式） | `monitor.py start` |
| 查看监控状态 | `monitor.py status` |
| 停止监控 | `monitor.py stop` |
| 做阶段小结 | 主 Agent 读取 transcript.txt + LLM |

---

## 依赖

依赖于 `cms-meeting-materials` skill 的脚本：
- `trigger-pull.py` — 增量拉取
- `stop-pull.py` — 停止拉取
- `list-my-meetings.py` — 列出可接入的会议

---

## 状态存储

监控状态存放在：
```
~/.openclaw/cms-meeting-monitor/{gateway}/{meeting_chat_id}/
├── state.json       # 监控状态
├── last_fragment_count  # 上次拉取的片段数
└── cron_job_id      # Cron Job ID
```

---

## 环境变量

| 变量 | 必须 | 说明 |
|------|------|------|
| `XG_BIZ_API_KEY` | 是 | AI慧记 API 鉴权 |
| `CMS_MEETING_MONITOR_ROOT` | 否 | 状态存储根目录 |
| `OPENCLAW_GATEWAY` | 否 | 多 gateway 场景隔离 |
