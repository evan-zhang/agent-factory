---
version: alpha
name: "02-B: Full-bleed Chapter Hero"
description: "大图 Hero 章节封面风 — 章节首页、趋势介绍页、核心观点展示页"
colors:
  primary: "#C97842"
  secondary: "#34A853"
  tertiary: "#FBBC05"
  accent: "#EA4335"
  text-primary: "#202124"
  text-body: "#5F6368"
  bg-white: "#FFFFFF"
typography:
  hero-title:
    fontFamily: "Inter"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: -2px
  hero-subtitle:
    fontFamily: "Inter"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.6
  chapter-number:
    fontFamily: "Inter"
    fontSize: 120px
    fontWeight: 800
    lineHeight: 1
    letterSpacing: -4px
  label-caps:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 600
    letterSpacing: 0.1em
rounded:
  none: 0px
spacing:
  sm: 16px
  md: 32px
  lg: 48px
  page-h: 96px
  page-v: 72px
components:
  hero-overlay:
    backgroundColor: "#000000"
    textColor: "#FFFFFF"
    height: 100vh
    width: 100%
  bottom-bar:
    backgroundColor: "{colors.primary}"
    height: 6px
    width: 100%
---

## Overview

电影海报感的章节封面。整页大图作为背景，轻微暗色遮罩（rgba(0,0,0,0.25)），左下角超大白色标题，右上角有大章节编号（极低透明度 0.15，装饰性）。顶部 1px 白色细线、底部 6px 主题色横条。

**视觉关键词：** 大图铺满、左下大标题、右上章节号、底部色带、图片暗化、电影海报感。

## Colors

底部色条按章节切换主题色：暖橙 #C97842、绿 #34A853、黄 #FBBC05、红 #EA4335。

遮罩层使用 rgba(0,0,0,0.25) 保持图片可读性。标题使用白色。

## Layout

图片铺满整个视口（100vh）。标题定位于左下角，章节编号定位于右上角。顶部 1px 白色细线，底部 6px 主题色横条。

内边距 72px 96px。

## Components

**Hero Overlay：** 全屏暗色遮罩层，承载白色文字。
**Bottom Bar：** 6px 主题色横条，随章节变色。通过改变 backgroundColor 切换暖橙/绿/黄/红。

## Do's and Don'ts

**Do：**
- 使用高质量商业摄影
- 图片暗化后确保白色文字可读
- 章节编号做装饰用，不喧宾夺主

**Don't：**
- 不要在标题旁边放太多文字
- 不要给遮罩加渐变效果
- 不要让章节编号抢标题的视觉权重
