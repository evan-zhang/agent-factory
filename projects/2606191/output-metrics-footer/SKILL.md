---
name: output-metrics-footer
version: "0.3.0"
description: "OpenClaw 代码插件：在每条消息底部追加 token 用量、模型名、配额百分比等指标。支持 per-session 缓存和 subagent 追加。"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2606191/output-metrics-footer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=output-metrics-footer
metadata:
  openclaw:
    emoji: "📊"
    requires:
      minGatewayVersion: "2026.4.23-beta.5"
---

# Output Metrics Footer

OpenClaw 代码插件，在每条消息底部自动追加 compact 的 token/模型/配额指标。

## 这不是 Skill

这是一个 **code plugin**（不是 SKILL.md 指令文件）。它通过 OpenClaw 插件 SDK 直接 hook 消息输出流程。

## 功能

- 每条回复底部追加：模型名 · token 用量 · context 占用 · 配额百分比
- per-session 缓存（默认 120 秒），避免频繁计算
- 可选追加到 subagent 输出
- 可按 channel 开关

## 配置与授权

### 安装

一行命令：

```bash
curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2606191/output-metrics-footer/install.sh | bash
```

安装后重启 gateway：

```bash
openclaw gateway restart
```

### 配置项

安装时自动注入默认配置，无需手动修改。如需调整：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `enabledChannels` | `[]`（全部） | 指定 channel 启用，空数组 = 全部 |
| `appendSubagents` | `true` | 是否对 subagent 输出也追加 footer |
| `cacheMs` | `120000` | 用量数据缓存时间（毫秒） |
| `quotaCacheMs` | `60000` | 配额数据缓存时间（毫秒） |
| `contextReserveTokens` | `40000` | context 预留 token 数 |

### 卸载

```bash
~/.openclaw/extensions/output-metrics-footer/uninstall.sh
```

或手动：
```bash
bash projects/2606191/output-metrics-footer/uninstall.sh
```

## 版本管理

版本号同步在三处（发版时全部更新）：

1. `VERSION` — 纯文本版本号
2. `src/package.json` — npm package 版本
3. `version.json` — 工厂版本记录

## 自定义模型 context 表

`src/index.ts` 中的 `MODEL_CONTEXT` 字典定义了各模型的 context window 大小。
如果使用了不在表中的模型，footer 会显示 "ctx: ?"。

添加新模型：编辑 `src/index.ts` → 在 `MODEL_CONTEXT` 中添加条目 → 升版本 → push。

## 问题反馈

- Issue：https://github.com/evan-zhang/agent-factory/issues/new?labels=output-metrics-footer
- 标题格式：`[footer] 简述问题`
- 请包含：OpenClaw 版本、操作系统、相关日志片段
