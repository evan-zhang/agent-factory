# DEV-REPORT — AF-20260330-002
# 慧集会议语义流处理器 · Phase A 交付报告

**项目编号**: AF-20260330-002
**日期**: 2026-03-30
**交付角色**: Assembler（交付总管）
**状态**: ✅ DONE

---

## 一、交付概览

Phase A 目标：在现有 `ai-huiji` v1.10.0 基础上，新增**会中实时语义流处理**能力（v1.10.1）。

| 交付物 | 文件 | 状态 |
|--------|------|------|
| 实时同步引擎 | `scripts/huiji/stream-sync.py` | ✅ 完成 |
| 语义事件处理器 | `scripts/huiji/event-processor.py` | ✅ 完成 |
| 自适应轮询调度器 | `scripts/huiji/poll-scheduler.py` | ✅ 完成 |
| SKILL.md 更新 | `SKILL.md`（v1.10.0 → v1.10.1） | ✅ 完成 |
| references/ | API 文档 + 现有脚本复制 | ✅ 完成 |
| requirements.txt | 依赖清单 | ✅ 完成 |

---

## 二、目录结构

```
04_execution/workspace/huiji-stream/
├── SKILL.md                          ← v1.10.1（新增"会中实时模式"章节）
├── requirements.txt
├── scripts/huiji/
│   ├── stream-sync.py               ← 核心：checkpoint + 增量拉取 + 事件生成
│   ├── event-processor.py           ← 事件消费：APPEND/REPLACE/DELETE + 滚动摘要
│   └── poll-scheduler.py            ← 自适应轮询：活跃2s/静默8s/断连恢复
├── references/
│   ├── openapi/huiji/               ← 5个 API 文档（从 source 复制）
│   └── scripts/huiji/               ← 6个现有脚本（从 source 复制）
└── .cache/                           ← SQLite DB（运行时自动创建）
    └── huiji_stream.db
```

---

## 三、核心设计实现

### 3.1 stream-sync.py

- **增量拉取**: `splitRecordListV2`，用 `lastStartTime` 作游标
- **Checkpoint 管理**: SQLite `checkpoints` 表，存储 `last_segment_id / last_start_time`
- **事件生成**:
  - APPEND: 新分片（version=1）
  - REPLACE: 二次转写（version=2，通过 `checkSecondSttV2` state=2 检测）
- **幂等键**: `UNIQUE(meeting_chat_id, segment_id, version)`
- **断连恢复**: `full_rollback_recovery()` 全量拉取，对比本地/远端片段数，补发缺失

### 3.2 event-processor.py

- **APPEND**: 追加新文本到 `fullText`，`new_fragments` 列表
- **REPLACE**: 静默替换旧文本，`fragments[seg_id].corrected=True`
- **滚动摘要**: 每 45 秒触发一次（`should_trigger_summary()`）
- **内存状态**: `MeetingState` 类，启动时从 DB 恢复，不丢状态

### 3.3 poll-scheduler.py

- **自适应间隔**: 活跃（近 10s 有新片段）→ 2s；静默（30s 无新片段）→ 8s
- **断连检测**: 连续 3 次失败 → 指数退避（2→4→8→16→30s）
- **并发限制**: 同时监控 ≤ 3 场会议
- **后台线程**: `threading.Thread` daemon 模式，`_poll_loop()` 顺序轮询所有流

### 3.4 SKILL.md 更新要点

- 版本从 v1.10.0 升至 v1.10.1
- 新增「会中实时模式」章节，包含：架构概览、启动条件、实时速记流（T+3s）、滚动摘要（T+30s）、会后自动切换、实时流命令表、事件模型、轮询策略、技术约束
- 意图路由表新增会中实时命令路由
- 能力树新增 `huiji-stream/` 子目录
- **不修改任何现有章节**，严格向后兼容

---

## 四、技术约束遵守情况

