# BD投前评估报告样式文件 V1.0

> 用途：供 AI 将普通 Markdown 文档转换为与参考 PDF 类似的正式评估报告版式。
> 参考来源：`report_01_SPI1005.pdf`，整体为蓝白商务风、章节化、表格密集、投前评估报告格式。

---

## 1. 整体风格定位

- 风格关键词：专业、审慎、医药BD、投前尽调、内部评估、咨询报告感。
- 主色调：深蓝 + 浅蓝灰 + 白色。
- 视觉基调：克制、清晰、留白充足，不使用花哨装饰。
- 页面适合导出为 PDF，A4 纵向。

---

## 2. 页面基础规格

```yaml
page:
  size: A4
  orientation: portrait
  margin:
    top: 26mm
    bottom: 22mm
    left: 24mm
    right: 24mm
  background: "#FFFFFF"
```

---

## 3. 字体规范

```yaml
font:
  chinese: "PingFang SC, Microsoft YaHei, Noto Sans CJK SC, SimSun"
  english: "Arial, Helvetica, sans-serif"
  body_size: 10.5pt
  line_height: 1.65
  color: "#1F2933"
```

### 字体使用

- 正文：10.5pt，常规字重。
- 一级章节标题：18–20pt，深蓝色，粗体。
- 二级标题：13–14pt，深蓝色，粗体。
- 三级标题：11.5–12pt，深灰色或深蓝色，粗体。
- 表格正文：9–10pt。
- 注释/参考：8.5–9pt，灰色。

---

## 4. 颜色系统

```yaml
colors:
  primary_blue: "#0068A8"
  dark_blue: "#004B7A"
  header_blue: "#0066A6"
  light_blue_bg: "#EEF4FA"
  table_alt_bg: "#F3F6FA"
  table_border: "#D6DEE8"
  text_main: "#1F2933"
  text_muted: "#5F6B7A"
  warning_red_bg: "#FDECEA"
  success_green_bg: "#EAF6EF"
  pending_orange: "#C8792A"
```

---

## 5. 封面样式

封面采用极简商务报告格式。

### 封面结构

```markdown
# B D 投 前 评 估 报 告 | 产品中心视角

## SPI-1005（Ebselen / 依布硒）

Sound Pharmaceuticals, Inc.

评估日期：2026年5月  
适用模板：模板三 — 早期创新药引进  
版本：v1.0  
评估视角：产品中心视角（科学 / 注册 / 医学差异化）  
保密等级：内部机密，限参与评估团队阅览
```

### 封面规则

- 主标题使用大字距效果，可通过在中文或英文字符之间增加空格实现。
- 产品名称作为视觉核心，字号高于普通正文。
- 封面不放复杂图形。
- 底部可增加保密等级。

---

## 6. 章节标题样式

一级标题格式：

```markdown
# 第三章 S-1 靶点科学评估
```

渲染规则：

```css
h1 {
  font-size: 20pt;
  font-weight: 700;
  color: #004B7A;
  border-bottom: 2px solid #0068A8;
  padding-bottom: 8px;
  margin-top: 28px;
  margin-bottom: 22px;
}
```

二级标题格式：

```markdown
## 3.1 靶点基础证据强度
```

渲染规则：

```css
h2 {
  font-size: 14pt;
  font-weight: 700;
  color: #0068A8;
  border-left: 4px solid #0068A8;
  padding-left: 10px;
  margin-top: 24px;
  margin-bottom: 12px;
}
```

三级标题格式：

```markdown
### 3.1.1 动物模型验证
```

渲染规则：

```css
h3 {
  font-size: 12pt;
  font-weight: 700;
  color: #1F2933;
  margin-top: 16px;
  margin-bottom: 8px;
}
```

---

## 7. 执行摘要样式

执行摘要应放在正文第一页之后，采用“关键信息表 + 核心结论 + 主要关注 + 建议”的结构。

```markdown
# 执行摘要（EXECUTIVE SUMMARY）

| 项目 | 内容 |
|---|---|
| 产品名称 | SPI-1005（Ebselen / 依布硒） |
| 当前最高研发阶段 | III期 RCT 完成，OLE 进行中 |
| FDA监管资格 | 突破性疗法认定（BTD）+ 快速通道认定（FTD） |
| 核心适应症 | 梅尼埃病；噪声性听力损失；药物性耳毒性 |
| 合作方 | Sound Pharmaceuticals, Inc. |

**核心结论：** ……

**主要关注：** ……

**建议：** ……
```

