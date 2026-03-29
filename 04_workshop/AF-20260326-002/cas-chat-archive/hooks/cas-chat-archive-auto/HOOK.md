---
name: cas-chat-archive-auto
description: "Auto-archive inbound/outbound messages to local append-only chat logs with fail-soft behavior"
homepage: https://docs.openclaw.ai/automation/hooks
metadata:
  {
    "openclaw":
      {
        "emoji": "🗄️",
        "events": ["message:preprocessed", "message:sent"],
      },
  }
---

# CAS Chat Archive Auto Hook

Automatically archives inbound/outbound messages for this gateway into:

`~/.openclaw/chat-archive/<gateway>/`

Behavior:
- **Fail-soft by default**: archival failures won't break user-visible messaging flow.
- Archives inbound on `message:preprocessed` (after media understanding).
- Archives outbound on `message:sent` when send succeeds.
- Applies attachment allowlist defaults to gateway-local media/upload paths.

Optional env vars:
- `CAS_ARCHIVE_SCRIPT`
- `CAS_ARCHIVE_ROOT`
- `CAS_ALLOWED_ATTACHMENT_ROOTS`
- `CAS_MAX_ASSET_MB`
- `CAS_DISK_WARN_MB`
- `CAS_DISK_MIN_MB`
- `CAS_STRICT_MODE` (default false)
- `CAS_SCOPE_MODE` (`gateway` default, `agent` for per-agent isolated backup)