| 约束 | 实现方式 | 状态 |
|------|----------|------|
| 纯 Python | 只用标准库 + requests + sqlite3 | ✅ |
| 不引入 Redis/MySQL | SQLite 本地文件 `huiji_stream.db` | ✅ |
| 不修改现有脚本 | 现有 6 个脚本只复制到 references/，未改动 | ✅ |
| 防幻觉原则 | 沿用 SKILL.md 约束，事件内容直接来自平台 | ✅ |
| AppKey 鉴权 | `XG_BIZ_API_KEY` Header | ✅ |
| 生产域名 | `sg-al-ai-voice-assistant.mediportal.com.cn/api` | ✅ |
| 同时监控 ≤ 3 场 | `MAX_STREAMS = 3` | ✅ |

---

## 五、待后续 Phase 完成

以下内容为 Phase B/C 范畴，不在本次交付范围内：

| 内容 | Phase |
|------|-------|
| 二次转写替换 + 幂等/去重 | B（第2周） |
| 滚动摘要 + 行动项抽取 | B（第2周） |
| 断连恢复全量校验 | B（第2周，已预留接口） |
| 行动项抽取 + 会后一键纪要导出 | C（第3周） |
| 单元测试 / 集成测试 / 断连测试 | 验收阶段 |

---

## 六、验证建议

```bash
# 1. 语法检查
python3 -m py_compile scripts/huiji/stream-sync.py
python3 -m py_compile scripts/huiji/event-processor.py
python3 -m py_compile scripts/huiji/poll-scheduler.py

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置鉴权
export XG_BIZ_API_KEY=your_app_key_here

# 4. 手动测试增量拉取（有进行中会议时）
python3 scripts/huiji/stream-sync.py

# 5. 测试事件处理
python3 -c "
from scripts.huiji.event_processor import EventProcessor
p = EventProcessor('.cache/huiji')
print(p.get_current_view('test_id'))
"
```

---

**交付人**: Assembler
**日期**: 2026-03-30 08:45 GMT+8

---

## 七、W-01~W-04 修复记录（Phase A 验收 Warning 修复）

**修复日期**: 2026-03-30
**修复人**: Assembler（交付总管）
**触发原因**: Phase A 验收报告发现 4 个 Warning 项，需全部修复后方可关闭

---

### W-01：清理鉴权兼容性（stream-sync.py）

**问题**: `build_headers()` 同时发送 `access-token`（XG_USER_TOKEN）和 `appKey`（XG_BIZ_API_KEY），与 GRV 契约不符（契约只要求 appKey）。

**修复**: 删除 `XG_USER_TOKEN` / `access-token` 相关逻辑，统一只使用 `XG_BIZ_API_KEY` + `appKey` Header。未设置时抛出明确错误。

**影响文件**: `scripts/huiji/stream-sync.py`

---

### W-02：统一 HTTP 客户端（stream-sync.py + requirements.txt）

**问题**: `requirements.txt` 声明 `requests>=2.28.0`，但代码实际使用 `urllib.request` + `ssl`，两者不一致。

**修复**:
- 删除 `import urllib.request` 和 `import ssl`
- 新增 `import requests`
- 将 `_call_api()` 改为使用 `requests.post()`，保持相同的重试逻辑（MAX_RETRIES=3，RETRY_DELAY=1s）
- `requests.txt` 中的 `requests>=2.28.0` 保持不变

**影响文件**: `scripts/huiji/stream-sync.py`（requirements.txt 无需变动，声明已正确）

---

### W-03：修复摘要计时器逻辑（event-processor.py）

**问题**: `update_summary_timer()` 在每次有新事件时重置 `last_summary_at`，导致高频场景下摘要永不触发（计时器总被重置）。

**修复**:
- 将单一的 `last_summary_at` 拆分为两个独立时间戳：
  - `last_event_at`：上次有新事件的时间（仅用于活跃度判断）
  - `last_summary_triggered_at`：上次触发摘要的时间（摘要间隔计算基准）
