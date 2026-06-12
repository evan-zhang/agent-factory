---
name: doc-viewer
description: "Markdown → HTML 转换 + 多目标上传预览。输入 .md 或 .html 文件，输出风格化 HTML（忠实/加工两种模式），可上传到 DocViewer（30 天公网链接）/ 玄关知识库（5 年内部分享链接）/ 自定义端点。触发词：上传文件、预览文件、生成链接、转 HTML、Markdown 转 HTML、HTML 存知识库、HTML 上传、HTML 预览、报告页面、知识库、存知识库"
version: "3.0.2"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
metadata: {"openclaw":{"requires":{"env":["DOCVIEWER_KB_APPKEY"]},"primaryEnv":"DOCVIEWER_KB_APPKEY"}}
---

# Doc Viewer — Markdown → HTML + 上传预览

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605101`
> 工厂主页：https://github.com/evan-zhang/agent-factory

**核心职责**：把一个 Markdown 文件变成一个可以预览/分享的 HTML 页面。

**两段式架构**：

| 阶段 | 输入 | 输出 | 副作用 |
|------|------|------|--------|
| **Stage 1：Markdown → HTML** | .md 文件 + 模式选择 | 本地 HTML 文件 | **零**（不上传） |
| **Stage 2：上传 + 返回链接** | HTML 文件 + target | 预览链接 | 上传到目标服务器 |

**Stage 2 支持的目标**：

| target | 用途 | 链接类型 | 有效期 | 配置 |
|--------|------|----------|--------|------|
| `docviewer` | DocViewer 服务（公网直链） | `raw_url` / `view` | 30 天 | 无需配置 |
| `kb` | 玄关知识库 | `previewUrl` | 5 年 | `DOCVIEWER_KB_APPKEY` |
| `custom` | 业务 skill 注入自己的端点 | 自定义 | 自定义 | 调用方注入 |

**为什么这样设计**：

- doc-viewer 只做格式转换 + 上传，**不解决内容创作**（素材由上游 skill 准备）
- 业务 skill（如 bd-eval-cms）可以：调 Stage 1 拿 HTML → 自己决定上传到哪
- 普通用户体验不变：给 md → 拿到预览链接

---

## 触发判断

```
收到消息 + 一个文件
 ├─ 文件是 .html / .htm
 │   → 跳过 Stage 1，直接走 Stage 2（见下方"HTML 直传模式"）
 │     ├─ 用户说"原样 / 不改" → 原样上传
 │     ├─ 用户说"存知识库 / 5 年" → Stage 2 (kb)
 │     └─ 没说 → Stage 2 (docviewer) 默认
 │
 ├─ 文件是 .md / .markdown
 │   ├─ 用户明确说"原样 / 忠实 / 不改 / 直接转"
 │   │   → Stage 1 忠实模式（风格 13）
 │   │
 │   └─ 其他情况（默认）
 │       → Stage 1 加工模式
 │         ├─ 没说偏好 → 风格 01
 │         ├─ "报告 / BD / 评估" → 风格 03
 │         ├─ "麦肯锡 / 深蓝 / CMS" → 风格 12
 │         ├─ "情报 / 日报" → 风格 04
 │         └─ "好看 / 专业" → 风格 01
 │
 └─ 其他文件格式
     → 不触发，请先转换为 md 或 html
