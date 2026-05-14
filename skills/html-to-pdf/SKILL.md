---
name: html-to-pdf
description: "将 HTML 文件或 URL 转换为 PDF。使用本地已安装的 Chrome（Headless）进行转换。触发词：转PDF、HTML转PDF、生成PDF、导出PDF、下载PDF"
version: "1.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/skills/html-to-pdf/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=html-to-pdf
---

# HTML to PDF — HTML 页面转换为 PDF

使用本地 Chrome（Headless 模式）将 HTML 文件或 URL 转换为 PDF。

## 触发判断

```
用户说：转PDF / HTML转PDF / 生成PDF / 导出PDF / 下载PDF / 打印为PDF
  → 触发本 Skill
```

## 核心原则

**输入**：HTML 原始文件（`.html`），**不是** doc-viewer 的预览页面 URL。
**转换**：使用本地 Chrome headless，读取 HTML 文件内容直接渲染，不经过预览壳。

## 使用方式

### CLI（临时转换）

```bash
SKILL_DIR=~/.openclaw/skills/html-to-pdf
INPUT=/path/to/input.html
OUTPUT=/path/to/output.pdf

node "$SKILL_DIR/scripts/html-to-pdf.js" "$INPUT" "$OUTPUT" [格式] [边距]

# 示例（默认A4，上下20mm左右）：
node "$SKILL_DIR/scripts/html-to-pdf.js" /tmp/report.html /tmp/report.pdf

# 示例（指定A4，上下26mm左右，左右24mm）：
node "$SKILL_DIR/scripts/html-to-pdf.js" /tmp/report.html /tmp/report.pdf A4 "{\"margin\":{\"top\":\"26mm\",\"right\":\"24mm\",\"bottom\":\"22mm\",\"left\":\"24mm\"}}"

# 示例（支持URL）：
node "$SKILL_DIR/scripts/html-to-pdf.js" "https://example.com" /tmp/out.pdf A4
```

### 通过 API 上传（最常用）

doc-viewer 生成 HTML 后，通过以下流程转 PDF：

```bash
# Step 1：上传 HTML 到 doc viewer
UPLOAD_RESP=$(curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@/path/to/report.html;filename=report.html")
DOC_ID=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HTML_RAW_URL="https://doc.20100706.xyz/raw/$DOC_ID"

# Step 2：用 html-to-pdf skill 转换
SKILL_DIR=~/.openclaw/skills/html-to-pdf
OUTPUT="/tmp/report_$(date +%Y%m%d_%H%M%S).pdf"
node "$SKILL_DIR/scripts/html-to-pdf.js" "$HTML_RAW_URL" "$OUTPUT"

# Step 3：上传 PDF 到 doc viewer
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@$OUTPUT;filename=report.pdf"
```

返回后取 `url`（view 链接）返回给用户，**不要取 raw 链接**（PDF raw 链接会触发下载而不是在线阅读）。

## 选项说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 格式 | `A4` | 支持：A4 / Letter / A3 / Legal |
| 边距 | `10mm 10mm 10mm 10mm` | 上右下左，单位：mm / px / in |
| 横向 | `false` | `true` = 横向打印 |
| 背景色 | `true` | 打印背景颜色和图片 |
| 缩放 | `1.0` | 0.1 ~ 2.0 |

## 常见用法

```bash
# 标准报告（A4，上下26mm地空，左右24mm侧空）
node "$SKILL_DIR/scripts/html-to-pdf.js" input.html output.pdf A4 \
  '{"margin":{"top":"26mm","right":"24mm","bottom":"22mm","left":"24mm"}}'

# 无边距（适合全出血打印）
node "$SKILL_DIR/scripts/html-to-pdf.js" input.html output.pdf A4 \
  '{"margin":{"top":"0","right":"0","bottom":"0","left":"0"}}'

# 横向
node "$SKILL_DIR/scripts/html-to-pdf.js" input.html output.pdf "" \
  '{"landscape":true}'

# 缩放90%
node "$SKILL_DIR/scripts/html-to-pdf.js" input.html output.pdf "" \
  '{"scale":0.9}'
```

## 完整选项列表

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `format` | string | `A4` | 纸张格式 |
| `landscape` | boolean | `false` | 横向打印 |
| `margin.top` | string | `10mm` | 上边距 |
| `margin.right` | string | `10mm` | 右边距 |
| `margin.bottom` | string | `10mm` | 下边距 |
| `margin.left` | string | `10mm` | 左边距 |
| `scale` | number | `1` | 缩放 0.1~2.0 |
| `printBackground` | boolean | `true` | 包含背景色 |
| `displayHeaderFooter` | boolean | `false` | 显示页码页脚 |

## 与 doc-viewer 的集成流程

```
doc-viewer 生成 HTML 文件
    ↓ 上传到 doc viewer（返回 raw URL）
    ↓ html-to-pdf 用 raw URL 转换
    ↓ PDF 上传到 doc viewer（返回 raw URL）
    ↓ 返回 PDF raw URL 给用户
```

## 注意事项

- **输入必须是 HTML 文件或 raw URL**，不能用 doc viewer 的预览页（`/view/`）
- 输入 HTML 建议使用 `file://` 绝对路径 或 URL，URL 需要可访问
- Chrome 路径：macOS 默认 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- 转换失败时报告错误信息，不静默跳过

## 环境要求

- macOS（Chrome 安装在默认路径）
- 或 Linux：`/usr/bin/google-chrome` 或 `/usr/bin/chromium-browser`
- Windows：待确认

## 依赖

无外部依赖，使用系统已安装的 Chrome。

## 问题反馈

https://github.com/evan-zhang/agent-factory/issues/new?labels=html-to-pdf
