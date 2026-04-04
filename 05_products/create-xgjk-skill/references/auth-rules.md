# 鉴权规则

## 哪些操作需要 token

| 操作类型 | 需要 token |
|---------|-----------|
| `get-skills` 查询（nologin接口）| ❌ 否 |
| Skill 包生成流程（Step 1-5）| ❌ 否 |
| `fetch_api_doc.py` 获取接口文档 | ❌ 否 |
| `register-skill` 注册 | ✅ 是 |
| `update-skill` 更新 | ✅ 是 |
| `delete-skill` 下架 | ✅ 是 |
| 上传七牛 | ✅ 是 |

## 核心规则

1. **禁止问用户任何关于 token/鉴权/登录的问题** — 遵循 `common/auth.md` 短路优先级规则
2. **只有需要鉴权的操作才获取 token**
3. 鉴权流程详见 `common/auth.md`

## 重试策略

脚本执行出错时：间隔 1 秒、最多重试 3 次，禁止无限重试。
