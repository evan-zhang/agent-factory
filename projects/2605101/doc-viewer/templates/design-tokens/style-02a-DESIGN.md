---
version: alpha
name: "02-A: Color Block Editorial Cover"
description: "Google 四色拼贴封面风 — 报告首页、专题入口页、年度趋势报告封面"
colors:
  primary: "#1A73E8"
  secondary: "#34A853"
  tertiary: "#FBBC05"
  accent: "#EA4335"
  text-primary: "#202124"
  text-body: "#5F6368"
  bg-white: "#FFFFFF"
typography:
  cover-title:
    fontFamily: "Inter"
    fontSize: 80px
    fontWeight: 900
    lineHeight: 1.0
    letterSpacing: -4px
  cover-subtitle:
    fontFamily: "Inter"
    fontSize: 20px
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 600
    letterSpacing: 0.1em
rounded:
  none: 0px
  sm: 2px
spacing:
  sm: 16px
  md: 32px
  page-h: 96px
  page-v: 72px
components:
  color-strip:
    backgroundColor: "{colors.primary}"
    height: 80px
    rounded: "{rounded.none}"
  photo-strip:
    backgroundColor: "{colors.bg-white}"
    height: 80px
    rounded: "{rounded.none}"
  cover-title-block:
    textColor: "{colors.text-primary}"
    typography: "{typography.cover-title}"
---

## Overview

杂志封面与品牌海报风格。白色背景、超大黑色标题、Google 四色横向色块、图片被裁切成长条或小矩形。

**视觉关键词：** 横向色块、大标题穿插、图片条带、非对称构图、视觉拼贴。

## Layout

标题和色块/图片条带交替排列，形成拼贴感。标题巨大（80px/900），图片和色块穿插在标题文字之间。非对称构图，左重右轻或上重下轻。

色块和图片条带高度统一（80px），间距极小（8px），形成连续的横向节奏。

内边距 72px 96px，max-width 1440px。

## Colors

使用 Google 四色作为色块：蓝 #1A73E8、绿 #34A853、黄 #FBBC05、红 #EA4335。标题使用 #202124 深黑。背景纯白。

## Components

**Color Strip：** 纯色横向色块，无圆角，高度 80px。使用 Google 四色交替。
**Photo Strip：** 真实商业摄影裁切成横向条带，与色块交替排列。

## Do's and Don'ts

**Do：**
- 让标题字和色块/图片交织
- 保持非对称的不完美感
- 色块用纯色，不加渐变

**Don't：**
- 不要做成对称的网格
- 不要给色块加圆角
- 不要在封面放太多文字
