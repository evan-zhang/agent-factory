# Responsive Specification — 多端适配规范

> 所有风格模板必须遵循本规范，确保在手机、平板、PC 三端均有良好阅读体验。

---

## 1. 响应式设计原则

### 1.1 核心原则

- **移动优先**：先确保移动端可读，再为平板/PC 增强
- **内容优先**：文字大小可读、表格可滚动、图片不变形
- **渐进增强**：不以手机体验为代价换取PC端华丽效果

### 1.2 三端定义

| 端 | 断点 | 屏幕宽度参考 |
|---|---|---|
| 手机 | ≤ 480px | iPhone SE / 小屏 Android |
| 平板 / 大手机 | 481px ~ 768px | iPad / 大屏 Android |
| PC | > 768px | 笔记本 / 台式机 |

---

## 2. 断点设计

### 2.1 标准断点

```css
/* 手机（默认样式，无需媒体查询） */
body { font-size: 9pt; }

/* 平板 */
@media screen and (min-width: 481px) {
  body { font-size: 10pt; }
}

/* PC */
@media screen and (min-width: 769px) {
  body { font-size: 10.5pt; }
}
```

### 2.2 媒体查询写法规范

```css
/* 写法一：小屏优先（推荐） */
/* 基础样式针对小屏，增强样式在大屏 */
@media screen and (min-width: 769px) { ... }

/* 写法二：单独处理大屏 */
/* 先处理小屏，再在大屏覆盖 */
@media screen and (min-width: 769px) { ... }
```

**禁止使用 `max-width` 作为主断点**，因为会导致在大屏幕设备上样式失效。

---

## 3. 各元素响应式规则

### 3.1 页面整体

```css
/* PC */
.page-wrap {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 48px;
}

/* 手机 */
@media screen and (max-width: 768px) {
  .page-wrap { padding: 16px; }
}
```

### 3.2 标题（H1/H2/H3）

```css
/* PC */
h1 { font-size: 17pt; padding: 10px 14px; }
h2 { font-size: 12.5pt; }

/* 手机 */
@media screen and (max-width: 768px) {
  h1 { font-size: 14pt; padding: 8px 10px; }
  h2 { font-size: 11.5pt; }
}
@media screen and (max-width: 480px) {
  h1 { font-size: 13pt; }
}
```

### 3.3 卡片网格

```css
/* PC：多列 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

/* 手机：单列 */
@media screen and (max-width: 768px) {
  .card-grid { grid-template-columns: 1fr; }
}
```

### 3.4 表格（见 table-spec.md）

移动端外层 `.table-wrap` 负责滚动，不压缩列宽。

---

## 4. 触摸交互规范

### 4.1 触摸目标最小尺寸

```css
/* 按钮 / 链接的触摸区域不小于 44×44px */
.btn, .filter-tag, .card {
  min-height: 44px;
  cursor: pointer;
}
```

### 4.2 触摸反馈

```css
.card:active {
  transform: scale(0.98);
  opacity: 0.9;
}
```

---

## 5. 图片响应式

```css
img {
  max-width: 100%;
  height: auto;
  display: block;
}
```

禁止固定宽高导致图片变形。

---

## 6. 打印样式（Print）

```css
@media print {
  /* 隐藏非内容元素 */
  .filter-bar, .toc-section { display: none; }

  /* 背景色打印 */
  th { -webkit-print-color-adjust: exact; }

  /* 白色背景 */
  body { background: #FFF; }

  /* 去掉阴影 */
  .card, .metric-card { box-shadow: none; }

  /* 链接打印真实 URL */
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 8pt;
    color: #666;
  }
}
```

---

## 7. 常见布局响应式对照

| 元素 | PC（>768px） | 手机（≤768px） |
|------|------------|--------------|
| 页面边距 | 40~64px | 12~16px |
| 标题字号 | 28~40pt | 13~18pt |
| 正文字号 | 10.5pt | 9~9.5pt |
| 卡片网格 | 3列/4列 | 单列 |
| 表格 | 撑满宽度 | 横向滚动 |
| Hero 区域 | 大字号 | 缩小字号 |
| 指标数字 | 36pt+ | 24pt |

---

## 8. Do's and Don'ts

**Do's：**
- ✅ 移动端字号不低于 9pt
- ✅ 触摸目标最小 44px
- ✅ 图片 max-width: 100%
- ✅ 表格用 `.table-wrap` 横向滚动
- ✅ 使用 `min-width` 而非 `max-width` 作为主断点

**Don'ts：**
- ❌ 移动端字号小于 9pt
- ❌ 固定宽度（`width: 1200px`）而不使用 max-width
- ❌ 长文字在移动端不换行导致溢出
- ❌ 忽略触摸设备的交互体验
