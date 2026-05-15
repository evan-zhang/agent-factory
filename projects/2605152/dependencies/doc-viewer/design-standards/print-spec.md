# Print Specification — 打印与 PDF 输出规范

> 适用于需要导出 PDF / Word 的文档页面（如 BD 报告、合同、方案等）。
> 核心目标：打印效果与屏幕显示效果尽可能一致，PDF 导出后布局不变形。

---

## 1. 打印与屏幕显示的关系

### 1.1 两种场景

| 场景 | 输出方式 | 核心要求 |
|------|---------|---------|
| 屏幕展示 | 直接打开 HTML | 响应式、多端适配 |
| 打印导出 | Chrome headless / 浏览器打印 | A4 纵向、页边距固定、内容不溢出 |

### 1.2 打印输出原理

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf=/tmp/output.pdf \
  --print-to-pdf-no-header \
  /tmp/input.html
```

PDF 输出为 A4 纵向（默认），由 Chrome 计算分页。

---

## 2. 页面布局规范

### 2.1 打印用 @page 规则

```css
@page {
  size: A4 portrait;
  margin: 20mm 20mm 20mm 20mm;
}
```

**规则：**
- 上下左右边距统一 20mm（适合装订）
- 报告类文档可调整为 `26mm 24mm 22mm 24mm`（天/地/左/右）
- 不使用 `margin: auto`（会导致页边距不固定）

### 2.2 章节分页

```css
/* 方法一：强制在章节前分页 */
.page-break {
  page-break-before: always;
}

/* 方法二：避免在章节内部分割 */
.chapter {
  page-break-inside: avoid;
}
```

**使用场景：**
- 封面 → 目录：需要分页
- 各章节之间：需要分页
- 表格内部：尽量不分割（`page-break-inside: avoid`）
- 卡片组：尽量不跨页分割

---

## 3. 字体在打印中的处理

### 3.1 使用 pt 单位（报告类）

```css
/* 报告类（适合打印）：正文用 pt */
body {
  font-family: "PingFang SC", "Microsoft YaHei", "SimSun", serif;
  font-size: 10.5pt;
  line-height: 1.7;
}

/* 屏幕展示类：用 px 或 rem */
body {
  font-size: 15px;
}
```

### 3.2 字体加载（打印环境无网络）

```css
/* 打印时无法访问 Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=...');

/* 正确做法：系统字体栈放在最前，Google Fonts 作为增强 */
font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
```

---

## 4. 颜色在打印中的处理

### 4.1 背景色打印

```css
/* 需要打印背景色时必须声明 */
th {
  background: #C9920A;
  -webkit-print-color-adjust: exact;  /* Chrome/Safari */
  print-color-adjust: exact;           /* 标准属性 */
  color-adjust: exact;
}
```

### 4.2 浅色文字打印

```css
/* 白色文字在彩色背景上 */
th {
  background: #C9920A;
  color: #FFFFFF;        /* 白色 */
}

/* 浅色文字（浅灰）在白色背景上，打印后可能看不清 */
p.light-text {
  color: #CCCCCC;       /* ❌ 打印后几乎看不见 */
  color: #666666;       /* ✅ 打印后仍可读 */
}
```

---

## 5. 表格打印处理

### 5.1 分页控制

```css
/* 避免在表格中间分页 */
table {
  page-break-inside: avoid;
}

/* 避免在表头和第一行之间分页 */
thead {
  page-break-after: avoid;
}
```

### 5.2 宽表格打印

```css
@media print {
  .table-wrap {
    overflow-x: visible;  /* 打印时取消滚动，显示完整表格 */
    width: 100%;
  }
  table {
    width: 100%;
    font-size: 9pt;       /* 打印时字体略小 */
  }
}
```

---

## 6. 图片在打印中的处理

```css
/* 宽度自适应，高度等比缩放 */
img {
  max-width: 100%;
  height: auto;
  page-break-inside: avoid;  /* 避免图片被切割到两页 */
}
```

---

## 7. Chrome Headless PDF 导出命令模板

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

"$CHROME" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT_PATH" \
  --print-to-pdf-no-header \
  "$INPUT_HTML"
```

**注意事项：**
- Chrome headless 默认 A4 纵向
- 如需横向：`--print-to-pdf-landscape`（少见，报告类一般用纵向）
- 禁止在导出时带 URL 栏或页码（`--no-pdf-header-footer` 已处理）

---

## 8. PDF 导出与 HTML 文件的关系

```
Markdown 内容
  ↓ doc-viewer 生成
HTML 页面（屏幕优先）
  ↓ Chrome headless 转换
PDF 文件（打印优先）
```

**两者的设计原则：**
- HTML 页面优先保证屏幕阅读体验（响应式、多端）
- PDF 在 HTML 基础上优化打印效果（字体 pt 单位、颜色打印声明）
- 两者共享同一份 HTML，通过 CSS `@media print` 区分屏幕/打印样式

---

## 9. Do's and Don'ts

**Do's：**
- ✅ 报告类文档正文使用 pt 单位
- ✅ 打印背景色使用 `-webkit-print-color-adjust: exact`
- ✅ 章节之间使用 `page-break-before: always`
- ✅ 表格外包裹 `.table-wrap` 确保打印时宽度正确

**Don'ts：**
- ❌ 使用 `px` 作为报告类正文的字号单位（屏幕显示没问题，打印会失真）
- ❌ 打印时依赖网络字体（网络断开字体消失）
- ❌ 重要表格内使用 `page-break-inside: auto`（默认值，可能在表格中间分页）
- ❌ 白色背景的表格直接打印（无边框、无底色）
