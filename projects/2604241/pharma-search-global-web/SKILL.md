---
name: pharma-search-global-web
description: 城市院外检索 Global 段：仅当合同 global_queries 非空时取证，并将结果规范追加到 evidence.jsonl。
skillcode: pharma-search-global-web
github: https://github.com/xgjk/xg-skills/tree/main/pharma-search-global-web
dependencies:
  - cms-auth-skills
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604241/pharma-search-global-web
version: 0.1.3
---

# pharma-search-global-web

## 核心定位

本 Skill 只做一件事：作为**Global 检索证据写入器**，仅当 **`search_spec.field_specs[].global_queries`** 非空时执行；脚本 **`append_global_evidence.py`** 只校验 **`query` 属于 `global_queries`** 后追加 **`evidence.jsonl`**。

## 当前版本

**`0.1.3`** · 接口 **`v1`**

## 能力概览

- **`globalweb`**：Global 单条证据校验与追加。

## 统一规范

- 真源：**`references/globalweb/README.md`**、run 内 **`search_spec.json`**（含 **`global_queries`** / **`channel_bindings`**）。

## 授权依赖

声明 **`cms-auth-skills`**；脚本 **`nologin`**（**`references/auth.md`**）。

## OpenClaw 运行时（与总控一致）

合同 **`GLOBAL_SEARCH`** **默认首项为 `minmax_web_search_mcp`**（与 **`init_run.py`** 规范化一致）；须在 **ACP / acpx** 或 **`sessions_spawn`（`runtime: "acp"`）** 中调用。**`tools.web` 非默认**；兜底与审计要求见 **`pharma-outpatient-orchestrator`** → **`references/run/README.md`**。

## 在本流水线中的触发关系

- **前置**：**`pharma-search-cn-policy`** 完成国内段后，由 **`pharma-outpatient-orchestrator`** 总控判断是否进入本 Skill。
- **进入条件（自动）**：仅当某 **`field_specs[]` 的 `global_queries`** **非空** 时，总控 **自动**调度本 Skill；**全部为空的 run 跳过本 Skill**。
- **下游（自动）**：Global 段完成后 → **`pharma-evidence-audit-loop`**（**`audit_run.py`**）→ 总控 **`summary.md`** → **`finalize_run.py`**。详见 **`pharma-outpatient-orchestrator`** 的 **「用户确认后的自动执行链」**。

## 建议工作流

1. 读 **`search_spec.json`**，仅对 **`global_queries` 非空** 的维度执行 Global 检索。
2. 每条证据读 **`references/globalweb/README.md`** 后调用 **`append_global_evidence.py`**。

## 路由与加载规则

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|----------|------|----------|----------|------|
| 追加 Global 证据一行 | `globalweb` | 校验 query ∈ global_queries | `./references/globalweb/README.md` | `./scripts/globalweb/append_global_evidence.py` |

## 宪章

- **不**对 **`global_queries` 为空** 的维度调用本 Skill。
- **不**用正/反查询顶替 Global（院外 §6）。
- **不**改合同、不写审计产物。

## 目录结构

```text
pharma-search-global-web/
├── SKILL.md
├── version.json
├── references/
│   ├── auth.md
│   ├── maintenance.md
│   └── globalweb/
│       └── README.md
└── scripts/
    └── globalweb/
        ├── README.md
        └── append_global_evidence.py
```
