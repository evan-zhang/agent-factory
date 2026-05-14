# design-standards — 通用设计规范层

本目录包含**所有风格模板共享的规范**，Agent 生成 HTML 时必须同时读取对应风格层的 token 和本目录的规范。

---

## 文件说明

| 文件 | 职责 |
|------|------|
| `base-html-rules.md` | HTML/CSS 基础规则：字体、颜色变量、间距、圆角、动画 |
| `table-spec.md` | 表格规范：方正表格、外层包裹 `.table-wrap`、移动端横向滚动 |
| `responsive-spec.md` | 多端适配规范：断点设计、三端字号对照、触摸交互 |
| `print-spec.md` | 打印/PDF 输出规范：A4 排版、页边距、分页控制 |

---

## 规范读取顺序

```
SKILL.md（判断风格）
    ↓
design-standards/（读取通用规范）
    ├ base-html-rules.md    ← 必须读
    ├ table-spec.md         ← 必须读
    ├ responsive-spec.md     ← 必须读
    └ print-spec.md         ← 报告类必须读
    ↓
templates/style-XX/（读取风格专属 token）
    ├ design-token.md       ← 必须读
    └ skeleton.html         ← 骨架参考
    ↓
Agent 生成 HTML
```

---

## 新增风格时的规范引用

新增风格时，Agent 读取顺序不变：
1. `design-standards/` 全部 4 个文件（通用规则不变）
2. `templates/style-XX/design-token.md`（该风格的颜色/字体/间距）
3. `templates/style-XX/skeleton.html`（该风格的 HTML 骨架）

风格自己的 `design-token.md` 中可以覆盖 `design-standards/` 里的默认值，但**不能违背基础规则**（如：不能把字体换成非中文）。

---

## 规范贡献

如需修改通用规范（影响所有风格），请通过 Issue 提交，标注 `[design-standards]`。
