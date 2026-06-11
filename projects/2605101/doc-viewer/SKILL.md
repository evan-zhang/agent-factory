---
name: doc-viewer
description: "HTML 内容页面生成器 + 多目标上传预览。生成风格化 HTML 页面（支持 13 种风格），可上传到 DocViewer（30 天公网链接）/ 玄关知识库（5 年内部分享链接）/ 自定义端点。也支持直接上传现成 .md/.html 文件。触发词：上传文件、预览文件、生成链接、生成页面、HTML页面、宣传页、报告页面、知识库、存知识库"
version: "2.10.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
metadata: {"openclaw":{"requires":{"env":["DOCVIEWER_KB_APPKEY"]},"primaryEnv":"DOCVIEWER_KB_APPKEY"}}
---

# Doc Viewer — HTML 页面生成 + 多目标上传预览

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605101`
> 工厂主页：https://github.com/evan-zhang/agent-factory

核心架构：**Stage 1（生成 HTML）** + **Stage 2（上传到目标）**。两个阶段可独立调用，也可一气呵成。

## 阶段化架构（v2.10.0 重构）

| 阶段 | 输入 | 输出 | 副作用 |
|------|------|------|--------|
| **Stage 1：HTML 生成** | 内容 + 风格 + 配色 | 本地 HTML 文件 | **零**（不上传任何服务器） |
| **Stage 2：上传 + 返回链接** | 本地 HTML 文件 + target | 预览链接 | 上传到目标服务器 |

**Stage 2 支持的目标**：

| target | 用途 | 链接类型 | 有效期 | 配置 |
|--------|------|----------|--------|------|
| `docviewer` | DocViewer 服务（公网直链） | `raw_url` / `view` | 30 天 | 无需配置 |
| `kb` | 玄关知识库 | `previewUrl` | 5 年 | `DOCVIEWER_KB_APPKEY` |
| `custom` | 业务 skill 注入自己的端点 | 自定义 | 自定义 | 由调用方提供 endpoint 函数 |

**为什么拆分**：

- 业务 skill（如 bd-eval-cms）需要「生成 HTML 但不上传，自己拿到 HTML 后走业务专属知识库」
- 用户体验不变：默认一气呵成（Stage 1 → Stage 2）
- sub-agent 不会被「读完 SKILL.md 默认两步都跑」坑到（参见 issue #71）

---

## 触发判断

```
收到消息
 ├─ 用户说「生成 HTML 给我 / 我自己上传 / 不要上传 / 给我本地文件」
 │   → 只调 Stage 1
 │
 ├─ 用户描述需求 + 没指定目标
 │   → Stage 1 → Stage 2（默认 target=docviewer）
 │
 ├─ 用户说「存知识库 / 上传知识库 / KB / 知识库存储」
 │   → Stage 1 → Stage 2（target=kb）
 │
 ├─ 用户发送了 .md / .html / .htm 文件
 │   → 跳过 Stage 1 → 直接 Stage 2（target=docviewer）
 │
 └─ 其他 → 不触发
```

**目标选择规则**：

- 用户说「生成页面 / 做一个页面 / HTML 页面」→ 默认 `target=docviewer`
- 用户说「存知识库 / 5 年链接 / 内部链接」→ `target=kb`
- 用户说「我自己处理 / 我有别的上传方式」→ 只跑 Stage 1
- 调用方是其他 skill（sub-agent）→ 优先看调用方传入的 `target` 参数

**支持的文件类型（直接上传场景）**：

- `target=docviewer`：仅支持 `.md`、`.markdown`、`.html`、`.htm`
- `target=kb`：支持所有格式，推荐 `.md`、`.html`、`.pdf`
- `target=custom`：由调用方决定

---

## Stage 1：HTML 生成

**输入**：内容 + 风格 + 配色（可选默认值）
**输出**：本地 HTML 文件路径
**副作用**：零（不调用任何网络接口）

### Step 1.1：风格选择

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

### Step 1.2：素材收集

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

### Step 1.3：读取规范（必须按顺序）

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

### Step 1.4：生成 HTML

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

### Step 1.5：质量验证

```bash
TEMPLATE_COUNT=$(grep -c '{{' output.html 2>/dev/null || echo 0)
if [ "$TEMPLATE_COUNT" -gt 0 ]; then
  echo "❌ FAIL: 发现 $TEMPLATE_COUNT 个未替换的模板变量"
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

