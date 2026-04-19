# GET https://sg-cwork-api.mediportal.com.cn/im/skill/nologin/list

## 作用

获取平台上所有已发布的 AI Skill 列表。

> **无需鉴权**：此接口为 nologin 接口，不需要 `access-token`。

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `Content-Type` | 否 | `application/json`（GET 请求可选） |

## 参数表

无参数。

## 响应 Schema

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": [
    {
      "id": "123",
      "code": "im-robot",
      "name": "IM 机器人管理",
      "description": "...",
      "version": 1,
      "label": "IM"
    }
  ]
}
```

## 脚本映射

- 执行脚本：`../../scripts/skill-management/get_skills.py`
