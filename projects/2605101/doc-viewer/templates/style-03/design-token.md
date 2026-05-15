---
version: alpha
name: "03: BD Pre-Investment Assessment Report"
description: "BD投前评估报告 — 深蓝商务风、A4纵向、表格密集、章节化、适合导出PDF/Word"
colors:
  primary: "#0068A8"
  primary-dark: "#004B7A"
  primary-header: "#0066A6"
  light-warm-bg: "#F7EFE7"
  table-alt-bg: "#F3F6FA"
  table-border: "#D6DEE8"
  text-main: "#1F2933"
  text-muted: "#5F6B7A"
  warning-red-bg: "#FDECEA"
  warning-red-border: "#C94C4C"
  success-green-bg: "#EAF6EF"
  success-green-header: "#3D8B5E"
  pending-orange: "#C8792A"
  bg-white: "#FFFFFF"
  footer-border: "#D6DEE8"
typography:
  cover-title:
    fontFamily: "PingFang SC, Arial"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: 0.15em
  cover-product:
    fontFamily: "PingFang SC, Arial"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
  cover-meta:
    fontFamily: "PingFang SC, Arial"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.8
  h1:
    fontFamily: "PingFang SC, Arial"
    fontSize: 27px
    fontWeight: 700
    lineHeight: 1.3
  h2:
    fontFamily: "PingFang SC, Arial"
    fontSize: 19px
    fontWeight: 700
    lineHeight: 1.4
  h3:
    fontFamily: "PingFang SC, Arial"
    fontSize: 16px
    fontWeight: 700
    lineHeight: 1.4
  body-md:
    fontFamily: "PingFang SC, Arial"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.65
  table-text:
    fontFamily: "PingFang SC, Arial"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.55
  table-header:
    fontFamily: "PingFang SC, Arial"
    fontSize: 13px
    fontWeight: 700
    lineHeight: 1.4
  footnote:
    fontFamily: "PingFang SC, Arial"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 1.5
  pending-label:
    fontFamily: "PingFang SC, Arial"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.65
rounded:
  none: 0px
  sm: 2px
spacing:
  xs: 4px
  sm: 6px
  md: 10px
  lg: 14px
  xl: 22px
  section-top: 28px
components:
  table-header-cell:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    padding: "9px 10px"
  table-body-cell:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.text-main}"
    padding: "9px 10px"
  table-body-cell-alt:
    backgroundColor: "{colors.table-alt-bg}"
    textColor: "{colors.text-main}"
    padding: "9px 10px"
  acceptance-must:
    backgroundColor: "{colors.success-green-header}"
    textColor: "#FFFFFF"
    padding: "9px 10px"
  acceptance-must-body:
    backgroundColor: "{colors.success-green-bg}"
    textColor: "{colors.text-main}"
    padding: "9px 10px"
  acceptance-veto:
    backgroundColor: "{colors.warning-red-border}"
    textColor: "#FFFFFF"
    padding: "9px 10px"
  acceptance-veto-body:
    backgroundColor: "{colors.warning-red-bg}"
    textColor: "{colors.text-main}"
    padding: "9px 10px"
  veto-box:
    backgroundColor: "{colors.warning-red-bg}"
    textColor: "{colors.text-main}"
    padding: "12px 14px"
  info-blockquote:
    backgroundColor: "{colors.table-alt-bg}"
    textColor: "{colors.text-main}"
    padding: "10px 14px"
---

## Overview

BD 投前评估报告样式。专业、审慎、医药BD尽调风格。深蓝+白色+浅蓝灰配色，克制清晰，适合导出为 A4 纵向 PDF 或 Word 文档。

与 style-01/02 的展示型网页不同，这是**文档输出型**：不需要 Tailwind，不需要动效，需要精确的 @page 设置、表格密集排版、章节结构化。

## Colors

深蓝色体系为主色。表格表头深蓝底白字，正文白底隔行浅蓝灰，否决项浅红底，必达项浅绿底。

- **Primary (#0068A8)：** 主暖橙色，表头、标题装饰线、二级标题
- **Primary Dark (#004B7A)：** 一级标题文字色
- **Light Warm BG (#F7EFE7)：** 高亮区块背景
- **Table Alt (#F3F6FA)：** 表格隔行底色
- **Warning Red (#FDECEA)：** 否决项背景，配合 #C94C4C 红色边框
- **Success Green (#EAF6EF)：** 必达标准背景
- **Pending Orange (#C8792A)：** 待补充/待确认标签

## Typography

**重要：token 中使用 px 单位是为了兼容 DESIGN.md 规范校验。生成 HTML 时，Agent 应将 px 替换为 pt 单位以适配 A4 打印。对应关系：32px→24pt, 27px→20pt, 24px→18pt, 19px→14pt, 16px→12pt, 15px→11pt, 14px→10.5pt, 13px→9.5pt, 11px→8.5pt。**

中文字体优先 PingFang SC，英文 Arial。不使用 Inter/Google Sans——这是文档而非网页。

正文 10.5pt（14px）/1.65 行距。一级标题底部 2px 蓝色线，二级标题左侧 4px 蓝色竖线。表格正文缩小到 9.5pt。页脚 8.5pt。

## Layout

A4 纵向，@page margin 26mm/24mm/22mm/24mm。不使用 max-width——宽度就是 A4 纸宽。

页面结构：封面 → 执行摘要 → 章节正文（1-14章）→ 附录 → 参考文献。章节间使用 `page-break-after: always` 分页。

**与 style-01/02 的核心区别：** 不使用 12 列 Grid，不使用 flexbox 居中，不使用 Tailwind。纯文档流排版。

## Elevation & Depth

不使用阴影和渐变。层次感通过边框、背景色差异和边距实现。

## Shapes

不使用圆角（border-radius: 0）。所有元素保持直角，符合正式文档规范。

## Components

**Table Header Cell：** 深蓝底白字，9.5pt 粗体，左对齐。
**Table Body Cell：** 白底/浅蓝灰隔行，9.5pt 常规，垂直顶部对齐。
**Acceptance Must（必达标准）：** 绿色表头（#3D8B5E，比原 #4F9D69 更深以满足 WCAG AA）+ 浅绿体。
**Acceptance Veto（否决触发）：** 红色表头 + 浅红体。
**Veto Box：** 左侧 5px 红色竖线 + 浅红背景，用于一票否决项。
**Info Blockquote：** 左侧 5px 蓝色竖线 + 浅蓝灰背景，用于引述和要点。

## Do's and Don'ts

**Do：**
- 使用 pt 而非 px 作为 CSS 字号单位（适配打印）
- 表格宽度 100%，border-collapse
- 用 page-break-after 分页
- 章节标题用"第X章"格式
- 待补充内容用橙色斜体标注
- 封面标题用 letter-spacing 加大字距
- 执行摘要用"关键信息表+核心结论+主要关注+建议"结构

**Don't：**
- 不要使用 TailwindCSS
- 不要使用动画和过渡效果
- 不要使用 web 字体（Inter、Google Fonts）
- 不要使用 viewport 单位（vh、vw）
- 不要使用花哨的装饰
- 不要偏离 A4 页面尺寸
- 不要在封面放复杂图形
