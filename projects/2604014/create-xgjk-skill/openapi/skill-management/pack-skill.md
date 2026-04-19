# 本地操作：打包 Skill 目录为 ZIP

## 作用

将指定的 Skill 目录打包成 `.zip` 文件，用于后续上传到七牛云存储。

> **本地操作**，不调用远程 API，无需鉴权。

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `skill_dir` | string | 是 | Skill 目录路径 |
| `--output` | string | 否 | 输出 ZIP 文件路径（默认 `<skill-name>.zip`） |

## 使用示例

```bash
python3 create-xgjk-skill/scripts/skill-management/pack_skill.py ./im-robot
python3 create-xgjk-skill/scripts/skill-management/pack_skill.py ./im-robot --output ./dist/im-robot-v1.zip
```

## 输出

- stderr: 打包进度（文件数、大小）
- stdout: ZIP 文件绝对路径（可管道传给 upload_to_qiniu.py）

## 脚本映射

- 执行脚本：`../../scripts/skill-management/pack_skill.py`
