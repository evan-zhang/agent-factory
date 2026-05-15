# BD 投前评估报告 HTML 生成规范

**基于 RHOFADE 报告（标杆版本）逆向提取**
**更新时间**: 2026-05-15

---

## 一、整体 HTML 结构

```
<html>
<head>
  <style> /* 全部 CSS 在 <style> 内 */ </style>
</head>
<body>
  <!-- 封面 -->
  <div class="cover page-break">...</div>

  <!-- 目录 -->
  <div class="toc-section page-break">...</div>

  <!-- 章节 1..N -->
  <div class="chapter page-break">
    <h1>第X.Y章 标题</h1>
    <h2>子标题</h2>
    <h3>孙标题</h3>
    <p>段落</p>
    <blockquote>引用块</blockquote>
    <div class="table-wrap"><table>...</table></div>
    <pre><code>代码块</code></pre>
    <div class="highlight-box">高亮框</div>
  </div>

  <!-- 下一个章节 -->
  <div class="chapter page-break">...</div>
</body>
</html>
```

---

## 二、封面（Cover）

```html
<div class="cover page-break">
  <div class="cover-topbar"></div>
  <div class="cover-badge">内部机密 · 限参与评估团队</div>
  <div class="cover-title">B&nbsp;D&nbsp;投&nbsp;前&nbsp;评&nbsp;估&nbsp;报&nbsp;告</div>
  <div class="cover-subtitle">{{PRODUCT_CODE}}（{{PRODUCT_EN}} / {{PRODUCT_CN}}）</div>
  <div class="cover-company">{{COMPANY_NAME}}</div>
  <div class="cover-meta">
    <div><span class="lbl">评估日期：</span>{{DATE}}</div>
    <div><span class="lbl">评估模板：</span>{{TEMPLATE}}</div>
    <div><span class="lbl">评估视角：</span>{{PERSPECTIVE}}</div>
    <div><span class="lbl">综合评级：</span><span class="b">{{RATING}}</span></div>
  </div>
  <div class="cover-confidential">⚠ 内部机密 — 仅限参与评估团队成员阅览</div>
  <div class="cover-rating-box">
    <div class="rating-label">推荐结论</div>
    <div class="rating-val">{{RATING_SHORT}}</div>
  </div>
</div>
```

**关键**: skeleton.html 已有此结构，只需替换 {{TOKEN}} 即可。

---

## 三、目录（TOC）

**⚠️ 必须使用 `<div class="toc-item">` 格式，不是 `<li>`！**

```html
<div class="toc-section page-break">
  <div class="toc-header">目 录</div>
  <div class="toc-grid">
    <div class="toc-item"><span class="toc-num">0.0</span><span class="toc-title">品种概述与评估框架说明</span></div>
    <div class="toc-item"><span class="toc-num">1.0</span><span class="toc-title">产品类型定义</span></div>
    <div class="toc-item"><span class="toc-num">1.1</span><span class="toc-title">PC-1 科学机制与差异化</span></div>
    ...
  </div>
</div>
```

**编号规则**：
- 从 markdown 标题中提取编号（如 "1.1 PC-1 ..." → num="1.1"）
- 如果标题没有编号，用序号（1, 2, 3...）
- "附" 字开头的用 "附" 作为 num

---

## 四、章节（Chapter）

**⚠️ 每个章节必须用 `<div class="chapter page-break">` 包裹！**

```html
<div class="chapter page-break">
<h1>第X.Y章 章节标题</h1>
<!-- 章节内容 -->
</div>
```

**章节标题**：
- 一级章节用 `<h1>`（如 "第0.0章 品种概述"、"第1.1章 PC-1 科学机制"）
- 如果 markdown 没有 "第X章" 格式，直接用原标题

---

## 五、Markdown → HTML 转换规则

### 5.1 表格
```html
<div class="table-wrap">
<table>
<thead><tr><th>列1</th><th>列2</th></tr></thead>
<tbody>
<tr><td>值1</td><td>值2</td></tr>
</tbody>
</table>
</div>
```

**关键**：表格外层必须有 `<div class="table-wrap">` 包裹（响应式横向滚动）