- `update_summary_timer()` 只更新 `last_event_at`，不再影响摘要触发计时
- `should_trigger_summary()` 基于 `last_summary_triggered_at` 计算，与事件频率无关
- 新增 `mark_summary_triggered()`，在摘要触发后更新 `last_summary_triggered_at`
- `process_events()` 中：触发摘要时自动调用 `mark_summary_triggered()`
- `trigger_summary()` 中：同步调用 `state.mark_summary_triggered()`
- 返回字段名由 `last_summary_at` 更名为 `last_summary_triggered_at`

**影响文件**: `scripts/huiji/event-processor.py`

---

### W-04：断连恢复后自动触发全量校验（poll-scheduler.py）

**问题**: `_do_poll()` 断连恢复成功后未自动调用 `full_rollback_recovery()`，违反 GRV"恢复后全量校验"要求。

**修复**:
- 在 `_StreamState` 中新增 `was_recovering: bool` 标志（默认 False）
- `record_success()` 中：在重置 `consecutive_fails` 之前，先判断当前是否处于恢复状态（`consecutive_fails >= MAX_CONSECUTIVE_FAILS`），并将结果记录到 `was_recovering`
- `_do_poll()` 中：在正常 `sync()` 之前，检测 `state.was_recovering`，若为 True 则先调用 `syncer.full_rollback_recovery()`，完成后重置 `state.was_recovering = False`

**影响文件**: `scripts/huiji/poll-scheduler.py`

---

### 修复状态汇总

| Warning ID | 文件 | 修复状态 |
|------------|------|----------|
| W-01 | stream-sync.py | ✅ 已修复 |
| W-02 | stream-sync.py | ✅ 已修复 |
| W-03 | event-processor.py | ✅ 已修复 |
| W-04 | poll-scheduler.py | ✅ 已修复 |

---

# Phase B 交付报告

**交付日期**: 2026-03-30
**交付角色**: Assembler（交付总管）
**基线版本**: v1.10.1（Phase A）
**交付版本**: v1.10.2

---

## 一、Phase B 目标回顾

| 目标 | 描述 |
|------|------|
| B1 | 二次转写替换完善（REPLACE 事件串联到展示层，附带 original_text） |
| B2 | 幂等/去重强化（_load_from_db 恢复时 APPEND+REPLACE 合并去重） |
| B3 | 滚动摘要实现（每 45s 产出结构化摘要卡片，内置轻量摘要引擎） |

---

## 二、交付物清单

| 文件 | 操作 | 状态 |
|------|------|------|
| `scripts/huiji/summarizer.py` | 新建 | ✅ 完成 |
| `scripts/huiji/event-processor.py` | 修改 | ✅ 完成 |
| `scripts/huiji/poll-scheduler.py` | 修改 | ✅ 完成 |
| `SKILL.md` | 修改（v1.10.1 → v1.10.2） | ✅ 完成 |
| `04_execution/state.json` | 更新（phase_b: done） | ✅ 完成 |

---

## 三、核心实现说明

### 3.1 summarizer.py（新建）

**定位**：轻量滚动摘要引擎，纯本地实现，不依赖外部 LLM API。

**三大提取能力**：

| 能力 | 实现方式 |
|------|----------|
| 主题提取 | 正则提取 2~8 字中文词组，词频排序，排除停用词（约 80 词），返回出现≥2次的 Top-8 |
| 决策识别 | 三组正则匹配：`决定|确定|同意|通过|批准`、`(大家/会议/我们)一致/决定/确认`、`已/将/下一步` 引导句 |
| 行动项抽取 | 正则 `([^，。]{2,8})(负责|跟进|提交|完成|处理|推进|落实|确认|安排)([^，。]{2,30})` |

**摘要文本**：取最近 10 条片段拼接，不超过 500 字。

