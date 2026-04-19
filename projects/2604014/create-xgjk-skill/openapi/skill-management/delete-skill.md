# POST https://sg-cwork-api.mediportal.com.cn/im/skill/delete

## 作用

下架（删除）一个已发布的 Skill。

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `access-token` | 是 | 鉴权 token（见 `common/auth.md`） |
| `Content-Type` | 是 | `application/json` |

## 参数表（Query）

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Skill ID |
| `deleteSkill` | string | 否 | 下架原因 |

> 注意：参数通过 URL Query String 传递，非 Body。

## 请求示例

```
POST /im/skill/delete?id=123&deleteSkill=已废弃
```

## 响应 Schema

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": null
}
```

## 脚本映射

- 执行脚本：`../../scripts/skill-management/delete_skill.py`
