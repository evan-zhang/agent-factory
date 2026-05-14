# Template Contribution Guide — 模板贡献规范

本目录为 doc-viewer 风格模板仓库。
如需贡献新风格，请遵循以下规范。

---

## 目录结构

```
doc-viewer/
├── design-standards/          ← 通用规范（所有人共享）
├── templates/
│   ├── README.md             ← 本文件
│   ├── style-01/             ← 风格 01
│   │   ├── design-token.md   ← 风格颜色/字体/间距变量（必须）
│   │   ├── skeleton.html     ← HTML 骨架参考（必须）
│   │   └── visual-spec.md    ← 视觉说明（可选）
│   ├── style-02/            ← 风格 02（六套变体）
│   │   ├── design-token.md   ← 共享 base token
│   │   ├── style-02a/        ← 变体 A（独立 token）
│   │   └── ...
│   ├── style-03/             ← 风格 03（文档报告型）
│   └── style-04/             ← 风格 04（情报日报）
│       └── ...
└── SKILL.md                  ← Skill 操作定义
```

---

## 风格文件夹命名

格式：`style-{编号}-{简短英文名}`

示例：
- `style-04-daily-report`
- `style-07-conference-agenda`
- `style-08-knowledge-base`

---

## 必需文件

每个风格至少包含两个文件：

### 1. `design-token.md`

```markdown
---
name: style-04-design
version: "1.0.0"
layout: 情报日报风
---

# Style 04 — 风格名称

## 色彩系统

| Token | 色值 | 用途 |
|-------|------|------|
| --bg | #FAFAFA | 页面背景 |
| --primary | #1A56DB | 主色 |

## 字体系统

- 主字体：`PingFang SC` ...
- 标题：700，22pt

## 组件规范

（描述该风格的特色组件）
```

**命名规则：**
- CSS 变量：以 `--` 开头，如 `--bg`
- 颜色 token：使用通用名称（primary/accent/pass/fail），不要用具体颜色名（red/blue）

### 2. `skeleton.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>模板标题</title>
<style>
/* CSS 变量必须定义在此 */
:root {
  --bg: #FAFAFA;
  --primary: #1A56DB;
  /* ... */
}

/* 基础样式 */
body { font-family: "PingFang SC", ...; }

/* 响应式 */
@media screen and (max-width: 768px) { ... }

/* 表格 */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { background: var(--primary); }

/* 打印 */
@media print { ... }
</style>
</head>
<body>
<!-- 示例结构，贡献者可删改 -->
<div class="page-wrap">
  <h1>页面标题</h1>
  <div class="table-wrap">
    <table>...</table>
  </div>
</div>
</body>
</html>
```

---

## 必须遵循的基础规则

1. **字体**：PingFang SC 优先，禁止使用 Inter/Roboto
2. **表格**：`width:100%`，外层包裹 `.table-wrap`
3. **颜色**：通过 CSS 变量定义，禁止直接写色值
4. **响应式**：至少覆盖 480px / 768px 断点
5. **charset**：`UTF-8`
6. **viewport**：`width=device-width, initial-scale=1`

---

## 提交流程

1. Fork 本仓库
2. 在 `templates/` 下创建风格文件夹
3. 包含 `design-token.md` 和 `skeleton.html`
4. 提交 Pull Request，标题格式：`[Template] style-XX: 风格名称`
5. 等待 review，SKILL.md 风格表自动更新

---

## 设计参考资源

- Tabler CSS 变量体系：https://github.com/tabler/tabler
- Tailwind CSS 颜色规范：https://tailwindcss.com/docs/customizing-colors
- Google Fonts（中文字体）：Noto Sans CJK SC

---

## 审核标准

| 维度 | 要求 |
|------|------|
| 文件完整性 | 必须包含 design-token.md 和 skeleton.html |
| 基础规则 | 字体/表格/响应式必须符合规范 |
| 视觉质量 | 颜色对比度达标、间距一致 |
| 示例完整性 | skeleton.html 包含完整示例结构 |
| 中文友好 | 主要面向中文用户场景 |
