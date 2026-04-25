# MiniMax Web Search MCP 配置指南

> 适用对象：需要联网搜索能力的 Agent
> 更新日期：2026-04-25

---

## 一、前置条件

| 条件 | 说明 |
|------|------|
| MiniMax Token Plan 订阅 | 需在 <https://platform.minimax.io/subscribe/token-plan> 订阅，获取专属 API Key（以 `sk-cp-` 开头） |
| uv / uvx | Python 包管理工具，用于运行 `minimax-coding-plan-mcp` |
| mcporter | MCP 管理工具，用于调用 MCP Server |

### 安装 uv（如未安装）

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证
which uvx
# 应输出类似：/Users/xxx/.local/bin/uvx
```

### 安装 mcporter（如未安装）

```bash
npm install -g mcporter

# 验证
mcporter --version
```

---

## 二、配置步骤

### Step 1：获取 API Key

1. 访问 <https://platform.minimax.io/subscribe/token-plan>
2. 订阅 Token Plan（Coding Plan）
3. 在控制台获取 API Key（格式：`sk-cp-j-xxxx...`）

> ⚠️ **注意**：Token Plan 的 Key 和普通 MiniMax API Key 不同。普通 Key（`sk-` 开头）不支持 web_search，必须是 Token Plan 的 Key（`sk-cp-` 开头）才行。

### Step 2：配置 mcporter

编辑 `~/.mcporter/mcporter.json`，添加 minimax server：

```json
{
  "mcpServers": {
    "minimax": {
      "command": "/Users/xxx/.local/bin/uvx",
      "args": ["minimax-coding-plan-mcp", "-y"],
      "env": {
        "MINIMAX_API_KEY": "sk-cp-j-你的TokenPlan密钥",
        "MINIMAX_API_HOST": "https://api.minimax.io"
      }
    }
  }
}
```

> **注意**：`command` 中的路径要替换为你机器上 uvx 的实际路径。用 `which uvx` 查看。

### Step 3：验证配置

```bash
# 检查 minimax server 状态
mcporter list --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d.get('servers', []):
    if s['name'] == 'minimax':
        print(f'Status: {s[\"status\"]}')
        print(f'Tools: {[t[\"name\"] for t in s.get(\"tools\", [])]}')
"

# 预期输出：
# Status: ok
# Tools: ['web_search', 'understand_image']
```

### Step 4：测试搜索

```bash
# 直接调用搜索
mcporter call minimax.web_search query="深圳 2026 落户政策"

# 预期返回 JSON 格式的搜索结果
```

---

## 三、可用工具

配置成功后，MiniMax MCP 提供两个工具：

### 1. web_search — 网页搜索

```bash
mcporter call minimax.web_search query="你的搜索词"
```

- 返回结果包含：title、link、snippet、date
- 建议查询词 3-7 个关键词，效果最佳
- 时效性内容可在查询中加入日期（如 `2026 最新`）

### 2. understand_image — 图片理解

```bash
mcporter call minimax.understand_image prompt="描述这张图片" image_url="https://example.com/image.jpg"
```

- 支持 JPEG、PNG、GIF、WebP（最大 20MB）
- 支持 URL 和本地文件路径

---

## 四、在 Agent 中使用

### 方式一：通过 exec 调用

在 Agent 执行时，直接用 exec 工具调用：

```bash
mcporter call minimax.web_search query="搜索内容"
```

### 方式二：通过 Skill 调用

安装 `minimax-cli-web-search` skill：

```bash
clawhub install minimax-cli-web-search --dir /path/to/workspace/skills
```

使用 skill 内的脚本：

```bash
# 环境检查
bash scripts/minimax_web_search.sh --preflight

# 搜索
bash scripts/minimax_web_search.sh --query "搜索内容" --count 5

# JSON 格式输出
bash scripts/minimax_web_search.sh --query "搜索内容" --json
```

---

## 五、常见问题

### Q1: `login fail` 或 `Authentication Failed`
- **原因**：API Key 不是 Token Plan 的 Key
- **解决**：确认 Key 以 `sk-cp-` 开头，在 <https://platform.minimax.io> 的 Token Plan 页面获取

### Q2: `timeout: command not found`（macOS）
- **原因**：macOS 没有 `timeout` 命令
- **解决**：`brew install coreutils`，然后修改 skill 脚本中的 `timeout` 为 `/opt/homebrew/bin/gtimeout`

### Q3: `Tool web_search not found`
- **原因**：装错了 MCP 包。`minimax-mcp-js` 只有 TTS/图片/视频，没有搜索
- **解决**：必须用 `minimax-coding-plan-mcp`（通过 uvx 运行）

### Q4: `uvx` 命令找不到
- **解决**：安装 uv（`curl -LsSf https://astral.sh/uv/install.sh | sh`），然后确认 `which uvx` 有输出

### Q5: mcporter 配置文件在哪？
- 默认路径：`~/.mcporter/mcporter.json`
- 也可能在 workspace 的 `config/mcporter.json`（会被 mcporter 自动导入）

---

## 六、配置文件位置速查

| 文件 | 路径 |
|------|------|
| mcporter 配置 | `~/.mcporter/mcporter.json` |
| uvx 二进制 | `/Users/xxx/.local/bin/uvx`（用 `which uvx` 确认） |
| MiniMax MCP 缓存 | `~/.cache/uv/archive-v0/` 下自动管理 |
| skill 脚本 | workspace `skills/minimax-cli-web-search/scripts/` |

---

## 七、最小配置模板

如果你只想快速跑起来，复制这个模板改两处就行：

```json
// ~/.mcporter/mcporter.json
{
  "mcpServers": {
    "minimax": {
      "command": "这里填 which uvx 的输出",
      "args": ["minimax-coding-plan-mcp", "-y"],
      "env": {
        "MINIMAX_API_KEY": "这里填你的 Token Plan API Key",
        "MINIMAX_API_HOST": "https://api.minimax.io"
      }
    }
  }
}
```

配置完成后运行 `mcporter list --json` 验证 status 为 `ok` 即可。

---

## 八、可选增强：Exa AI 搜索

Exa AI 支持精准的 `includeDomains` 定向搜索，可以专门搜索 gov.cn 官方来源。作为 MiniMax 的补充，非必选。

### 配置步骤

1. 获取 Exa API Key：访问 https://exa.ai 注册，免费额度 1000 次/月

2. 添加 mcporter 配置：

```bash
mcporter add exa -s user -- npx -y @anthropic-ai/exa-mcp-server
```

或在 `~/.mcporter/mcporter.json` 中手动添加：

```json
{
  "mcpServers": {
    "minimax": { ... },
    "exa": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "你的Exa Key"
      }
    }
  }
}
```

3. 验证：

```bash
mcporter list --json | grep exa
```

### 使用场景

- MiniMax 搜索不到 gov.cn 页面时，用 Exa `includeDomains: ["gov.cn"]` 定向搜索
- 特定城市官网搜索：`includeDomains: ["lanzhou.gov.cn"]`
- 采集完成后统计来源质量，Exa 搜索到的结果官方占比更高

### 注意事项

- 免费额度 1000 次/月，一次完整采集约消耗 100 次
- 非必选，不配置不影响基础采集流程
- setup-minimax.sh 会自动检测 Exa 是否可用
