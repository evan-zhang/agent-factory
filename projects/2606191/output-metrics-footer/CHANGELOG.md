# Changelog

## v0.3.0 (2026-06-24)

- **Fix**: `%ctx` 百分比在多轮 tool call 时飙到 200%+ 的根因修复
  - 原因：OpenClaw runtime 的 `getUsageTotals()` 把一个 turn 内所有 model call 的 input 累加，除以 context window 后轻松超 100%
  - 修复：改用 `event.lastAssistant.usage`（最后一次 API 调用的单次 input），真实反映当前 context 占用
- **New**: 安装时可选一键应用推荐压缩配置（256k 甜蜜点）
  - `install.sh` 检测当前配置与推荐配置差异，交互式三选一（应用/保留/查看文档）
  - 支持 `--apply-recommended` / `--keep-current` 非交互模式
- **New**: `docs/compaction-config.md` 完整设计文档（源码级触发公式分析 + 256k 方案推导）
- **Optimize**: `MODEL_CONTEXT` 表所有 1M 模型 fallback 值改为 256k，与推荐配置对齐
- **Optimize**: 颜色阈值调整（80→70 红），贴近 73% preflight 压缩触发点
- **Optimize**: `contextTokenBudget` 读取增加 `ctx.contextTokenBudget` fallback

## v0.2.2 (2026-06-19)

- Fix: `latestUsage()` strict session isolation — no more cross-session data leakage (P0)
- Fix: use runtime `contextTokenBudget` from `llm_output` event instead of hardcoded table (P1)
- Fix: add `vip-newapi/glm-5.2` to MODEL_CONTEXT fallback table
- Followup: `recentBySession` Map cleanup mechanism (P2, tracked)

## v0.2.1 (2026-06-19)

- 从 `~/.openclaw/extensions/` 迁入工厂项目管理
- 初始版本：token 用量 + 模型名 + 配额百分比 footer 插件
- 支持 per-session 缓存、subagent 追加、context 预留 token 配置
