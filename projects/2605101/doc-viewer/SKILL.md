---
name: doc-viewer
description: "上传 Markdown/HTML 文件到 Doc Viewer 服务，返回在线预览链接。触发词：上传文件、预览文件、文件链接、上传到网站、生成链接"
version: "1.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
---

# Doc Viewer — 文件上传与在线预览

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605101`
> 工厂主页：https://github.com/evan-zhang/agent-factory

将用户提供的 Markdown (.md) 或 HTML (.html/.htm) 文件上传到 Doc Viewer 服务，返回在线预览链接。

> 部署细节见 `references/deployment.md`，维护信息见 `references/maintenance.md`

## 支持的文件类型

仅支持：`.md`、`.markdown`、`.html`、`.htm`。其他类型明确告知用户不支持。

## 触发判断

```
收到消息
 ├─ "上传文件" / "预览文件" / "生成链接" / "上传到网站"
 │   └─ 检查文件类型
 │       ├─ .md / .html → 执行上传
 │       └─ 其他 → 告知不支持
 └─ 非上传意图 → 不触发
```

## 操作步骤

### Step 1: 获取文件

来源：Telegram 附件、本地路径、用户粘贴文本。

### Step 2: 验证文件类型

扩展名必须是 `.md`、`.markdown`、`.html`、`.htm`。

### Step 3: 调用 API 上传

```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

或上传文本内容：
```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "content=<文本内容>" -F "format=markdown"
```

### Step 4: 返回预览链接

返回 JSON 中的 `url` 字段：`http://doc.20100706.xyz/view/<doc_id>`

## 失败处理

| 场景 | 处理 |
|------|------|
| 文件 > 10MB | 告知用户文件大小限制 |
| 非 md/html 文件 | 告知仅支持 Markdown 和 HTML |
| 上传超时 | 重试一次，仍失败则报告错误 |
| 服务不可用 | 告知用户 Doc Viewer 服务暂时不可用 |

## 示例

```
用户：帮我把这个文件上传到网站
Agent：curl -s -X POST http://doc.20100706.xyz/upload -F "file=@report.html;filename=report.html"
Agent：✅ 预览链接：http://doc.20100706.xyz/view/897e2d322c8f
```

## 注意事项

- 最大文件 10MB，保留 30 天
- 上传时必须用原始文件名（`filename=` 参数）
- HTML 直接渲染，无工具栏；Markdown 转换后渲染（带导航栏）

## API 参考

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传文件（multipart）或文本内容 |
| `/view/{id}` | GET | 渲染预览 |
| `/raw/{id}` | GET | 原始文件内容 |
| `/api/{id}` | GET | 文档 JSON 元信息 |
| `/api/list` | GET | 所有文档列表（按时间倒序） |
| `/api/{id}` | DELETE | 删除文档 |

## 配置与授权

安装后无需额外配置即可使用。

| 配置项 | 必填 | 说明 | 获取方式 |
|--------|------|------|----------|
| 无 | — | 服务地址已内置（`http://doc.20100706.xyz`） | — |

服务运维需 SSH 到部署服务器（`140.235.37.79`），详见 `references/deployment.md`。

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`

**建议包含**：
1. 重现步骤
2. 预期行为 vs 实际行为
3. 环境信息（OpenClaw 版本、操作系统）
4. 相关日志或错误信息
