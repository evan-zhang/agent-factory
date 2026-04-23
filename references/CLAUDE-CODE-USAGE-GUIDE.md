# OpenClaw 调用 Claude Code / Codex 指南 v3.0

> 2026-04-23 | v2.0 → v3.0 新增 Codex 完整调用指南

---

## 概述

OpenClaw 通过 `exec` 工具调用 Claude Code CLI 或 OpenAI Codex CLI。两者各有适用场景：

| 工具 | 模型 | API | 适用场景 |
|------|------|-----|----------|
| Claude Code | GLM 系列（智谱网关） | api.z.ai/api/anthropic | 代码生成、审查、文件编辑 |
| OpenAI Codex | GPT-5.4（OpenAI 原生） | OpenAI 官方 | 联网搜索、研究、多步推理 |

---

## 一、Claude Code

### 实际模型映射

| settings.json 名称 | 实际模型 | 用途 |
|---|---|---|
| opus | GLM-5（智谱） | 默认模型，主 Agent 推理 |
| sonnet | GLM-4.7（智谱） | 子 Agent / 轻量任务 |
| haiku | GLM-4.5-air（智谱） | 快速简单任务 |

API 端点：`api.z.ai/api/anthropic`（智谱 Anthropic 兼容接口）

### 调用方式

**短任务（< 30 秒）**：
```bash
exec command:"claude --print --permission-mode bypassPermissions '任务'" timeout:30
```

**长任务（推荐后台模式）**：
```bash
exec background:true command:"claude --print --permission-mode bypassPermissions '任务'" timeout:600
```

**文件传递任务（最稳定）**：
```bash
# 1. 写任务文件
write path:/tmp/task.txt content:"详细任务描述..."
# 2. 执行
exec background:true command:"claude --print --permission-mode bypassPermissions '读取 /tmp/task.txt 并执行，结果写入 /tmp/result.md'" timeout:600
```

### 参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `background` | 长任务 `true` | 后台运行，避免 SIGKILL |
| `timeout` | 短 30s / 长 600s | exec 默认 1800s |
| `pty` | `false` | Claude Code 不需要 PTY |
| `yieldMs` | **不要用** | 会导致前台内存泄漏 → SIGKILL |

### 内存要求

- 最低：系统可用内存 > 2GB（free + inactive）
- Claude Code 自身占 200-300MB
- 不足时先关大内存应用（Discord、Chrome 等）

---

## 二、OpenAI Codex

### 核心参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 模型 | gpt-5.4 | Codex 默认模型 |
| 沙箱 | **必须关闭** | 否则无法联网 + 无法写入目标目录 |
| PTY | `true` | Codex CLI 需要 PTY |
| `--full-auto` | 短任务可用 | 自动审批，但不能与 bypass sandbox 同时用 |

### ⚠️ 沙箱问题（已解决）

Codex v0.56.0 默认启用沙箱 `workspace-write [workdir, /tmp, $TMPDIR]`，导致：
1. **无法写入** `/Users/evan/.openclaw/...` 等目标目录
2. **无法联网**（Clash TUN + fake-ip 与沙箱网络栈冲突）

**解决方案：用 `--dangerously-bypass-approvals-and-sandbox` 关闭沙箱。**

该参数同时自动设置 approval=never，等效于 full-auto，不需要再加 `--full-auto`。

### 调用方式

**标准调用（推荐）**：
```bash
exec pty:true background:true command:"codex exec --dangerously-bypass-approvals-and-sandbox '任务描述'" timeout:900
```

**带 workdir 指定**：
```bash
exec pty:true background:true command:"codex exec -C /path/to/project --dangerously-bypass-approvals-and-sandbox '任务描述'" timeout:900
```

**短任务（前台）**：
```bash
exec pty:true command:"codex exec --dangerously-bypass-approvals-and-sandbox '任务'" timeout:60
```

### ⚠️ 不要混用的参数组合

| 组合 | 结果 | 说明 |
|------|------|------|
| `--full-auto` + `--dangerously-bypass-...` | ❌ 报错互斥 | 二者不能同时使用 |
| `--full-auto` 单独用 | ⚠️ 沙箱内运行 | 无法联网 + 无法写外部目录 |
| `--dangerously-bypass-...` 单独用 | ✅ 全权限 | 推荐方式，自动 approval=never |
| `-c 'shell_environment_policy.inherit=all'` | ❌ 无效 | 无法解决沙箱网络隔离问题 |

