---
name: doc-viewer
description: "文件上传预览 + HTML 内容页面生成器。提供现成文件可直接上传预览；描述内容需求可自动生成风格化 HTML 页面并上传。触发词：上传文件、预览文件、生成链接、生成页面、HTML页面、宣传页、报告页面"
version: "2.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
---

# Doc Viewer — 文件上传预览 + HTML 页面生成器

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605101`
> 工厂主页：https://github.com/evan-zhang/agent-factory

提供两条路径，自动分流：

- **路径 A（快速上传）**：用户提供现成文件，直接上传返回预览链接
- **路径 B（内容创作）**：用户描述需求，生成风格化 HTML 页面后上传

## 触发判断

```
收到消息
 ├─ 用户发送了 .md / .html / .htm 文件
 │   → 路径 A（快速上传）
 │
 ├─ 用户意图包含：生成页面 / 做一个页面 / HTML页面 / 宣传页 / 展示页 / 报告页面
 │   → 路径 B（内容创作）
 │
 ├─ 用户说：上传文件 / 预览文件 / 生成链接 / 上传到网站
 │   → 检查是否附带文件
 │     ├─ 有文件 → 路径 A
 │     └─ 无文件 → 路径 B（将用户内容生成为页面）
 │
 └─ 其他 → 不触发
```

## 支持的文件类型（路径 A）

仅支持：`.md`、`.markdown`、`.html`、`.htm`。其他类型明确告知不支持。

---

## 路径 A：快速上传

### Step 1: 获取文件

来源：附件、本地路径、用户粘贴文本。

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

---

## 路径 B：内容创作

### Step 1：风格选择

根据用户意图推荐风格（不罗列所有选项，只推荐最匹配的）：

**推荐规则**：
- 用户说「封面」「首页」→ 推荐 02-A 或 02-B
- 用户说「报告正文」「分析」→ 推荐 02-C
- 用户说「数据」「指标」→ 推荐 02-E
- 用户说「案例」「行业」→ 推荐 02-F
- 用户说「模块」「方法论」→ 推荐 02-D
- 用户没明确偏好 → 推荐 01（综合风格）

**可用风格**：

**风格 01 — Data & AI Report（企业数据智能白皮书）**
- 综合风格，适合完整报告页面
- 定义：`templates/style-01-data-ai-report.md`
- HTML 骨架：`templates/style-01-base.html`

**风格 02 — Google Cloud / IDC 企业报告视觉系统（6 套变体）**
- 定义：`templates/style-02-google-cloud-idc.md`
- 变体：

| 编号 | 名称 | 适用场景 |
|------|------|----------|
| 02-A | 四色拼贴封面风 | 报告首页/入口页 |
| 02-B | 大图 Hero 章节封面风 | 章节页/观点页 |
| 02-C | 白底咨询报告内容页 | 正文页/分析页 |
| 02-D | 彩色模块矩阵风 | 方法论/模块清单 |
| 02-E | 数据洞察大数字风 | 指标页/数据页 |
| 02-F | 案例/行业卡片风 | 场景页/案例页 |

### Step 2：素材收集

通过对话逐项收集：

**必填项**：
- 页面标题（主标题）
- 页面内容（正文/观点/数据，用户口述即可，Agent 负责结构化）

**可选项**（用户不提供则用模板默认值）：
- 副标题
- 数据点（如 "73% 的企业已采用 AI"）
- 图片（用户发送附件，或使用占位图）
- 作者/来源信息
- 页脚信息

### Step 3：生成 HTML

1. 读取所选风格模板规范（`templates/style-XX.md`）
2. 参考 HTML 骨架（`templates/style-01-base.html`）
3. 根据内容结构和模板规范生成完整 HTML

**HTML 规范**：
- 单文件，内联 CSS
- 使用 TailwindCSS CDN：`<script src="https://cdn.tailwindcss.com">`
- 轻量动效：fade-in、slide-up、counter（数字跳动）
- 响应式设计（移动端适配）
- 图片使用用户提供的 URL 或占位图
- 不使用 JavaScript 框架，纯 HTML + CSS + 原生 JS
- 文件大小 < 1MB（不含图片，图片使用外链）

### Step 4：上传与交付

```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@output.html;filename=<标题>.html"
```

返回预览链接：`http://doc.20100706.xyz/view/<doc_id>`

### Step 5：迭代修改（可选）

用户查看后可要求修改，使用更新接口（链接不变）：

```bash
curl -X PUT http://doc.20100706.xyz/api/{doc_id} \
  -F "file=@updated.html;filename=<标题>.html"
```

---

## 更新已有文档（路径 A/B 通用）

对已上传的文档进行内容更新，链接保持不变：

```bash
# 用新文件更新
curl -X PUT http://doc.20100706.xyz/api/{doc_id} \
  -F "file=@新文件.md;filename=新文件.md"

# 用文本内容更新
curl -X PUT http://doc.20100706.xyz/api/{doc_id} \
  -F "content=新内容" -F "format=markdown"
```

更新后：doc_id 不变、预览链接不变，元信息中会增加 `updated_at` 字段。

---

## 失败处理

| 场景 | 处理 |
|------|------|
| 路径 A：文件 > 10MB | 告知用户文件大小限制 |
| 路径 A：非 md/html 文件 | 告知仅支持 Markdown 和 HTML |
| 路径 B：用户素材不足 | 提示缺少哪些必填项，不强行生成 |
| 路径 B：生成失败 | 重试一次，仍失败则报告错误 |
| 路径 B：生成文件超过 10MB | 将 HTML 文件直接发送给用户作为附件 |
| 上传失败（两条路径共用） | 重试一次，仍失败则报告错误 |
| Doc Viewer 服务不可用 | 告知用户服务暂时不可用 |

---

## API 参考

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传文件（multipart）或文本内容 |
| `/view/{id}` | GET | 渲染预览 |
| `/raw/{id}` | GET | 原始文件内容 |
| `/api/{id}` | PUT | 更新已有文档（文件或文本），保留 doc_id 和链接不变 |
| `/api/{id}` | GET | 文档 JSON 元信息 |
| `/api/list` | GET | 所有文档列表（按时间倒序） |
| `/api/{id}` | DELETE | 删除文档 |

## 注意事项

- 最大文件 10MB，保留 30 天
- 上传时必须用原始文件名（`filename=` 参数）
- HTML 直接渲染，无工具栏；Markdown 转换后渲染（带导航栏）

## 配置与授权

无需配置即可使用。服务地址已内置（`http://doc.20100706.xyz`），无权限控制。

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`

**建议包含**：
1. 重现步骤
2. 预期行为 vs 实际行为
3. 环境信息（OpenClaw 版本、操作系统）
4. 相关日志或错误信息