```

**支持的文件类型**：
- `.md` / `.markdown` → Stage 1 处理（md → HTML）
- `.html` / `.htm` → 跳过 Stage 1，直接 Stage 2（已经是 HTML，原样上传）
- 其他格式 → 不触发，请先转换为 md

**注意**：doc-viewer **不做素材收集**。如果用户口述需求（没有 md 文件），请上游 skill 或通用助手先组织成 md 文件，再调 doc-viewer。

---

## 模式对比（先看这个再选）

| 维度 | 忠实模式 | 加工模式 |
|------|----------|----------|
| 语义 | md 原样渲染，给内容穿一件衣服 | sub-agent 读 md → 理解结构 → 重构后套模板 |
| 风格 | 13（程序化渲染） | 01-12（sub-agent 拼装） |
| 内容 | **完全保留**，不增不减 | 内容来自 md，但**结构可能调整** |
| 速度 | 5-10 秒（Python 脚本） | 30-60 秒（sub-agent） |
| 确定性 | 100% 可复现 | 概率性，每次略不同 |
| 适合 | 已有完善结构的 md，不想被改 | md 内容好但缺专业排版 |

**默认走加工模式**（风格 01）。理由：用户找 doc-viewer 通常是为了"专业排版"，不是"原样转"；原样转用 pandoc 即可。

---

## HTML 直传模式（跳过 Stage 1）

**适用场景**：用户已经有 HTML 文件，只需要上传预览 / 存知识库 / 拿分享链接。

**触发词**：
- "上传这个 HTML"
- "HTML 存知识库"
- "HTML 预览 / 拿链接"
- "这个页面帮我存起来"
- 直接发一个 .html/.htm 文件

**跳过 Stage 1**——不接受加工，原样走 Stage 2。

**用户说话示例**：

```
用户：“这个 HTML 帮我存到知识库”
  → 跳过 Stage 1，直接 Stage 2 (kb) 调 saveFileByPath + 5 年 preview ticket

用户：“这是我的页面，拿一个 30 天分享链接”
  → 跳过 Stage 1，直接 Stage 2 (docviewer)

用户发来一个 xxx.html 文件
  → 如果附带说"原样 / 直接" → 跳 Stage 1 忠实模式 = Stage 1 不加工（该文件已经是 HTML，不需转）
  → 如果附带说"加工 / 优化" → 报错（HTML 不能被加工）
  → 如果没说 → 默认走 Stage 2 (docviewer) 拿 30 天链接
```

**调用代码示例**：

```python
# Python 调用
preview_url = await doc_viewer.stage2_upload(
    html_path="/path/to/existing.html",
    target="kb",  # 或 "docviewer" / "custom"
    project_id="2060176831872499713",  # kb 模式必填
    path="DocViewer/2026Q2"  # 可选，默认 DOCVIEWER_KB_PATH
)
```

---

## Stage 1：Markdown → HTML

### Step 1.0：模式选择（必做）

按上方"触发判断"确定模式。如果不明确，**默认加工模式**。加工模式的具体风格选择见下方"风格推荐规则"节。

### 模式 A：忠实模式（Faithful）

固定使用风格 13，**当前只有一个默认皮肤**（13-a 浅色）。

> 扩展口：将来可加 13-b（深蓝）、13-c（暖色）等主题变体，但**只改视觉皮肤，不改内容结构**。
> ⚠️ **注意**：13-b 和 13-c 尚未实现。当前只能使用 13-a。如果用户要求 13-b/13-c，请告知「暂未实现，当前仅支持 13-a」。

**输入**：.md 文件

**实现**：

```bash
# 风格 13 提供 Python 脚本（templates/style-13/report_renderer.py）
python3 templates/style-13/report_renderer.py <input.md> > output.html
```

**读取规范**：
- `design-standards/base-html-rules.md`（HTML/CSS 基础规则）
- `design-standards/table-spec.md`（表格规范）
- `design-standards/responsive-spec.md`（多端适配）
- `design-standards/print-spec.md`（打印优化）
- `templates/style-13/design-token.md`（风格 13 的 token）

**质量验证**：

```bash
# 验证 1：所有 md 的标题都在 HTML 中
python3 -c "
import re
md = open('input.md').read()
html = open('output.html').read()
md_titles = set(re.findall(r'^#+\s+(.+)$', md, re.MULTILINE))
html_titles = set(re.findall(r'<h[1-6][^>]*>(.+?)</h[1-6]>', html, re.MULTILINE))
missing = md_titles - html_titles
if missing:
    print(f'❌ 缺失标题: {missing}')
    exit(1)
print('✅ 全部标题保留')
"

