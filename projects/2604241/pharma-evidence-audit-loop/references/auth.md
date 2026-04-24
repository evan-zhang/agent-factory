# 鉴权模式：本 Skill

| 动作 | 模式 | 说明 |
|------|------|------|
| `audit_run.py` | **`nologin`** | 读取本 run 的 `search_spec.json` 与 `evidence.jsonl`，生成 **`audit_report.json`** 与 **`gap_report.md`**。 |

声明 **`cms-auth-skills`**；脚本不读 AppKey。
