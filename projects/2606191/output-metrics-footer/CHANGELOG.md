# Changelog

## v0.2.2 (2026-06-19)

- Fix: `latestUsage()` strict session isolation — no more cross-session data leakage (P0)
- Fix: use runtime `contextTokenBudget` from `llm_output` event instead of hardcoded table (P1)
- Fix: add `vip-newapi/glm-5.2` to MODEL_CONTEXT fallback table
- Followup: `recentBySession` Map cleanup mechanism (P2, tracked)

## v0.2.1 (2026-06-19)

- 从 `~/.openclaw/extensions/` 迁入工厂项目管理
- 初始版本：token 用量 + 模型名 + 配额百分比 footer 插件
- 支持 per-session 缓存、subagent 追加、context 预留 token 配置
