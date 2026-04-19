---
name: cas-chat-archive
version: 1.2.0
description: Append-only chat archive operations for OpenClaw gateways with optional agent-isolated scope. Use when initializing archive folders, recording inbound/outbound messages, storing attachments with timestamped sanitized filenames, generating daily backup reports/search, and running manual daily/weekly/monthly review + share-dedup workflows under ~/.openclaw/chat-archive/<gateway>/.
metadata:
  openclaw:
    requires:
      bins: [python3]
      python: ">=3.10"
---

## ⚡ 快速开始（安装后必做）

安装完成后，向 AI 发送以下指令完成一键初始化：

> 帮我初始化 CAS 成长体系

AI 将自动创建三个复盘 cron 任务（每日日报/每周复盘/每月复盘），无需任何手工配置。

---

# CAS Chat Archive

Use `scripts/cas_archive.py` for deterministic archive writes.

Core commands:
- `init`: Create required folder tree and daily log header.
- `record-message`: Append INBOUND/OUTBOUND markdown blocks and auto-handle session boundaries.
- `record-asset`: Copy files into dated inbound/outbound asset folders and append ASSET blocks.
- `record-bundle`: Record a full inbound+outbound turn in one command (used by auto hook).
- `cas_inspect.py report|search`: Daily backup summary and log search for operator queries (gateway or agent scope).
- `cas_review.py daily|weekly|monthly|share-status|mark-shared`: Manual review generation and share dedup ledger operations.

Hardening defaults:
- Gateway name is validated (prevents path traversal like `../`).
- Lock wait has timeout (default 5s, configurable).
- Asset copy has size guard (default max 100MB, configurable).
- Disk thresholds are enforced (`--disk-warn-mb` default 500, `--disk-min-mb` default 200).
- Hook accepts only attachment paths from allowlisted roots.

Defaults:
- Archive root: `~/.openclaw/chat-archive`
- Session timeout: 30 minutes
- Log file: `logs/YYYY-MM-DD.md`
- Assets: `assets/YYYY-MM-DD/{inbound|outbound}`

Notes:
- Runtime baseline: Python 3.10+.
- Writes are append-only.
- Concurrent writes are guarded by file lock.
- Invalid filename characters are replaced with `_`.

## 成长复盘体系

> 时时有记录、日日有汇报、周周有总结、月月有复盘

cas-chat-archive 实现完整的四层成长闭环：

| 层次 | 触发时间 | 核心价值 |
|------|----------|----------|
| 实时归档 | 每条消息 | 完整记录人机协作过程 |
| 日报 Daily Growth Log | 每日 19:00（北京） | AI 经验沉淀 + 主人洞察 |
| 周复盘 Weekly Joint Review | 每周六 10:00（北京） | 跨 Agent 知识同步 + 致同伴 |
| 月复盘 Monthly Org Review | 每月最后周五 18:00（北京） | 组织治理 + 职能边界审查 |

安装后激活方式：通过 OpenClaw 聊天发送以下指令配置 cron：

- 日报：`请设置每天19点自动生成CAS日报`
- 周复盘：`请设置每周六10点自动生成CAS周复盘`
- 月复盘：`请设置每月最后一个周五18点自动生成CAS月复盘`