**持久化**：写入 SQLite `summaries` 表（UPSERT），向后兼容旧表（自动 `ALTER TABLE ADD COLUMN decisions`）。

**接口**：
- `Summarizer(db_path)` — 初始化，自动确保表结构
- `Summarizer.generate(meeting_chat_id, fragments) -> dict` — 产出摘要卡片并持久化
- `Summarizer.get_latest(meeting_chat_id) -> dict|None` — 从 SQLite 读取最新摘要

---

### 3.2 event-processor.py（B1 + B2 + B3 修改）

**B1 — REPLACE 展示完善（get_fragments）**

修改后 fragment 格式：
```python
{
    "startTime": 120034,
    "realTime": 1716349200000,
    "text": "校正后文本（若有）或原始文本",
    "corrected": True/False,
    "original_text": "原始文本（仅 corrected=True 时存在）"
}
```
- `original_text` 字段仅在 `corrected=True` 时附带，减少冗余传输
- `add_fragment()`、`replace_fragment()` 全部统一维护 `original_text`

**B2 — _load_from_db 去重强化**

原实现：REPLACE 只更新 corrected_text，未维护 original_text；且恢复顺序可能导致 original_text 丢失。

修改后：
- 按 `id ASC` 顺序处理（保证 APPEND 先于 REPLACE）
- APPEND 处理时额外保存 `_raw_text`（内部临时字段）
- REPLACE 处理时：`original_text = _raw_text`，`text = REPLACE.text`，`corrected=True`
- 全部加载完成后清理 `_raw_text` 临时字段
- 兼容"只有 REPLACE 无 APPEND"的极罕见情况

**B3 — Summarizer 集成**

- `process_events()` 中，触发摘要时自动调用 `_run_summarizer()`（best-effort，失败不影响主流程）
- `trigger_summary()` 返回结果中包含 `summary_card` 字段
- 新增 `get_latest_summary()` 方法，供 `poll-scheduler.py` 的 `get_current_text()` 调用
- `process_events()` 返回值新增 `latest_summary` 字段

---

### 3.3 poll-scheduler.py（Phase B 修改）

**摘要触发串联**：
- `_do_poll()` 检测到 `view["summary_trigger"]=True` 时，显式调用 `EventProcessor.trigger_summary()`
- 作为 `process_events()` 内部摘要触发的双重保险（防止内部静默失败遗漏）

**get_current_text() 增强**：
```python
{
    "ok": True,
    "full_text": "...",
    "latest_summary": {摘要卡片} 或 None,   # Phase B 新增
    "fragment_count": 42,
    "status": "active",
    "last_sync_at": 1716349200000
}
```
- `latest_summary` 通过 `EventProcessor.get_latest_summary()` 从 SQLite 读取

---

### 3.4 SKILL.md 更新（v1.10.1 → v1.10.2）

- 版本号更新为 v1.10.2
- 「滚动摘要」小节更新：
  - 明确每 45s 自动更新
  - 说明摘要内容（议题关键词、决策记录、行动项列表）
  - 说明使用 `stream-status <meetingChatId>` 可随时查看最新摘要
  - 说明使用内置轻量引擎，不依赖外部 LLM API

---

## 四、技术约束遵守

| 约束 | 状态 |
|------|------|
| 纯标准库 + sqlite3，不引入 spacy/jieba/transformers | ✅ summarizer.py 只用 re、json、sqlite3、time |
| best-effort 摘要，不影响主流程 | ✅ _run_summarizer() 捕获所有异常，失败返回 None |
| 向后兼容，不破坏 Phase A 接口 | ✅ process_events/get_current_view/trigger_summary 签名不变 |
| get_fragments() 新字段向后兼容 | ✅ original_text 仅 corrected=True 时附带 |
| SQLite 表结构兼容 | ✅ ALTER TABLE ADD COLUMN decisions（幂等，失败忽略） |

---

## 五、语法验证

