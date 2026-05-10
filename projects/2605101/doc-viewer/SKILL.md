---
name: doc-viewer
version: "1.0.0"
description: 将 Markdown 或 HTML 文件上传到 Doc Viewer 服务，返回在线预览链接。触发条件：用户要求上传文件到网站、预览文件、获取文件链接。
triggers:
  - 上传文件
  - 预览文件
  - 文件链接
  - 上传到网站
  - 生成链接
---

# Doc Viewer — 文件上传与在线预览

将用户提供的 Markdown (.md) 或 HTML (.html/.htm) 文件上传到 Doc Viewer 服务，返回在线预览链接。

> 部署细节见 `references/deployment.md`

## 支持的文件类型

仅支持以下两种：
- **Markdown**: `.md`, `.markdown`
- **HTML**: `.html`, `.htm`

其他文件类型（PDF、DOCX、图片等）**不支持**，应明确告知用户。

## 服务信息

- **服务地址**：`http://doc.20100706.xyz`
- **部署服务器**：`140.235.37.79`（Nginx 反代 → FastAPI 8080）
- **版本**：v1.1.0（含文件列表、按天分组、暗色模式）
- **源码路径**（本机）：`/data/doc-viewer/app.py`

## API 接口

### 上传文件

```
POST http://doc.20100706.xyz/upload
Content-Type: multipart/form-data
```

**参数：**
- `file` — 文件（与 `content` 二选一）
- `content` — 文本内容（与 `file` 二选一）
- `format` — 文本格式：`markdown` / `html` / `auto`（仅 `content` 模式需要）

**文件上传示例：**
```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

**文本上传示例：**
```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "content=<文本内容>" \
  -F "format=markdown"
```

**返回：**
```json
{
  "id": "897e2d322c8f",
  "filename": "executive-summary-v5.html",
  "format": "html",
  "size": 28618,
  "url": "http://doc.20100706.xyz/view/897e2d322c8f",
  "raw_url": "http://doc.20100706.xyz/raw/897e2d322c8f"
}
```

### 其他接口

- `GET /view/{id}` — 渲染预览（HTML 直接渲染，Markdown 转 HTML 渲染）
- `GET /raw/{id}` — 返回原始文件内容
- `GET /api/{id}` — 返回文档 JSON 元信息
- `GET /api/list` — 返回所有文档列表（JSON 数组，按时间倒序）
- `DELETE /api/{id}` — 删除文档
- `GET /` — 首页（上传 + 文件列表，按天分组）

## 触发条件

当用户表达以下意图时触发本 Skill：
- "帮我上传这个文件"
- "我要预览这个文件"
- "给我一个链接"
- "把这个文件上传到网站"
- "生成预览链接"

## 操作步骤

### Step 1: 获取文件

文件来源可能是：
1. **Telegram 附件** — 文件缓存在 `/root/.hermes/cache/documents/` 下，文件名格式 `doc_<hash>_<original_filename>`
2. **本地路径** — 用户直接提供文件路径
3. **用户提供内容** — 用户直接粘贴文本内容

### Step 2: 验证文件类型

检查文件扩展名，必须是 `.md`、`.markdown`、`.html`、`.htm` 之一。
如果是其他类型，告知用户："目前仅支持 Markdown (.md) 和 HTML (.html/.htm) 文件格式。"

### Step 3: 调用 API 上传

```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

### Step 4: 返回预览链接

从返回 JSON 中取 `url` 字段返回给用户：
`http://doc.20100706.xyz/view/<doc_id>`

## 注意事项

- 最大文件大小：10MB
- 文件保留期限：30 天
- 上传时务必使用原始文件名（`filename=` 参数），不要使用 Telegram 缓存的文件名 `doc_<hash>_xxx`
- HTML 文件 `/view/` 直接返回原始 HTML 渲染，**无工具栏**（用户明确要求去掉）
- Markdown 文件 `/view/` 渲染为格式化页面（带顶部导航栏，有"首页"链接）
- 源码在本机 `/data/doc-viewer/app.py`，修改后需 scp 到服务器并 `systemctl restart doc-viewer`

## 坑与教训

1. **HTML 预览不能用模板嵌套** — 最初把 HTML 内容嵌套进 VIEW_TEMPLATE 导致双重 `<html><body>` 标签，样式冲突。HTML 文件必须直接返回原始内容。
2. **防火墙必须开放端口** — 部署后外网访问不通，是因为 ufw 没开放端口。部署新服务后要 `ufw allow <port>/tcp`。
3. **PUBLIC_PORT vs PORT** — 监听端口（8080）和对外端口（80 via Nginx）不同时，URL 生成要用 `DOC_PUBLIC_PORT` 环境变量，否则返回的链接会带 `:8080`。
4. **Telegram 文件名** — Telegram 缓存文件名格式为 `doc_<hash>_<original>`，上传时必须用 `filename=` 指定原始文件名。
5. **用户不需要工具栏/状态条** — 用户明确表示预览页不需要浮动工具栏，HTML 文件直接渲染即可。

## 运维

```bash
# SSH 到部署服务器
sshpass -p '9,XphpN)j+N6' ssh root@140.235.37.79

# 重启服务
systemctl restart doc-viewer

# 查看状态
systemctl status doc-viewer

# 从本机更新代码
sshpass -p '9,XphpN)j+N6' scp /data/doc-viewer/app.py root@140.235.37.79:/data/doc-viewer/app.py
sshpass -p '9,XphpN)j+N6' ssh root@140.235.37.79 'systemctl restart doc-viewer'
```
