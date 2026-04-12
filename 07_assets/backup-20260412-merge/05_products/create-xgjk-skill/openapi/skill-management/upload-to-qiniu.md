# GET https://sg-cwork-api.mediportal.com.cn/ai-business/qiNiu/getSimpleUploadCredentials + POST https://up-z2.qiniup.com/

## 作用

两步操作：
1. 调用七牛凭证接口获取上传 token 和域名
2. 将文件上传到七牛云存储，返回下载地址

## Headers（凭证接口）

| Header | 必填 | 说明 |
|---|---|---|
| `access-token` | 是 | 鉴权 token（见 `common/auth.md`） |

## 参数表（凭证接口，Query）

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileKey` | string | 是 | 文件在七牛中的 key |
| `corpId` | string | 否 | 企业 ID |

## 凭证响应

```json
{
  "resultCode": 1,
  "data": {
    "token": "七牛上传 token",
    "domain": "cdn-domain.example.com"
  }
}
```

## 上传参数（FormData）

| 字段 | 说明 |
|---|---|
| `file` | 文件内容 |
| `token` | 凭证接口返回的 token |
| `key` | fileKey |

## 最终输出

上传成功后，下载地址为：`https://{domain}/{fileKey}`

## 脚本映射

- 执行脚本：`../../scripts/skill-management/upload_to_qiniu.py`
