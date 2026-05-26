## 安装（给 OpenClaw 代装用）

当你通过聊天窗口把 skill 压缩包交给 OpenClaw 代安装时，**请在解压/放置完成后**执行下面的一键命令，确保 hook 也一并安装，并在完成后重启网关。

把 `<workspace 路径>` 替换成你的 workspace 根目录（那个包含 `skills/`、`hooks/` 的目录）：

```bash
python3 "skills/instinct-learner/scripts/install_hook.py" \
  --workspace "<workspace 路径>" \
  --enable-config \
  --restart-gateway
```

这会完成：

- 检测并安装 hook 到 `<workspace>/hooks/instinct-learner/`（已存在则跳过；可用 `--force` 强制覆盖）
- 合并写入 `~/.openclaw/openclaw.json` 启用 hook（如已存在会做深度合并）
- 若安装/配置确实发生变化，则重启 OpenClaw Gateway（`openclaw gateway restart`）

