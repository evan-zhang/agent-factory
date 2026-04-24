# 模块 `globalweb`：Global 查询证据落盘

## 适用场景

某 **`field_name`** 在 **`search_spec.json`** 中 **`global_queries` 非空**，Agent 已按**所列原句**完成 Global 检索，需追加一条证据。

## 鉴权

**`nologin`**（见 **`../auth.md`**）。

## 动作

| 动作 | 脚本 |
|------|------|
| 追加一条 Global 证据 | `scripts/globalweb/append_global_evidence.py` |

## 输入

- **`--run-root`**：RUN 根目录。
- **`--evidence-json`** 或 **`--evidence-json-stdin`**：单对象 JSON（键同国内证据 + **`query` 必须等于合同 `global_queries` 中某一项**（占位符已按 run 替换后的最终句））。

## 约束

- **`global_queries` 为空**的维度**不得**调用本脚本。
- **禁止**用 **`positive_queries` / `counter_queries`** 的结果冒充 Global 行（院外 §6）。