```bash
python3 -m py_compile scripts/huiji/summarizer.py      # ✅ OK
python3 -m py_compile scripts/huiji/event-processor.py # ✅ OK
python3 -m py_compile scripts/huiji/poll-scheduler.py  # ✅ OK
```

---

**交付人**: Assembler
**日期**: 2026-03-30 09:10 GMT+8

---

## 八、最终收口（2026-03-30）

- Phase B 最终验收：**PASS**
- 修复项：SKILL.md 中两处 T+30s 文案已统一修正为 T+45s
- 最终验收记录：`05_closure/ACCEPTANCE-PHASE-B-20260330.md`


---

## 九、范围锁定交付：会议素材镜像器（meeting-id transcript only）

**交付日期**: 2026-03-30  
**交付角色**: Assembler（交付总管）  
**范围约束**: 仅 meetingChatId 文本素材拉取与落盘，不包含总结/问答/纪要增强。

### 9.1 目标脚本（最小可用）

已在 `04_execution/workspace/huiji-stream/scripts/huiji/` 实现/补齐：

1. `pull-meeting.py <meetingChatId> [--name ...] [--force]`
2. `meeting-status.py <meetingChatId>`
3. `stop-pull.py <meetingChatId>`

### 9.2 落盘结构

每场会议写入：`materials/{meetingChatId}/`

- `manifest.json`
- `checkpoint.json`
- `fragments.ndjson`
- `transcript.txt`
- `pull.log`
- `.stop`（可选）

### 9.3 关键逻辑落实

- 去重主键：`meetingChatId + segment_id + version`
- 已拉完跳过：`manifest.is_fully_pulled=true` 且未 `--force` 时直接返回 `skipped`
- 已结束会议：一次全量拉取收口，状态置 `completed` + `is_fully_pulled=true`
- 进行中会议：按 `checkpoint.last_start_time` 增量拉取，轮询检测结束后自动收口
- fail-soft：异常写入 `pull.log`，不覆盖/破坏既有落盘文件

### 9.4 文档与状态同步

- `SKILL.md` 已新增「会议素材镜像器（meeting-id transcript only）」章节
- `04_execution/state.json` 已更新：
  - `scope_mode: "meeting-id-transcript-only"`
  - `materials_pipeline: "done"`

### 9.5 语法验证

```bash
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/meeting-status.py
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/stop-pull.py
```

验证结果：✅ 全部通过。

### 9.6 示例命令（无需联网）

```bash
# 1) 拉取会议（首次）
python3 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py huijiXgMt_demo123 --name "产品周会"

# 2) 查询本地镜像状态
python3 04_execution/workspace/huiji-stream/scripts/huiji/meeting-status.py huijiXgMt_demo123
python3 04_execution/workspace/huiji-stream/scripts/huiji/meeting-status.py huijiXgMt_demo123 --json

# 3) 请求停止进行中的增量轮询
python3 04_execution/workspace/huiji-stream/scripts/huiji/stop-pull.py huijiXgMt_demo123

# 4) 强制重拉（忽略 is_fully_pulled）
python3 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py huijiXgMt_demo123 --force
```

---

## 十、入口优化：AppKey 自动发现会议ID

**交付日期**: 2026-03-30  
**交付角色**: Assembler（交付总管）

### 10.1 新增能力

- 新增 `scripts/huiji/list-my-meetings.py`：基于 `chatListByPage` 列出当前 appKey 可访问会议（默认最近 20 条）。
- 人类可读输出包含：序号、meetingChatId（优先 `originChatId`，否则自动剥离 `_id` 的 `__后缀`）、会议名、状态、更新时间（可读时间）。
- 支持参数：
  - `page_num`（默认 0）
  - `page_size`（默认 20）
  - `--state {0,1,2,3}`
  - `--name-blur <关键词>`
  - `--json`

### 10.2 pull-meeting.py 入口增强

保留原有 `pull-meeting.py <meetingChatId>` 用法不变，并新增：

