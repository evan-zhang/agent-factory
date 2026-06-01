---
version: alpha
name: Data & AI Report
description: "企业数据智能白皮书 — Google Cloud / IDC 风格综合报告页面"
colors:
  primary: "#4285F4"
  primary-dark: "#2F6FE4"
  primary-light: "#5B8DEF"
  secondary: "#34A853"
  secondary-dark: "#2FA24A"
  secondary-light: "#43B866"
  tertiary: "#FBBC05"
  tertiary-dark: "#F4B400"
  accent: "#EA4335"
  accent-dark: "#E8453C"
  text-primary: "#1F2937"
  text-body: "#5F6368"
  text-muted: "#6B7280"
  text-subtle: "#9CA3AF"
  bg-white: "#FFFFFF"
  bg-light: "#F5F6F7"
  bg-warm: "#EFEFEF"
  bg-grid: "#E5E7EB"
typography:
  hero-title:
    fontFamily: "Inter"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: -2px
  section-title:
    fontFamily: "Inter"
    fontSize: 36px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -1px
  card-title:
    fontFamily: "Inter"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
  body-lg:
    fontFamily: "Inter"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.7
  body-md:
    fontFamily: "Inter"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
  body-sm:
    fontFamily: "Inter"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0.08em
  data-number:
    fontFamily: "Inter"
    fontSize: 72px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: -3px
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  full: 999px
spacing:
  xs: 8px
  sm: 16px
  md: 32px
  lg: 48px
  xl: 80px
  section: 120px
components:
  hero-overlay:
    backgroundColor: "#2F6FE4"
    textColor: "#FFFFFF"
    height: 100vh
    width: 100%
  color-card:
    backgroundColor: "{colors.primary-dark}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  image-card-bottom:
    backgroundColor: "{colors.secondary}"
    textColor: "#FFFFFF"
    height: 8px
    width: 100%
  data-circle:
    backgroundColor: "#EBF5EC"
    textColor: "{colors.secondary}"
    rounded: "{rounded.full}"
    size: 240px
  section-content:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.text-primary}"
    padding: "{spacing.xl}"
  footer-block:
    backgroundColor: "{colors.bg-light}"
    textColor: "{colors.text-muted}"
    padding: "{spacing.xl}"
---

## Overview

企业级数据智能白皮书风格。视觉语言来自 Google Cloud 2023 Data and AI Trends Report 和 IDC 咨询报告。

不是互联网产品 UI，不是 SaaS 后台。是年度战略报告、AI 趋势白皮书、企业数据治理方案、高管汇报材料的视觉标准。

**关键词：** 极简企业级、Data + AI + Enterprise、大面积留白、强网格系统、杂志化排版。

## Colors

使用 Google 四色作为核心品牌色，配合中性灰和白底。

- **Primary (#4285F4)：** 科技蓝，用于 Hero Banner、主标题区、核心交互
- **Secondary (#34A853)：** 数据绿，用于数据治理、正反馈、安全议题
- **Tertiary (#FBBC05)：** 分析黄，用于 Analytics、BI、强调模块
- **Accent (#EA4335)：** 风险红，用于警告、风险议题、重点突出
- **Text Primary (#1F2937)：** 深墨色，用于标题
- **Text Body (#5F6368)：** 中灰，用于正文
- **Bg White (#FFFFFF)：** 主背景
- **Bg Light (#F5F6F7)：** 区块背景

## Typography

Inter 字体家族。标题极大、超低行距、强压迫感、左对齐。正文克制、行距宽松。

Hero 标题 64px/700，数据数字 72px/700，正文 16px/400。通过字号和字重的极端对比制造视觉层次。

## Layout

12 列 Grid 系统，gap 32px。内容极少：每页一个核心观点、一个视觉焦点、少量文字。

页面结构：Hero 区 → 内容区（左标题+说明 / 右图片/数据/卡片）→ 数据区（大数字 + 解释）→ 结尾区（极简总结、Logo、页脚）。

**留白原则：** padding 不低于 80px 120px，元素之间用空间而非线条分隔。

## Elevation & Depth

不使用阴影和复杂边框。层次感通过背景色差异和空间留白实现。

唯一例外：底部色条（image-card 的 8px solid border-bottom）作为视觉锚点。

## Shapes

卡片无圆角（border-radius: 0），这是 IDC 咨询风格的核心特征。
数据圆使用正圆（999px）。
全局克制圆角使用，保持方块感。

## Components

**Hero Overlay：** 全屏高度，蓝色渐变遮罩（#2F6FE4 到 #4285F4），承载白色大标题。
**Color Card：** 深蓝背景 + 白色文字 + 无圆角 + 无阴影。用于方法论矩阵和重点模块。背景使用 primary-dark (#2F6FE4) 而非 primary，确保与白色文字的 WCAG AA 对比度。
**Image Card Bottom：** 8px 绿色底部色条，作为图片卡片的视觉锚点。
**Data Circle：** 240px 正圆、浅绿色底、绿色数字。用于数据洞察展示。
**Section Content：** 白底主内容区，统一内边距。

## Do's and Don'ts

**Do：**
- 使用真实商业摄影（建筑、飞机、楼梯、城市、企业办公、抽象空间）
- 大面积留白
- 每页一个焦点
- 用 Google 四色做色块
- 图片统一 filter: brightness(0.95) contrast(1.02) saturate(0.9)

**Don't：**
- 不要用卡通插画、二次元
- 不要用赛博朋克、霓虹科技线
- 不要用复杂阴影和边框
- 不要用花哨渐变和过度动画
- 不要用 SaaS 后台风格的 UI 组件
- 不要用超过 fade/slide 的复杂动效
