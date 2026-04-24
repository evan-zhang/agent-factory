# 模块 `cn`：国内政策证据落盘

## 适用场景

Agent 已用 **`minmax_web_search_mcp`**（或合同允许的等价通道）完成一次查询，需要将**单条**证据以 JSON 形式追加到 **`RUN_ROOT/evidence.jsonl`**。

## 鉴权

见 **`../auth.md`**：`nologin`。

## 动作

| 动作 | 脚本 |
|------|------|
| 追加一条证据 | `scripts/cn/append_evidence.py` |

## 输入

- **`--run-root`**：RUN 根目录（含 **`evidence.jsonl`**）。
- **`--evidence-json`**：文件路径，内容为**单个** JSON 对象；或使用 **`--evidence-json-stdin`** 从 stdin 读入一对象。

## 证据最小键（与总契约一致）

`evidence_id`、`task_id`、`subtask_id`、`field_name`、`query_kind`（`positive`|`counter`）、`query`、`source_url`、`evidence_quote`、`captured_at`。

**`subtask_id`**：推荐与 **`field_name` 相同（UTF-8）**（见院外 §7）。

## 输出

向 **`evidence.jsonl`** 追加一行（UTF-8 JSON，无多余空白）；stdout 打印 `{"success":true,"evidence_id":...}`。
