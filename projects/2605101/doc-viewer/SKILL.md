---
name: doc-viewer
description: "文件上传预览 + HTML 内容页面生成器 + 知识库存储。提供现成文件可直接上传预览；描述内容需求可自动生成风格化 HTML 页面并上传；用户配置知识库 appKey 后可选择将文件存储到个人知识库。触发词：上传文件、预览文件、生成链接、生成页面、HTML页面、宣传页、报告页面、知识库、存知识库"
version: "2.9.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
metadata: {"openclaw":{"requires":{"env":["DOCVIEWER_KB_APPKEY"]},"primaryEnv":"DOCVIEWER_KB_APPKEY"}}
---

# Doc Viewer — 文件上传预览 + HTML 页面生成器 + 知识库存储

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605101`
> 工厂主页：https://github.com/evan-zhang/agent-factory

提供三条路径，自动分流：

- **路径 A（快速上传）**：用户提供现成文件，上传到 DocViewer 服务，返回公网预览链接
- **路径 B（内容创作）**：用户描述需求，生成风格化 HTML 页面后上传
- **路径 C（知识库存储）**：用户配置知识库 appKey 后，可选择将文件存储到个人知识库，返回内部分享链接

## 触发判断

```
收到消息
 ├─ 用户意图包含：生成页面 / 做一个页面 / HTML页面 / 宣传页 / 展示页 / 报告页面
 │   → 路径 B（内容创作）
 │
 ├─ 用户意图包含：存知识库 / 上传知识库 / KB / 知识库存储
 │   → 路径 C（知识库存储）
 │
 ├─ 用户发送了 .md / .html / .htm 文件
 │   → 路径 A（快速上传）
 │
 └─ 其他 → 不触发
```

**路径 A 和路径 C 的选择规则**：

当用户说「上传文件 / 预览文件 / 生成链接 / 上传到网站」且附带了文件时：
- **已配置 kb.appKey** → 主动询问用户：「存 DocViewer（公网链接）还是知识库（内部链接）？」
- **未配置 kb.appKey** → 直接走路径 A（DocViewer）

## 支持的文件类型（路径 A / 路径 C）

路径 A：仅支持 `.md`、`.markdown`、`.html`、`.htm`
路径 C：支持所有格式，推荐 `.md`、`.html`、`.pdf`

其他类型明确告知不支持。

---

## 路径 A：快速上传

### Step 1: 获取文件

来源：附件、本地路径、用户粘贴文本。

### Step 2: 验证文件类型

扩展名必须是 `.md`、`.markdown`、`.html`、`.htm`。

### Step 3: 确认存储方式

用户已配置 kb.appKey 时，上传前主动询问：

> 「检测到您已配置知识库。文件存哪里？」
> - A：DocViewer（公网链接，无需登录）
> - B：知识库（内部链接，需要玄关账号）

用户选择后执行对应上传流程。选择 B 则进入路径 C。

### Step 4: 调用 API 上传

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

### Step 5: 返回链接

上传成功后，根据文件类型返回对应链接：

- **HTML 文件** → 取 `raw_url`，浏览器直接渲染 HTML 内容
- **PDF 文件** → 取 `url`（view），浏览器内嵌 PDF 阅读器在线查看

```bash
# HTML → raw URL
URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['raw_url'])")

