---
name: pharma-search-cn-policy
description: 城市院外检索国内段：按合同串行维度取证，将 minmax_web_search_mcp 结果规范追加到 evidence.jsonl。
skillcode: pharma-search-cn-policy
github: https://github.com/xgjk/xg-skills/tree/main/pharma-search-cn-policy
dependencies:
  - cms-auth-skills
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604241/pharma-search-cn-policy
version: 0.1.3
---

# pharma-search-cn-policy

## 核心定位

本 Skill 只做一件事：作为**国内检索证据写入器**，对 **`search_spec.field_specs`** 串行执行 **`positive_queries`** 再 **`counter_queries`**；检索由 Agent 按合同通道完成；脚本只负责**校验并追加** **`evidence.jsonl`**。

## 当前版本

**`0.1.3`**（见 **`version.json`**） · 接口 **`v1`**

## 能力概览

- **`cn`**：单条证据校验与追加。

## 统一规范

- 真源：**`references/cn/README.md`**、run 内 **`search_spec.json`**、模板中的 **`channel_bindings.CN_SEARCH`**。
- 日志：**.cms-log/log/pharma-search-cn-policy/**（可选，后续扩展）。

## 授权依赖

声明 **`cms-auth-skills`**；当前脚本 **`nologin`**，见 **`references/auth.md`**。

## OpenClaw 运行时（与总控一致）

合同 **`CN_SEARCH`** **默认首项为 `minmax_web_search_mcp`**（**`init_run.py`** 会保证顺序）。该 MCP 由网关 **acpx** 注入，须在 **ACP 类会话**（或 **`sessions_spawn` + `runtime: "acp"`**）中调用。**`tools.web`（Brave）不是院外默认检索**；仅 MCP 不可用且已按总控文档允许降级时使用，并须在证据链中可审计说明。

## 输入完整性规则

- **`append_evidence.py`** 必须满足最小键集合（见 **`references/cn/README.md`**）。
- **`query_kind`** 仅 **`positive`** / **`counter`**。

## 在本流水线中的触发关系

- **上游**：**`pharma-outpatient-orchestrator`** 在用户确认城市并完成 **`init_run.py`** 之后，**自动进入本 Skill**（无需用户再次点名本 Skill）。
- **本步职责**：按 **`search_spec.json`** 对 **`field_specs`** 串行跑 **正查 → 反查**，用合同 **`CN_SEARCH`**（如 **`minmax_web_search_mcp`**）检索；每条可引用证据调用 **`append_evidence.py`**。
- **下游（自动）**：国内段结束后 → 若存在 **`global_queries` 非空** 的维度，由总控自动进入 **`pharma-search-global-web`**；否则跳过 Global → 自动进入 **`pharma-evidence-audit-loop`**（**`audit_run.py`**）→ 总控写 **`summary.md`** → **`finalize_run.py`**。详见 **`pharma-outpatient-orchestrator`** 的 **「用户确认后的自动执行链」**。

## 建议工作流

1. 读 **`references/cn/README.md`**。
2. Agent 按维度执行检索（先正后反）。
3. 每条可引用证据调用 **`append_evidence.py`** 一次。

## 脚本使用规则

- 一条成功检索 → 一行 **`evidence.jsonl`**；**只追加**、不改合同。

## 路由与加载规则

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|----------|------|----------|----------|------|
| 追加国内政策证据一行 | `cn` | 校验 JSON 并 append | `./references/cn/README.md` | `./scripts/cn/append_evidence.py` |

## 宪章

- **不**修改 **`search_spec.json`** 中的验收字段。
- **不**写 **`audit_report` / `gap_report`**。
- 商业站线索若落盘，**`source_url` 须为官域可引用页**（院外 §3）。

## 目录结构

```text
pharma-search-cn-policy/
├── SKILL.md
├── version.json
├── references/
│   ├── auth.md
│   ├── maintenance.md
│   └── cn/
│       └── README.md
└── scripts/
    └── cn/
        ├── README.md
        └── append_evidence.py
```
