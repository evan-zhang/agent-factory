# 通过 SSH 远程调用 Claude Code 指南

## 架构

```
本机 (Mac mini, 内存有限)
  └─ SSH ──→ 远程 Mac Studio (192.168.91.72)
                └─ Claude Code CLI + MCP Web Search
```

本机内存不足，无法运行 Claude Code。通过 SSH 调用远程机器上的 Claude Code，并启用 MCP web search 获取实时数据。

---

## 前提条件

### 远程机器
- macOS / Linux
- 已安装 Claude Code CLI：`npm install -g @anthropic-ai/claude-code`
- 已配置 MCP server（web search）
- 已配置 Anthropic API Key

### 本机
- 已安装 `sshpass`：`brew install hudochenkov/sshpass/sshpass`
- SSH 可达远程机器

---

## 远程机器配置

### 1. Claude Code CLI 安装

```bash
# 通过 Homebrew
brew install node
npm install -g @anthropic-ai/claude-code

# 验证
claude --version
```

### 2. API Key 配置

编辑 `~/.claude/settings.json`：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1
  }
}
```

如果用第三方代理（如 z.ai）：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your-zai-key",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1
  }
}
```

### 3. MCP Web Search 配置

```bash
# 添加 zai MCP server（自带 web search）
claude mcp add zai-mcp-server -s user -- npx -y @z_ai/mcp-server

# 设置环境变量
# 在 claude mcp add 时通过 -e 参数，或直接在 settings.json 里加
```

验证 MCP server 状态：

```bash
claude mcp list
```

应看到：
```
zai-mcp-server: npx -y @z_ai/mcp-server - ✓ Connected
```

---

## 调用方式

### 基础调用

```bash
# 本地调用
claude --print --dangerously-skip-permissions --max-turns 3 "你的问题"

# 远程 SSH 调用
sshpass -p '密码' ssh -o StrictHostKeyChecking=no 用户@IP \
  "export PATH=/opt/homebrew/bin:\$PATH; claude --print --dangerously-skip-permissions --max-turns 3 '你的问题'"
```

### 启用 Web Search

在 prompt 中指示 Claude 使用 MCP 工具：

```bash
sshpass -p '密码' ssh 用户@IP \
  "export PATH=/opt/homebrew/bin:\$PATH; \
   claude --print --dangerously-skip-permissions \
   --model claude-sonnet-4-20250514 \
   --max-turns 3 \
   '请先使用你的 MCP web search 工具搜索最新信息，然后回答：XXX的最新新闻'"
```

**关键点：**
- 必须在 prompt 中明确要求使用 web search
- `--max-turns` 至少 2（1 次搜索 + 1 次回答）
- 超时建议 300 秒（web search 需要时间）

### Python 调用

```python
import subprocess

def run_claude_remote(prompt, timeout=300, max_turns=3):
    """通过 SSH 远程调用 Claude Code"""
    
    # 注入 web search 指令
    web_prompt = (
        "请先使用你的 MCP web search 工具搜索最新信息，"
        "然后基于搜索结果回答以下问题。确保引用来源。\n\n" + prompt
    )
    
    remote_cmd = (
        f"export PATH=/opt/homebrew/bin:$PATH; "
        f"claude --print"
        f" --dangerously-skip-permissions"
        f" --model claude-sonnet-4-20250514"
        f" --max-turns {max_turns}"
        f" {subprocess.list2cmdline([web_prompt])}"
    )
    
    ssh_cmd = [
        "sshpass", "-p", "密码",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "用户@IP",
        remote_cmd,
    ]
    
    result = subprocess.run(
        ssh_cmd,
        capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "TERM": "dumb"},
    )
    
    if result.returncode == 0 and result.stdout.strip():
        return {"success": True, "content": result.stdout.strip()}
    else:
        return {"success": False, "error": result.stderr[:200]}
```

---

## SSH 非交互 Shell 注意事项

**问题：** SSH 非交互登录不会加载 `.zshrc`/`.bashrc`，导致 PATH 不完整。

**现象：**
```bash
# 直接 SSH 调用
ssh user@host "which claude"  # → not found

# 但交互式 SSH 可以
ssh user@host  # 进入 shell 后
$ which claude  # → /opt/homebrew/bin/claude
```

**解决：** 在命令前手动设置 PATH：

```bash
ssh user@host "export PATH=/opt/homebrew/bin:\$PATH; claude --version"
```

常见的 Homebrew 路径：
- Apple Silicon Mac: `/opt/homebrew/bin`
- Intel Mac: `/usr/local/bin`
- nvs (Node Version Manager): `source ~/.zshrc` 或直接用完整路径

---

## 踩坑记录

### 1. 本机 OOM
- **现象：** 本机运行 Claude Code 时内存不足被 SIGKILL
- **解决：** 优先使用远程机器，不在本机运行

### 2. SSH 认证失败
- **现象：** `Too many authentication failures`
- **解决：** 使用 `sshpass` 密码认证，不要依赖 SSH key

### 3. MCP 工具超时
- **现象：** web search 耗时超过默认超时
- **解决：** 超时设为 300 秒，`--max-turns` 至少 2

### 4. yfinance TLS 错误
- **现象：** `SSL connect error` 但数据仍能获取
- **说明：** yfinance 有重试机制，偶尔 TLS 错误不影响最终结果

### 5. `--allowedTools` 格式
- **现象：** 指定 `--allowedTools 'mcp__zai-mcp-server__*'` 后执行超时
- **解决：** 不加 `--allowedTools`，让 Claude 自动使用已配置的 MCP server

---

## 配置参数速查

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--print` | 非交互模式 | 必须加 |
| `--dangerously-skip-permissions` | 跳过权限确认 | 必须加 |
| `--model` | 模型选择 | `claude-sonnet-4-20250514` |
| `--max-turns` | 最大交互轮数 | 预分析 3，校验 2 |
| timeout | Python subprocess 超时 | 预分析 300s，校验 180s |
| `TERM=dumb` | 禁用终端颜色 | 建议加 |

---

## 文件位置

- Claude 配置: `~/.claude/settings.json`
- MCP server 配置: `claude mcp list` 查看
- Python 调用封装: `tradingagents/dataflows/claude_analysis.py`
- 新闻搜索封装: `tradingagents/dataflows/news_search.py`
