---
name: doc-viewer
description: "文件上传预览 + HTML 内容页面生成器。提供现成文件可直接上传预览；描述内容需求可自动生成风格化 HTML 页面并上传。触发词：上传文件、预览文件、生成链接、生成页面、HTML页面、宣传页、报告页面"
version: "2.6.0"
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
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"
```

### Step 4: 返回链接

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

> **📐 架构说明：样式 × 颜色 两个正交维度**
> 
> **样式（skeleton.html）**：决定页面结构、章节排版、组件布局。目前 style-01 ~ 11 代表 11 种结构方案。
> 
> **颜色（color-themes/*.yml）**：决定配色体系，只替换 CSS 变量值，不改变结构。同一套骨架换一套配色即可。
> 
> **适用场景**：同一份报告内容（如投资评估），可以套用 style-03 骨架 + investment-blue 配色来生成；同骨架换 amber 配色则变为 BD 报告风格。

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
| `design-standards/print-spec.md` | 打印优化规范（报告类必须读）：CSS @media print / @page / page-break（**HTML转PDF由独立skill负责，不在本skill范围内**） |

**第二步 — 读取所选风格的 Token 和骨架**：

| 风格 | Token 文件 | 骨架文件 | 配色方案 |
|------|-----------|---------|
| 风格 01 | `templates/style-01/design-token.md` | `templates/style-01/skeleton.html` | — |
| 风格 02 | `templates/style-02/design-token.md` | `templates/style-02/skeleton.html` | — |
| 风格 03 | `templates/style-03/design-token.md` | `templates/style-03/skeleton.html` | `templates/style-03/color-themes/amber.yml`（琥珀金）或 `yellow.yml`（阳光黄）或 `investment-blue.yml`（投资蓝） |
| 风格 04 | `templates/style-04/design-token.md` | `templates/style-04/skeleton.html` | — |
| 风格 05 | `templates/style-05/design-token.md` | `templates/style-05/skeleton.html` | — |
| 风格 06 | `templates/style-06/design-token.md` | `templates/style-06/skeleton.html` | — |
| 风格 07 | `templates/style-07/design-token.md` | `templates/style-07/skeleton.html` | — |
| 风格 08 | `templates/style-08/design-token.md` | `templates/style-08/skeleton.html` | — |
| 风格 09 | `templates/style-09/design-token.md` | `templates/style-09/skeleton.html` | — |
| 风格 10 | `templates/style-10/design-token.md` | `templates/style-10/skeleton.html` | — |
| 风格 11 | `templates/style-11/design-token.md` | `templates/style-11/skeleton.html` | `templates/style-11/color-themes/dark-technical.yml`（暗色技术风）|
| 风格 12 | `templates/style-12/design-token.md` | `templates/style-12/skeleton.html` | `templates/style-12/color-themes/mckinsey-navy.yml`（麦肯锡深蓝）或 `investment-blue.yml`（投资蓝）或 `burgundy-wine.yml`（勃艮第酒红）或 `forest-teal.yml`（森林青） |

Design Token 包含：
- **YAML front matter**：机器可读的 tokens（颜色、字体、间距、圆角）
- **Markdown body**：设计理念、组件规范、Do's and Don'ts

Skeleton 包含：
- 该风格的完整 HTML 骨架参考（表格结构、卡片结构等）

### Step 4：生成 HTML

**核心原则：**
- 风格 Token 的颜色/字号 → 直接使用，不自行调整
- 通用规范的表格/响应式/打印要求 → 必须遵守

**HTML 规范**：
- 单文件，内联 CSS
- 字体：PingFang SC / Microsoft YaHei / Noto Sans CJK SC（中文友好，**禁止 Inter/Roboto**）
- 表格：PC 端 `width:100%`，外层包裹 `.table-wrap{overflow-x:auto}`（见 table-spec.md）
- 响应式：至少覆盖 480px / 768px 断点（见 responsive-spec.md）
- 打印报告类：正文字号用 `pt` 单位，`@page` 边距固定（见 print-spec.md）
- 图片：外链 URL 或占位图，禁止 base64
- 不使用 JS 框架，纯 HTML + CSS
- 文件大小 < 1MB

**风格 03（BD报告）生成流程（必须严格遵循）**：

⚠️ 风格 03 的 `skeleton.html` 包含 `{{占位符}}` 模板变量，**不能直接使用 skeleton.html 作为输出**。

正确流程：
1. 读取 `reference-amber.html` 或 `reference-yellow.html`（根据配色选择）作为基底
2. 保留其中的完整 CSS 样式（已替换好所有颜色值，不要修改）
3. 只替换 body 部分的内容（封面信息、章节内容、目录）
4. 如果必须从 skeleton.html 生成，**必须**将 `color-themes/*.yml` 中的所有值替换到 CSS 的 `{{变量}}` 中，再将内容填入 body 占位符

禁止事项：
- 禁止输出包含 `{{` 或 `}}` 的 HTML 文件
- 禁止跳过模板变量替换直接上传
- 禁止混用深蓝色（#0068A8）和琥珀金（#C9920A）配色

### Step 5：质量验证（上传前必须执行）

**验证命令**：
```bash
# 检查是否有未替换的模板变量
TEMPLATE_COUNT=$(grep -c '{{' output.html 2>/dev/null || echo 0)
if [ "$TEMPLATE_COUNT" -gt 0 ]; then
  echo "❌ FAIL: 发现 $TEMPLATE_COUNT 个未替换的模板变量，禁止上传"
  grep -n '{{' output.html | head -10
  exit 1
fi

echo "✅ PASS: 无未替换变量"
```

**验证清单**（上传前逐项确认）：
- [ ] HTML 文件中 `grep -c '{{'` 结果为 0（无残留模板变量）
- [ ] 封面页包含实际产品名称、公司名称、日期（不是占位符文本）
- [ ] CSS 样式中有具体的颜色值（如 `#C9920A`），不是 `{{变量名}}`
- [ ] 表格表头有背景色（不是透明/白色）
- [ ] 文件大小 > 10KB（内容确实已填充）

**任何一项不通过，禁止上传，必须修复后重新验证。**

### Step 6：上传与交付

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@output.html;filename=<标题>.html"
```

返回后：
- HTML → 返回 `raw_url`
- PDF → 返回 `url`（view）

不要给 PDF 返回 raw 链接。

---

## 更新已有文档（路径 A/B 通用）

```bash
curl -X PUT https://doc.20100706.xyz/api/{doc_id} \
  -F "file=@新文件.html;filename=<标题>.html"
```

更新后：doc_id 不变、链接不变。

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
| `/view/{id}` | GET | 渲染预览（含导航栏壳） |
| `/raw/{id}` | GET | **原始文件**，直接打开即为最终效果 |
| `/api/{id}` | PUT | 更新已有文档，保留 doc_id 和链接不变 |
| `/api/{id}` | GET | 文档 JSON 元信息 |
| `/api/list` | GET | 所有文档列表（按时间倒序） |
| `/api/{id}` | DELETE | 删除文档 |

## 注意事项

- 最大文件 10MB，保留 30 天
- 上传时必须用原始文件名（`filename=` 参数）
- **HTML 返回 raw 链接，PDF 返回 view 链接**
- HTML 直接渲染，无工具栏；Markdown 转换后渲染

---

## 可用风格一览

### 风格 01 — Data & AI Report（企业数据智能白皮书）
**分类**：通用型

综合风格，适合完整报告页面。蓝紫渐变主调，数据密集型。

| 文件 | 说明 |
|------|------|
| `templates/style-01/design-token.md` | Design Token（颜色/字体/间距） |
| `templates/style-01/skeleton.html` | HTML 骨架参考 |
| `templates/style-01/style-01-data-ai-report.md` | 视觉说明与内容结构 |

### 风格 02 — Google Cloud / IDC 企业报告视觉系统（6 套变体）
**分类**：系列型

以 Google Yellow 为核心色，共享一套 base token，6 种变体覆盖不同场景。

| 编号 | 名称 | 适用场景 |
|------|------|----------|
| 02-A | 四色拼贴封面风 | 报告首页/入口页 |
| 02-B | 大图 Hero 章节封面风 | 章节页/观点页 |
| 02-C | 白底咨询报告内容风 | 正文页/分析页 |
| 02-D | 彩色模块矩阵风 | 方法论/模块清单 |
| 02-E | 数据洞察大数字风 | 指标页/数据页 |
| 02-F | 案例/行业卡片风 | 场景页/案例页 |

**Token 文件**：`templates/style-02/style-02*-DESIGN.md`

### 风格 03 — BD 投前评估报告（文档输出型）
**分类**：专用型 | **目录导航**：按需开启

A4 纵向，章节密集，表格整齐。专为导出 PDF/Word 设计。

**配色方案（color-themes/）**：
- **琥珀金（amber）**：深金 #C9920A，沉稳高端，适合高管/BD报告（默认）
- **暗色技术风（dark-technical）**：暗黑 #070707 + 橙红 #FF4A22，适合 AI 极客/技术海报报告
- **阳光黄（yellow）**：亮黄 #F4B400，现代活力，适合内部审阅
- **投资蓝（investment-blue）**：深海蓝 #1D4ED8，专业金融，适合投资报告

用户说「琥珀金」「金色」→ amber；说「阳光黄」「黄色」→ yellow；说「投资蓝」「蓝色」「金融报告」→ investment-blue；未指定 → amber。

| 文件 | 说明 |
|------|------|
| `templates/style-03/design-token.md` | Design Token |
| `templates/style-03/skeleton.html` | HTML 骨架（含 {{TOKEN}} 占位符） |
| `templates/style-03/style-03-bd-report.md` | 视觉说明与内容结构 |
| `templates/style-03/color-themes/amber.yml` | 琥珀金配色 Token |
| `templates/style-03/color-themes/dark-technical.yml` | 暗色技术风配色 Token（橙红）|
| `templates/style-03/color-themes/yellow.yml` | 阳光黄配色 Token |
| `templates/style-03/color-themes/investment-blue.yml` | 投资蓝配色 Token |
| `templates/style-03/reference-amber.html` | 琥珀金版完整参考范例（CG-0255） |
| `templates/style-03/reference-yellow.html` | 阳光黄版完整参考范例（CG-0255） |

**生成流程**：
1. 读取 `skeleton.html`（骨架含 {{TOKEN}} 占位符）
2. 根据用户指定的配色读取对应 `color-themes/*.yml`
3. 将 Token 值替换到骨架 CSS 中
4. 将报告内容填入 body 占位符（{{PRODUCT_CODE}}、{{CHAPTERS}} 等）
5. 生成完整 HTML 并上传

### 风格 04 — 情报日报风（新闻/资讯列表）
**分类**：通用型 | **目录导航**：✅ 默认开启

大日期 + 小标题，报告名称收敛。适合每日情报汇总、动态速览。

| 文件 | 说明 |
|------|------|
| `templates/style-04/design-token.md` | Design Token |
| `templates/style-04/skeleton.html` | HTML 骨架参考 |

### 风格 05 — 数据看板/指标卡风格
**分类**：通用型 | **目录导航**：✅ 默认开启

大数字 + 图表，适合 KPI 展示、数据概览。

| 文件 | 说明 |
|------|------|
| `templates/style-05/design-token.md` | Design Token |
| `templates/style-05/skeleton.html` | HTML 骨架参考 |

### 风格 06 — 产品介绍页
**分类**：通用型 | **目录导航**：✅ 默认开启

多 section + Hero，适合产品/服务介绍页。

| 文件 | 说明 |
|------|------|
| `templates/style-06/design-token.md` | Design Token |
| `templates/style-06/skeleton.html` | HTML 骨架参考 |

### 风格 11 — Linear 暗色技术风（技术海报 + 仪表盘）
**分类**：专用型 | **目录导航**：按需开启

暗黑背景 + 橙红主色，技术海报风格，适合 Claude Code 深度教程 / AI 极客内容 / 开发者文档。

**配色方案（color-themes/）**：
- **dark-technical（暗色技术风）**：暗黑 #070707 + 橙红 #FF4A22 + 暖白文字，适合技术海报（默认）

用户说「暗色」「Linear」「暗色主题」「高级感」「极客」「AI 教程」「技术海报」→ 推荐 style-11 + dark-technical。

| 文件 | 说明 |
|------|------|
| `templates/style-11/design-token.md` | Design Token |
| `templates/style-11/skeleton.html` | HTML 骨架（含 {{TOKEN}} 占位符）|
| `templates/style-11/color-themes/dark-technical.yml` | 暗色技术风配色 Token（橙红主色）|

**生成流程**：同风格 03，从 skeleton.html + color-themes/*.yml 生成。

### 风格 12 — CMS 康哲药业投前评估报告（Gate门控型）
**分类**：专用型 | **目录导航**：按需开启

A4 纵向，专为 CMS 投前评估体系设计。Gate 结论卡 + Battle 对抗审查 + 置信度徽章 + 一票否决框。

**配色方案（color-themes/）**：
- **麦肯锡深蓝（mckinsey-navy）**：深蓝 #1a3a5c，经典咨询公司风格（默认）
- **投资蓝（investment-blue）**：投资蓝 #1D4ED8，投行/基金报告风格
- **勃艮第酒红（burgundy-wine）**：酒红 #7B2D3B，欧洲老牌药企风格
- **森林青（forest-teal）**：青绿 #1B6B5A，现代药企/ESG 风格

用户说「麦肯锡」「深蓝」「咨询」→ mckinsey-navy；说「投资蓝」「蓝色」「金融」→ investment-blue；说「酒红」「勃艮第」→ burgundy-wine；说「青绿」「森林」「ESG」→ forest-teal；未指定 → mckinsey-navy。

| 文件 | 说明 |
|------|------|
| `templates/style-12/design-token.md` | Design Token |
| `templates/style-12/skeleton.html` | HTML 骨架（含 {{TOKEN}} 占位符） |
| `templates/style-12/style-12-cms-eval.md` | 视觉说明与内容结构 |
| `templates/style-12/generation-spec.md` | 生成规范（Markdown→HTML映射） |
| `templates/style-12/prompt.md` | 生成 prompt（给 Agent 用） |
| `templates/style-12/color-themes/mckinsey-navy.yml` | 麦肯锡深蓝配色 Token |
| `templates/style-12/color-themes/investment-blue.yml` | 投资蓝配色 Token |
| `templates/style-12/color-themes/burgundy-wine.yml` | 勃艮第酒红配色 Token |
| `templates/style-12/color-themes/forest-teal.yml` | 森林青配色 Token |
| `templates/style-12/reference-mckinsey-navy.html` | 麦肯锡深蓝版完整参考范例（MB-001） |

**CMS 专属组件**：
- Gate 结论卡（`.gate-card` + `.gate-pass` / `.gate-conditional` / `.gate-stop`）
- 置信度徽章（`.confidence-badge` + `.conf-a` / `.conf-b` / `.conf-c` / `.conf-d`）
- Battle 对抗审查（`.battle-auditor` + `.battle-executor`）
- 一票否决框（`.veto-box`）
- 信息冲突框（`.conflict-box`）
- 阶段标签（`.stage-tag` + `.stage-a` / `.stage-b`）
- DRL 优先级（`.drl-priority` + `.drl-p0` / `.drl-p1` / `.drl-p2`）
- 风险等级（`.risk-high` / `.risk-medium` / `.risk-low`）
- 中立审查框（`.neutral-review`）

**生成流程**：风格 12 提供专用 Python 转换脚本 `convert-md-to-html.py`，可直接从 Markdown 报告程序化生成 HTML，不需要 AI 手写 HTML。

```bash
python3 templates/style-12/convert-md-to-html.py <报告目录> <配色名> [输出路径]
```

脚本自动完成：读取 04-final-report.md → 提取封面元信息 → 识别 CMS 专属结构（Gate 结论卡、Battle 框、置信度标注等）→ 套用 skeleton.html + 配色 → 输出完整 HTML。

如需 AI 手动生成（路径 B），则从 skeleton.html + color-themes/*.yml 生成，封面使用 CMS 专属字段（案件代号、评估技能、业务主体）。

---

## 通用设计规范（design-standards/）

所有风格共享，Agent 生成 HTML 前必须读取：

| 文件 | 职责 |
|------|------|
| `design-standards/base-html-rules.md` | HTML/CSS 基础规则：字体/颜色变量/间距/圆角/动画 |
| `design-standards/table-spec.md` | 表格规范：`.table-wrap`包裹、`width:100%`、移动端横向滚动 |
| `design-standards/responsive-spec.md` | 多端适配：480px/768px 断点、三端字号对照 |
| `design-standards/print-spec.md` | 打印/PDF：@page 边距、`pt` 单位、page-break |

---

## 配置与授权

无需配置即可使用。服务地址已内置（`https://doc.20100706.xyz`），无权限控制。

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer

**标题格式**：`[BUG] doc-viewer: 简短描述` 或 `[FEATURE] doc-viewer: 简短描述`
