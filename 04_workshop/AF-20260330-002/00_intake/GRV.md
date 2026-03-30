# GRV — 慧集会议语义流处理器 契约文档

**项目编号**：TPR-20260329-002
**版本**：v1.0
**日期**：2026-03-30
**起草**：三省工作台

---

## 1. 项目目标

在现有 `ai-huiji` Skill（v1.10.0）基础上，新增**会中实时语义流处理**能力，实现"会中优先、会后兼容"的会议智能助手。

## 2. 交付物

### 2.1 必须交付

| # | 交付物 | 说明 |
|---|--------|------|
| 1 | **实时同步引擎** (`stream-sync.py`) | 核心模块：checkpoint 管理 + 增量轮询 + 事件去重 + 二次转写修正 |
| 2 | **语义事件处理器** (`event-processor.py`) | APPEND/REPLACE/DELETE 事件消费 + 滚动摘要更新 |
| 3 | **自适应轮询调度器** (`poll-scheduler.py`) | 活跃 2s / 静默 8s 自适应切换 + 断连恢复 |
| 4 | **SKILL.md 更新** | 在现有 v1.10.0 基础上新增会中模式章节，保持会后能力不变 |
| 5 | **本地存储层** | SQLite 存储 checkpoint + 事件日志（不引入 Redis 等外部依赖） |

### 2.2 验收标准

**功能验收**：
- ✅ 指定一个进行中的会议，系统能在 8 秒内拉到新片段并可见
- ✅ 同一片段不会重复处理（幂等）
- ✅ 二次转写完成后自动替换旧文本
- ✅ 断网恢复后 60 秒内追平
- ✅ 会后模式（现有全部能力）不受影响

**质量验收**：
- 端到端延迟 P95 ≤ 8s
- 重复事件率 ≤ 0.5%
- 丢片段率 ≤ 0.1%
- 二次转写替换成功率 ≥ 99%

## 3. 技术架构

### 3.1 整体流程

```
慧集平台 API
    │
    ▼
poll-scheduler.py（自适应轮询调度）
    │
    ▼
stream-sync.py（增量拉取 + checkpoint）
    │
    ├─ 新片段 → APPEND 事件
    ├─ 二次转写完成 → REPLACE 事件
    │
    ▼
event-processor.py（语义处理）
    │
    ├─ 实时速记流（T+3s）
    ├─ 结构化卡片（T+30s 滚动更新）
    └─ 会后纪要（会议结束后）
```

### 3.2 Checkpoint 数据结构

```json
{
  "meetingChatId": "xxx",
  "lastSegmentId": "seg_12345",
  "lastStartTime": 120034,
  "lastChatPage": 3,
  "lastPollAt": 1716349200000,
  "secondSttVersion": {},
  "status": "active|completed"
}
```

### 3.3 事件模型

| 事件类型 | 触发条件 | 幂等键 |
|----------|----------|--------|
| APPEND | 新增分片（id > lastSegmentId） | meeting_id + segment_id |
| REPLACE | 二次转写完成（checkSecondSttV2 state=2） | meeting_id + segment_id + version |
| DELETE | 平台标记删除（如有） | meeting_id + segment_id |

### 3.4 本地存储（SQLite）

```sql
-- checkpoint 表
CREATE TABLE checkpoints (
  meeting_chat_id TEXT PRIMARY KEY,
  last_segment_id TEXT,
  last_start_time INTEGER,
  last_poll_at INTEGER,
  status TEXT DEFAULT 'active'
);

-- 事件日志表
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  meeting_chat_id TEXT,
  event_type TEXT,  -- APPEND/REPLACE/DELETE
  segment_id TEXT,
  version INTEGER DEFAULT 1,
  payload TEXT,     -- JSON
  processed INTEGER DEFAULT 0,
  created_at INTEGER,
  UNIQUE(meeting_chat_id, segment_id, version)
);

-- 滚动摘要缓存
CREATE TABLE summaries (
  meeting_chat_id TEXT PRIMARY KEY,
  summary_text TEXT,
  action_items TEXT,  -- JSON array
  topics TEXT,        -- JSON array
  updated_at INTEGER
);
```

### 3.5 轮询策略

```
会议活跃（近 10 秒有新片段）→ interval = 2s
会议静默（30 秒无新片段）  → interval = 8s
断连检测（连续 3 次失败）  → 进入恢复模式
恢复模式：指数退避（2s→4s→8s→16s，上限 30s）
恢复后：全量校验（对比本地 vs 远端片段数）
```

## 4. 接口使用映射

| 能力 | API | 说明 |
|------|-----|------|
| 发现任意进行中会议 | chatListByPage (state=0) | 入口：定时扫描或用户触发 |
| 增量拉取新片段 | splitRecordListV2 | 核心：lastStartTime 作游标 |
| 检测二次转写 | checkSecondSttV2 | 轮询检查，state=2 时拉取 |
| 全量校验（断连恢复） | splitRecordList | 对比本地与远端片段数 |
| 按会议号发现 | listHuiJiIdsByMeetingNumber | 用户指定会议号时使用 |

## 5. SKILL.md 新增章节结构

在现有 v1.10.0 的 SKILL.md 基础上，新增以下章节（**不修改现有内容**）：

```markdown
## 会中实时模式

### 启动条件
- 用户说"开始监控这场会议" / "实时跟踪"
- 或检测到进行中会议 + 用户确认

### 实时速记流
- 每 2-8 秒增量拉取
- 展示新增文本（T+3s）
- 二次转写到达时静默修正

### 滚动摘要
- 每 30-60 秒更新一次结构化卡片
- 包含：议题列表、关键决策、行动项

### 会后切换
- 检测到会议结束 → 自动切换到会后模式
- 生成完整纪要，保留会中所有修正

### 命令
- `start-stream <meetingChatId>` — 开始实时监控
- `stop-stream` — 停止监控
- `stream-status` — 查看当前监控状态
```

## 6. 约束与边界

1. **纯客户端实现**：不改造慧记平台，不引入外部中间件
2. **向后兼容**：现有会后能力（总结/待办/专题/共享）全部保留
3. **鉴权不变**：继续使用 appKey，无需新增鉴权
4. **存储轻量**：SQLite 本地文件，不依赖 Redis/MySQL
5. **防幻觉原则**：沿用现有 SKILL.md 的严格约束（禁止虚构时间/人物/数据/决策）
6. **隐藏技术细节**：用户只看到结果，不暴露轮询/缓存/事件等技术过程

## 7. 风险项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 平台无推送能力 | 需轮询，资源消耗 | 自适应间隔 + 静默时降低频率 |
| API 频率限制未知 | 可能被限流 | 内置限流保护 + 指数退避 |
| 二次转写延迟不确定 | 用户体验 | 先展示一转，静默替换 |
| 大量并发会议 | 本地存储/计算压力 | 限制同时监控数（建议 ≤3） |

## 8. 验收流程

1. **单元测试**：checkpoint 管理、事件去重、幂等处理
2. **集成测试**：用真实进行中会议跑一轮完整流程
3. **断连测试**：模拟网络中断后恢复
4. **性能测试**：验证 P95 延迟 ≤ 8s
5. **回归测试**：确认会后模式不受影响