### 参数速查

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `background` | `true` | Codex 任务通常较长 |
| `pty` | `true` | Codex CLI 需要 TTY |
| `timeout` | 600-900s | 联网研究任务需要较长时间 |

---

## 三、模型上下文限制

| 模型 | contextWindow | maxTokens |
|------|---------------|-----------|
| GLM-5（opus） | 200,000 | 128,000 |
| GLM-4.7（sonnet） | 200,000 | 131,072 |
| GLM-4.5-air（haiku） | 200,000 | 131,072 |
| GPT-5.4（Codex） | ~200K | ~16K output |

Claude Code 的 `CLAUDE_CONTEXT_CAPACITY` 配置为 128000。

---

## 四、环境配置

### Clash fake-IP 环境

宿主机使用 Clash TUN + fake-ip（198.18.x.x），需配置：

```json
{
  "tools": {
    "web": {
      "fetch": {
        "ssrfPolicy": {
          "allowRfc2544BenchmarkRange": true
        }
      }
    }
  }
}
```

此配置解决 OpenClaw `web_fetch` 的 SSRF 拦截。Codex 的联网问题通过关闭沙箱解决。

### Git 仓库

Claude Code 必须在 git 仓库中运行：
```bash
cd /tmp && git init -q
```

Codex 不强制要求 git 仓库，但建议使用 `-C` 指定工作目录。

---

## 五、监控与获取结果

### 后台任务监控

```bash
# 查看进度
process action:poll sessionId:<id> timeout:300000

# 查看日志
process action:log sessionId:<id>

# 等待完成后读取输出文件
cat /tmp/result.md
```

后台 exec 完成后会自动返回结果到当前对话。

---

## 六、完整示例

### 示例 1：Claude Code 快速代码生成
```bash
exec command:"claude --print --permission-mode bypassPermissions '用 Python 写快速排序'" timeout:30
```

### 示例 2：Claude Code 网络调研（后台 + 文件传递）
```bash
write path:/tmp/research-task.txt content:"调研 OpenClaw ACP agents 配置方式"
exec background:true command:"claude --print --permission-mode bypassPermissions '读取 /tmp/research-task.txt 执行调研，结果写入 /tmp/research-result.md'" timeout:300
```

### 示例 3：Codex 联网研究（推荐方式）
```bash
exec pty:true background:true command:"codex exec --dangerously-bypass-approvals-and-sandbox '搜索2026年中国创新药医保谈判最新政策变化，总结关键要点'" timeout:300
```

### 示例 4：Codex 写文件到目标目录
```bash
exec pty:true background:true command:"codex exec -C /Users/evan/.openclaw/gateways/life/domains/agent-factory --dangerously-bypass-approvals-and-sandbox '读取 /tmp/task.md 并按要求在 projects/2604231/ 下创建文件'" timeout:600
```

---

## 七、常见问题

**Q: Claude Code 被 SIGKILL 杀死？**
A: 内存不足。关闭大内存应用，确认用了 `background:true`。

**Q: Claude Code 无输出？**
A: 可能搜索卡住。缩短 prompt 或用文件传递。

**Q: Codex 无法联网？**
A: 沙箱阻止了 Clash TUN 的网络访问。用 `--dangerously-bypass-approvals-and-sandbox` 关闭沙箱。

**Q: Codex 无法写入目标目录？**
A: 同上，沙箱限制了写入范围。关闭沙箱即可。

**Q: `--full-auto` 和 `--dangerously-bypass-...` 冲突？**
A: 对，二者互斥。只用 `--dangerously-bypass-approvals-and-sandbox` 即可，它自动包含 auto-approve。

**Q: Codex 联网但 Clash fake-ip 拦截？**
A: 关闭沙箱后 Codex 走正常系统网络栈，Clash TUN 正常接管，问题自动解决。

---

## 版本历史

- **v3.0** (2026-04-23): 新增 Codex 完整调用指南，解决沙箱+联网问题
- **v2.0** (2026-04-21): 新增模型映射、内存要求、Clash SSRF 配置
- **v1.0** (2026-04-20): 初始版本

---

## 参考

- Claude Code 配置：`~/.claude/settings.json`
- Codex 配置：`~/.codex/settings.json`
- Gateway 模型配置：`Gateway 模型与上下文配置标准 v1.0`
- OpenClaw coding-agent skill：`/opt/homebrew/lib/node_modules/openclaw/skills/coding-agent/SKILL.md`
