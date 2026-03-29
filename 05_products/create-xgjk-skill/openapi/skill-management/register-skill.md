# POST https://sg-cwork-api.mediportal.com.cn/im/skill/register

## 作用

注册（发布）一个新的 AI Skill 到平台。

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `access-token` | 是 | 鉴权 token（见 `common/auth.md`） |
| `Content-Type` | 是 | `application/json` |

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 是 | Skill 唯一标识 |
| `name` | string | 是 | Skill 名称 |
| `description` | string | 否 | Skill 描述 |
| `downloadUrl` | string | 否 | Skill 包下载地址 |
| `label` | string | 否 | Skill 标签 |
| `isInternal` | boolean | 否 | 是否为内部 Skill |

## 请求 Schema

```json
{
  "code": "im-robot",
  "name": "IM 机器人管理",
  "description": "管理 IM 机器人的注册、配置、删除等操作",
  "downloadUrl": "https://example.com/skills/im-robot.zip",
  "label": "IM",
  "isInternal": false
}
```

## 响应 Schema

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": { ... }
}
```

## 脚本映射

- 执行脚本：`../../scripts/skill-management/register_skill.py`
