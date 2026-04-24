---
name: pharma-outpatient-orchestrator
description: 城市院外药品公开信息检索总控：按模板建 RUN、调度国内/Global/审计子 Skill，并产出人读 summary 与 run_meta。
skillcode: pharma-outpatient-orchestrator
github: https://github.com/xgjk/xg-skills/tree/main/pharma-outpatient-orchestrator
dependencies:
  - cms-auth-skills
# bump 时须同步修改同目录下 version.json 的 version 字段
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604241/pharma-outpatient-orchestrator
version: 0.1.5
---

# pharma-outpatient-orchestrator

## 核心定位

本 Skill 只做一件事：作为**总控编排器**管理 run 生命周期——按 **`references/run/orchestrator-contract.md`** 与 **`references/run/README.md`** 启动 run、调度子 Skill、并在末端收口 **`summary.md`** 与 **`run_meta.json`**。检索与审计执行由子 Skill 完成。

## 当前版本

- **Skill 版本**：`0.1.5`（见 **`version.json`**）
- **接口版本**：`v1`（与 `search_spec.spec_version` 独立；后者随模板 bump）

## 能力概览

- **`run`**：初始化 RUN 目录与 **`search_spec.json`**；收尾校验必落文件并补 **`run_meta.json`**。

## 统一规范

- 真源：**`references/run/orchestrator-contract.md`**、**`references/run/README.md`**、**`scripts/run/README.md`**。
- 运行日志：工作区 **`.cms-log/log/pharma-outpatient-orchestrator/`**（脚本写入）。
- 不在 Skill 包内写运行态缓存。

## 授权依赖

- YAML 声明 **`cms-auth-skills`** 以符合组织基线。
- 当前 **`scripts/run/*.py`** 鉴权模式为 **`nologin`**（仅本地文件）；细则 **`references/auth.md`**。

## 输入完整性规则

- **`init_run.py`** 必须提供 **`--task-id`、`--run-id`、`--city`**；**`--template`** 在无法自动发现仓库内模板时必填。
- 进入 **`finalize_run.py`** 前，须已由子 Skill 写好 **`audit_report.json`、`gap_report.md`、`summary.md`** 等（可用 **`--no-require-summary`** 仅作调试）。

## 用户只提供检索城市（如「深圳」）

**闸门（必须先做）**：在调用 **`init_run.py`** 之前，Agent **必须**向用户展示待确认信息，并**明确等待**用户回复 **`确认` / `开始` / `是`**（或等价肯定）后再进入下方「自动执行链」。不得仅凭城市名直接落盘 RUN。

**待确认信息最小清单**（展示给用户，缺省可写「将使用默认值」）：

| 项 | 说明 |
|----|------|
| **城市** | 用户给出的检索城市（如 深圳） |
| **task_id** | 默认可由 Agent 生成建议值（如 `outpatient-<城市拼音>-<YYYYMMDD>`），用户可改 |
| **run_id** | 默认建议（如 `run-001` 或时间戳），用户可改 |
| **工作目录** | 执行 **`init_run.py`** 时的 **`cwd`**（决定 **`network-search-runs`** 落在哪个 workspace）；深圳 + `demo-task` + `run-001` 的落盘示例见 **`scripts/run/README.md`** |
| **合同模板** | **`--template`** 缺省时使用的模板路径（见 **`init_run.py`** 自动发现规则） |
| **国内 / Global 检索** | **默认**均走 **`minmax_web_search_mcp`**（合同 **`channel_bindings`** 首项；**`init_run.py`** 会规范化）；**`tools.web`（Brave）不是院外默认** |
| **OpenClaw 承载** | 默认 MCP 需在 **ACP/acpx** 会话中调用；**embedded** 时用 **`sessions_spawn` + `runtime: "acp"`**；仅 MCP 不可用且已记录失败后，才允许组织策略下的 **`tools.web`** 等兜底，细则 **`references/run/README.md`** |
| **风险/前提** | 需 **`exec`** 跑脚本；检索以 **`minmax_web_search_mcp`** 为准；子 Skill **不**修改合同验收字段 |

## 用户确认后的自动执行链（须遵守）

用户一旦确认，Agent **应自动连续执行**下列步骤，**无需**在每步再问用户（遇错再中断汇报）：

| 步骤 | 触发条件 | 使用 Skill / 动作 | 产出 |
|------|----------|-------------------|------|
| **1** | 用户已确认 | **`pharma-outpatient-orchestrator`** → **`scripts/run/init_run.py`** | **`RUN_ROOT`**、`search_spec.json`、空 **`evidence.jsonl`** |
| **2** | 步骤 1 成功 | **`pharma-search-cn-policy`**：按 **`search_spec.field_specs`** **串行**维度，先 **`positive_queries`** 再 **`counter_queries`**，**默认用合同 `CN_SEARCH` 首项 `minmax_web_search_mcp`** 检索；每条可引用结果调用 **`append_evidence.py`** | 追加 **`evidence.jsonl`** |
| **3** | 某维度 **`global_queries` 非空** | **`pharma-search-global-web`**：**默认用合同 `GLOBAL_SEARCH` 首项 `minmax_web_search_mcp`** 检索并 **`append_global_evidence.py`** | 追加 **`evidence.jsonl`** |
| **4** | 步骤 2（及按需步骤 3）完成 | **`pharma-evidence-audit-loop`** → **`audit_run.py`** | **`audit_report.json`**、**`gap_report.md`** |
| **5** | 步骤 4 成功 | 总控 Agent（本流水线）按院外 **§4.1** 撰写 **`summary.md`** | **`summary.md`** |
| **6** | 步骤 5 完成 | **`pharma-outpatient-orchestrator`** → **`finalize_run.py`** | 校验并收口 **`run_meta.json`** |

