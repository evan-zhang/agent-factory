---
name: pharma-evidence-audit-loop
description: 城市院外检索审计闭环：读取 search_spec 与 evidence，产出 audit_report.json 与人读 gap_report.md。
skillcode: pharma-evidence-audit-loop
github: https://github.com/xgjk/xg-skills/tree/main/pharma-evidence-audit-loop
dependencies:
  - cms-auth-skills
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604241/pharma-evidence-audit-loop
version: 0.1.1
---

# pharma-evidence-audit-loop

## 核心定位

本 Skill 只做一件事：作为**证据审计器**，读取 **`search_spec.json`** 与本 run **`evidence.jsonl`** 做首版启发式审计，写入 **`audit_report.json`** 与 **`gap_report.md`**。**不**回改 **`evidence.jsonl`**。

## 当前版本

**`0.1.1`** · 接口 **`v1`**

## 能力概览

- **`audit`**：单机审计脚本 **`audit_run.py`**。

## 统一规范

- 真源：**`references/audit/README.md`**、run 内 **`search_spec.json`**、错误码约定（见 **`references/maintenance.md`**）。

## 授权依赖

声明 **`cms-auth-skills`**；脚本 **`nologin`**。

## 在本流水线中的触发关系

- **前置**：**`pharma-search-cn-policy`**（及按需 **`pharma-search-global-web`**）写完 **`evidence.jsonl`** 后，由 **`pharma-outpatient-orchestrator`** 总控 **自动**调度本 Skill。
- **本步职责**：执行 **`audit_run.py --run-root <RUN_ROOT>`** → **`audit_report.json`**、**`gap_report.md`**。
- **下游（自动）**：总控根据 **`audit_report.field_verdicts`** 撰写 **`summary.md`**（院外 §4.1）→ **`finalize_run.py`**。详见 **`pharma-outpatient-orchestrator`** 的 **「用户确认后的自动执行链」**。

## 建议工作流

1. 读 **`references/audit/README.md`**。
2. 执行 **`audit_run.py --run-root ...`**。
3. 将 **`audit_report.field_verdicts`** 交总控撰写 **`summary.md`**（院外 §4.1）。

## 路由与加载规则

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|----------|------|----------|----------|------|
| 跑一轮证据审计 | `audit` | 生成 audit_report + gap_report | `./references/audit/README.md` | `./scripts/audit/audit_run.py` |

## 宪章

- **不**修改、删除 **`evidence.jsonl`** 行。
- **不**改写 **`search_spec.json`**。
- 错误码集合与总契约 §5.4 **对齐命名**；语义以总契约为准。

## 目录结构

```text
pharma-evidence-audit-loop/
├── SKILL.md
├── version.json
├── references/
│   ├── auth.md
│   ├── maintenance.md
│   └── audit/
│       └── README.md
└── scripts/
    └── audit/
        ├── README.md
        └── audit_run.py
```
