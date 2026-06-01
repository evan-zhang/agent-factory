---
version: "1.0"
name: "12: CMS 康哲药业投前评估报告"
description: "CMS投前评估报告 — 咨询公司风格、A4纵向、Gate结论卡+Battle对抗审查+置信度徽章、适合投委会决策"
colors:
  primary: "#1a3a5c"
  primary-dark: "#0F1B2D"
  primary-light: "#2c5282"
  light-bg: "#EDF2F7"
  table-alt-bg: "#EDF2F7"
  table-border: "#CBD5E1"
  text-main: "#1A1A2E"
  text-muted: "#4A5568"
  pass-green: "#15803D"
  cond-amber: "#92400E"
  fail-red: "#DC2626"
  bg-white: "#F8F9FB"
  footer-border: "#E2E8F0"
typography:
  cover-title:
    fontFamily: "PingFang SC, Arial"
    fontSize: 30pt
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: 0.06em
  cover-product:
    fontFamily: "PingFang SC, Arial"
    fontSize: 18pt
    fontWeight: 600
    lineHeight: 1.3
  cover-meta:
    fontFamily: "PingFang SC, Arial"
    fontSize: 11pt
    fontWeight: 400
    lineHeight: 2.1
  h1:
    fontFamily: "PingFang SC, Arial"
    fontSize: 17pt
    fontWeight: 700
    lineHeight: 1.3
  h2:
    fontFamily: "PingFang SC, Arial"
    fontSize: 12.5pt
    fontWeight: 700
    lineHeight: 1.4
  h3:
    fontFamily: "PingFang SC, Arial"
    fontSize: 11pt
    fontWeight: 700
    lineHeight: 1.4
  body-md:
    fontFamily: "PingFang SC, Arial"
    fontSize: 10.5pt
    fontWeight: 400
    lineHeight: 1.65
  table-text:
    fontFamily: "PingFang SC, Arial"
    fontSize: 9.5pt
    fontWeight: 400
    lineHeight: 1.55
  table-header:
    fontFamily: "PingFang SC, Arial"
    fontSize: 9.5pt
    fontWeight: 700
    lineHeight: 1.4
  footnote:
    fontFamily: "PingFang SC, Arial"
    fontSize: 8.5pt
    fontWeight: 400
    lineHeight: 1.5
  gate-title:
    fontFamily: "PingFang SC, Arial"
    fontSize: 12pt
    fontWeight: 700
    lineHeight: 1.4
  gate-label:
    fontFamily: "PingFang SC, Arial"
    fontSize: 9pt
    fontWeight: 600
    lineHeight: 1.4
  badge-text:
    fontFamily: "PingFang SC, Arial"
    fontSize: 9pt
    fontWeight: 700
    lineHeight: 1.3
rounded:
  none: 0px
  badge: 3px
  card: 4px
spacing:
  xs: 4px
  sm: 6px
  md: 10px
  lg: 14px
  xl: 22px
  section-top: 28px
---

## Overview

CMS（康哲药业）投前评估报告样式。专为 CMS 投前评估体系设计，在风格 03 的文档输出型基础上，新增 Gate 结论卡、Battle 对抗审查、置信度徽章、一票否决框等 CMS 专属组件。

与风格 03 共享 A4 纵向文档输出规范（pt 单位、@page、无 Tailwind、无动画），但组件体系完全不同。

## Colors

以麦肯锡深蓝（#1a3a5c）为默认主色。根据 color-themes 切换：
- **mckinsey-navy**：深蓝 #1a3a5c — 经典咨询风格（默认）
- **investment-blue**：投资蓝 #1D4ED8 — 投行报告风格
- **burgundy-wine**：酒红 #7B2D3B — 老牌药企风格
- **forest-teal**：青绿 #1B6B5A — 现代药企/ESG 风格

状态色在所有配色中保持一致：
- 通过（Pass）：绿 #15803D
- 条件通过（Conditional）：琥珀 #92400E / #B45309
- 停止/否决（Stop/Veto）：红 #DC2626
- 信息冲突（Conflict）：黄 #F59E0B

## Typography

**单位规则**：所有字号使用 pt 单位（适配 A4 打印）。

中文字体优先 PingFang SC，英文 Arial。不使用 Inter/Google Sans。

正文 10.5pt / 1.65 行距。Gate 标题 12pt。置信度徽章 9pt。

## Layout

A4 纵向，@page margin 26mm/24mm/22mm/24mm。纯文档流排版，不使用 Tailwind。

页面结构：封面 → 目录 → 执行摘要 → 各 Gate 章节 → Battle 对抗审查 → 综合结论 → 附录 → 参考文献。章节间 `page-break-after: always`。

## CMS 专属组件

### Gate 结论卡（.gate-card）
每个 Gate 评估后生成的结论卡，左侧色条标识状态：
- `.gate-pass`：绿色 — 通过
- `.gate-conditional`：琥珀色 — 有条件通过
- `.gate-stop`：红色 — 停止

### 置信度徽章（.confidence-badge）
四档置信度，内联标签：
- `.conf-a`：绿色 — 高置信度
- `.conf-b`：蓝色 — 中等置信度
- `.conf-c`：橙色 — 待验证
- `.conf-d`：红色 — 基于假设

### Battle 对抗审查（.battle-*）
双层审查结构：
- `.battle-auditor`：审查层（灰色调）
- `.battle-executor`：执行层（主色调）
- `.battle-dispute`：争议点高亮（黄色）

### 一票否决框（.veto-box）
红色醒目边框 + 浅红背景，用于标记一票否决项。

### 信息冲突框（.conflict-box）
黄色边框 + 浅黄背景，用于标记审查中发现的矛盾数据。

### 阶段标签（.stage-tag）
- `.stage-a`：阶段 A 标签
- `.stage-b`：阶段 B 标签

### DRL 优先级（.drl-priority）
- `.drl-p0`：P0 最高优先级（红色）
- `.drl-p1`：P1 中优先级（橙色）
- `.drl-p2`：P2 低优先级（蓝色）

### 风险等级（.risk-*）
- `.risk-high`：高风险（红色）
- `.risk-medium`：中风险（橙色）
- `.risk-low`：低风险（绿色）

### 中立审查框（.neutral-review）
灰色调，用于第三方中立审查内容。

## Do's and Don'ts

**Do：**
- 使用 pt 而非 px 作为 CSS 字号单位
- 每个 Gate 章节后必须包含 Gate 结论卡
- 置信度标注使用 .confidence-badge 组件
- Battle 审查使用 .battle-auditor / .battle-executor 双层结构
- 表格宽度 100%，border-collapse
- 用 page-break-after 分页
- 状态色（pass/conditional/stop）保持一致，不随主色变化

**Don't：**
- 不要使用 TailwindCSS
- 不要使用动画和过渡效果
- 不要使用 web 字体
- 不要使用 viewport 单位（vh、vw）
- 不要在 Gate 结论卡中混用不同状态色
- 不要跳过 Battle 审查章节
