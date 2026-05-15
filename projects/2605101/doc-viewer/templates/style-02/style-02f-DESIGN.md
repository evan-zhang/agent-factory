---
version: alpha
name: "02-F: Industry Case Cards"
description: "案例/行业卡片风 — 行业案例页、解决方案场景页、客户应用页"
colors:
  primary: "#C97842"
  secondary: "#34A853"
  tertiary: "#FBBC05"
  accent: "#EA4335"
  text-primary: "#202124"
  text-body: "#5F6368"
  bg-white: "#FFFFFF"
  bg-light: "#F8F9FA"
typography:
  card-heading:
    fontFamily: "Inter"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3
  card-body:
    fontFamily: "Inter"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  section-title:
    fontFamily: "Inter"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.5px
  card-tag:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 600
    letterSpacing: 0.06em
rounded:
  none: 0px
  sm: 2px
spacing:
  sm: 16px
  md: 32px
  lg: 48px
  page-h: 96px
  page-v: 72px
components:
  case-card:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.none}"
    height: 100%
  card-image:
    backgroundColor: "{colors.bg-light}"
    height: 200px
    width: 100%
  card-content:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.text-body}"
    padding: "{spacing.md}"
  card-tag-label:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.primary}"
    typography: "{typography.card-tag}"
---

## Overview

行业案例展示页。白底、顶部标题、下方 3 列案例卡片。每张卡片包含图片+小标题+简短说明。图片比例统一、内容密度适中。

**视觉关键词：** 三列卡片、图片在上、标题+简短正文、行业场景、企业案例。

## Layout

顶部标题区 + 下方三列等宽卡片网格（1fr 1fr 1fr），gap 32px。每张卡片结构：图片区（200px 高）→ 内容区（标签 + 标题 + 简短说明）。

内边距 72px 96px，max-width 1440px。

## Components

**Case Card：** 白底卡片，无圆角，底部 4px 蓝色线（#C97842）。图片统一滤镜处理（brightness(0.95) contrast(1.02) saturate(0.9)），保持视觉一致性。

## Do's and Don'ts

**Do：**
- 卡片图片使用统一比例和滤镜
- 每张卡片文字控制在 2-3 行
- 用标签标注行业分类

**Don't：**
- 不要给卡片加阴影和圆角
- 不要放太多文字在卡片里
- 不要使用不一致的图片比例
