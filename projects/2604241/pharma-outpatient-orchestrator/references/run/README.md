# 模块 `run`：院外 RUN 初始化与收尾

## 适用场景

用户已给出 **`task_id`、`run_id`、`city`**，需要落盘本 run 的合同与目录骨架。

## 鉴权

见 **`../auth.md`**：当前为 **`nologin`**。

## 动作与脚本

| 动作 | 脚本 | 说明 |
|------|------|------|
| 初始化 RUN | `scripts/run/init_run.py` | 生成 `search_spec.json`、`run_meta.json`、空 `evidence.jsonl` |
| 收尾校验 | `scripts/run/finalize_run.py` | 校验必落文件、补全 `run_meta` 时间戳 |

## 输入要点（`init_run.py`）

- **`--task-id`** / **`--run-id`** / **`--city`**：必填。  
- **`--template`**：合同模板 JSON 路径；缺省时尝试从本 Skill 根目录上溯到 OpenClaw 仓库根并定位 **`网络搜索/pharma-city-outpatient-search-spec.template.json`**（失败则必须显式传入）。  
- **`--base-dir`**：默认 **`./network-search-runs`**（相对**当前工作目录**）。  
- **`--domain-append-json`**：可选，JSON 数组，域名字符串并入 **`source_policy.include_domains`**（去重）。

## 输出

**RUN_ROOT** 下 `search_spec.json`、`run_meta.json`、空 **`evidence.jsonl`**；不在此阶段写 `audit_*` / `summary.md`。

## 检索执行默认（合同真源）

- **`search_spec.channel_bindings.CN_SEARCH`** 与 **`GLOBAL_SEARCH`**：**默认以 `minmax_web_search_mcp` 为第一条**（**`init_run.py`** 会在落盘前再次规范化，避免旧模板漏写）。
- **不得**把 OpenClaw 内置 **`tools.web`（Brave 等）**当作院外流水线的默认检索实现；仅在 **MCP 不可用或连续失败** 后，按组织策略显式降级，并在 **`evidence.jsonl` / `gap_report.md`** 中可审计地注明实际通道。

## OpenClaw：如何让默认 MCP 可用（ACP 承载 + 极少数兜底）

与 **`~/.openclaw/openclaw.json`** 中 **`plugins.entries.acpx.config.mcpServers.minmax_web_search_mcp`** 对齐；**不要**把同一 MCP 配到 Cursor。

| 轨道 | 何时成立 | Agent 怎么做 |
|------|-----------|----------------|
| **默认** | 合同已绑定 **`minmax_web_search_mcp`** | 在 **ACP / acpx** 会话中直接调用该 MCP（网关注入）完成 **CN_SEARCH / GLOBAL_SEARCH** 的检索 |
| **兜底 A** | 主会话为 **embedded** 但必须用同一 MCP | **`sessions_spawn`** + **`runtime: "acp"`** 开子会话跑检索，再回到主会话执行 **`append_evidence.py` / `append_global_evidence.py`** |
| **兜底 B** | MCP 不可用且已记录失败 | 经用户或宪章允许的 **`tools.web`** 等通道；**须**在证据与审计材料中写明实际工具与限制 |

**密钥（推荐）**：`MINIMAX_API_KEY` / `MINIMAX_API_HOST` 放在 **`~/Library/LaunchAgents/ai.openclaw.gateway.plist`** 的 **`EnvironmentVariables`**（LaunchAgent **不读** `~/.zshrc`）。`acpx` 的 **`mcpServers.*.env`** 里只能写**字符串**；密钥靠网关进程环境继承即可。

**改配置后**：`openclaw config validate`，再 **`openclaw gateway restart`**。

**可选**：若希望 **`pharma-outpatient-search`** 默认整会话走 ACP（需本机 harness），可在 **`agents.list`** 里为该 `id` 增加（路径按你机器调整）：

```json
"runtime": {
  "type": "acp",
  "acp": {
    "agent": "codex",
    "backend": "acpx",
    "mode": "persistent",
    "cwd": "/Users/nancy/.openclaw/workspace/pharma-outpatient-search"
  }
}
```