规则：

- “核心结论 / 主要关注 / 建议”必须加粗开头。
- 结论段控制在 1–2 段。
- 语言偏投委会/立项会风格，避免口语化。

---

## 8. 正文段落规则

```css
p {
  font-size: 10.5pt;
  line-height: 1.65;
  margin: 0 0 10px 0;
  color: #1F2933;
}
```

写作要求：

- 每段 80–180 字为宜。
- 事实、判断、风险分开写。
- 重要判断使用：`核心结论：`、`评估建议：`、`风险提示：`。
- 待补充信息统一写成：`[待补充：具体内容]`。

---

## 9. 列表样式

普通列表：

```markdown
- 第一项；
- 第二项；
- 第三项。
```

编号列表：

```markdown
1. 完成数据室资料索取；
2. 启动 CNIPA 专利检索；
3. 开展 NMPA 注册路径预沟通。
```

规则：

- 每条尽量不超过两行。
- 同一列表中句式保持一致。
- 关键行动清单使用编号列表。

---

## 10. 表格样式

表格是该文档的核心视觉元素。

### 标准表格 Markdown

```markdown
| 评估维度 | 评分（1–5分） | 证据来源 | 风险备注 |
|---|---:|---|---|
| 致病因果证据 | 4 | 动物模型 / 临床数据 | 直接遗传证据尚不充分 |
| 靶点可成药性 | 4 | 化学结构 / 文献 | 已有多适应症临床数据支撑 |
```

### CSS 样式

```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 22px 0;
  font-size: 9.5pt;
}

th {
  background: #0068A8;
  color: #FFFFFF;
  font-weight: 700;
  text-align: left;
  padding: 9px 10px;
  border: 1px solid #0068A8;
}

td {
  padding: 9px 10px;
  border: 1px solid #D6DEE8;
  vertical-align: top;
  line-height: 1.55;
}

tr:nth-child(even) td {
  background: #F3F6FA;
}
```

---

## 11. 特殊表格：三级验收标准

用于“必达标准 / 参考标准 / 否决触发条件”类矩阵。

```markdown
| 评估维度 | 必达标准（不达即暂停） | 参考标准（允许条件性通过） | 否决触发条件 |
|---|---|---|---|
| 临床有效性 | …… | …… | …… |
| 安全性 | …… | …… | …… |
```

样式规则：

```css
.acceptance-table th:nth-child(2) { background: #4F9D69; }
.acceptance-table th:nth-child(3) { background: #0068A8; }
.acceptance-table th:nth-child(4) { background: #C94C4C; }
.acceptance-table td:nth-child(2) { background: #EAF6EF; }
.acceptance-table td:nth-child(4) { background: #FDECEA; }
```

---

## 12. 风险 / 否决项样式

用于一票否决清单。

```markdown
> **V1 — 活性成分安全性黑盒警告**  
> III期 CSR 或数据包中存在系统性严重安全性信号，且无明确风险缓解措施。
```

样式：

```css
blockquote {
  border-left: 5px solid #0068A8;
  background: #F3F6FA;
  padding: 10px 14px;
  margin: 14px 0;
  color: #1F2933;
}
```

高风险否决项可使用：

```html
<div class="veto-box">
<strong>V1 — 活性成分安全性黑盒警告</strong><br>
III期 CSR 或数据包中存在系统性严重安全性信号，且无明确风险缓解措施。
</div>
```

```css
.veto-box {
  border-left: 5px solid #C94C4C;
  background: #FDECEA;
  padding: 12px 14px;
  margin: 14px 0;
  line-height: 1.6;
}
```

---

## 13. 标签与状态文本

统一状态表达：

```yaml
status_terms:
  pending: "[待补充]"
  to_confirm: "[待确认]"
  to_model: "[待建模]"
  conditional_go: "条件性推进（Conditional Go）"
  no_go: "暂停 / 否决"
```

样式：

```css
.pending {
  color: #C8792A;
  font-style: italic;
  font-weight: 600;
}
```

---

## 14. 页眉页脚

页脚建议：

```text
{项目名称} BD投前评估报告 v{版本号} | {日期} | 产品中心内部机密文件 | {合作方名称}
```

样式：

```css
footer {
  font-size: 8.5pt;
  color: #5F6B7A;
  border-top: 1px solid #D6DEE8;
  padding-top: 6px;
}
```

---

## 15. 推荐 Markdown 文档结构

