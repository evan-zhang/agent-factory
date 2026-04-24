# 模块 `audit`：证据审计与缺口报告

## 适用场景

本 run **`evidence.jsonl`** 已写完（国内/Global 段结束），需生成 **`audit_report.json`** 与 **`gap_report.md`**。

## 鉴权

**`nologin`**（**`../auth.md`**）。

## 动作

| 动作 | 脚本 |
|------|------|
| 运行审计 | `scripts/audit/audit_run.py` |

## 输入

- **`--run-root`**：RUN 根目录（须含 **`search_spec.json`**、**`evidence.jsonl`**）。

## 输出

- **`audit_report.json`**：`field_verdicts[]` 含 **`field_name`、`stance`、`reasons`、`codes`**（错误码见总契约 §5.4）。
- **`gap_report.md`**：表头见院外 §4.2。

## 限制（首版）

- 来源等级由 **`source_url` 主机名**粗映射（`gov.cn` / `nmpa.gov.cn` 等），**不**替代人工法理判断。
- **`E_DEDUP_COLLISION`** 等需复杂去重的项可能未触发。