- `--auto`：自动发现会议并选择 meetingChatId
- `--pick-index <n>`：在候选列表中按 1-based 序号选择
- `--prefer-state <0|2>`：默认 0（优先进行中）；无匹配时回退到最近列表

选择逻辑：
1. `--auto` 且未显式传 `meetingChatId` 时，先拉取最近可访问会议
2. 按 `--prefer-state` 优先筛选
3. 若传 `--pick-index`，按候选序号选
4. 否则自动取第一条

选不到会议时：返回明确错误，并提示先执行 `list-my-meetings.py` 查看列表后再拉取。

### 10.3 文档同步

- 已更新 `SKILL.md` 的「会议素材镜像器」章节：新增「推荐入口（AppKey 自动发现）」并给出两种用法：
  1) 自动发现 + 拉取（推荐）
  2) 已知 meetingChatId 直接拉取（兼容）

### 10.4 自检记录

```bash
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/list-my-meetings.py

python3 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py --help
python3 04_execution/workspace/huiji-stream/scripts/huiji/list-my-meetings.py --help
```

结果：✅ 通过（语法检查 + 帮助命令均可用）

---

## 十一、列表可用性优化

**交付日期**: 2026-03-30  
**交付角色**: Assembler（交付总管）

### 11.1 会议列表排序策略升级（list-my-meetings.py）

- 默认排序改为：**进行中优先（state=0）→ 更新时间倒序**。
- 当显式传入 `--state` 过滤时，排序改为：**更新时间倒序**（不再做进行中优先分组）。
- 为便于排查排序行为，`--json` 输出新增 `sort_key` 字段。

### 11.2 人类可读输出增强（非 --json）

每条会议现在至少展示：

- 序号
- 会议名称
- meetingChatId
- 状态（进行中/处理中/已完成/失败）
- 更新时间（可读时间）
- 创建时间（可读时间）
- 录制人/发起人（creatorName/ownerName/userName 等择优）
- 会议号（若可得）
- 会议时长（毫秒转可读）

并在列表末尾追加：

- 推荐候选（优先进行中第一条；若无则最近已完成第一条）
- 对应拉取示例命令：`python3 scripts/huiji/pull-meeting.py --auto --pick-index <n>`

### 11.3 JSON 输出增强（--json）

`meetings[]` 现包含以下关键字段（可为 null）：

- `index`
- `meetingName`
- `meetingChatId`
- `state` / `stateText`
- `updateTime` / `updateTimeText`
- `createTime` / `createTimeText`
- `ownerName`
- `meetingNumber`
- `meetingLengthMs` / `meetingLengthText`
- `sort_key`

并新增 `recommended` 节点，便于调用方直接消费推荐候选。

### 11.4 --auto 联动升级（pull-meeting.py）

- `--auto` 的候选选择逻辑已与列表排序完全对齐：默认进行中优先 + 更新时间倒序。
- `--pick-index` 仍按候选集 1-based 选择，兼容原行为。
- 日志新增自动选择明细：**名称 + 状态 + 更新时间**，便于审计和回放。

### 11.5 文档同步

- `SKILL.md` 的列表示例已补充说明：`list-my-meetings.py` 默认"进行中优先"，且会给出推荐候选与 `--pick-index` 示例。

### 11.6 自检

```bash
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/list-my-meetings.py
python3 -m py_compile 04_execution/workspace/huiji-stream/scripts/huiji/pull-meeting.py
```

结果：✅ 通过。


## 十二、120秒调度护栏化改造（v1.10.6）

**改造目标**：将进行中会议拉取改为“调度驱动短任务模式”，避免主会话阻塞，并支持用户提前触发一次。

### 12.1 新增与改造文件

