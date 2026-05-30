# CMS 投前评估报告 HTML 生成规范

**版本**: 1.0
**更新时间**: 2026-05-30

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

  <!-- 章节 -->
  <div class="chapter page-break">
    <h1>第X章 标题</h1>
    <h2>子标题</h2>
    <p>段落</p>
    <table>...</table>
    <!-- Gate 结论卡 -->
    <div class="gate-card gate-conditional">...</div>
  </div>

  <!-- Battle 审查 -->
  <div class="chapter page-break">
    <h1>第X章 Battle 对抗审查</h1>
    <div class="battle-auditor">...</div>
    <div class="battle-executor">...</div>
  </div>

</body>
</html>
```

---

## 二、封面（Cover）

封面使用 CMS 专属元信息：

```html
<div class="cover page-break">
  <div class="cover-topbar"></div>
  <div class="cover-badge">内部机密 · 限参与评估团队</div>
  <div class="cover-title">C&nbsp;M&nbsp;S&nbsp;投&nbsp;前&nbsp;评&nbsp;估&nbsp;报&nbsp;告</div>
  <div class="cover-subtitle">{{PRODUCT_CODE}}（{{PRODUCT_EN}} / {{PRODUCT_CN}}）</div>
  <div class="cover-company">{{COMPANY_NAME}}</div>
  <div class="cover-meta">
    <div><span class="lbl">案件代号：</span>{{CASE_CODE}}</div>
    <div><span class="lbl">评估技能：</span>{{SKILL_CODE}}</div>
    <div><span class="lbl">业务主体：</span>{{BUSINESS_UNIT}}</div>
    <div><span class="lbl">评估日期：</span>{{DATE}}</div>
    <div><span class="lbl">综合评级：</span><span class="b">{{RATING}}</span></div>
  </div>
  <div class="cover-confidential">⚠ 内部机密 — 仅限参与评估团队成员阅览</div>
  <div class="cover-rating-box">
    <div class="rating-label">推荐结论</div>
    <div class="rating-val">{{RATING_SHORT}}</div>
  </div>
</div>
```

**CMS 与风格 03 封面区别**：
- 标题：`CMS投前评估报告`（非 `BD投前评估报告`）
- 新增字段：案件代号、评估技能、业务主体
- 移除字段：评估模板、评估视角

---

## 三、Markdown → HTML 转换规则

### 3.1 基础元素（同风格 03）

- 标题 → h1/h2/h3/h4
- 段落 → p
- 列表 → ul/ol
- 表格 → table（外层 div.table-wrap）
- 粗体 → strong
- 斜体 → em

### 3.2 CMS 专属映射规则

#### Gate 结论卡

Markdown 中的结论块：
```markdown
## Gate X 结论卡
结论：有条件通过
置信度：低
...
```

转换为：
```html
<div class="gate-card gate-conditional">
  <div class="gate-title">Gate X — 名称 结论卡</div>
  <div class="gate-body">
    <p><span class="gate-label">结论</span> 有条件通过</p>
    ...
  </div>
</div>
```

#### 置信度标注

Markdown 中的 `[C级-待验证]` → `<span class="confidence-badge conf-c">C级-待验证</span>`
Markdown 中的 `[D级-基于假设]` → `<span class="confidence-badge conf-d">D级-基于假设</span>`
Markdown 中的 `[B级]` → `<span class="confidence-badge conf-b">B级</span>`
Markdown 中的 `[A级]` → `<span class="confidence-badge conf-a">A级</span>`

#### Battle 审查

Markdown 中的审查层段落：
```markdown
### 异议 N：标题
...
```

转换为 `.battle-auditor`，紧跟的执行层回应转换为 `.battle-executor`。

#### 阶段标签

Markdown 中的 `[阶段A]` → `<span class="stage-tag stage-a">阶段A</span>`
Markdown 中的 `[阶段B]` → `<span class="stage-tag stage-b">阶段B</span>`

#### 风险等级

Markdown 中的风险评级段落 → 对应 `.risk-high` / `.risk-medium` / `.risk-low`

---

## 四、CSS 变量替换

skeleton.html 中的 {{TOKEN}} 占位符必须全部替换。

### CSS 变量（来自 color-themes/*.yml）
完整列表见 `color-themes/mckinsey-navy.yml`（默认）

### 内容变量
- `{{TITLE}}` — 报告标题
- `{{PRODUCT_CODE}}` — 产品编号
- `{{PRODUCT_EN}}` — 英文名
- `{{PRODUCT_CN}}` — 中文名
- `{{COMPANY_NAME}}` — 公司名称
- `{{CASE_CODE}}` — 案件代号
- `{{SKILL_CODE}}` — 评估技能
- `{{BUSINESS_UNIT}}` — 业务主体
- `{{DATE}}` — 评估日期
- `{{RATING}}` — 综合评级
- `{{RATING_SHORT}}` — 推荐结论
- `{{TOC_ITEMS}}` — 目录 HTML
- `{{CHAPTERS}}` — 章节内容 HTML
- `{{badge-radius}}` — 固定值 `3px`

### 验证
替换后必须检查：`grep -c '{{' output.html` → 结果必须为 **0**

---

## 五、生成流程

1. 读取 `skeleton.html`
2. 根据用户指定的配色读取 `color-themes/*.yml`（默认 mckinsey-navy）
3. 将所有 Token 值替换到骨架 CSS 中
4. 解析 Markdown 报告：
   - 提取封面元信息（案件代号、产品名、公司等）
   - 按一级标题拆分章节
   - 生成 TOC
   - 转换 CMS 专属组件（Gate 卡、置信度、Battle）
5. 替换 {{TOC_ITEMS}} 和 {{CHAPTERS}}
6. 验证零残留 {{TOKEN}}
7. 上传到 Doc Viewer

---

## 六、常见错误

| 错误 | 修复 |
|------|------|
| Gate 卡用 blockquote | 必须用 `.gate-card` + 状态类 |
| 置信度用纯文本 | 必须用 `.confidence-badge` |
| Battle 审查不分层 | 必须用 `.battle-auditor` + `.battle-executor` |
| 缺少 Gate 汇总表 | 综合评估必须包含汇总表 |
| 混用风格 03 封面 | CMS 封面有不同字段 |