### 5.2 标题层级
- markdown `## 标题` → `<h2>标题</h2>`（章节内子标题）
- markdown `### 标题` → `<h3>标题</h3>`
- markdown `#### 标题` → `<h4>标题</h4>`

**注意**：`<h1>` 只用于章节顶部标题，不用于章节内部

### 5.3 引用块
```html
<blockquote><p>引用内容</p></blockquote>
```

### 5.4 代码块
```html
<pre><code>代码内容</code></pre>
```

### 5.5 行内格式
- `**粗体**` → `<strong>粗体</strong>`
- `*斜体*` → `<em>斜体</em>`
- `` `代码` `` → `<code>代码</code>`
- `[链接](url)` → `<a href="url">链接</a>`

### 5.6 列表
```html
<ul>
<li>项目1</li>
<li>项目2</li>
</ul>
```

### 5.7 段落
- 非空、非 HTML 标签开头的行 → `<p>内容</p>`
- 空行 → 不输出（换行间距由 CSS margin 控制）

---

## 六、CSS 变量替换

skeleton.html 中共有 **87 个** `{{TOKEN}}` 占位符，必须全部替换。

### CSS 变量（来自 amber.yml，共 ~70 个）
完整列表见 `~/.agents/skills/doc-viewer/templates/style-03/color-themes/amber.yml`

### 内容变量（共 ~17 个）
- `{{TITLE}}` — 报告标题（浏览器标签名）
- `{{PRODUCT_CODE}}` — 产品编号/商品名
- `{{PRODUCT_EN}}` — 英文名
- `{{PRODUCT_CN}}` — 中文名
- `{{COMPANY_NAME}}` — 公司名称
- `{{DATE}}` — 评估日期
- `{{TEMPLATE}}` — 评估模板名
- `{{PERSPECTIVE}}` — 评估视角
- `{{RATING}}` — 综合评级
- `{{RATING_SHORT}}` — 推荐结论（emoji + 文字）
- `{{TOC_ITEMS}}` — 目录 HTML
- `{{CHAPTERS}}` — 章节内容 HTML
- `{{cover-topbar-class}}` — 固定值 "cover-topbar"

### 验证
替换后必须检查：`grep -c '{{' output.html` → 结果必须为 **0**

---

## 七、上传与更新

### 首次上传
```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@report.html;filename=report-amber.html"
```
返回 `id` 和 `raw_url`。

### 更新（保持链接不变）
```bash
curl -s -X PUT "https://doc.20100706.xyz/api/{doc_id}" \
  -F "file=@report.html;filename=report-amber.html"
```
**链接不变**，`id` 不变。

---

## 八、完整生成脚本模板

```python
# 1. 读取 skeleton.html
# 2. 从 amber.yml 读取所有 CSS token → 替换
# 3. 设置报告元数据（code, en, cn, company, date, template, perspective, rating, rating_short）
# 4. 读取 markdown 文件
# 5. 按 "# "（一级标题）拆分为章节列表
# 6. 生成 TOC: <div class="toc-item"><span class="toc-num">编号</span><span class="toc-title">标题</span></div>
# 7. 生成章节: <div class="chapter page-break"><h1>标题</h1>{md_to_html(内容)}</div>
# 8. 替换 {{TOC_ITEMS}} 和 {{CHAPTERS}}
# 9. 验证: 零个未替换 token
# 10. 如有 doc_id → PUT /api/{doc_id} 更新；否则 → POST /upload 新建
```

---

## 九、常见错误清单

| 错误 | 症状 | 修复 |
|------|------|------|
| 只替换部分 token | 封面/样式全是 `{{XXX}}` | 替换全部 87 个 token |
| TOC 用 `<li><a>` | 目录样式错误 | 必须用 `<div class="toc-item">` |
| section 没有 chapter 包裹 | 内容撑满全宽，无留白 | 包裹 `<div class="chapter page-break">` |
| 表格没有 table-wrap | 移动端表格溢出 | 包裹 `<div class="table-wrap">` |
| 用 POST 新建而非 PUT 更新 | 链接每次变化 | 更新用 `PUT /api/{id}` |