# PDF → view URL
URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
```

**常见错误**：给 PDF 也返回 raw 链接，这样浏览器会下载而不是在线查看。

---

## 路径 B：内容创作

### Step 1：风格选择

根据用户意图推荐风格：

#### 风格分类体系

**程序化型（Programmatic）**：风格 13
- 特点：Python 脚本直接将 Markdown 转为 HTML，不需要 AI 手写
- 目录导航：自动从 ## 标题生成
- 适用：任意结构的 Markdown 长文档，保留原章节，只做视觉渲染

**专用型（Domain-Specific）**：风格 03、11、12
- 特点：有 color-themes、专用组件、不能随便填其他内容
- 目录导航：按需开启（长文档推荐）
- 适用：特定领域的专业文档（BD 报告、技术海报、投前评估）

**系列型（Family）**：风格 02
- 特点：6 套变体（02-A~F）共享 base，覆盖不同场景
- 目录导航：按变体决定（封面不开启，内容页开启）
- 适用：企业报告系统，多变体协同

**通用型（General）**：风格 01、04、05、06、07、08、09、10
- 特点：单一骨架，适配多种内容
- 目录导航：✅ 默认开启（除超短内容）
- 适用：通用内容页，灵活性高

#### 推荐规则
- 用户说「麦肯锡风格」「深蓝咨询」「Markdown转HTML报告」「咨询风格」→ 推荐 **风格 13**（程序化渲染，保留原结构）
- 用户说「报告」「BD」「评估」「尽调」「投前」「文档」「分析」→ 推荐 **风格 03**
  - 进一步判断配色：「琥珀金」「金色」→ amber（默认）；「阳光黄」「黄色」→ yellow；「投资蓝」「蓝色」「金融报告」→ investment-blue
- 用户说「情报」「日报」「动态」「资讯」「新闻」→ 推荐 **风格 04**
- 用户说「指标」「KPI」「数据」「数字」「看板」→ 推荐 **风格 05**
- 用户说「产品介绍」「产品页」「服务页」→ 推荐 **风格 06**
- 用户说「日系」「暖色」「极简」「Claude」「Arc」「Notion」「创作」「AI 产品页」→ 推荐 **风格 07**
- 用户说「苹果」「Apple」「极简」「电影感」「keynote」→ 推荐 **风格 08**
- 用户说「文档」「编辑器」「Notion」「笔记」「知识库」→ 推荐 **风格 09**
- 用户说「开发者」「Stripe」「API」「代码」「开发者平台」→ 推荐 **风格 10**
- 用户说「暗色」「Linear」「暗色主题」「高级感」「极客」「技术海报」「AI 教程」→ 推荐 **风格 11 + dark-technical**
- 用户说「CMS评估」「投前评估」「康哲评估」「CMS报告」→ 推荐 **风格 12**
  - 进一步判断配色：「麦肯锡」「深蓝」「咨询」→ mckinsey-navy（默认）；「投资蓝」「蓝色」「金融」→ investment-blue；「酒红」「勃艮第」→ burgundy-wine；「青绿」「森林」「ESG」→ forest-teal；未指定 → mckinsey-navy
- 用户说「封面」「首页」→ 推荐 **风格 02-A** 或 **02-B**
- 用户说「案例」「客户案例」→ 推荐 **风格 02-F**
- 用户没明确偏好 → 推荐 **风格 01**

### Step 2：素材收集

通过对话逐项收集：

**必填项**：
- 页面标题（主标题）
- 页面内容（正文/观点/数据，用户口述即可，Agent 负责结构化）

**可选项**（用户不提供则用模板默认值）：
- 副标题
- 数据点
- 图片（用户发送附件，或使用占位图）
- 作者/来源信息
- 页脚信息

### Step 3：读取规范（必须按顺序）

Agent 生成 HTML 前必须读取以下文件：

**第一步 — 读取通用设计规范（所有模板共享）**：

| 文件 | 说明 |
|------|------|
| `design-standards/base-html-rules.md` | HTML/CSS 基础规则，必须读 |
| `design-standards/table-spec.md` | 表格规范，必须读 |
| `design-standards/responsive-spec.md` | 多端适配规范，必须读 |
| `design-standards/print-spec.md` | 打印优化规范（报告类必须读） |

**第二步 — 读取所选风格的 Token 和骨架**：

| 风格 | Token 文件 | 骨架文件 | 配色方案 |
|------|-----------|---------|---------|
| 风格 01 | `templates/style-01/design-token.md` | `templates/style-01/skeleton.html` | — |
| 风格 02 | `templates/style-02/design-token.md` | `templates/style-02/skeleton.html` | — |
| 风格 03 | `templates/style-03/design-token.md` | `templates/style-03/skeleton.html` | `color-themes/amber.yml`（默认）/ `yellow.yml` / `investment-blue.yml` |
| 风格 04 | `templates/style-04/design-token.md` | `templates/style-04/skeleton.html` | — |
| 风格 05 | `templates/style-05/design-token.md` | `templates/style-05/skeleton.html` | — |
| 风格 06 | `templates/style-06/design-token.md` | `templates/style-06/skeleton.html` | — |
| 风格 07 | `templates/style-07/design-token.md` | `templates/style-07/skeleton.html` | — |
| 风格 08 | `templates/style-08/design-token.md` | `templates/style-08/skeleton.html` | — |
| 风格 09 | `templates/style-09/design-token.md` | `templates/style-09/skeleton.html` | — |
| 风格 10 | `templates/style-10/design-token.md` | `templates/style-10/skeleton.html` | — |
| 风格 11 | `templates/style-11/design-token.md` | `templates/style-11/skeleton.html` | `color-themes/dark-technical.yml` |
| 风格 12 | `templates/style-12/design-token.md` | `templates/style-12/skeleton.html` | `color-themes/mckinsey-navy.yml`（默认）/ `investment-blue.yml` / `burgundy-wine.yml` / `forest-teal.yml` |

### Step 4：生成 HTML

**核心原则：**
- 风格 Token 的颜色/字号 → 直接使用，不自行调整
- 通用规范的表格/响应式/打印要求 → 必须遵守

**HTML 规范**：
- 单文件，内联 CSS
- 字体：PingFang SC / Microsoft YaHei / Noto Sans CJK SC（中文友好，**禁止 Inter/Roboto**）
- 表格：PC 端 `width:100%`，外层包裹 `.table-wrap{overflow-x:auto}`
- 响应式：至少覆盖 480px / 768px 断点
- 打印报告类：正文字号用 `pt` 单位，`@page` 边距固定
- 图片：外链 URL 或占位图，禁止 base64
- 不使用 JS 框架，纯 HTML + CSS
- 文件大小 < 1MB

### Step 5：质量验证（上传前必须执行）

```bash
TEMPLATE_COUNT=$(grep -c '{{' output.html 2>/dev/null || echo 0)
if [ "$TEMPLATE_COUNT" -gt 0 ]; then
  echo "❌ FAIL: 发现 $TEMPLATE_COUNT 个未替换的模板变量，禁止上传"
  grep -n '{{' output.html | head -10
  exit 1
