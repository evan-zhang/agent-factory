# 鉴权模式：本 Skill

| 动作 | 模式 | 说明 |
|------|------|------|
| `append_global_evidence.py` | **`nologin`** | 仅追加 **`evidence.jsonl`**。**Global 检索**由 Agent 按合同 **`channel_bindings.GLOBAL_SEARCH`** 调用（实现以部署为准），本脚本校验 **`query` 属于该维 `global_queries`** 后再落盘。 |

声明 **`cms-auth-skills`** 为组织基线；当前脚本不读 AppKey。
