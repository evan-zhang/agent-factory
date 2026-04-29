### cms-tbs-scene-create：access-token 获取与注入（强制）

这份规则用于约束 Agent：任何需要执行本 Skill 的 `scripts/*.py` 的链路，access-token 获取必须通过依赖 Skill `cms-auth-skills` 完成。

#### 必须做
- 只要确定要进入本 Skill 的执行链路（`exec python3 scripts/<name>.py`），在调用目标脚本之前，**必须先调用** `cms-auth-skills` 获取有效的 **TBS** `access-token`。
- 将 `cms-auth-skills` 返回的 access-token **以 `--access-token` 注入**到后续执行命令中（例如：`python3 scripts/tbs-scene-create.py ... --access-token "<ACCESS_TOKEN>"`）。
  - 注意：`tbs-scene-validate.py` 不依赖 access-token；access-token 在 `tbs-scene-fetch-config.py` 与 `tbs-scene-create.py`（调用 API）时必需。

#### 必须禁止
- 禁止自行从环境变量读取 access-token（例如：`TBS_ACCESS_TOKEN` 等）。
- 禁止按某种“自动解析逻辑”（如根据 businessDomain/department/drug 文本推断 token）去获取 access-token。
- 禁止向用户索要 access-token（不要问“把 token 发我/让我用哪个键”这类问题）。
- 禁止在 `cms-auth-skills` 未返回可用 access-token 时继续调用 `scripts/*.py`（尤其是 `tbs-scene-fetch-config.py` / `tbs-scene-create.py`）。

#### 失败处理
- `cms-auth-skills` 获取失败或无可用 access-token：必须停止当前链路，并引导用户重新完成授权/登录；然后再重新尝试进入执行链路。