### Step 1.6：交付

将生成的 HTML 文件路径返回给调用方。**不要在 Stage 1 阶段执行任何上传**。

> ⚠️ **重要边界**：Stage 1 完成后，sub-agent 必须停下来等待调用方指令。如果调用方是普通用户，转 Stage 2 docviewer。如果调用方是其他 skill，等调用方决定下一步。

---

## Stage 2：上传 + 返回预览链接

**输入**：本地 HTML 文件 + target（必填）+ 可选参数
**输出**：预览链接

### Step 2.1：选择 target

| target | 何时选 | 配置要求 |
|--------|--------|----------|
| `docviewer` | 用户要公网 30 天链接 / 没特殊要求 | 无 |
| `kb` | 用户要 5 年内部链接 / 玄关知识库 | `DOCVIEWER_KB_APPKEY` |
| `custom` | 业务 skill 自己有上传端点 | 调用方注入 endpoint |

### Step 2.2：执行上传（按 target 分发）

#### target=docviewer（DocViewer 服务）

**接口**：`POST https://doc.20100706.xyz/upload`

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

**返回**：

```json
{
  "raw_url": "https://doc.20100706.xyz/raw/<doc_id>",
  "url": "https://doc.20100706.xyz/view/<doc_id>",
  ...
}
```

**链接选择**：

- **HTML 文件** → 取 `raw_url`，浏览器直接渲染 HTML
- **PDF 文件** → 取 `url`（view），浏览器内嵌 PDF 阅读器

```bash
URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['raw_url'])")
```

#### target=kb（玄关知识库）

**前置条件**：用户已配置 `DOCVIEWER_KB_APPKEY`。

**重要变更（v2.10.0）**：
- **支持外部 projectId**：调用方可直接传 `projectId` 参数（如 `2060176831872499713`），跳过个人知识库自动获取
- **支持外部 path**：调用方可传 `path` 参数覆盖默认 `DOCVIEWER_KB_PATH`
- 当 `projectId` 未传入时，自动走原路径 C 逻辑（getProjectId → 个人知识库）

##### 模式 A：调用方指定 projectId（业务 skill 推荐）

```bash
# 调用方直接传入 projectId 和 path（可与个人知识库无关）
PROJECT_ID="<调用方传入>"
KB_PATH="<调用方传入，默认 DocViewer>"
APPKEY="$DOCVIEWER_KB_APPKEY"

# Step 1：物理文件上传
RESOURCE_ID=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/uploadWholeFile" \
  -H "appKey: $APPKEY" \
  -F "file=@<文件路径>;filename=<原始文件名>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# Step 2：绑定到指定 KB 节点
FILE_ID=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveFileByPath" \
  -H "appKey: $APPKEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"projectId\": $PROJECT_ID,
    \"path\": \"$KB_PATH\",
    \"name\": \"<原始文件名>\",
    \"fileType\": \"file\",
    \"resourceId\": $RESOURCE_ID,
    \"suffix\": \"<后缀>\",
    \"size\": <文件大小>
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# Step 3：换取 access-token
ACCESS_TOKEN=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=$APPKEY" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['xgToken'])")

# Step 4：获取公网预览链接（5年）
PREVIEW_URL=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/doc-preview/api/preview/ticket" \
  -H "access-token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"bizType\": \"kb\",
    \"bizId\": \"$FILE_ID\",
    \"format\": \"<后缀>\",
    \"title\": \"<原始文件名>\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['previewUrl'])")

echo "✅ 已存储到指定知识库"
echo "📁 路径：知识库 / $KB_PATH / <原始文件名>"
echo "🔗 预览链接：$PREVIEW_URL（公网可访问，有效期 5 年）"
```

##### 模式 B：个人知识库（用户交互默认）

```bash
# Step 1：自动获取个人知识库 projectId
PROJECT_ID=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/personal/getProjectId" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# 后续 Step 2-4 同模式 A
```

