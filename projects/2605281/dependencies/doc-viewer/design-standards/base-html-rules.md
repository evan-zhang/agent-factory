# Base HTML Rules — 所有模板通用规范

> 本文件是所有风格模板的**必读基础规范**。
> 风格骨架 `style-XX-base.html` 必须遵循本文件的全部规则。

---

## 1. HTML 结构规范

### 1.1 必含头部

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>页面标题</title>
<!-- 可选：TailwindCSS CDN（轻量页面可不加） -->
<!-- 不使用 JS 框架，纯 HTML + CSS + 原生 JS -->
</head>
```

### 1.2 lang 属性

必须设置 `lang="zh-CN"`，确保中文排版引擎正确。

### 1.3 viewport

```html
<meta name="viewport" content="width=device-width,initial-scale=1">
```
禁止删除此行，否则移动端无法正常缩放。

---

## 2. 字体规范

### 2.1 字体栈（按优先级）

```css
font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "SimSun", Arial, sans-serif;
```

**规则：**
- 第一优先 PingFang SC（macOS/iOS 系统字体）
- 第二优先 Microsoft YaHei（Windows 常用中文字体）
- 第三优先 Noto Sans CJK SC（Google 开源中文字体，网络加载）
- 第四优先 SimSun（Windows 旧系统中文）
- 最后加 Arial/sans-serif 作为 fallback
- **禁止使用**：Inter、Roboto（这两是西文字体，中文支持差）

### 2.2 字号层级

| 层级 | PC 端 | 移动端 | 字重 | 用途 |
|------|-------|--------|------|------|
| 页面标题（H1） | 28~40pt | 18~22pt | 700~800 | 主标题 |
| 章节标题（H2） | 18~22pt | 14~16pt | 700 | 章节名 |
| 卡片标题（H3） | 14~16pt | 13~14pt | 600 | 卡片标题 |
| 正文 | 13~15pt | 12~13pt | 400 | 正文内容 |
| 辅助文字 | 11~12pt | 10~11pt | 400 | 时间、来源等 |
| 标签/角标 | 9~11pt | 9~10pt | 600~700 | 分类标签 |

### 2.3 行高

- 正文：`line-height: 1.6~1.8`
- 标题：`line-height: 1.2~1.4`
- 标签/按钮：`line-height: 1`

---

## 3. 颜色规范

### 3.1 必须通过 CSS 变量定义

```css
:root {
  --bg: #FFFFFF;
  --text: #111827;
  --subtext: #6B7280;
  --border: #E5E7EB;
  /* 风格主色在此定义 */
}
```

禁止在 HTML 里直接写颜色值（如 `color="#111827"`），必须通过 CSS 变量引用。

### 3.2 颜色使用场景

| 颜色用途 | 使用场景 |
|---------|---------|
| 主色（Primary） | 标题、按钮、链接、表格表头 |
| 强调色（Accent） | 徽章、高亮块、图标背景 |
| 通过/正向（Green） | 状态通过、上升趋势 |
| 警告（Yellow/Amber） | 待确认、持平 |
| 危险（Red） | 否决、下降趋势、失败 |
| 边框色（Border） | 表格线、分隔线、卡片边框 |

### 3.3 颜色对比度

- 主文字与背景对比度 ≥ 4.5:1（WCAG AA）
- 辅助文字与背景对比度 ≥ 3:1
- 禁止在白色背景使用纯灰色（#CCCCCC）作为文字色

---

## 4. 间距规范

### 4.1 页面边距

| 断点 | 页面左右边距 |
|------|------------|
| PC（>768px） | 40px ~ 64px |
| 平板（480~768px） | 16px ~ 24px |
| 手机（<480px） | 12px ~ 16px |

### 4.2 间距系统（8px 基准）

```
4px  = 极紧密（标签内边距）
8px  = 紧凑（表格单元格）
12px = 标准（卡片内边距）
16px = 宽松（组件间距）
24px = 大间距（section 之间）
32px+ = 超大间距（page-wrap 上下边距）
```

---

## 5. 圆角规范

| 元素 | 圆角值 |
|------|--------|
| 卡片 | 8px ~ 12px |
| 按钮 | 6px ~ 8px |
| 标签/徽章 | 4px ~ 20px（胶囊形） |
| 输入框 | 6px |
| 图片 | 0px（除非特殊风格） |

---

## 6. 阴影规范

| 级别 | 规则 | 适用场景 |
|------|------|---------|
| 微阴影 | `0 1px 3px rgba(0,0,0,0.06)` | 默认卡片 |
| 中阴影 | `0 4px 12px rgba(0,0,0,0.1)` | 悬停卡片 |
| 强阴影 | `0 8px 24px rgba(0,0,0,0.15)` | 弹窗/模态框 |

---

## 7. 动画规范

### 7.1 允许的动画类型

- `transition: all 0.2s ease`（卡片悬停）
- `opacity: 0 → 1, 300ms ease`（淡入）
- `transform: translateY(-2px)`（卡片悬停上浮）
- 数字计数器（数字跳动效果）

### 7.2 禁止的动画

- 页面加载时的复杂动画（用户等待体验差）
- 闪烁、旋转动画（干扰阅读）
- 超过 400ms 的过渡动画

---

## 8. 链接与按钮规范

### 8.1 链接

- 默认颜色：`--accent`（风格主色）
- 悬停：加下划线或颜色加深
- 访问过：`--accent` + 下划线

### 8.2 按钮

```css
.btn-primary {
  background: var(--primary);
  color: #FFFFFF;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  transition: all 0.2s;
}
.btn-primary:hover {
  filter: brightness(0.9);
  transform: translateY(-1px);
}
```

---

## 9. 图片规范

- 使用用户提供的 URL 或高质量占位图
- 宽高比固定：`<img width="xxx" height="xxx">`
- 禁止使用 base64 编码的大图（文件体积超标）

---

## 10. 文件输出规范

| 指标 | 上限 |
|------|------|
| HTML 文件大小 | < 1MB（不含图片） |
| CSS 内联 | 不允许外部 CSS 文件 |
| JS | 仅允许原生 JS（无框架） |
| 图片引用 | 外链 URL，禁止 base64 |

---

## 11. Do's and Don'ts

**Do's：**
- ✅ 所有颜色通过 CSS 变量定义
- ✅ 使用 8px 基准间距系统
- ✅ 响应式断点至少覆盖 480px / 768px / 1024px
- ✅ 字体栈以中文字体优先
- ✅ 设置 `:root` CSS 变量定义风格颜色

**Don'ts：**
- ❌ 在 HTML 中直接写颜色值
- ❌ 使用非中文字体作为主字体
- ❌ 硬编码宽度（如 `width: 1200px`），使用 `max-width` + `100%`
- ❌ 省略 viewport meta 标签
- ❌ 使用 JS 动画框架
