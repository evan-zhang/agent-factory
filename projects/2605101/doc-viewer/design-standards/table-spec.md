# Table Specification — 表格规范

> 所有风格模板的表格必须遵循本规范，确保 PC 端方正整齐、移动端可横向滚动查看。

---

## 1. 表格基础规则

### 1.1 基础 HTML 结构

```html
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>表头列1</th>
        <th>表头列2</th>
        <th>表头列3</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>内容1</td>
        <td>内容2</td>
        <td>内容3</td>
      </tr>
    </tbody>
  </table>
</div>
```

**关键点：**
- 表格外层必须包裹 `<div class="table-wrap">`
- 使用 `<thead>` 和 `<tbody>` 明确语义结构
- 禁止省略 `border-collapse: collapse`

### 1.2 基础 CSS（所有风格通用）

```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0 18px;
  font-size: 9.5pt;
}
th {
  background: var(--primary);      /* 风格主色 */
  color: #FFFFFF;
  font-weight: 700;
  text-align: left;
  padding: 8px 10px;
  border: 1px solid var(--primary);
}
td {
  padding: 7px 10px;
  border: 1px solid var(--border);
  vertical-align: top;
  line-height: 1.5;
}
.table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 12px 0 18px;
}
```

### 1.3 列宽策略

- **PC 端（>768px）**：`width: 100%`，表格撑满容器，列宽由内容自动分配
- **长文本列**：在 `<th>` 或 `<td>` 上加 `style="min-width: 120px"` 防止挤压
- **重要列（如评估结论）**：固定 `width: 180px`，优先级高的列不被压缩

**错误做法（禁止）：**
```css
/* ❌ 这样会导致每行独立宽度，列不对齐 */
table { width: max-content; }

/* ❌ 固定死宽度在移动端会溢出 */
table { width: 900px; }
```

---

## 2. 表格变体

### 2.1 按表头颜色分类

| 变体类名 | 表头背景色 | 适用场景 |
|---------|-----------|---------|
| `.th-default`（默认） | `--primary` | 一般表格 |
| `.th-green` | 绿色 `#059669` | 通过/正向类表格 |
| `.th-red` | 红色 `#DC2626` | 否决/危险类表格 |
| `.th-blue` | 蓝色 `#1E40AF` | 信息/分步骤表格 |

**CSS 写法：**
```css
.th-green th { background: #059669 !important; border-color: #059669 !important; }
.th-red th { background: #DC2626 !important; border-color: #DC2626 !important; }
.th-blue th { background: #1E40AF !important; border-color: #1E40AF !important; }
```

**HTML 用法：**
```html
<table class="th-green">...</table>
```

### 2.2 按行背景色分类

| 类名 | 效果 | 适用场景 |
|------|------|---------|
| `.amber-row td` | 淡金色交替 `#FFF8E7` | 琥珀风格表格 |
| `.blue-row td` | 淡蓝色交替 `#EEF4FA` | 信息类表格 |
| `.green-row td` | 淡绿色交替 `#EDF5E8` | 通过类表格 |
| `.red-row td` | 淡红色交替 `#FDEEEE` | 否决类表格 |

**交替行写法（不需要额外类）：**
```css
tr:nth-child(even) td { background: var(--row-alt, #FFF8E7); }
```

### 2.3 特殊单元格样式

**第一列加粗（标签列）：**
```css
.td-label td:first-child {
  background: var(--row-alt) !important;
  font-weight: 600;
  white-space: nowrap;
  width: 160px;
}
```
```html
<table class="td-label">...</table>
```

---

## 3. 合并单元格

- 使用标准 `colspan` / `rowspan` 属性
- 合并单元格后，该单元格边框处理与普通单元格一致
- 复杂合并建议用最小化合并，避免多行多列交叉

---

## 4. 表格内文字处理

### 4.1 文字截断

```css
/* 单行截断 + 省略号 */
td {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

### 4.2 允许多行的场景

```css
td.multi-line {
  white-space: normal; /* 允许换行 */
  line-height: 1.6;
}
```

---

## 5. 表格中的状态标记

使用彩色文字标记，不用 emoji：

| 状态 | 标记方式 | CSS 颜色 |
|------|---------|---------|
| 通过 | `<span class="pass">✅ 通过</span>` | `--pass: #059669` |
| 条件通过 | `<span class="cond">⚠️ 条件</span>` | `--cond: #D97706` |
| 否决 | `<span class="fail">❌ 否决</span>` | `--fail: #DC2626` |
| 待确认 | `<span class="pending">🔄 待确认</span>` | `--pending: #6B7280` |

```css
.pass { color: #059669; font-weight: 700; }
.cond { color: #D97706; font-weight: 700; }
.fail { color: #DC2626; font-weight: 700; }
.pending { color: #6B7280; font-style: italic; font-weight: 600; }
```

---

## 6. 移动端横向滚动

**规则：外层 `.table-wrap` 负责滚动，表格本身保持正常宽度。**

```css
/* PC 端：正常显示 */
.table-wrap { overflow-x: visible; }

/* 移动端：超出部分滚动 */
@media screen and (max-width: 768px) {
  .table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 12px 0 18px;
  }
  table {
    /* 不再设 width: max-content，保证撑满可用宽度 */
    width: max-content;
    min-width: 100%;
  }
}
```

---

## 7. 打印处理

```css
@media print {
  table { width: 100%; }
  .table-wrap { overflow-x: visible; }
  th { background: #333 !important; color: #fff !important; -webkit-print-color-adjust: exact; }
}
```

---

## 8. Do's and Don'ts

**Do's：**
- ✅ 外层包裹 `<div class="table-wrap">`
- ✅ 使用 `border-collapse: collapse`
- ✅ 表头用深色背景 + 白字
- ✅ 交替行用淡色背景区分

**Don'ts：**
- ❌ `width: max-content` 在 PC 端让列各自独立宽度
- ❌ 直接在 HTML 里写 `style="background: red"` 而不用 CSS 类
- ❌ 表格内文字不换行导致溢出
