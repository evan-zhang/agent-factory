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
| 手机 | ≤ 768px | iPhone / 小屏 Android |
| 平板 / 大手机 | 769px ~ 1024px | iPad / 大屏 Android / 小笔记本 |
| PC | > 1024px | 笔记本 / 台式机 |

**说明**：
- 768px 断点：移动端与桌面端分界
- 1024px 断点：侧边栏布局启用（目录导航由浮动按钮切换为固定侧边栏）

---

## 2. 断点设计

### 2.1 标准断点

```css
/* 手机（默认样式，无需媒体查询） */
body { font-size: 9pt; }

/* 平板 / 大屏手机 */
@media screen and (min-width: 769px) {
  body { font-size: 10pt; }
}

/* PC（侧边栏启用） */
@media screen and (min-width: 1025px) {
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

**断点选择建议**：
- 常规布局：768px 断点（移动/桌面分界）
- 侧边栏布局：1024px 断点（启用固定侧边栏）
- 如需 PC 大屏优化：可增加 1280px 断点

**禁止使用 `max-width` 作为主断点**，因为会导致在大屏幕设备上样式失效。

### 2.3 侧边栏布局规范

适用于目录导航、工具栏等浮动组件。

#### 移动端（≤ 768px）
- **布局**：浮动按钮（固定在右下角）
- **宽度**：44×44px 触摸区域
- **交互**：点击弹出全屏抽屉（左侧滑入）
- **遮罩**：半透明黑色遮罩，点击关闭

#### 平板端（769px ~ 1024px）
- **布局**：浮动按钮（固定在右上角）
- **宽度**：200px 侧边栏
- **交互**：点击展开/收起
- **遮罩**：无遮罩

#### PC 端（> 1024px）
- **布局**：固定侧边栏（右侧，240px 宽）
- **交互**：默认展开，无切换按钮
- **主内容区**：自动避让（max-width 适配）

```css
/* 示例：侧边栏三端适配 */
.sidebar {
  /* 移动端：浮动按钮 */
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
}

@media screen and (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    /* 平板端：浮动按钮（右上角） */
    top: 16px;
    bottom: auto;
  }
}

@media screen and (min-width: 1025px) {
  .sidebar {
    /* PC 端：固定侧边栏 */
    top: 40px;
    right: 40px;
    width: 240px;
    height: auto;
    max-height: calc(100vh - 80px);
  }
}
```

---

## 3. 各元素响应式规则

### 3.1 页面整体

```css
/* 手机（默认样式） */
.page-wrap {
  max-width: 100%;
  padding: 16px;
}

/* 平板 */
@media screen and (min-width: 769px) {
  .page-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 24px 32px;
  }
}

/* PC（侧边栏预留空间） */
@media screen and (min-width: 1025px) {
  .page-wrap {
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 48px;
  }
}
```

### 3.2 标题（H1/H2/H3）

```css
/* 手机（默认样式） */
h1 { font-size: 13pt; padding: 8px 10px; }
h2 { font-size: 11.5pt; }

/* 平板 */
@media screen and (min-width: 769px) {
  h1 { font-size: 14pt; padding: 10px 12px; }
  h2 { font-size: 12pt; }
}

/* PC */
@media screen and (min-width: 1025px) {
  h1 { font-size: 17pt; padding: 10px 14px; }
  h2 { font-size: 12.5pt; }
}
```

### 3.3 卡片网格

```css
/* 手机：单列 */
.card-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

/* 平板：双列 */
@media screen and (min-width: 769px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

/* PC：三列/四列 */
@media screen and (min-width: 1025px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
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

| 元素 | PC（>1024px） | 平板（769~1024px） | 手机（≤768px） |
|------|--------------|-------------------|----------------|
| 页面边距 | 40~64px | 24~32px | 12~16px |
| 标题字号（H1） | 17pt | 14pt | 13pt |
| 正文字号 | 10.5pt | 10pt | 9pt |
| 卡片网格 | 3列/4列 | 2列 | 单列 |
| 表格 | 撑满宽度 | 撑满宽度 | 横向滚动 |
| Hero 区域 | 大字号 | 中等字号 | 缩小字号 |
| 指标数字 | 36pt+ | 30pt | 24pt |
| 侧边栏 | 固定 240px | 浮动按钮 | 浮动按钮 |
| 目录导航 | 默认展开 | 点击展开 | 全屏抽屉 |

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
