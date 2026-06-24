---
name: output-metrics-footer
version: "0.3.0"
description: "OpenClaw 代码插件：在每条消息底部追加 token 用量、模型名、配额百分比等指标。安装时可一键应用推荐压缩配置（256k 甜蜜点）。"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2606191/output-metrics-footer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=output-metrics-footer
metadata:
  openclaw:
    emoji: "📊"
    requires:
      minGatewayVersion: "2026.4.23-beta.5"
---

# Output Metrics Footer

OpenClaw 代码插件，在每条回复底部自动追加 compact 的 token/模型/配额指标。

## 这不是 Skill

这是一个 **code plugin**（不是 SKILL.md 指令文件）。它通过 OpenClaw 插件 SDK 直接 hook 消息输出流程。

## 功能

- 每条回复底部追加：模型名 · token 用量 · context 占用 · 配额百分比
- per-session 缓存（默认 120 秒），避免频繁计算
- 可选追加到 subagent 输出
- 可按 channel 开关
- **安装时可选一键应用推荐压缩配置**（详见下文）

## 安装

一行命令：

```bash
curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2606191/output-metrics-footer/install.sh | bash
```

如果你在交互式终端中运行，安装脚本会：

1. 安装插件并注册到 openclaw.json
2. 检测当前压缩配置，与推荐配置对比
3. 如果有差异，提示你三选一：
   - **[A] 应用推荐配置** — 自动备份并写入 256k 甜蜜点配置
   - **[K] 保留当前配置** — 只装插件，不改压缩参数
   - **[D] 查看文档** — 打开 `docs/compaction-config.md` 了解后再决定

**非交互模式**（通过管道执行时）默认保留当前配置。如需强制应用：

```bash
bash install.sh --apply-recommended
```

跳过提问保留当前配置：

```bash
bash install.sh --keep-current
```

安装后重启 gateway：

```bash
openclaw gateway restart
```

## 推荐压缩配置（256k 甜蜜点）

### 为什么要把 1M 模型调到 256k？

业界共识（NIAH 基准测试反复验证）：几乎所有标称 1M+ 的模型，超过 200k 后信息检索能力会从 95%+ 跌到 50% 以下。模型在 128k-256k 区间内表现最稳定。

主动调小窗口的好处：模型更聪明、回复更准、响应更快、成本更低、压缩更早触发（保留精华比堆原始历史质量高）。

### 推荐参数

| 参数 | 推荐值 | 说明 |
|---|---|---|
| `agents.defaults.contextTokens` | 256,000 | 落入模型甜蜜点 |
| `compaction.reserveTokensFloor` | 40,000 | 回复+工具空间 |
| `compaction.keepRecentTokens` | 50,000 | 压缩后保留近期对话 |
| `compaction.maxHistoryShare` | 0.65 | 压缩后历史占比 |
| `compaction.memoryFlush.softThresholdTokens` | 30,000 | preflight 触发提前量 |
| `compaction.notifyUser` | false | 不打扰 |
| `compaction.timeoutSeconds` | 120 | 给压缩留足时间 |

代入源码公式后的触发点：
- **preflight 压缩**：186k（占 73%）— 最先触发
- **pre-prompt 检查**：216k（占 84%）

完整设计文档见 `docs/compaction-config.md`。

### 与 footer 显示的关系

footer 的 `%ctx` 分母来自 runtime 传入的 `contextTokenBudget`，这个值已经包含了 `agents.defaults.contextTokens` 的封顶逻辑。

**应用推荐配置后，footer 会自动按 256k 算分母**，显示的百分比真实反映"距离压缩还有多远"。

| 对话累积 | 应用前（1M） | 应用后（256k） |
|---|---|---|
| 100k | 10%（虚假的"轻松"） | 39%（真实负担） |
| 180k | 18%（模型已变笨） | 70%（接近压缩触发） |

## 配置项

安装时自动注入默认配置，无需手动修改。如需调整：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `enabledChannels` | `[]`（全部） | 指定 channel 启用，空数组 = 全部 |
| `appendSubagents` | `true` | 是否对 subagent 输出也追加 footer |
| `cacheMs` | `120000` | 用量数据缓存时间（毫秒） |
| `quotaCacheMs` | `60000` | 配额数据缓存时间（毫秒） |
| `contextReserveTokens` | `40000` | context 预留 token 数 |

## 卸载

```bash
~/.openclaw/extensions/output-metrics-footer/uninstall.sh
```

卸载只移除插件本身，不会还原压缩配置。如需还原，使用安装时生成的备份文件：

```bash
# 查看备份
ls ~/.openclaw/gateways/*/openclaw.json.bak-*
# 还原
cp <备份文件路径> ~/.openclaw/gateways/<gateway>/openclaw.json
openclaw gateway restart
```

## 版本管理

版本号同步在三处（发版时全部更新）：

1. `VERSION` — 纯文本版本号
2. `src/package.json` — npm package 版本
3. `version.json` — 工厂版本记录

### v0.3.0 变更

- **修复**：`%ctx` 百分比在多轮 tool call 时飙到 200%+ 的问题（改用 `lastAssistant.usage` 单次值代替累加值）
- **新增**：安装时可选应用推荐压缩配置（256k 甜蜜点）
- **新增**：`docs/compaction-config.md` 完整设计文档
- **优化**：`MODEL_CONTEXT` 表对齐 256k 推荐值
- **优化**：颜色阈值调整（70% 红 / 50% 黄），贴近 73% 压缩触发点

### v0.2.2

- per-session 隔离，修复跨 session 数据串用
- footer 消费锁（per-session per-turn），避免重复追加
- before_dispatch hook 兜底

## 自定义模型 context 表

`src/index.ts` 中的 `MODEL_CONTEXT` 字典定义了各模型的 context window 大小（fallback 用）。
正常情况下 runtime 会传入准确的 `contextTokenBudget`，表仅在 fallback 场景使用。

添加新模型：编辑 `src/index.ts` → 在 `MODEL_CONTEXT` 中添加条目 → 升版本 → push。

## 问题反馈

- Issue：https://github.com/evan-zhang/agent-factory/issues/new?labels=output-metrics-footer
- 标题格式：`[footer] 简述问题`
- 请包含：OpenClaw 版本、操作系统、相关日志片段
