---
version: alpha
name: "02-C: Consulting Report Content Page"
description: "白底咨询报告内容页 — 正文分析页、趋势解释页、方案说明页"
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
  content-title:
    fontFamily: "Inter"
    fontSize: 36px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -1px
  body-md:
    fontFamily: "Inter"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.8
  side-caption:
    fontFamily: "Inter"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.5
  label-caps:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 600
    letterSpacing: 0.08em
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
  content-title-block:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.primary}"
    typography: "{typography.content-title}"
    padding: "{spacing.sm}"
  footer-bar:
    backgroundColor: "{colors.primary}"
    height: 4px
    width: 100%
  inline-tag:
    backgroundColor: "{colors.bg-white}"
    textColor: "{colors.primary}"
    typography: "{typography.label-caps}"
---

## Overview

咨询公司报告正文页。大面积白底、左侧标题+正文、右侧图片/图表/数据。内容分栏明显、页面干净克制、重点文字使用主题色。

**视觉关键词：** 左文右图、双栏布局、强留白、少量正文、页脚色带、小标签。

## Layout

双栏等宽布局（1fr 1fr），gap 72px。左侧放标题和正文，右侧放图片、图表或数据卡片。底部 4px 主题色横条。

内边距 72px 96px，max-width 1440px。

## Colors

标题使用主题色 #1A73E8。正文使用中灰 #5F6368。背景纯白 #FFFFFF。

## Components

**Content Title Block：** 标题区，文字使用主题蓝色。
**Footer Bar：** 底部 4px 色条，比封面的 6px 更细，保持轻盈感。
**Inline Tag：** 正文中的小标签，蓝色大写字母，用于标注类别或来源。

## Do's and Don'tts

**Do：**
- 文字克制，每段不超过 3 行
- 右侧图片/图表作为视觉补充
- 用标签标注关键信息来源

**Don't：**
- 不要做成密集的长文页
- 不要两侧都放大量文字
- 不要使用复杂边框和装饰线
