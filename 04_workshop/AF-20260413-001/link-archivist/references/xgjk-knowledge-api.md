# 知识库 API 快速参考

**Base URL**: `https://sg-al-cwork-web.mediportal.com.cn/open-api`
**Header**: `appKey: {用户Key}`

---

## 1. 获取个人项目 ID

```
GET /document-database/project/personal/getProjectId
```

返回: `{ resultCode: 1, data: { projectId, projectName } }`

## 2. 获取文件列表

```
GET /document-database/file/getChildFiles?projectId={pid}&parentId={folderId}
```

返回: 文件列表（含 id/name/type/size/createTime）

## 3. 搜索文件

```
GET /document-database/file/searchFile?projectId={pid}&keyword={kw}
```

返回: `{ data: [{ fileId, fileName, summary, ... }] }`

## 4. 上传内容（创建文件+文件夹）

```
POST /ai-huiji/uploadContentToPersonalProject
Body: { projectId, content, fileName, folderName }
```

- `folderName` 支持路径分隔：`知识档案/K-260406-001`
- 同 folderName + 同 fileName 会创建副本 "(1)"
- 返回: `{ data: { fileId, folderId, downloadUrl } }`

## 5. 删除文件

```
POST /document-database/file/deleteFile
Body: { fileId: number }
```

返回: `{ data: true }`

## 6. 更新文件（无直接 API）

使用 **deleteFile + uploadContent** 两步实现：
1. 记录原文件的 folderName
2. deleteFile 删除旧文件
3. uploadContent 用相同 folderName 重新上传

---

## 错误处理

| resultCode / HTTP | 含义 | 处理 |
|---|---|---|
| 401/403 | Key 失效 | 停止→引导 Story0 |
| 400 | 参数错误 | 检查请求体 |
| 500 | 服务器错误 | 重试1次，失败保留本地 |
| resultCode=1 | 成功 | 继续 |
