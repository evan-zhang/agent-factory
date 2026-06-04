---
version: "1.0"
name: "13: 麦肯锡通用报告（Markdown→HTML 程序化渲染）"
description: "将任意 Markdown 报告转为麦肯锡风格 HTML。只做渲染不改结构，Python 程序化生成，不需要 AI 手写 HTML"
colors:
  navy: "#071E41"
  blue: "#0B5CAB"
  blue-2: "#174A7C"
  cyan: "#00A3E0"
  ink: "#111827"
  text: "#243041"
  muted: "#5D6878"
  line: "#D8DEE8"
  soft: "#F6F8FB"
  white: "#FFFFFF"
  page-bg: "#EDEFF3"
  table-header-bg: "#071E41"
  table-alt-bg: "#F7F9FC"
  code-bg: "#F8FAFD"
  blockquote-bg: "#F4F7FB"
  blockquote-border: "#00A3E0"
  code-border: "#0B5CAB"
  section-border: "#071E41"
typography:
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, PingFang SC, Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif"
    fontSize: 34px
    fontWeight: 700
    lineHeight: 1.25
    color: "#FFFFFF"
  subtitle:
    fontSize: 16px
    lineHeight: 1.72
    color: "#F4F7FB"
  h2:
    fontSize: 25px
    fontWeight: 700
    lineHeight: 1.4
    color: "#071E41"
  h3:
    fontSize: 18px
    fontWeight: 700
    color: "#174A7C"
  body:
    fontSize: 16px
    lineHeight: 1.72
    color: "#243041"
  code:
    fontSize: 14px
    lineHeight: 1.68
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
layout:
  maxWidth: 1160px
  contentPadding: 48px
  pageMargin: 28px
features:
  - "程序化 Markdown→HTML 转换（Python 脚本）"
  - "保留原始章节结构，不强制套模板"
  - "自动生成双栏可点击目录"
  - "图片 Base64 内嵌，转发不丢图"
  - "打印友好（@media print 优化）"
  - "响应式（780px 断点）"
  - "支持表格、代码块、引用块、流程图文本"
---

# 风格 13 — 麦肯锡通用报告（Markdown→HTML 程序化渲染）

## 设计理念

咨询汇报风格，克制干净。深蓝主色调，黑白灰为辅，少量亮蓝强调色。

适合管理层汇报、项目方案、会议纪要、调研报告等任意结构的长文档。

## 核心原则

**只做渲染，不改结构。** 保留用户 Markdown 原有章节顺序，不强制套固定模板。

## 与其他风格的区别

- 其他 12 种风格：AI 读取 design token + skeleton.html，手写 HTML
- 风格 13：Python 脚本直接把 Markdown 转成 HTML，不需要 AI 参与 HTML 生成

## 视觉特征

- 主色：深蓝 #071E41（标题栏、表格头、章节下划线）
- 强调色：亮蓝 #00A3E0（标题栏底边线、引用块左边线）
- 背景：浅灰 #EDEFF3（页面底色）
- 内容底色：白色（容器卡片）
- 表格：深蓝表头白字，偶数行浅蓝底
- 代码/流程块：浅灰底 + 蓝色左边框
- 目录：浅灰卡片，双栏排列
- 页面宽度：约 1160px

## 组件规范

### 标题栏
- 深蓝背景，白色大标题（34px）
- 底部 6px 亮蓝边线
- 副标题区域为稍浅深蓝（#102B57）

### 目录
- 浅灰背景卡片
- "目录" 二级标题
- 有序列表，双栏排列
- 链接色为 #174A7C

### 章节（h2）
- 深蓝色，25px
- 底部 2px 深蓝实线下划线
- 间距：上 38px 下 16px

### 表格
- 顶部 3px 深蓝边线
- 表头深蓝背景白字
- 偶数行浅蓝底
- 首列深蓝加粗（22% 宽度）

### 引用块
- 浅蓝灰背景
- 左侧 5px 亮蓝边线

### 代码块
- 浅灰背景 + 蓝色左边框（5px）
- text/flow 类型特殊渲染为流程说明样式

### 图片
- 居中，灰色背景框
- 底部灰色说明文字
- 默认 Base64 内嵌

## Do's and Don'ts

### ✅ Do
- 保留用户原始 Markdown 结构
- 自动从 ## 标题生成目录
- 图片默认内嵌为 Base64
- 响应式适配移动端

### ❌ Don't
- 不要强制套固定章节
- 不要自动补"背景、目标、方案"等章节
- 不要重写用户结论或删掉"待补充"
- 不要使用卡通风、营销海报风或过度装饰