fi
echo "✅ PASS: 无未替换变量"
```

**验证清单**：
- [ ] `grep -c '{{'` 结果为 0
- [ ] 封面页包含实际内容（非占位符）
- [ ] CSS 颜色为具体值，非 `{{变量}}`
- [ ] 表格表头有背景色
- [ ] 文件大小 > 10KB

### Step 6：上传与交付

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@output.html;filename=<标题>.html"
```

返回后：HTML → `raw_url`；PDF → `url`（view）。

---

## 路径 C：知识库存储

将文件上传到用户的个人知识库（需提前配置 appKey）。

### 前置条件

用户必须已配置知识库 appKey（通过 `skills.entries.doc-viewer.env` 注入）。未配置时，提示用户执行：

```
请先配置知识库 appKey：
在 openclaw.json 的 skills.entries.doc-viewer.env 中添加：
{
  "DOCVIEWER_KB_APPKEY": "你的appKey",
  "DOCVIEWER_KB_PATH": "DocViewer"
}

或联系系统管理员协助配置。
```

配置说明详见「配置与授权」节。

### Step 1：获取用户 projectId

```bash
# 自动获取当前 appKey 对应的个人知识库 projectId
curl -s "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/personal/getProjectId" \
  -H "appKey: <kb.appKey>"
```

### Step 2：物理文件上传

```bash
# 将文件作为物理资源上传到知识库存储层
# 返回 resourceId（用于后续绑定 KB 节点）
curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/uploadWholeFile" \
  -H "appKey: <kb.appKey>" \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

响应：`{"resultCode":1,"data":<resourceId>}`

### Step 3：绑定 KB 节点

```bash
# 将物理资源绑定到知识库的 DocViewer 目录下
# path 默认值为 "DocViewer"，来自 process.env.DOCVIEWER_KB_PATH
curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveFileByPath" \
  -H "appKey: <kb.appKey>" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": <projectId>,
    "path": "<kb.path>",
    "name": "<原始文件名>",
    "fileType": "file",
    "resourceId": <resourceId>,
    "suffix": "<后缀>",
    "size": <文件大小>
  }'
```

响应：`{"resultCode":1,"data":<fileId>}`

> `saveFileByPath` 接口会自动创建不存在的中间目录（包括 path 指定的文件夹）。

### Step 4：换取 access-token

```bash
# 用 appKey 换取 access-token（doc-preview 接口需要）
ACCESS_TOKEN=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=<kb.appKey>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['xgToken'])")
```

### Step 5：获取公网预览链接

```bash
# 调用文档预览服务，生成公网可访问的预览链接（5年有效期）
PREVIEW_RESP=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/doc-preview/api/preview/ticket" \
  -H "access-token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"bizType\": \"kb\",
    \"bizId\": \"<fileId>\",
    \"format\": \"<后缀>\",
    \"title\": \"<原始文件名>\"
  }")
