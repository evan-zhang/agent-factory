# DISCOVERY — 慧集会议语义流处理器

**项目编号**：TPR-20260329-002
**日期**：2026-03-30
**编写**：三省工作台（编排 Agent）

---

## 1. 项目背景

AI慧记（Huiji）是公司内部的会议智能助手平台，提供语音转写、会议记录查询、二次改写等能力。当前已有基础 Skill（`ai-huiji` v1.10.0），支持：
- 查询会议列表（归属维度 / 会议号维度）
- 获取转写原文（全量 / 增量 / 二次改写）
- AI 分析（总结 / 待办提取 / 专题分析）

**痛点**：当前 Skill 是"会后模式"——会议结束后再拉取、再分析。但实际场景中，**会中实时消费 transcript 的价值远大于会后补总结**。

## 2. 核心需求

### 2.1 功能定位

**"会中优先、会后兼容"的会议语义流处理器。**

关键不是"会后总结"，而是"会中持续增量消费 transcript"。

### 2.2 会中实时同步（核心）

- **增量拉取**：基于 checkpoint 游标（last_segment_id / last_timestamp_ms）做短轮询增量同步
- **二次转写修正**：会议结束后，二次转写到达时静默修正旧文本，标注"已校正"
- **同步语义保障**：
  - 事件模型：APPEND（新增）/ REPLACE（二次转写修订）/ DELETE
  - 幂等键：meeting_id + segment_id + version
  - 顺序保证：按 event_time + segment_id 排序消费
  - 窗口聚合：每 30~60 秒做一次滚动摘要更新

### 2.3 会中体验分层

| 时间层 | 展示内容 |
|--------|----------|
| T+3~5秒 | 实时速记流（原始/一转文本） |
| T+10~30秒 | 结构化卡片（议题、决策、行动项） |
| 二次转写到达时 | 静默修正旧文本，标注"已校正" |

### 2.4 会后兼容

现有 Skill 的全部会后能力保持不变：
- 会议列表查询
- 全文获取与分析
- 待办提取、专题分析
- 共享资料机制

### 2.5 自适应轮询

- 会议活跃时：2 秒轮询间隔
- 会议静默时：8 秒轮询间隔
- 断连恢复后 60 秒内追平 backlog

## 3. 技术约束

### 3.1 API 能力

| 接口 | 路径 | 用途 |
|------|------|------|
| chatListByPage | /ai-huiji/meetingChat/chatListByPage | 列表查询 |
| listHuiJiIdsByMeetingNumber | /ai-huiji/meetingChat/listHuiJiIdsByMeetingNumber | 按会议号查询 |
| splitRecordList | /ai-huiji/meetingChat/splitRecordList | 全量分片转写 |
| splitRecordListV2 | /ai-huiji/meetingChat/splitRecordListV2 | **增量分片转写** |
| checkSecondSttV2 | /ai-huiji/meetingChat/checkSecondSttV2 | 二次改写状态 |

- **生产域名**：`https://sg-al-ai-voice-assistant.mediportal.com.cn/api`
- **鉴权**：appKey（Header），无需用户登录态
- **当前无 webhook / stream 推送能力**，需用拉模式

### 3.2 平台依赖

- 依赖 `cms-auth-skills` 做鉴权
- 运行环境：OpenClaw / EasyClaw

## 4. 验收硬指标

| 指标 | 目标值 |
|------|--------|
| 端到端延迟 P95 | ≤ 8s（从平台可读到 Skill 可见） |
| 重复事件率 | ≤ 0.5% |
| 丢片段率 | ≤ 0.1% |
| 二次转写替换成功率 | ≥ 99% |
| 断连恢复追平时间 | ≤ 60s |

## 5. 实施路线（建议）

| Phase | 周期 | 内容 |
|-------|------|------|
| A | 第1周 | 增量拉取 + checkpoint + 流展示 |
| B | 第2周 | 二次转写替换 + 幂等/去重 + 滚动摘要 |
| C | 第3周 | 行动项抽取 + 会后一键纪要导出 |

## 6. 输入物清单（已随交付包提供）

- `source/extracted/openapi/huiji/` — 5 个 API 文档
- `source/extracted/scripts/huiji/` — 6 个 Python 示例脚本
- `source/extracted/examples/huiji/` — 使用场景与触发条件
- `source/extracted/SKILL.md` — 现有 Skill 完整规范（v1.10.0）

## 7. 不做的事

- 不改造慧记平台本身（纯客户端/Skill 层实现）
- 不引入外部消息队列（Redis/SQLite 本地存储即可）
- 不做音视频处理（只处理文本流）
