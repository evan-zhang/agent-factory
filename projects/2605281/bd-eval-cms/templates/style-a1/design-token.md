---
version: "0.9.0"
name: "A1: CMS BD 通用模板内核"
description: "CMS BD 通用模板内核 Style A1 — 支持多 Profile（A-1/A-5/A-7 等），从单一 A-1 覆盖测试升级为通用模板体系。完整覆盖 A-1 原始模板结构能力（密级栏、互斥规则框、One-pager、Gate 1-6、Battle 对抗机制）+ 通用组件（封面/术语表/参考文献/水印/页眉页脚/置信度/阶段标签）+ Profile 机制（业务场景差异化配置）"
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
  # 职能层色彩
  role-bd: "#1a3a5c"
  role-tech: "#2563eb"
  role-comm: "#7c3aed"
  role-support: "#059669"
  role-ai: "#db2777"
  role-decision: "#dc2626"
  role-pmo: "#d97706"
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

CMS 投前评估报告 Style A1，完整覆盖 A-1 原始模板需求和 TRTL-729 示例结构。

与 Style 12 共享麦肯锡深蓝视觉体系，但扩展了以下结构能力：
- classification-bar 密级与呈报对象栏
- 多种特殊框（conclusion/risk/neutral/veto/conflict/exclusion）
- glossary-table 术语与缩写表
- 业务主体互斥规则约束框
- One-pager 终局先立结构
- 七色/四职能层视觉体系
- 完整的 Gate 1-6 承载能力

## Colors

以麦肯锡深蓝（#1a3a5c）为默认主色。支持多主题切换：
- **mckinsey-navy**：深蓝 #1a3a5c — 经典咨询风格（默认）
- **investment-blue**：投资蓝 #1D4ED8 — 投行报告风格
- **burgundy-wine**：酒红 #7B2D3B — 老牌药企风格
- **forest-teal**：青绿 #1B6B5A — 现代药企/ESG 风格

**职能层色彩**（七色体系）：
- role-bd: #1a3a5c（BD 深蓝）
- role-tech: #2563eb（技术蓝）
- role-comm: #7c3aed（商务紫）
- role-support: #059669（支持绿）
- role-ai: #db2777（AI 粉红）
- role-decision: #dc2626（决策红）
- role-pmo: #d97706（PMO 琥珀）

状态色在所有配色中保持一致：
- 通过（Pass）：绿 #15803D
- 条件通过（Conditional）：琥珀 #92400E
- 停止/否决（Stop/Veto）：红 #DC2626
- 信息冲突（Conflict）：黄 #F59E0B

## Typography

**单位规则**：所有字号使用 pt 单位（适配 A4 打印）。

中文字体优先 PingFang SC，英文 Arial。正文 10.5pt / 1.65 行距。

## Layout

A4 纵向，@page margin 26mm/24mm/22mm/24mm。纯文档流排版，不使用 Tailwind。

页面结构：封面 → 密级栏 → 目录 → 正文章节 → 附录 → 参考文献。章节间 `page-break-after: always`。

## Style A1 专属组件

### 密级与呈报对象栏（.classification-bar）
页面顶部固定栏，显示：
- 左侧：密级标识（内部机密）
- 右侧：呈报对象（投委会成员 | 评估团队）

### 结论框（.conclusion-box）
绿色左边框 + 浅绿背景，用于标记结论性内容。

### 风险框（.risk-box）
红色左边框 + 浅红背景，用于标记风险内容。

### 中立框（.neutral-box）
灰色左边框 + 浅灰背景，用于第三方中立审查内容。

### 一票否决框（.veto-box）
红色醒目边框 + 浅红背景，用于标记一票否决项。

### 冲突框（.conflict-box）
黄色边框 + 浅黄背景，用于标记信息冲突。

### 互斥规则约束框（.exclusion-box）
红色边框 + 浅粉红背景，用于业务主体互斥规则约束。

### 术语表（.glossary-table）
双列表格，左侧术语（深色背景），右侧解释。

### One-pager 结构（.one-pager）
带标题和边框的容器，用于终局先立内容。

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

### 阶段标签（.stage-tag）
- `.stage-a`：阶段 A 标签（绿色）
- `.stage-b`：阶段 B 标签（琥珀色）
- `.stage-c`：阶段 C 标签（红色）

### DRL 优先级（.drl-priority）
- `.drl-p0`：P0 最高优先级（红色）
- `.drl-p1`：P1 中优先级（橙色）
- `.drl-p2`：P2 低优先级（蓝色）

### 风险等级（.risk-*）
- `.risk-high`：高风险（红色）
- `.risk-medium`：中风险（橙色）
- `.risk-low`：低风险（绿色）

## Gate 1-6 承载能力

### Gate 1：前提门
权属/授权链、合作可能性、注册路径、合规资质、数据可得性、主体合法组合。

### Gate 2：证据/技术门
MoA、临床/非临床、BA/PK/PD、统计、CDE/注册沟通、CMC/GMP、数据完整性。

### Gate 3：商业/准入门
患者池、指南/SOC、竞品格局、准入/支付、价格走廊、渠道、院内/院外。

### Gate 4：准入与定价路径（.gate-4-pricing）
NMPA/目标市场监管机构、准入落地时间曲线、支付路径、价格走廊。

### Gate 5：供应链与 CMC（.gate-5-cmc）
供应链策略、CMC、技术转移、质量协议、生产策略。

### Gate 6：交易结构与财务回报（.gate-6-deal）
TS、合同、首付款/里程碑/分成、退出权、IRR/rNPV/回收期。

## 一票否决清单、红旗台账

### 一票否决清单（.veto-list）
红色边框容器，列出所有一票否决项。

### 红旗台账/风险登记表（.risk-ledger）
黄色边框容器，列出所有风险事项。

### 信息冲突附录（.conflict-appendix）
琥珀色边框容器，列出所有信息冲突。

### 参考文献外壳（.references-shell）
灰色边框容器，列出所有参考文献。

## 其他视觉元素

### @page 页眉页脚
使用 @page 规则定义页面边距，第一页无边距。

### caption/figcaption 图表编号样式
斜体，灰色，居中，带编号前缀。

### redacted / watermark-internal
- `.redacted`：涂黑标记
- `.watermark-internal`：内部水印（45度旋转，大字号，低透明度）

## Do's and Don'ts

**Do：**
- 使用 pt 而非 px 作为 CSS 字号单位
- 每个 Gate 章节后必须包含 Gate 结论卡
- 置信度标注使用 .confidence-badge 组件
- Battle 审查使用 .battle-auditor / .battle-executor 双层结构
- 表格宽度 100%，border-collapse
- 用 page-break-after 分页
- 状态色（pass/conditional/stop）保持一致
- 密级栏使用 .classification-bar 固定在顶部

**Don't：**
- 不要使用 TailwindCSS
- 不要使用动画和过渡效果
- 不要使用 web 字体
- 不要使用 viewport 单位（vh、vw）
- 不要在 Gate 结论卡中混用不同状态色
- 不要跳过 Battle 审查章节
- 不要遗漏密级栏