```markdown
# B D 投 前 评 估 报 告 | 产品中心视角

## 产品名称

合作方名称

评估日期：  
适用模板：  
版本：  
评估视角：  
保密等级：  

\pagebreak

# 执行摘要（EXECUTIVE SUMMARY）

| 项目 | 内容 |
|---|---|

**核心结论：**  
**主要关注：**  
**建议：**  

\pagebreak

# 第一章 产品类型定义与引进场景

## 1.1 产品类型认定

## 1.2 典型引进场景描述

# 第二章 核心差异化重点

# 第三章 S-1 靶点科学评估

# 第四章 S-2 候选化合物评估

# 第五章 S-3 临床数据解读

# 第六章 S-4 中国市场与竞争格局评估

# 第七章 S-5 中国注册策略评估

# 第八章 S-6 财务评估框架

# 第九章 S-7 专利与知识产权评估

# 第十章 S-8 合作方评估

# 第十一章 S-9 生产与供应链评估

# 第十二章 一票否决检查表

# 第十三章 三级验收标准

# 第十四章 快速启动清单

# 附录

# 参考文献
```

---

## 16. AI 转换指令模板

把下面这段直接给 AI 使用：

```text
请将我提供的 Markdown 文档转换为一份正式的 BD 投前评估报告。

样式要求：
1. 使用 A4 纵向 PDF 报告版式，整体风格为深蓝 + 白色 + 浅蓝灰的医药BD尽调报告风格。
2. 一级标题使用深蓝色、大字号、下划线分隔；二级标题使用左侧蓝色竖线。
3. 所有表格使用深蓝色表头、白字、浅蓝灰隔行底色、细边框。
4. 执行摘要采用“关键信息表 + 核心结论 + 主要关注 + 建议”的结构。
5. 一票否决项使用醒目的浅红或浅蓝提示框。
6. 三级验收标准表中，“必达标准”使用浅绿色背景，“否决触发条件”使用浅红色背景。
7. 正文保持专业、审慎、投委会汇报口吻，不要口语化。
8. 所有“待补充/待确认/待建模”内容用橙色斜体突出。
9. 页脚统一为：项目名称 BD投前评估报告 v版本号 | 日期 | 产品中心内部机密文件 | 合作方名称。
10. 输出为适合导出 PDF 的 HTML 或 Word 文档。
```

---

## 17. 可直接使用的 HTML/CSS 样式骨架

```html
<style>
@page {
  size: A4;
  margin: 26mm 24mm 22mm 24mm;
}

body {
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.65;
  color: #1F2933;
  background: #FFFFFF;
}

h1 {
  font-size: 20pt;
  font-weight: 700;
  color: #004B7A;
  border-bottom: 2px solid #0068A8;
  padding-bottom: 8px;
  margin-top: 28px;
  margin-bottom: 22px;
}

h2 {
  font-size: 14pt;
  font-weight: 700;
  color: #0068A8;
  border-left: 4px solid #0068A8;
  padding-left: 10px;
  margin-top: 24px;
  margin-bottom: 12px;
}

h3 {
  font-size: 12pt;
  font-weight: 700;
  color: #1F2933;
  margin-top: 16px;
  margin-bottom: 8px;
}

p {
  margin: 0 0 10px 0;
}

ul, ol {
  margin-top: 6px;
  margin-bottom: 12px;
  padding-left: 22px;
}

li {
  margin-bottom: 6px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 22px 0;
  font-size: 9.5pt;
}

th {
  background: #0068A8;
  color: #FFFFFF;
  font-weight: 700;
  text-align: left;
  padding: 9px 10px;
  border: 1px solid #0068A8;
}

td {
  padding: 9px 10px;
  border: 1px solid #D6DEE8;
  vertical-align: top;
  line-height: 1.55;
}

tr:nth-child(even) td {
  background: #F3F6FA;
}

blockquote {
  border-left: 5px solid #0068A8;
  background: #F3F6FA;
  padding: 10px 14px;
  margin: 14px 0;
}

.veto-box {
  border-left: 5px solid #C94C4C;
  background: #FDECEA;
  padding: 12px 14px;
  margin: 14px 0;
  line-height: 1.6;
}

.pending {
  color: #C8792A;
  font-style: italic;
  font-weight: 600;
}

.page-break {
  page-break-after: always;
}

.footer {
  font-size: 8.5pt;
  color: #5F6B7A;
  border-top: 1px solid #D6DEE8;
  padding-top: 6px;
  margin-top: 30px;
}
</style>
```
