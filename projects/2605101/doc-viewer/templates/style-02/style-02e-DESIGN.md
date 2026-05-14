---
version: alpha
name: "02-E: Insight Metrics Bubble"
description: "数据洞察大数字风 — 数据洞察页、关键指标页、统计结论页"
colors:
  primary: "#1A73E8"
  secondary: "#34A853"
  tertiary: "#FBBC05"
  accent: "#EA4335"
  text-primary: "#202124"
  text-body: "#5F6368"
  text-muted: "#9AA0A6"
  bg-white: "#FFFFFF"
  bg-light: "#F8F9FA"
typography:
  metric-number:
    fontFamily: "Inter"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: -2px
  section-title:
    fontFamily: "Inter"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.5px
  metric-label:
    fontFamily: "Inter"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.5
  body-md:
    fontFamily: "Inter"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
rounded:
  full: 999px
  sm: 2px
spacing:
  sm: 16px
  md: 32px
  lg: 48px
  xl: 72px
  page-h: 96px
  page-v: 72px
components:
  bubble-green:
    backgroundColor: "#EBF5EC"
    textColor: "{colors.secondary}"
    rounded: "{rounded.full}"
    size: 200px
  bubble-yellow:
    backgroundColor: "#FDF6E0"
    textColor: "{colors.tertiary}"
    rounded: "{rounded.full}"
    size: 200px
  bubble-red:
    backgroundColor: "#FCEDEB"
    textColor: "{colors.accent}"
    rounded: "{rounded.full}"
    size: 200px
  bubble-blue:
    backgroundColor: "#E8F0FE"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    size: 200px
---

## Overview

数据洞察页。白底、右侧或中间放大数字、数字放在半透明圆形气泡中。页面文字很少，数字极大成为视觉中心。

**视觉关键词：** 大数字、半透明圆形、气泡分布、极简统计页、数据即主角。

## Colors

气泡背景使用极低饱和度的主题色浅色版本。数字使用对应的实色（绿/黄/红/蓝）。

## Layout

左侧短标题和简短说明，右侧展示 2-3 个关键数据气泡。气泡尺寸统一（200px），通过位置和颜色区分。

内边距 72px 96px，max-width 1440px。

## Components

**Bubble（绿/黄/红/蓝）：** 200px 正圆，浅色背景+对应实色文字。内含大数字（64px/700）和简短标签。

## Do's and Don'ts

**Do：**
- 让数字成为页面绝对主角
- 气泡数量控制在 2-4 个
- 每个数字配一句简短解释

**Don't：**
- 不要在气泡里放长文本
- 不要使用不透明的色块
- 不要加坐标轴和复杂图表
