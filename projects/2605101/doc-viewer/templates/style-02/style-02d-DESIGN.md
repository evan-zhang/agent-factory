---
version: alpha
name: "02-D: Color Tile Matrix"
description: "彩色模块矩阵风 — 方法论总览、模块清单、趋势列表、产品矩阵"
colors:
  primary: "#C97842"
  secondary: "#34A853"
  tertiary: "#FBBC05"
  accent: "#EA4335"
  tile-5: "#5B8DEF"
  tile-6: "#43B866"
  text-primary: "#202124"
  text-body: "#5F6368"
  bg-white: "#FFFFFF"
typography:
  section-title:
    fontFamily: "Inter"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.5px
  tile-title:
    fontFamily: "Inter"
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.25
  tile-number:
    fontFamily: "Inter"
    fontSize: 14px
    fontWeight: 700
    letterSpacing: 0.05em
  body-md:
    fontFamily: "Inter"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
rounded:
  none: 0px
  sm: 2px
spacing:
  sm: 16px
  md: 32px
  lg: 48px
  xl: 72px
  page-h: 96px
  page-v: 72px
components:
  tile-1:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  tile-2:
    backgroundColor: "{colors.secondary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  tile-3:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  tile-4:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  tile-5:
    backgroundColor: "{colors.tile-5}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  tile-6:
    backgroundColor: "{colors.tile-6}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
---

## Overview

方法论总览页。白底、左侧说明文字、右侧 2×3 彩色模块。每个模块是纯色大卡片、白色大字、无圆角、无阴影。

**视觉关键词：** 2×3 网格、彩色方块、方法论地图、模块编号、左说明右矩阵。

## Layout

页面分为左侧说明区（1fr）和右侧矩阵区（2fr）。矩阵使用 2×3 网格，gap 16px。每个 tile 是纯色方块，无圆角无阴影，内部包含小编号（半透明白色）和白色大标题。

内边距 72px 96px，max-width 1440px。

## Components

**Tile 1-6：** 六个彩色模块，分别使用暖橙/绿/黄/红/浅暖橙/浅绿。每个内含编号和标题。编号使用 14px 白色半透明（rgba(255,255,255,0.7)），标题使用 22px 白色粗体。

## Do's and Don'ts

**Do：**
- 每个模块一个明确的概念
- 编号作为辅助信息，半透明处理
- 保持色块纯色，不加渐变或纹理

**Don't：**
- 不要在色块内放图片
- 不要加圆角和阴影
- 不要在模块内放长文本
