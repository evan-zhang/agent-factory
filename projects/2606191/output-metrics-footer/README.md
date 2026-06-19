# Output Metrics Footer

OpenClaw 代码插件：每条消息底部自动追加 token 用量、模型名、配额百分比等指标。

## 快速安装

一行命令：

```bash
curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/main/projects/2606191/output-metrics-footer/install.sh | bash
```

安装后重启：

```bash
openclaw gateway restart
```

## 快速卸载

```bash
~/.openclaw/extensions/output-metrics-footer/uninstall.sh
```

## 安装脚本做了什么

1. 从 GitHub sparse-checkout 取插件源码（3 个文件，~14KB）
2. 复制到 `~/.openclaw/extensions/output-metrics-footer/`
3. 自动 patch `openclaw.json`（三处：allow + entries + load.paths）
4. 自动备份 openclaw.json（`.bak-footer-install-*`）

**不改其他配置**，只加 footer 插件相关的三个条目。

## 升级

重新跑安装命令即可（会覆盖旧文件）：

```bash
curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/main/projects/2606191/output-metrics-footer/install.sh | bash
openclaw gateway restart
```

## 系统要求

- OpenClaw >= 2026.4.23-beta.5
- git、python3
- macOS / Linux / WSL

## 自定义配置

安装后如需调整（如关闭 subagent footer、改缓存时间），编辑 `openclaw.json`：

```json
"plugins": {
    "entries": {
        "openclaw-output-metrics-footer": {
            "config": {
                "appendSubagents": false,
                "cacheMs": 60000
            }
        }
    }
}
```

改完重启 gateway。

## 添加新模型

如果用了表中没有的模型，footer 会显示 `ctx: ?`。

编辑 `~/.openclaw/extensions/output-metrics-footer/index.ts`，在 `MODEL_CONTEXT` 字典中添加：

```typescript
"你的模型名": context_window大小,
```

然后重启 gateway。