# 验证 2：无未替换模板变量
TEMPLATE_COUNT=$(grep -c '{{' output.html 2>/dev/null || echo 0)
if [ "$TEMPLATE_COUNT" -gt 0 ]; then exit 1; fi
```

### 模式 B：加工模式（Composed）

根据用户意图选择风格 01-12 之一。

**输入**：.md 文件 + 风格选择

**实现**：sub-agent 读取 .md → 理解内容结构 → 读取对应风格的 token + skeleton → 手工拼装 HTML。

**读取规范**（按所选风格）：

| 风格 | Token | Skeleton | 配色 |
|------|-------|----------|------|
| 01 | `templates/style-01/design-token.md` | `templates/style-01/skeleton.html` | — |
| 02 | `templates/style-02/design-token.md` | `templates/style-02/skeleton.html` | — |
| 03 | `templates/style-03/design-token.md` | `templates/style-03/skeleton.html` | `color-themes/amber.yml`（默认）|
| 04 | `templates/style-04/design-token.md` | `templates/style-04/skeleton.html` | — |
| 05 | `templates/style-05/design-token.md` | `templates/style-05/skeleton.html` | — |
| 06 | `templates/style-06/design-token.md` | `templates/style-06/skeleton.html` | — |
| 07 | `templates/style-07/design-token.md` | `templates/style-07/skeleton.html` | — |
| 08 | `templates/style-08/design-token.md` | `templates/style-08/skeleton.html` | — |
| 09 | `templates/style-09/design-token.md` | `templates/style-09/skeleton.html` | — |
| 10 | `templates/style-10/design-token.md` | `templates/style-10/skeleton.html` | — |
| 11 | `templates/style-11/design-token.md` | `templates/style-11/skeleton.html` | `color-themes/dark-technical.yml` |
| 12 | `templates/style-12/design-token.md` | `templates/style-12/skeleton.html` | `color-themes/mckinsey-navy.yml`（默认）|

**风格推荐规则**（用户没说偏好时由 sub-agent 判断）：

- md 是 **报告/分析/BD 评估/尽调** → 风格 03
- md 是 **CMS 投前评估/麦肯锡/深蓝** → 风格 12
- md 是 **日报/情报/资讯** → 风格 04
- md 是 **数据/KPI/指标** → 风格 05
- md 是 **产品介绍** → 风格 06
- md 是 **API/开发者文档** → 风格 10
- md 是 **技术教程/暗色/AI 教程** → 风格 11
- md 是 **Notion/笔记/文档** → 风格 09
- md 是 **日系/极简/AI 产品** → 风格 07
- md 是 **Apple/电影感/keynote** → 风格 08
- 都不像 → 风格 01（默认）

**HTML 规范**（所有风格通用）：
- 单文件，内联 CSS
- 字体：PingFang SC / Microsoft YaHei / Noto Sans CJK SC（**禁止 Inter/Roboto**）
- 表格：PC 端 `width:100%`，外层包裹 `.table-wrap{overflow-x:auto}`
- 响应式：至少覆盖 480px / 768px 断点
- 打印报告类：正文字号用 `pt` 单位，`@page` 边距固定
- 图片：外链 URL 或占位图，禁止 base64
- 不使用 JS 框架，纯 HTML + CSS
- 文件大小 < 1MB

**质量验证**：

```bash
TEMPLATE_COUNT=$(grep -c '{{' output.html 2>/dev/null || echo 0)
if [ "$TEMPLATE_COUNT" -gt 0 ]; then
  echo "❌ FAIL: 发现 $TEMPLATE_COUNT 个未替换的模板变量"
  exit 1
