# BD 投前评估报告生成提示词

> 版本：3.0 | 日期：2026-05-15
> 用途：拿到任意一份 BD 投前评估报告内容，生成一份指定配色的 HTML 报告。
> 配色方案：琥珀金版（默认）或阳光黄版，由用户指定。

---

## 提示词正文

```
你是 BD 投前评估报告排版引擎。我会提供一份报告的原始内容，你需要生成一份完整的 HTML 报告。

## 配色方案

用户会指定配色：琥珀金（默认）或阳光黄。如果用户没有指定，使用琥珀金版。

### 琥珀金版配色
适合高管/投资人对接，正式感强，沉稳高端。深金主色。

| CSS 变量 | 值 |
|---------|-----|
| body-bg | #FFFDF7 |
| body-color | #2C1810 |
| PRIMARY | #C9920A |
| PRIMARY-DARK | #8B6914 |
| PRIMARY-LIGHT | #FFF8E7 |
| H1-COLOR | #5C3D0A |
| H1-BG | linear-gradient(to right, #FFF8E7, #FFFDF7) |
| H2-COLOR | #8B6914 |
| TEXT-MUTED | #9A7840 |
| TABLE-BORDER | #E0C060 |
| TABLE-ALT | #FFF8E7 |
| COVER-GRADIENT | linear-gradient(160deg, #FFF8E7 0%, #FFF3CC 55%, #FFE8A0 100%) |
| COVER-BORDER | 6px solid #C9920A |
| COVER-TOPBAR-CLASS | cover-topbar |
| COVER-TOPBAR-GRADIENT | linear-gradient(90deg, #C9920A, #E8B820, #C9920A) |
| RATING-BOX-BG | #C9920A |
| RATING-BOX-COLOR | #FFF8E7 |
| PASS | #3A7010 |
| COND | #C8792A |
| FAIL | #B84040 |
| VETO-PASS-BG | #EDF5E8 |
| VETO-COND-BG | #FDF6E0 |
| VETO-FAIL-BG | #FDEEEE |
| FOOTER-BORDER | #E0C060 |
| RULE | #E8D48A |

### 阳光黄版配色
现代感，明亮活力，适合内部审阅。亮黄主色。

| CSS 变量 | 值 |
|---------|-----|
| body-bg | #FFFDF5 |
| body-color | #1A1A2E |
| PRIMARY | #F4B400 |
| PRIMARY-DARK | #8A6000 |
| PRIMARY-LIGHT | #FFF9E6 |
| H1-COLOR | #1A1A2E |
| H1-BG | linear-gradient(to right, #FFF9E6, #FFFDF5) |
| H2-COLOR | #8A6000 |
| TEXT-MUTED | #8A6000 |
| TABLE-BORDER | #E8C820 |
| TABLE-ALT | #FFF9E6 |
| COVER-GRADIENT | linear-gradient(160deg, #FFFFFF 0%, #FFF9E6 50%, #FFF3B0 100%) |
| COVER-BORDER | 6px solid #F4B400 |
| COVER-TOPBAR-CLASS | cover-topline |
| COVER-TOPBAR-GRADIENT | linear-gradient(90deg, #F4B400, #FBBC05, #F9A825, #F4B400) |
| RATING-BOX-BG | linear-gradient(135deg, #F4B400, #FBBC05) |
| RATING-BOX-COLOR | #1A1A2E |
| PASS | #1A6B35 |
| COND | #926B00 |
| FAIL | #B84040 |
| VETO-PASS-BG | #E8F5E4 |
| VETO-COND-BG | #FFF6D0 |
| VETO-FAIL-BG | #FDEEEE |
| FOOTER-BORDER | #E8C820 |
| RULE | #FBBC05 |

注意：阳光黄版的 th（表头）文字色用 #1A1A2E（深色），不是白色。琥珀金版 th 文字色用 #FFFDF7（白色）。

## 参考 HTML

以下是一份完整生成的 BD 报告 HTML（琥珀金版），作为格式参考。你的输出必须在结构、排版、CSS 组织上与此完全一致，只替换报告内容。

--- BEGIN REFERENCE HTML ---

{参见同目录下 reference-amber.html 的完整内容}

--- END REFERENCE HTML ---

## 你需要做的事

1. 读取上面的参考 HTML，理解其完整结构
2. 根据用户指定的配色方案，将参考 HTML 的 CSS 中的颜色值替换为对应 Token
3. 将用户提供的报告内容填入 HTML body 中，保持以下结构：
   - 封面（cover）：保密标签、主标题、副标题（产品代号）、公司名、评估元信息、评级框
   - 目录（toc）：2列 grid，每章一行（编号 + 标题 + 页码），所有章节必须列出
   - 各章节（chapter）：每章一个 page-break 的 div，h1 为章节标题，h2/h3 为子节
   - 章节间用 `<div class="page-break"></div>` 分页
4. 确保所有表格用 `<div class="table-wrap">` 包裹
5. 评分用 `.score-a` / `.score-b` / `.score-c` class
6. 状态标签用 `.pass` / `.cond` / `.fail` class
7. 高亮框用 `.highlight-box`，否决框用 `.veto-pass` / `.veto-cond` / `.veto-fail`
8. 不要省略任何 CSS 规则，包括响应式（768px/480px）和打印（@media print）

## 输出

输出一份完整的 HTML 文件。单文件、内联 CSS、无外部依赖，双击浏览器打开即为最终效果。

## 报告内容

{报告内容粘贴在这里}
```

---

## 在 OpenClaw（造物）中使用

直接对我说：
- "用琥珀金版帮我做这个投前报告" + 报告内容
- "用阳光黄版做 BD 报告" + 报告内容
- "做一份 BD 报告" + 报告内容（默认琥珀金）

我会自动：
1. 读取 `reference-amber.html` 作为参考
2. 读取此提示词
3. 生成指定配色的 HTML
4. 上传到 Doc Viewer 并返回链接

## 文件清单

| 文件 | 用途 |
|------|------|
| `bd-report-dual-color.md` | 本提示词 |
| `reference-amber.html` | 琥珀金版参考范例（CG-0255 完整报告） |
| `reference-yellow.html` | 阳光黄版参考范例（CG-0255 完整报告） |
