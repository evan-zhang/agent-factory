# Changelog

All notable changes to CAS Chat Archive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-03-28

### Fixed
- handler.ts: 修复硬编码脚本路径，改为基于 import.meta.url 动态解析，支持跨机器/跨用户安装
- SKILL.md: 补充 requires.python >=3.10 声明

## [1.1.0-rc1] - 2026-03-27

### Changed
- Release scope frozen to `life/ops/company` for this cycle (`code` deferred by product decision).
- Added release-closure SOP with go/no-go gates, rollback playbook, and 3-day observation criteria.
- Internal distribution executed via xgjk-skill toolchain and registered as internal skill (`code=cas-chat-archive`).

## [1.1.0-test.1] - 2026-03-27

### Fixed
- Timestamp parser now accepts RFC3339 `...Z` format on Python 3.10 (prevents bundle write failures from hook ISO strings).
- Publish packaging now includes `hooks/` and validates required archive entries.
- Test suite now covers internal hook `hooks/cas-chat-archive-auto/handler.ts` integration (agent scope + allowlist block).

### Changed
- Compatibility baseline clarified to Python 3.10+ for current codebase.

## [1.1.0-test] - 2026-03-27

### Added
- Agent-scope archive support (`--scope-mode agent --agent <id>`), with gateway mode kept as default for testing safety.
- Review workflow helper script `cas_review.py`:
  - generate daily/weekly/monthly review skeletons
  - share dedup checks (`share-status`)
  - share ledger writes (`mark-shared`)
- Inspect script enhancement: `cas_inspect.py` now supports gateway/agent scope.

### Changed
- Auto hook now forwards session-derived agent id and optional scope mode (`CAS_SCOPE_MODE`) to archive script.
- Documentation updated for test-phase rollout and manual-review mode.

### Notes
- Current rollout stage: **TESTING**.
- Recommended default during test: `CAS_SCOPE_MODE=gateway`; switch to `agent` after validation.

## [1.0.3] - 2026-03-27

### Added
- New `record-bundle` command to archive a full inbound/outbound turn in one process.
- Disk threshold controls: `--disk-warn-mb` and `--disk-min-mb`.
- Hook attachment allowlist:
  - defaults include `uploads/` and `state/media/{inbound,outbound}`
  - optional `CAS_ALLOWED_ATTACHMENT_ROOTS`
- Fail-soft hook mode by default (`CAS_STRICT_MODE=false`), to avoid impacting user-visible turn flow.

### Changed
- Hook now sends one bundle payload to archive script (fewer subprocess calls per turn).
- Session-state persistence uses unique temp files to avoid concurrent replace conflicts.
- Test suite expanded to 11 checks, including allowlist and concurrency regression.

### Fixed
- Concurrent `session-state.json.tmp` collision under multi-process writes.
- Arbitrary file attachment ingestion outside allowed roots.

## [1.0.0] - 2026-03-26

### Added
- Initial release
- Core archiving functionality (`cas_archive.py`)
  - Append-only message logging
  - Asset archiving with timestamped sanitized filenames
  - Session boundary detection (30-minute timeout)
  - File locking for concurrent write safety
- Gateway integration (`cas_hook.py`)
  - Post-response hook for automatic archiving
  - Environment variable configuration
- Dual-channel publishing (`publish.py`)
  - ClawHub public registry support
  - Company internal marketplace support
  - Package validation and .skill file generation
- Documentation
  - Comprehensive README with usage examples
  - Gateway configuration example
  - Search and retrieval guide
- Testing
  - Automated test suite (`test_cas.py`)
  - 6 test cases covering all core functionality
  - All tests passing

### Technical Details
- Python 3.8+ compatible
- Zero external dependencies (uses only stdlib)
- Cross-platform support (macOS, Linux)
- Default archive location: `~/.openclaw/chat-archive/`
- Session timeout: 30 minutes
- Log format: Markdown with blockquote styling
- Asset naming: `{direction}-{date}-{time}-{ms}-{filename}`

### Security
- Input validation and sanitization
- Safe filename handling (replaces invalid characters)
- File locking prevents race conditions
- No sensitive data in logs (attachments only store metadata)