PREVIEW_URL=$(echo "$PREVIEW_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['previewUrl'])")
```

### Step 6：返回结果

```
✅ 已存储到知识库

📁 路径：知识库 / <kb.path> / <文件名>
🔗 预览链接：<previewUrl>（公网可访问，有效期 5 年）

💡 提示：知识库中的文件通过玄关知识库网页端管理。
```

---

## 更新已有文档（路径 A/B/C 通用）

### 路径 A/B（DocViewer 服务）

```bash
curl -X PUT https://doc.20100706.xyz/api/{doc_id} \
  -F "file=@新文件.html;filename=<标题>.html"
```

### 路径 C（知识库）

```bash
# Step 1：上传新版本物理文件
RESOURCE_ID=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/uploadWholeFile" \
  -H "appKey: <kb.appKey>" \
  -F "file=@<新文件>;filename=<文件名>" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# Step 2：绑定到已有 KB 文件（更新版本）
curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/updateFileVersion" \
  -H "appKey: <kb.appKey>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": <已有文件的fileId>,
    "projectId": <projectId>,
    "resourceId": <新resourceId>,
    "versionStatus": 2
  }'

# Step 3：重新获取预览链接
ACCESS_TOKEN=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=<kb.appKey>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['xgToken'])")
PREVIEW_URL=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/doc-preview/api/preview/ticket" \
  -H "access-token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"bizType\":\"kb\",\"bizId\":\"<已有文件的fileId>\",\"format\":\"<后缀>\",\"title\":\"<文件名>\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['previewUrl'])")
```

更新后：fileId 不变，知识库中生成新版本，预览链接需重新获取。

---

## 失败处理

| 场景 | 处理 |
|------|------|
| 路径 A：文件 > 10MB | 告知用户文件大小限制 |
| 路径 A：非 md/html 文件 | 告知仅支持 Markdown 和 HTML |
| 路径 B：用户素材不足 | 提示缺少哪些必填项，不强行生成 |
| 路径 B：生成失败 | 重试一次，仍失败则报告错误 |
| 路径 B：生成文件超过 10MB | 将 HTML 文件直接发送给用户作为附件 |
| 路径 C：未配置 kb.appKey | 提示用户先配置，提供配置命令 |
| 路径 C：appKey 无效 | 告知"appKey 无效，请检查" |
| 路径 C：上传失败 | 重试一次，仍失败则报告错误 |
| Doc Viewer 服务不可用 | 告知用户服务暂时不可用 |

---

## API 参考

### DocViewer 服务（路径 A/B）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传文件 |
| `/view/{id}` | GET | 渲染预览（含导航栏壳） |
| `/raw/{id}` | GET | 原始文件 |
| `/api/{id}` | PUT | 更新已有文档 |
| `/api/{id}` | GET | 文档 JSON 元信息 |
| `/api/list` | GET | 所有文档列表 |
| `/api/{id}` | DELETE | 删除文档 |

### 知识库（路径 C）

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /document-database/project/personal/getProjectId` | 获取个人知识库 projectId |
| `POST /cwork-file/uploadWholeFile` | 物理文件上传，返回 resourceId |
| `POST /document-database/file/saveFileByPath` | 绑定到 KB 节点，自动创建目录 |
| `POST /document-database/file/updateFileVersion` | 更新 KB 文件版本 |
| `GET /user/login/appkey` | 用 appKey 换取 access-token（用于 doc-preview） |
| `POST /doc-preview/api/preview/ticket` | 生成公网预览链接（Header: access-token） |

---

## 注意事项

### 路径 A/B（DocViewer）
- 最大文件 10MB，保留 30 天
- HTML 返回 raw 链接，PDF 返回 view 链接

### 路径 C（知识库）
- **公网预览链接**：通过 `doc-preview` 服务生成 `doc.aishuo.co` 链接，**公网可访问，有效期 5 年**
- **文件管理**：删除或移动文件请通过玄关知识库网页端操作
- **存储路径**：默认存储在 `知识库 / <kb.path> /` 下，可通过 `DOCVIEWER_KB_PATH` 配置覆盖
- **支持格式**：推荐 md/html/pdf，任意格式均可上传
- **access-token 有效期**：由系统管理，调用时每次重新换取即可

