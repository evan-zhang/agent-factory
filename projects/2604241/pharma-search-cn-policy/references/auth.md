# 鉴权模式：本 Skill

| 动作 | 模式 | 说明 |
|------|------|------|
| `append_evidence.py` | **`nologin`** | 仅向 **`evidence.jsonl`** 追加 JSON 行；**实际检索**由 Agent 使用合同绑定 **`minmax_web_search_mcp`** 完成后再调用本脚本落盘。 |

依赖 **`cms-auth-skills`** 为组织基线声明；当前脚本不读取 AppKey。
