# Issue #9 诊断报告：cas-chat-archive hook 未注册导致对话不记录

**诊断时间**: 2026-04-02 13:00 CST
**诊断人**: 子代理（factory-orchestrator spawn）
**状态**: 已完成，修复已应用

---

## 一、根因分析

### 1.1 症状

4 个 gateway（life/ops/company/code）的 `openclaw.json` 中 `hooks.internal` 均为 `null`，导致 `cas-chat-archive-auto` hook 从未被触发，所有对话不落盘。

### 1.2 根因

**hook 安装 ≠ hook 启用，两步流程被遗漏了启用步骤。**

| 步骤 | 状态 | 证据 |
|------|------|------|
| 1. Hook handler 安装到 gateway state 目录 | ✅ 完成 | 4 个 gateway 的 `state/hooks/cas-chat-archive-auto/` 均有 `handler.ts` 和 `HOOK.md`（3 月 27 日） |
| 2. Hook 写入 gateway `openclaw.json` 的 `hooks.internal.entries` | ❌ 未完成 | 4 个 gateway 的 `openclaw.json` 中 `hooks.internal` 均为 `null` |

### 1.3 直接原因

`openclaw hooks enable cas-chat-archive-auto` 命令**只对当前运行的 gateway 生效**（由 `OPENCLAW_CONFIG_PATH` 环境变量决定）。运行方式是通过 LaunchAgent 启动的 life gateway，该命令只修改了 `life/openclaw.json`。

对于其他 3 个 gateway（ops/company/code），从未执行过 `openclaw hooks enable`，且没有自动化手段从非默认 gateway 上下文中执行此命令。

### 1.4 深层原因

DEPLOYMENT.md 声称"已同步并启用"4 个 gateway，但：
- 实际只完成了 handler 文件的部署（安装），未完成配置文件的修改（启用）
- 没有验收步骤验证 hook 是否真正在 gateway 配置中注册
- 没有检测到 `openclaw hooks enable` 的 gateway 约束性（只操作默认 gateway）

---

## 二、修复步骤

### 2.1 已执行的修复

**Step 1 — life gateway（通过 CLI）**:
```bash
openclaw hooks enable cas-chat-archive-auto
```
结果：`life/openclaw.json` 已更新，`hooks.internal.enabled=true`, `entries["cas-chat-archive-auto"].enabled=true`

**Step 2 — ops/company/code（通过手动 jq 编辑）**:
```bash
for g in ops company code; do
  cfg=~/.openclaw/gateways/$g/openclaw.json
  jq '.hooks = {"internal": {"enabled": true, "entries": {"cas-chat-archive-auto": {"enabled": true}}}}' "$cfg" > "${cfg}.tmp" && mv "${cfg}.tmp" "$cfg"
done
```

**Step 3 — 验证**:
```bash
for g in life ops company code; do
  enabled=$(jq '.hooks.internal.entries["cas-chat-archive-auto"].enabled' ~/.openclaw/gateways/$g/openclaw.json)
  echo "$g: hook enabled = $enabled"
done
```
结果：4 个 gateway 均显示 `enabled = true` ✅

### 2.2 待执行步骤

- [ ] **Gateway restart** — `openclaw gateway restart`，让运行中的 gateway 加载新配置
- [ ] **发送测试消息** — 在 4 个 gateway 的频道中各发一条测试消息
- [ ] **验证落盘** — 检查 `~/.openclaw/chat-archive/{gw}/logs/2026-04-02.md` 是否生成

### 2.3 验收命令

```bash
# 1. 验证 hook 配置
for g in life ops company code; do
  echo "=== $g ==="
  jq '.hooks.internal.enabled, .hooks.internal.entries["cas-chat-archive-auto"]' ~/.openclaw/gateways/$g/openclaw.json
done

# 2. 验证 hook 运行
openclaw hooks list

# 3. 验证日志落盘（在测试消息发送后）
today=$(date +%F)
for g in life ops company code; do
  echo "=== $g ==="
  ls ~/.openclaw/chat-archive/$g/logs/$today.md 2>/dev/null || echo "(no log today)"
done
```

---

## 三、防复发建议

### 3.1 增强 `openclaw hooks enable` 的 gateway 覆盖

`openclaw hooks enable` 只影响运行中的 gateway。建议提交 feature request：
- 添加 `--gateway <name>` 选项，允许为非运行中的 gateway 配置 hook
- 或在 `openclaw hooks list` 中显示每个 gateway 的启用状态（当前只显示"ready"但未区分"已启用"）

### 3.2 在发布流程中增加配置验证步骤

在 `publish.py` 或 `DEPLOYMENT.md` 中添加验收脚本，在安装后自动验证 hook 是否真正注册：

```bash
# 验收：检查 hook 在所有目标 gateway 的配置中是否启用
FAIL=0
for g in life ops company code; do
  enabled=$(jq '.hooks.internal.entries["cas-chat-archive-auto"].enabled' ~/.openclaw/gateways/$g/openclaw.json)
  if [ "$enabled" != "true" ]; then
    echo "FAIL: $g - hook not enabled in config"
    FAIL=1
  fi
done
[ $FAIL -eq 0 ] && echo "All hooks verified" || echo "Some hooks missing!"
```

### 3.3 Gateway 启动时自动验证 hook 注册

在 handler.ts 中添加启动时检查：若运行中但 config 未注册，输出警告日志（不阻断，因为 fail-soft 约定）。

### 3.4 文档修正

DEPLOYMENT.md 中的"同步并启用"应改为更精确的描述：
- **同步** = 文件部署到 state 目录
- **启用** = 需要对每个 gateway 运行 `openclaw hooks enable`（仅 life 通过 CLI 完成，其余需手动编辑配置）

---

## 四、关键文件路径

| 文件 | 路径 |
|------|------|
| Hook handler | `~/.openclaw/gateways/{gw}/state/hooks/cas-chat-archive-auto/handler.ts` |
| Gateway 配置 | `~/.openclaw/gateways/{gw}/openclaw.json` |
| 归档根目录 | `~/.openclaw/chat-archive/` |
| Skill 源码 | `skills/cas-chat-archive/` |
| 发布脚本 | `skills/cas-chat-archive/scripts/publish.py` |
