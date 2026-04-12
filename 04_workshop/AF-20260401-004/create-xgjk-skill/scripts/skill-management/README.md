# skill-management 脚本清单

## 脚本列表

| 脚本 | 接口文档 | 说明 | 需要鉴权 |
|---|---|---|---|
| **`publish_skill.py`** | [publish-skill.md](../../openapi/skill-management/publish-skill.md) | **一站式发布：打包→上传→注册/更新** | **是** |
| `pack_skill.py` | [pack-skill.md](../../openapi/skill-management/pack-skill.md) | 打包 Skill 目录为 ZIP | 否 |
| `upload_to_qiniu.py` | [upload-to-qiniu.md](../../openapi/skill-management/upload-to-qiniu.md) | 获取七牛凭证 + 上传文件 | 是 |
| `register_skill.py` | [register-skill.md](../../openapi/skill-management/register-skill.md) | 注册（发布）新 Skill | 是 |
| `update_skill.py` | [update-skill.md](../../openapi/skill-management/update-skill.md) | 更新已有 Skill | 是 |
| `delete_skill.py` | [delete-skill.md](../../openapi/skill-management/delete-skill.md) | 下架（删除）Skill | 是 |
| `get_skills.py` | [get-skills.md](../../openapi/skill-management/get-skills.md) | 获取 Skill 列表 | 否 |

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `XG_USER_TOKEN` | publish/upload/register/update/delete | access-token，pack 和 get-skills 无需鉴权 |

## 一站式发布（推荐）

```bash
# 首次发布（打包 + 上传七牛 + 注册，一条命令搞定）
python3 scripts/skill-management/publish_skill.py \
  ./im-robot --code im-robot --name "IM 机器人"

# 更新已有 Skill（打包 + 上传七牛 + 更新）
python3 scripts/skill-management/publish_skill.py \
  ./im-robot --code im-robot --update --version 2
```

## 分步操作

```bash
# 查看当前已发布的 Skill（无需 token）
python3 scripts/skill-management/get_skills.py

# 仅打包（无需 token）
python3 scripts/skill-management/pack_skill.py ./im-robot

# 仅上传（需要 XG_USER_TOKEN）
python3 scripts/skill-management/upload_to_qiniu.py ./im-robot.zip

# 仅注册（需要 XG_USER_TOKEN）
python3 scripts/skill-management/register_skill.py \
  --code im-robot --name "IM 机器人" --download-url "https://..."

# 仅更新（需要 XG_USER_TOKEN）
python3 scripts/skill-management/update_skill.py \
  --code im-robot --download-url "https://..." --version 2

# 下架（需要 XG_USER_TOKEN）
python3 scripts/skill-management/delete_skill.py --id 123 --reason "已废弃"
```
