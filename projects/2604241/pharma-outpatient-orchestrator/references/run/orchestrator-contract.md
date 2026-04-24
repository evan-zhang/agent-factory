# 总控契约摘要（非全文真源）

完整流程以 **`../../../../../网络搜索/院外药品搜索.md`** §5 为准。

## 本 Skill 脚本分工

| 脚本 | 阶段 |
|------|------|
| `init_run.py` | 建 **RUN_ROOT**，占位符替换后原子写 **`search_spec.json`**，写 **`run_meta.json`** 头、可选 **`include_domains_resolution`**，并创建空 **`evidence.jsonl`**。 |
| `finalize_run.py` | 校验必落文件存在，补 **`run_meta.json`** 完成字段，不代写 **`summary.md`** 正文（由 Agent 按 §4.1 撰写）。 |

## 占位符

`{{TASK_ID}}`、`{{RUN_ID}}`、`{{GENERATED_AT}}`、`{{CITY}}`；`city_or_topic` 默认 **`{CITY}-院外全景`**（与模板一致）。

## RUN_ROOT

`<base_dir>/<task_id>/<city_or_topic_slug>/<run_id>/`，slug 规则见院外文档 §2 / §7。

## 调度

检索与审计由 **`pharma-search-cn-policy`**、**`pharma-search-global-web`**、**`pharma-evidence-audit-loop`** 完成；总控 Skill 负责编排与 **`summary.md`**。

## 检索通道默认

合同 **`channel_bindings`**：**国内与 Global 均以 `minmax_web_search_mcp` 为默认执行首项**；**`init_run.py`** 落盘前会规范化绑定顺序。OpenClaw 侧需 **acpx** 注入该 MCP（通常经 **ACP** 会话）；不以 **`tools.web`（Brave）** 作为院外默认。

## 谁调用 MCP

**Agent**（执行检索步的会话）按合同调 **`minmax_web_search_mcp`**；**`pharma-search-cn-policy`** / **`pharma-search-global-web`** 的 Python 脚本**只负责校验与追加 `evidence.jsonl`**。**`pharma-outpatient-orchestrator`** 与 **`pharma-evidence-audit-loop`** **不调 MCP**。详见 **`SKILL.md`** §「谁调用 MCP」表。

## 用户确认闸门与自动链

执行 **`init_run.py`** 前须完成 **`SKILL.md`** 中的 **「用户只提供检索城市」** 确认；用户确认后按 **「用户确认后的自动执行链」** 自动依次触发各子 Skill（见 **`SKILL.md`** 表格）。
