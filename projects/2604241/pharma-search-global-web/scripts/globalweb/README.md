# 脚本索引：`globalweb`

| 脚本 | 鉴权 | 用途 |
|------|------|------|
| `append_global_evidence.py` | `nologin` | 校验 `query` ∈ 合同 `global_queries` 后追加 `evidence.jsonl` |

## 示例

```bash
python3 scripts/globalweb/append_global_evidence.py \
  --run-root "/path/to/RUN_ROOT" \
  --evidence-json "./one-global-evidence.json"
```