---

## 可用风格一览

### 风格 01 — Data & AI Report
**分类**：通用型 | **目录导航**：✅ 默认开启

蓝紫渐变主调，数据密集型报告页面。

### 风格 02 — Google Cloud / IDC 企业报告（6 套变体）
**分类**：系列型

以 Google Yellow 为核心色，6 种变体覆盖不同场景。

| 编号 | 名称 | 适用场景 |
|------|------|----------|
| 02-A | 四色拼贴封面风 | 报告首页/入口页 |
| 02-B | 大图 Hero 章节封面风 | 章节页/观点页 |
| 02-C | 白底咨询报告内容风 | 正文页/分析页 |
| 02-D | 彩色模块矩阵风 | 方法论/模块清单 |
| 02-E | 数据洞察大数字风 | 指标页/数据页 |
| 02-F | 案例/行业卡片风 | 场景页/案例页 |

### 风格 03 — BD 投前评估报告
**分类**：专用型 | **目录导航**：按需开启

A4 纵向，章节密集，表格整齐，专用配色体系。

**配色**：amber（琥珀金，默认）/ yellow（阳光黄）/ investment-blue（投资蓝）/ dark-technical（暗色技术风）

### 风格 04 — 情报日报风
**分类**：通用型 | **目录导航**：✅ 默认开启

大日期 + 小标题，适合每日情报汇总。

### 风格 05 — 数据看板/指标卡风格
**分类**：通用型 | **目录导航**：✅ 默认开启

大数字 + 图表，适合 KPI 展示。

### 风格 06 — 产品介绍页
**分类**：通用型 | **目录导航**：✅ 默认开启

多 section + Hero，适合产品/服务介绍。

### 风格 07 — 日系/Notion 风格
**分类**：通用型 | **目录导航**：✅ 默认开启

极简暖色，适合 AI 产品页、内容创作。

### 风格 08 — Apple 极简风格
**分类**：通用型 | **目录导航**：✅ 默认开启

电影感强，适合高端展示。

### 风格 09 — 文档/编辑器风格
**分类**：通用型 | **目录导航**：✅ 默认开启

Notion 风格，适合知识库文档。

### 风格 10 — Stripe/开发者平台风格
**分类**：通用型 | **目录导航**：✅ 默认开启

适合 API 文档、开发者文档。

### 风格 11 — Linear 暗色技术风
**分类**：专用型 | **目录导航**：按需开启

暗黑 + 橙红，适合技术海报/AI 教程。

### 风格 12 — CMS 康哲药业投前评估报告
**分类**：专用型 | **目录导航**：按需开启

Gate 门控型，CMS 评估体系专用。

**配色**：mckinsey-navy（麦肯锡深蓝，默认）/ investment-blue / burgundy-wine / forest-teal

### 风格 13 — 程序化 Markdown 渲染
**分类**：程序化型 | **目录导航**：✅ 自动生成

Python 脚本直接渲染 Markdown，不改结构，适合长文档。

---

## 通用设计规范（design-standards/）

| 文件 | 职责 |
|------|------|
| `base-html-rules.md` | HTML/CSS 基础规则 |
| `table-spec.md` | 表格规范 |
| `responsive-spec.md` | 多端适配 |
| `print-spec.md` | 打印/PDF 规范 |

---

## 配置与授权

### 路径 A/B（无需配置）

服务地址已内置（`https://doc.20100706.xyz`），无权限控制。

### 路径 C（知识库）

用户需在 `openclaw.json` 中配置自己的玄关开放平台 appKey：

```json
{
  "skills": {
    "entries": {
      "doc-viewer": {
        "env": {
          "DOCVIEWER_KB_APPKEY": "你的appKey",
          "DOCVIEWER_KB_PATH": "DocViewer"
        }
      }
    }
  }
}
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `DOCVIEWER_KB_APPKEY` | 是 | 玄关开放平台 API 密钥 |
| `DOCVIEWER_KB_PATH` | 否 | 存储目录，默认 `DocViewer` |

**获取 appKey**：玄关开放平台 → 个人设置 → API 密钥

**说明**：
- 文件将存储在用户自己的个人知识库中（`知识库 / <DOCVIEWER_KB_PATH> /`）
- 分享链接需要玄关内部账号登录
- 如需修改存储目录，设置 `DOCVIEWER_KB_PATH`（如 `项目A/汇报`）

---

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`