fi
echo "✅ PASS: 无未替换变量"
```

**验证清单**：
- [ ] `grep -c '{{'` 结果为 0
- [ ] CSS 颜色为具体值，非 `{{变量}}`
- [ ] 表格表头有背景色
- [ ] 文件大小 > 10KB

### Step 1.9：模式切换（可选）

如果用户对当前输出不满意：

- **忠实 → 加工**：询问偏好风格（01/03/04/12 等），重新跑模式 B
- **加工 → 忠实**：说明"将保持原内容结构，仅调整视觉皮肤"，重新跑模式 A

切换成本：忠实模式 5-10 秒，加工模式 30-60 秒。

### Step 1.10：交付

将生成的 HTML 文件路径返回给调用方。**不要在 Stage 1 阶段执行任何上传**。

---

## Stage 2：上传 + 返回预览链接

**输入**：本地 HTML 文件 + target（必填）

### Step 2.1：选择 target

| target | 何时选 |
|--------|--------|
| `docviewer` | 默认 / 用户要公网 30 天链接 |
| `kb` | 用户要 5 年内部链接 / 玄关知识库 |
| `custom` | 业务 skill 自己有上传端点 |

### Step 2.2：执行上传

#### target=docviewer

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

**返回链接选择**：
- HTML 文件 → 取 `raw_url`
- PDF 文件 → 取 `url`（view）

```bash
URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['raw_url'])")
```

#### target=kb（玄关知识库）

**前置条件**：用户已配置 `DOCVIEWER_KB_APPKEY`。

**v2.10.0 引入（v3.0.0 保留）**：
- **支持外部 projectId**：调用方可传 `projectId` 参数（如 `2060176831872499713`），跳过个人知识库自动获取
- **支持外部 path**：调用方可传 `path` 参数覆盖默认 `DOCVIEWER_KB_PATH`
- 当 `projectId` 未传入时，自动走个人知识库

##### 模式 A：调用方指定 projectId（业务 skill 推荐）

```bash
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
```

##### 模式 B：个人知识库（用户交互默认）

```bash
# Step 1：自动获取个人知识库 projectId
PROJECT_ID=$(curl -s "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/personal/getProjectId" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# 后续 Step 2-4 同模式 A
```

#### target=custom

业务 skill 自行实现上传逻辑。doc-viewer 不内置实现。

调用方注入 endpoint 函数即可。**未来路线**：当 custom 模式被多个业务 skill 共用时，将 Stage 2 拆分为独立 skill `html-uploader`。

### Step 2.3：返回链接

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

### 范式 1：一气呵成（普通用户默认）

```
用户：「把这个 md 转成报告页」
→ Stage 1 加工模式（默认风格 01）
→ Stage 2（target=docviewer）
→ 返回 30 天公网链接
```

### 范式 2：仅生成 HTML（业务 skill 标准用法）

```python
# 业务 skill 的伪代码
output_path = await doc_viewer.stage1_md_to_html(
    md_path="report.md",
    mode="composed",   # 或 "faithful"
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
# Stage 1：加工模式生成 HTML
html_path = await doc_viewer.stage1_md_to_html(
    md_path="report.md",
    mode="composed",
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

---

## 失败处理

| 场景 | 处理 |
|------|------|
| Stage 1 忠实：标题缺失 | 验证脚本检测到缺失 → 报错，重跑 |
| Stage 1 加工：模板变量未替换 | `grep -c '{{'` 检测到非 0 → 报错，重跑 |
| Stage 1：文件 > 1MB | 减小内容或图片 |
| Stage 2 docviewer：文件 > 10MB | 告知用户文件大小限制 |
| Stage 2 docviewer：上传失败 | 重试一次，仍失败则报告错误 |
| Stage 2 kb：未配置 appKey | 提示用户先配置，提供配置命令 |
| Stage 2 kb：appKey 无效 | 告知"appKey 无效，请检查" |
| Stage 2 kb：上传失败 | 重试一次，仍失败则报告错误 |
| Stage 2 kb：调用方传了 projectId 但没有权限 | 告知"无权限访问 projectId=<x>"，不 fallback |
| Stage 2 custom：endpoint 抛错 | 直接透传错误，由调用方处理 |
| Doc Viewer 服务不可用 | 告知用户服务暂时不可用 |

---

## API 参考

### DocViewer 服务（target=docviewer）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传文件 |
| `/view/{id}` | GET | 渲染预览 |
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
| `GET /user/login/appkey` | 用 appKey 换取 access-token |
| `POST /doc-preview/api/preview/ticket` | 生成公网预览链接（5 年） |

---

## 注意事项

### 通用
- Stage 1 严格无网络副作用（除读取本地文件外）
- Stage 2 才会产生网络调用
- doc-viewer **不解决内容创作**，上游负责把需求组织成 md

### target=docviewer
- 最大文件 10MB，保留 30 天
- HTML 返回 raw 链接

### target=kb
- 公网预览链接 5 年有效
- 删除或移动文件通过玄关知识库网页端
- 默认路径 `知识库 / DocViewer /`，可被 `path` 参数覆盖
- access-token 每次重新换取

---

## 风格一览

### 忠实模式（仅风格 13）

**风格 13** — 程序化 Markdown 渲染
- 分类：程序化型
- 目录导航：✅ 自动从 ## 标题生成
- 实现：Python 脚本（`templates/style-13/report_renderer.py`）
- 适合：任意结构的 Markdown 长文档，保留原章节，只做视觉渲染
- 主题变体（扩展口）：13-a 浅色（默认）/ 13-b 深蓝 / 13-c 暖色

### 加工模式（风格 01-12）

| 风格 | 分类 | 适合 |
|------|------|------|
| 01 | 通用型 | 默认兜底 |
| 02 | 系列型 | 企业报告系统（6 套变体） |
| 03 | 专用型 | BD 投前评估报告（amber / yellow / investment-blue） |
| 04 | 通用型 | 情报日报风 |
| 05 | 通用型 | 数据看板/KPI |
| 06 | 通用型 | 产品介绍页 |
| 07 | 通用型 | 日系/Notion 风 |
| 08 | 通用型 | Apple 极简风 |
| 09 | 通用型 | 文档/编辑器风 |
| 10 | 通用型 | Stripe 开发者平台风 |
| 11 | 专用型 | Linear 暗色技术风 |
| 12 | 专用型 | CMS 康哲药业投前评估（mckinsey-navy 默认） |

详细 token 和配色方案见 `templates/` 目录下各风格子目录。

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

服务地址已内置（`https://doc.20100706.xyz`）。

### target=kb（需要配置）

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

### target=custom（无需配置）

由调用方注入 endpoint 函数。

---

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`

---

## 从 v2.x 迁移到 v3.0.0

v3.0.0 是破坏性变更，主要变化：

- **输入限制为 Markdown 文件**：v2.x 接受的「口述需求」「文本」「现有 HTML」输入已移除
- **新增双模式架构**：忠实模式（风格 13，原样渲染）vs 加工模式（风格 01-12，重构渲染，默认）
- **要求上游提供 md**：doc-viewer 不做素材收集

**迁移指南**：

1. **口述需求用户**：如果之前习惯「帮我做个 XX 页面」口述生成，请：
   - 手动写一个 .md 描述需求（标题、正文、数据点、表格）
   - 发送给 doc-viewer 转换为 HTML

2. **直接发 .html 的用户**：请改为发 .md 文件，doc-viewer 会自动转换后上传。

3. **业务 skill 调用方**（如 bd-eval-cms）：调用方式不变（都是传 md 拿 HTML），无需调整。

4. **期望「原样转 HTML」的用户**：明说「原样 / 忠实 / 不改内容」可走忠实模式（风格 13），md 原样保留只加视觉皮肤。

**降级到 v2.10.0**（不推荐）：如必须保留 v2.x 习惯，切到 `git checkout v2.10.0 -- projects/2605101/doc-viewer/`。

---

## 版本历史

- **v3.0.2**（2026-06-12）：加 HTML 直传模式明确入口
  - frontmatter description 加「.html」输入说明 + 3 个 HTML 触发词
  - 触发判断流程图拆分 .md / .html 两路，HTML 跳过 Stage 1
  - 新增「## HTML 直传模式」章节，说明适用场景 / 触发词 / 调用代码
  - 补「存知识库」触发词路径
  - 补 .html 文件处理路径
  - 加风格 13-b/13-c 未实现警告
  - 修正「v3.0.0 新增」版本标注错误（实为 v2.10.0 引入）
  - 加工模式 Step 1.0 加风格推荐规则引用
  - 加「从 v2.x 迁移到 v3.0.0」迁移指南
- **v3.0.0**（2026-06-12）：架构重构为"md → HTML 转换 + 上传预览"管道
  - 输入统一为 Markdown 文件（删除口述/文本/素材收集）
  - 拆分为忠实模式（风格 13）和加工模式（风格 01-12）
  - 默认走加工模式（风格 01）
  - 忠实模式支持主题变体扩展口（13-a/13-b/13-c）
  - 加模式切换机制
  - 修复 issue #71：target=kb 支持外部 projectId
- **v2.10.0**（2026-06-12）：Stage 1/2 拆分初版（已废弃）
- **v2.9.0**：路径 C 知识库存储
- 早期版本：基础路径 A/B（DocViewer）
