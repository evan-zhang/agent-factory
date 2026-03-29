# GET https://cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey={CWork Key}

## 作用

**Query 参数**
| 参数 | 必填 | 说明 |
|---|---|---|
| `appCode` | 是 | 固定 `cms_gpt` |
| `appKey` | 是 | CWork Key |

**Headers**
- `Content-Type: application/json`

## 响应（关键字段）

**仅使用：** `data.xgToken`

示例：
```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": {
    "xgToken": "xxx"
  }
}
```

## 脚本映射

- 认证逻辑：`../../common/auth.md`