- 新增 `scripts/huiji/pull_core.py`：抽离单次拉取核心逻辑（供 pull-once / pull-meeting 共用）
- 新增 `scripts/huiji/pull-once.py`：单次增量拉取后退出
- 新增 `scripts/huiji/trigger-pull.py`：用户提前触发一次
- 改造 `scripts/huiji/pull-meeting.py`：兼容入口，内部循环调用 short-runner（默认 120s）
- 改造 `scripts/huiji/meeting-status.py`：新增锁/停机/熔断/空跑计数输出
- 更新 `SKILL.md`：版本升级到 v1.10.6，新增“调度驱动模式（120s）+ trigger”章节

### 12.2 三大护栏实现

1. **互斥锁**：同会议粒度 `{gateway}:{meetingChatId}` lockfile（TTL=150s）；获取失败返回 `skipped_locked=true`
2. **自动停机**：
   - 明确结束（`status=completed`）
   - 连续 3 次无增量且非 active
   - 运行超过 10 小时 TTL
3. **退避 + 熔断**：
   - 429/5xx/网络类 → 30→60→120→300 秒指数退避 + 抖动
   - 连续失败 ≥5 → 熔断 15 分钟（返回 `skipped_circuit_open`）
   - 4xx 参数类错误 → terminal fail，不重试

### 12.3 manifest 新增字段

- `started_at`
- `stopped_at`
- `stopped_reason`
- `consecutive_empty_polls`
- `consecutive_failures`
- `circuit_open_until`
- `last_error`
- `next_retry_after`
- `lock`（锁元数据）


## 十三、Issue #4 修复（v1.10.7）

**修复日期**: 2026-03-30  
**交付角色**: Assembler（交付总管）  
**目标**: 修复依赖文档、缺失脚本、子代理通知、_id 透明化四项问题，形成可发布补丁。

### 13.1 高优先：依赖与文档

- 已移除 `SKILL.md` frontmatter 中 `dependencies: cms-auth-skills`。
- 鉴权章节明确：仅需 `XG_BIZ_API_KEY`，无需 `cms-auth-skills`。
- 新增「快速开始（1分钟）」：
  1) 设置 `XG_BIZ_API_KEY`
  2) `list-my-meetings.py --json` 验证
  3) `list-by-meeting-number.py --json` 验证会议号查询

### 13.2 高优先：新增 list-by-meeting-number.py

新增文件：`scripts/huiji/list-by-meeting-number.py`

- 必填参数：`meetingNumber`
- 可选参数：`--last-ts`、`--json`
- 接口：`/open-api/ai-huiji/meetingChat/listHuiJiIdsByMeetingNumber`
- 输出字段：`chatId/open/isDoneRecordingFile/start/stop`
- 错误处理：业务错误与网络错误均输出清晰失败原因
- 鉴权风格：与 `pull-meeting.py` 同源（复用 `pull_core` 的 header/API 调用风格）

### 13.3 中优先：子代理主动通知（notify-file）

已为下列脚本新增 `--notify-file <path>`：

- `scripts/huiji/pull-once.py`
- `scripts/huiji/trigger-pull.py`

行为：执行结束后追加写入 JSONL 单行事件，至少包含：
- `meetingChatId`
- `status`
- `new_fragments`
- `timestamp`

### 13.4 中优先：_id 后缀透明化

修改文件：`scripts/huiji/list-my-meetings.py`

- `--json` 输出新增：
  - `rawId`
  - `originChatId`
  - `normalizedMeetingChatId`
  - `idNormalizationApplied`
- 文本模式新增归一化提示（仅后缀截断时显示）：
  - `ID 归一化: <rawId> -> <meetingChatId>`
- 同步更新 `SKILL.md` 的「_id 透明处理（对 AI 可见）」说明。

### 13.5 版本与兼容性

- `SKILL.md` 版本：`v1.10.6 -> v1.10.7`
- 现有命令参数保持兼容；新增参数均为可选，不影响旧调用。

### 13.6 验证

```bash
python3 -m py_compile scripts/huiji/*.py
```

结果：✅ 通过。