**触发关系一句话**：确认后 **总是**先 **`pharma-outpatient-orchestrator`（init_run）** → **总是** **`pharma-search-cn-policy`** → **仅当**合同有 Global 查询时 **`pharma-search-global-web`** → **总是** **`pharma-evidence-audit-loop`** → **总控写 `summary.md`** → **总是** **`finalize_run.py`**。

## 建议工作流

1. 读 **`references/run/orchestrator-contract.md`** 与 **`references/run/README.md`**。
2. 读 **`scripts/run/README.md`**（参数与示例命令）。
3. 若用户只给城市：先完成本节 **「用户只提供检索城市」** 的确认闸门，再继续。
4. 执行 **`init_run.py`** 得到 **`run_root`**。
5. 按上表自动执行 **`pharma-search-cn-policy`**、条件性 **`pharma-search-global-web`**、**`pharma-evidence-audit-loop`**，撰写 **`summary.md`**，最后 **`finalize_run.py`**。

## 谁调用 MCP（四 Skill 边界）

「用户确认城市 → 自动拆维度与查询」由 **执行流水线的 Agent**（在 **`pharma-outpatient-search`** 等工作区、按本 Skill 自动链）完成；**调用 MCP 的主体是 Agent 运行时**，不是 Python 脚本。四包分工如下：

| Skill | 是否调 MCP | 合同通道 | 脚本做什么 |
|-------|------------|-----------|------------|
| **`pharma-outpatient-orchestrator`** | **否** | — | **`init_run.py`** / **`finalize_run.py`** 只落盘与校验；总控写 **`summary.md`**；**宪章：总控不亲自调检索 MCP** |
| **`pharma-search-cn-policy`** | **是（Agent）** | **`channel_bindings.CN_SEARCH`**，默认首项 **`minmax_web_search_mcp`** | **`append_evidence.py`**：校验并 **append** **`evidence.jsonl`** |
| **`pharma-search-global-web`** | **是（Agent）** | **`channel_bindings.GLOBAL_SEARCH`**，默认首项 **`minmax_web_search_mcp`** | **`append_global_evidence.py`**：校验 query ∈ **`global_queries`** 后 append |
| **`pharma-evidence-audit-loop`** | **否** | — | **`audit_run.py`**：读 **`search_spec` + `evidence.jsonl`**，写 **`audit_report` / `gap_report`** |

**自动触发顺序**（确认后）：总控 **init_run** → **cn-policy**（国内 MCP 检索 + append）→ 条件 **global-web**（Global MCP 检索 + append）→ **audit-loop**（无 MCP）→ 总控 **summary** → **finalize**。

## 姐妹 Skill（同流水线）

| Skill | 目录（相对 `workspace/skills/`） |
|-------|-----------------------------------|
| `pharma-search-cn-policy` | `pharma-search-cn-policy/` |
| `pharma-search-global-web` | `pharma-search-global-web/` |
| `pharma-evidence-audit-loop` | `pharma-evidence-audit-loop/` |

## 脚本使用规则

- 执行前必读对应 **`references/run/README.md`**。
- 使用 **`python3`**；在含 **`scripts/run/`** 的 Skill 根目录下传入相对路径，或使用绝对路径。

## 路由与加载规则

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|----------|------|----------|----------|------|
| 开始一次院外检索 run | `run` | 建 RUN_ROOT、渲染 search_spec | `./references/run/README.md` | `./scripts/run/init_run.py` |
| 结束一次 run 并校验落盘 | `run` | 校验必落文件、补 run_meta | `./references/run/README.md` | `./scripts/run/finalize_run.py` |

## 宪章

- 总控是**控制面专职**：只负责编排、门禁、收口；不承担检索/审计执行职责。
- 总控**不**亲自调用检索 MCP、**不**修改合同中的 **`acceptance_rule` / required_evidence_count / min_source_grade`**。
- **不**在总控内写 **`audit_report`/`gap_report` 正文**（由审计 Skill 产出）。
- **`search_spec.json`** 与模板 **`field_name`** 以 JSON 与 **§1.1** 为真源。

## 目录结构（能力树）

```text
pharma-outpatient-orchestrator/
├── SKILL.md
├── version.json
├── references/
│   ├── auth.md
│   ├── maintenance.md
│   └── run/
│       ├── README.md
│       └── orchestrator-contract.md
└── scripts/
    └── run/
        ├── README.md
        ├── init_run.py
        └── finalize_run.py
```
