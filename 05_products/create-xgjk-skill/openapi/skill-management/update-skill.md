# POST https://sg-cwork-api.mediportal.com.cn/im/skill/update

## 作用

更新已注册 Skill 的信息（名称、描述、下载地址等）。

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `access-token` | 是 | 鉴权 token（见 `common/auth.md`） |
| `Content-Type` | 是 | `application/json` |

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 是 | Skill 唯一标识 |
| `name` | string | 否 | 新的 Skill 名称 |
| `description` | string | 否 | 新的描述 |
| `downloadUrl` | string | 否 | 新的下载地址 |
| `label` | string | 否 | 新的标签 |
| `version` | integer | 否 | 版本号 |
| `isInternal` | boolean | 否 | 是否为内部 Skill |

## 请求 Schema

```json
{
  "code": "im-robot",
  "name": "IM 机器人管理 v2",
  "description": "更新后的描述",
  "version": 2
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

- 执行脚本：`../../scripts/skill-management/update_skill.py`
