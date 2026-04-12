# 一站式发布 Skill（打包 → 上传七牛 → 注册/更新）

## 作用

一键完成 Skill 发布的完整流程：
1. 将 Skill 目录打包为 ZIP
2. 获取七牛凭证并上传 ZIP
3. 用下载地址注册（或更新）Skill 到平台

支持两种模式：
- **注册模式**（默认）：首次发布新 Skill
- **更新模式**（`--update`）：更新已发布 Skill 的包和信息

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `access-token` | 是 | 鉴权 token（见 `common/auth.md`），用于七牛上传和注册/更新 |

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `skill_dir` | string | 是 | Skill 目录路径 |
| `--code` | string | 是 | Skill 唯一标识 |
| `--name` | string | 注册时必须 | Skill 名称 |
| `--description` | string | 否 | Skill 描述 |
| `--label` | string | 否 | Skill 标签 |
| `--version` | integer | 否 | 版本号（更新时使用） |
| `--update` | flag | 否 | 更新模式（默认注册模式） |
| `--output` | string | 否 | ZIP 输出路径（默认 `<skill-name>.zip`） |
| `--file-key` | string | 否 | 七牛文件 key（默认自动生成） |
| `--internal` | flag | 否 | 标记为内部 Skill |

## 使用示例

```bash
# 首次发布
python3 create-xgjk-skill/scripts/skill-management/publish_skill.py \
  ./im-robot --code im-robot --name "IM 机器人" --description "管理 IM 机器人"

# 更新已有 Skill
python3 create-xgjk-skill/scripts/skill-management/publish_skill.py \
  ./im-robot --code im-robot --update --version 2
```

## 内部流程

```
skill_dir → pack_skill.py → .zip → upload_to_qiniu.py → download_url → register/update_skill.py
```

## 脚本映射

- 执行脚本：`../../scripts/skill-management/publish_skill.py`
