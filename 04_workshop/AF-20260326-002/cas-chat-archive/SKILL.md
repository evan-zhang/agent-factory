---
name: cas-chat-archive
version: 1.1.1
description: Append-only chat archive operations for OpenClaw gateways with optional agent-isolated scope. Use when initializing archive folders, recording inbound/outbound messages, storing attachments with timestamped sanitized filenames, generating daily backup reports/search, and running manual daily/weekly/monthly review + share-dedup workflows under ~/.openclaw/chat-archive/<gateway>/.
metadata:
  openclaw:
    requires:
      bins: [python3]
      python: ">=3.10"
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
