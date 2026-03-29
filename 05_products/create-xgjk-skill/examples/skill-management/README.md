# skill-management 使用场景

## 触发条件

| 场景 | 触发意图 | 对应接口 | 需要鉴权 |
|---|---|---|---|
| 用户要查看平台上有哪些 Skill | "查看 Skill 列表"、"有哪些 Skill" | get-skills | 否 |
| 用户要把 Skill 打成 ZIP 包 | "打包 Skill"、"生成 ZIP" | pack-skill | 否 |
| 用户要上传 ZIP 到七牛 | "上传到七牛"、"上传 ZIP" | upload-to-qiniu | 是 |
| 用户完成 Skill 包开发，要发布到平台 | "发布 Skill"、"注册 Skill" | register-skill | 是 |
| 用户要更新已发布 Skill 的信息 | "更新 Skill"、"修改 Skill 描述" | update-skill | 是 |
| 用户要下架一个已发布的 Skill | "下架 Skill"、"删除 Skill" | delete-skill | 是 |

## 标准流程

### 发布新 Skill（完整流程）

1. 确认 Skill 包已通过验证清单（A-H）
2. 调用 `pack_skill.py` 将 Skill 目录打包为 ZIP
3. 调用 `upload_to_qiniu.py` 上传 ZIP 到七牛，获取下载地址
4. 调用 `register_skill.py` 注册 Skill，传入下载地址
5. 确认注册成功

### 更新已有 Skill

1. 通过 `get_skills.py` 查看当前已发布的 Skill
2. 如有新版本包，重新打包 + 上传获取新地址
3. 调用 `update_skill.py` 更新（传入新的下载地址、版本号等）
4. 确认更新成功

### 下架 Skill

1. 通过 `get_skills.py` 确认目标 Skill 的 `id`
2. 确认下架原因
3. 调用 `delete_skill.py` 下架
4. 确认下架成功