**两种模式的区别**：
- 模式 A：调用方必须传 `projectId`；适用于业务 skill（bd-eval-cms 等）
- 模式 B：自动 getProjectId；适用于普通用户的「存知识库」意图

#### target=custom（业务自定义）

业务 skill 自行实现上传逻辑。doc-viewer 不内置实现。

**调用范式**：

```python
# 业务 skill 在调用 doc-viewer 时注入 endpoint
upload_endpoint = my_custom_upload  # 自定义上传函数
result = await doc_viewer.stage2_upload(
    html_path=output_path,
    target="custom",
    upload_fn=upload_endpoint  # 业务自己的上传函数
)
```

**未来路线**：当 `target=custom` 模式被多个业务 skill 共用时，将 Stage 2 拆分为独立 skill `html-uploader`。当前版本保留为 doc-viewer 内的扩展点。

### Step 2.3：返回链接

按 target 返回对应格式：

**docviewer**：
```
✅ 上传成功

🔗 预览链接：<raw_url>（公网直链，30 天有效）
```

**kb**：
```
✅ 已存储到知识库

📁 路径：知识库 / <kb.path> / <文件名>
🔗 预览链接：<previewUrl>（公网可访问，有效期 5 年）
```

**custom**：
```
✅ 上传成功（自定义目标）

🔗 预览链接：<调用方返回的链接>
```

---

## 阶段化调用范式

### 范式 1：一气呵成（普通用户）

```
用户：「帮我做一个 CMS 评估报告」
→ Stage 1（生成 HTML）
→ Stage 2（target=docviewer，默认）
→ 返回 30 天公网链接
```

### 范式 2：仅生成 HTML（业务 skill 标准用法）

```python
# 业务 skill 的伪代码
output_path = await doc_viewer.stage1_generate_html(
    content=evaluation_content,
    style="12",
    color_theme="mckinsey-navy"
)
# output_path 是本地 HTML 文件，业务 skill 自行后续处理
```

**典型场景**：bd-eval-cms 生成 CMS 投前评估报告 HTML → 自行上传到「产品引进知识库」。

### 范式 3：仅上传（已有 HTML 文件）

```python
preview_url = await doc_viewer.stage2_upload(
    html_path="/path/to/existing.html",
    target="kb",
    project_id="2060176831872499713",  # 业务知识库
    path="CMS评估/2026Q2"
)
```

### 范式 4：阶段化编排（业务 skill 完整流程）

```python
# Stage 1：用 doc-viewer 风格生成 HTML
html_path = await doc_viewer.stage1_generate_html(
    content=...,
    style="12",
    color_theme="mckinsey-navy"
)

# Stage 2：业务自己上传到专属知识库
preview_url = await doc_viewer.stage2_upload(
    html_path=html_path,
    target="kb",
    project_id="2060176831872499713",
    path="CMS评估"
)
```

**优势**：
- 业务 skill 明确控制每个阶段，sub-agent 不会跑飞
- HTML 质量由 doc-viewer 把关，上传路由由业务决定
- 复用 doc-viewer 的 13 种风格 + 4 套配色

---

## 更新已有文档

### target=docviewer

```bash
curl -X PUT https://doc.20100706.xyz/api/{doc_id} \
  -F "file=@新文件.html;filename=<标题>.html"
```

### target=kb

