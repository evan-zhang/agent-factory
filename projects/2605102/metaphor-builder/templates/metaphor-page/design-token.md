---
name: metaphor-page-design-token
version: "0.1.0"
skillcode: metaphor-builder
purpose: 隐喻故事 HTML 页面设计规范（基于风格 11 — 暗色 Linear 系）
---

# Metaphor Page 设计规范

## 风格基线
基于风格 11（暗色 Linear 系）：深色背景、高对比度、极简排版、微动效。

---

## 1. 颜色系统

### 主色板

| Token | 值 | 用途 |
|-------|-----|------|
| --bg-primary | #0a0a0a | 页面背景 |
| --bg-secondary | #111111 | 卡片背景 |
| --bg-elevated | #1a1a1a | 悬浮/高亮区域 |
| --bg-reveal | #0d1117 | 揭晓区域背景（略带蓝调） |
| --text-primary | #fafafa | 主文字 |
| --text-secondary | #a1a1a1 | 次要文字 |
| --text-tertiary | #525252 | 辅助文字 |
| --accent | #ffffff | 强调色 |
| --accent-subtle | rgba(255,255,255,0.06) | 柔和强调 |

### 语义色

| Token | 值 | 用途 |
|-------|-----|------|
| --border-subtle | rgba(255,255,255,0.08) | 微妙边框 |
| --border-default | rgba(255,255,255,0.12) | 默认边框 |
| --glow-reveal | rgba(99,102,241,0.15) | 揭晓区域光晕 |

---

## 2. 字体

| Token | 值 |
|-------|-----|
| --font-sans | -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif |
| --font-serif | 'Georgia', 'Times New Roman', serif |
| --font-mono | 'SF Mono', 'Fira Code', monospace |

### 字号规范

| 元素 | 字号 | 行高 | 字重 |
|------|------|------|------|
| 页面标题 | 2rem | 1.2 | 700 |
| 世界观副标题 | 1.125rem | 1.6 | 400 |
| 故事正文 | 1.0625rem (17px) | 1.8 | 400 |
| 场景分隔标记 | 0.75rem | 1 | 500, uppercase |
| 概念名（揭晓） | 1.75rem | 1.2 | 700 |
| 定义文本 | 1.125rem | 1.6 | 400 |
| 映射表 | 0.875rem | 1.6 | 400 |
| 注释/来源 | 0.75rem | 1.5 | 400 |

### 故事正文使用 serif 字体，其余使用 sans-serif。

---

## 3. 间距系统

基础单位：4px

| Token | 值 | 用途 |
|-------|-----|------|
| --space-xs | 4px | 紧凑间距 |
| --space-sm | 8px | 小间距 |
| --space-md | 16px | 默认间距 |
| --space-lg | 24px | 段落间距 |
| --space-xl | 32px | 区块间距 |
| --space-2xl | 48px | 章节间距 |
| --space-3xl | 64px | 大区块间距 |

### 布局宽度

| Token | 值 |
|-------|-----|
| --max-width-story | 680px |
| --max-width-page | 800px |
| --padding-page | 24px（移动端 16px） |

---

## 4. 页面结构

```
┌─────────────────────────────────┐
│         封面区 (Cover)           │
│   标题 + 世界观一句话描述        │
│         滚动指示器 ↓             │
├─────────────────────────────────┤
│         故事区 (Story)           │
│                                 │
│   ┌─ 场景 1 ───────────────┐   │
│   │  分隔标记               │   │
│   │  故事段落（serif）       │   │
│   └────────────────────────┘   │
│                                 │
│   ┌─ 场景 2 ───────────────┐   │
│   │  分隔标记               │   │
│   │  故事段落               │   │
│   └────────────────────────┘   │
│                                 │
│   ... 更多场景 ...              │
│                                 │
├─────────────────────────────────┤
│       揭晓区 (Reveal)           │
│   特殊背景 + 光晕效果           │
│                                 │
│   概念名称（大字）              │
│   核心定义                      │
├─────────────────────────────────┤
│       解释区 (Interpretation)   │
│                                 │
│   ┌─ 卡片 1：概念本身 ──────┐  │
│   │  定义 + 要点             │  │
│   └────────────────────────┘   │
│                                 │
│   ┌─ 卡片 2：隐喻映射 ──────┐  │
│   │  映射表                  │  │
│   └────────────────────────┘   │
│                                 │
│   ┌─ 卡片 3：理论对应 ──────┐  │
│   │  精确对应 + 简化说明     │  │
│   └────────────────────────┘   │
│                                 │
├─────────────────────────────────┤
│         尾部 (Footer)           │
│   来源标注 + 分享提示           │
└─────────────────────────────────┘
```

---

## 5. 动效规范

### 进入动画

| 元素 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 封面标题 | fade-in + slight-up | 800ms | ease-out |
| 场景分隔标记 | fade-in | 400ms | ease |
| 揭晓区域 | fade-in + scale(0.98→1) | 1000ms | ease-out |

### 滚动触发

- 所有场景区块使用 Intersection Observer
- 进入视口时触发 fade-in + slight-up（translateY: 12px → 0）
- 揭晓区域额外添加 glow 脉冲动画

### 揭晓特效

```css
@keyframes reveal-glow {
  0% { box-shadow: 0 0 0 rgba(99,102,241,0); }
  50% { box-shadow: 0 0 60px rgba(99,102,241,0.15); }
  100% { box-shadow: 0 0 0 rgba(99,102,241,0); }
}
```

### 尊重用户偏好

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

---

## 6. 卡片样式

```css
.interpretation-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}
```

---

## 7. 响应式断点

| 断点 | 宽度 | 调整 |
|------|------|------|
| 移动端 | < 640px | padding 16px, 标题 1.5rem, 卡片纵向堆叠 |
| 平板 | 640-1024px | 保持默认 |
| 桌面 | > 1024px | 最大宽度 680px 居中 |
