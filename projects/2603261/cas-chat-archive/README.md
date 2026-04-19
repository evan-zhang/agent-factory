# CAS Chat Archive

CAS (Chat Archive System) 是一个 append-only 的聊天记录归档系统，专为 OpenClaw Gateway 设计。

## 特性

- **全量记录**: 记录所有用户消息和助手回复
- **附件归档**: 自动归档所有上传和下载的文件
- **Append-only**: 不覆盖、不删除历史记录
- **会话分段**: 自动按 30 分钟间隔分割会话
- **并发安全**: 使用文件锁保护并发写入
- **双发布**: 支持 ClawHub 和公司内部市场
- **作用域可选**: 支持 gateway 级或 agent 隔离归档（测试阶段默认 gateway）
- **手动复盘**: 支持日/周/月复盘文档生成与分享去重台账

## 目录结构

```
~/.openclaw/chat-archive/
└── {gateway}/
    ├── logs/
    │   └── YYYY-MM-DD.md
    ├── assets/
    │   └── YYYY-MM-DD/
    │       ├── inbound/
    │       └── outbound/
    ├── meta/
    │   └── session-state.json
    └── agents/                    # scope-mode=agent 时使用
        └── {agent-id}/
            ├── logs/YYYY-MM-DD.md
            ├── assets/YYYY-MM-DD/{inbound,outbound}
            └── meta/session-state.json
```

## 运行要求

- Python **3.10+**
- Node.js（仅在本地运行 internal hook 测试时需要）

## 安装

### 方式 1: 从 ClawHub 安装

```bash
clawhub install cas-chat-archive
```

### 方式 2: 从公司内部市场安装

```bash
# 根据公司内部市场配置
clawhub install cas-chat-archive --registry <internal-registry>
```

## 使用

### 1. 初始化归档目录

```bash
python3 scripts/cas_archive.py init --gateway life
```

### 2. 记录消息

```bash
# 记录用户消息（gateway级）
python3 scripts/cas_archive.py record-message \
  --gateway life \
  --direction inbound \
  --sender Evan \
  --text "你好"

# 记录助手回复（agent隔离）
python3 scripts/cas_archive.py record-message \
  --gateway life \
  --scope-mode agent \
  --agent factory-orchestrator \
  --direction outbound \
  --sender Assistant \
  --text "你好！有什么可以帮助你的？"
```

### 3. 归档附件

```bash
# 归档用户上传的文件
python3 scripts/cas_archive.py record-asset \
  --gateway life \
  --direction inbound \
  --source /path/to/file.pdf

# 归档助手生成的文件
python3 scripts/cas_archive.py record-asset \
  --gateway life \
  --direction outbound \
  --source /path/to/report.pdf
```

## Gateway 钩子集成

当前采用 OpenClaw internal hook：`cas-chat-archive-auto`（已支持 message:preprocessed/message:sent）。

环境变量：
- `CAS_ARCHIVE_ROOT`: 归档根目录 (默认: `~/.openclaw/chat-archive`)
- `CAS_SCOPE_MODE`: `gateway`（默认）或 `agent`（按 agent 隔离）
- `CAS_DISK_WARN_MB`: 低磁盘告警阈值（默认 500）
- `CAS_DISK_MIN_MB`: 低磁盘拒绝写入阈值（默认 200）
- `CAS_MAX_ASSET_MB`: 单附件大小上限 MB（默认 100）
- `CAS_ALLOWED_ATTACHMENT_ROOTS`: 额外允许的附件根目录（多个目录用系统 path 分隔符）
- `CAS_STRICT_MODE`: 严格模式（默认 false）。默认 fail-soft，不影响用户主流程。

说明：测试阶段建议默认 `CAS_SCOPE_MODE=gateway`，验证稳定后再切换 `agent`。

## 发布

### 发布到 ClawHub

```bash
python3 scripts/publish.py --channel clawhub --version 1.0.0 --changelog "Initial release"
```

### 发布到公司内部市场

```bash
export CAS_INTERNAL_REGISTRY=/path/to/internal/registry
python3 scripts/publish.py --channel internal --version 1.0.0 --changelog "Initial release"
```

### 双通道发布

```bash
python3 scripts/publish.py --channel both --version 1.0.0 --changelog "Initial release"
```

## 日志格式示例

```markdown
# Chat Log — 2026-03-26
# Gateway: life
# Mode: append-only

---

## Session #1 — 14:23:01

**[INBOUND]** 14:23:01 | Evan
> 你好，帮我查一下今天的日程

**[OUTBOUND]** 14:23:45 | Assistant
> 好的，正在为你查询...

**[ASSET]** 14:23:45 | out | schedule.pdf
> Path: assets/2026-03-26/outbound/out-2026-03-26-14-23-45-schedule.pdf
> Size: 245678 bytes | MIME: application/pdf
```

## 运营查询（推荐）

使用内置查询脚本（更适合“今天存了多少会话/备份情况”）：

```bash
# 今日备份总览（所有 gateway）
python3 scripts/cas_inspect.py report --gateway all

# 指定某个 gateway
python3 scripts/cas_inspect.py report --gateway life

# 查询今天日志里某个关键词
python3 scripts/cas_inspect.py search --gateway all --query "关键词" --ignore-case
```

它会输出：会话数、in/out条数、资产条数、日志字节数、附件字节数。

## 手动复盘与去重分享（推荐）

```bash
# 生成今日复盘（默认按agent视角）
python3 scripts/cas_review.py daily --scope-mode agent --gateway all --agent all --out-dir ./design/reviews

# 生成周复盘 / 月复盘
python3 scripts/cas_review.py weekly --week 2026-W13 --out-dir ./design/reviews
python3 scripts/cas_review.py monthly --month 2026-03 --out-dir ./design/reviews

# 查询某日是否已分享
python3 scripts/cas_review.py share-status --period daily --key 2026-03-27 --share-log ./design/SHARE-LOG.jsonl

# 标记已分享（避免重复）
python3 scripts/cas_review.py mark-shared --period daily --key 2026-03-27 --channel telegram:group:xxx --message-id 12345 --share-log ./design/SHARE-LOG.jsonl
```

默认策略：未分享优先；已分享跳过；除非用户明确“强制分享”。

## 搜索日志

使用 grep 或 ripgrep 搜索日志：

```bash
# 搜索关键词
grep "日程" ~/.openclaw/chat-archive/life/logs/*.md

# 搜索特定日期
grep "2026-03-26" ~/.openclaw/chat-archive/*/logs/2026-03-26.md

# 跨 Gateway 搜索
rg "关键词" ~/.openclaw/chat-archive/*/logs/
```

## 版本历史

- v1.0.0 (2026-03-26): 初始版本
  - append-only 消息记录
  - 附件归档
  - 会话分段
  - 并发安全
  - 双发布支持

## 许可证

MIT License