```bash
# Step 1：上传新版本物理文件
RESOURCE_ID=$(curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/uploadWholeFile" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  -F "file=@<新文件>;filename=<文件名>" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# Step 2：绑定到已有 KB 文件（更新版本）
curl -s -X POST "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/updateFileVersion" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": <已有文件的fileId>,
    "projectId": <projectId>,
    "resourceId": <新resourceId>,
    "versionStatus": 2
  }'

# Step 3：重新获取预览链接
ACCESS_TOKEN=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=$DOCVIEWER_KB_APPKEY" \
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
| Stage 1：模板变量未替换 | 验证脚本 `grep -c '{{'` 检测到非 0 时报错，禁止进入 Stage 2 |
| Stage 1：文件 > 1MB | 减小内容或图片 |
| Stage 2 docviewer：文件 > 10MB | 告知用户文件大小限制 |
| Stage 2 docviewer：非 md/html 文件 | 告知仅支持 Markdown 和 HTML |
| Stage 2 docviewer：生成失败 | 重试一次，仍失败则报告错误 |
| Stage 2 kb：未配置 appKey | 提示用户先配置，提供配置命令 |
| Stage 2 kb：appKey 无效 | 告知"appKey 无效，请检查" |
| Stage 2 kb：上传失败 | 重试一次，仍失败则报告错误 |
| Stage 2 kb：调用方传了 projectId 但没有该知识库权限 | 告知"无权限访问 projectId=<x>"，不 fallback 到个人知识库 |
| Stage 2 custom：endpoint 抛错 | 直接透传错误，由调用方处理 |
| Doc Viewer 服务不可用 | 告知用户服务暂时不可用 |

---

## API 参考

### DocViewer 服务（target=docviewer）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传文件 |
| `/view/{id}` | GET | 渲染预览（含导航栏壳） |
| `/raw/{id}` | GET | 原始文件 |
| `/api/{id}` | PUT | 更新已有文档 |
| `/api/{id}` | GET | 文档 JSON 元信息 |
| `/api/list` | GET | 所有文档列表 |
| `/api/{id}` | DELETE | 删除文档 |

### 知识库（target=kb）

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /document-database/project/personal/getProjectId` | 获取个人知识库 projectId |
| `POST /cwork-file/uploadWholeFile` | 物理文件上传，返回 resourceId |
| `POST /document-database/file/saveFileByPath` | 绑定到 KB 节点（支持任意 projectId + path） |
| `POST /document-database/file/updateFileVersion` | 更新 KB 文件版本 |
| `GET /user/login/appkey` | 用 appKey 换取 access-token（用于 doc-preview） |
| `POST /doc-preview/api/preview/ticket` | 生成公网预览链接（Header: access-token） |

> v2.10.0 变更：`saveFileByPath` 的 `projectId` 字段不再限定为个人知识库，调用方可传入任意有权限的 projectId。

---

## 注意事项

### 通用
- Stage 1 严格无网络副作用（除读取本地 token/skeleton 文件外）
- Stage 2 才会产生网络调用

### target=docviewer
- 最大文件 10MB，保留 30 天
- HTML 返回 raw 链接，PDF 返回 view 链接

### target=kb
- **公网预览链接**：通过 `doc-preview` 服务生成 `doc.aishuo.co` 链接，**公网可访问，有效期 5 年**
- **文件管理**：删除或移动文件请通过玄关知识库网页端操作
- **存储路径**：默认 `知识库 / DocViewer /`，可被 `path` 参数覆盖
- **支持格式**：推荐 md/html/pdf，任意格式均可上传
- **access-token 有效期**：由系统管理，调用时每次重新换取即可
- **权限要求**：调用方传入的 projectId 必须有 appKey 对应权限；权限不足会报错，不自动 fallback

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

### target=docviewer（无需配置）

服务地址已内置（`https://doc.20100706.xyz`），无权限控制。

### target=kb（需要配置）

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
| `DOCVIEWER_KB_PATH` | 否 | 默认存储目录，调用方可被 `path` 参数覆盖 |

**获取 appKey**：玄关开放平台 → 个人设置 → API 密钥

**说明**：
- 当调用方不传 `projectId` 时，文件将存储在用户自己的个人知识库中（`知识库 / <DOCVIEWER_KB_PATH> /`）
- 当调用方传入 `projectId` 时，文件存储到指定知识库（需 appKey 有对应权限）
- 5 年分享链接公网可访问，但 30 天后需玄关账号登录管理

### target=custom（无需配置）

由调用方注入 endpoint 函数，doc-viewer 不读取任何环境变量。

---

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`

---

## 版本历史

- **v2.10.0**（2026-06-12）：重构为 Stage 1/Stage 2 架构。新增 `target=kb` 模式 A（支持外部 projectId），新增 `target=custom` 模式。修复 issue #71。
- **v2.9.0**：路径 C 知识库存储
- **v2.8.0**：风格 08-13
- 早期版本：基础路径 A/B（DocViewer）
