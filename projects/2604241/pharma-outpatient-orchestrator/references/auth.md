# 鉴权模式：本 Skill

| 动作 | 模式 | 说明 |
|------|------|------|
| `init_run.py` / `finalize_run.py` | **`nologin`** | 仅创建/校验本地 **RUN_ROOT** 下文件，不调用 XGJK CMS API、不读取 AppKey。 |

本包仍声明依赖 **`cms-auth-skills`** 以符合组织 Skill 基线；若后续脚本扩展为调用内部 API，再改为 `appKey` / `access-token` 并由上游注入。
