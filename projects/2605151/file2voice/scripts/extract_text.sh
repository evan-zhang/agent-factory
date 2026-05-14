#!/usr/bin/env bash
# extract_text.sh — 根据文件类型提取纯文本
# 用法: extract_text.sh <input_file> <output_file>
set -euo pipefail

INPUT="$1"
OUTPUT="$2"

# 获取文件扩展名（小写）
EXT="${INPUT##*.}"
EXT=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

case "$EXT" in
  txt|md|markdown)
    # 纯文本直接复制
    cp "$INPUT" "$OUTPUT"
    ;;
  
  html|htm)
    # HTML: 用 python 去标签提取正文
    python3 - "$INPUT" "$OUTPUT" <<'PYEOF'
import sys, re

with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

# 去掉 script 和 style
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

# 保留段落分隔
html = re.sub(r'<br\s*/?\s*>', '\n', html, flags=re.IGNORECASE)
html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
html = re.sub(r'</h[1-6]>', '\n\n', html, flags=re.IGNORECASE)
html = re.sub(r'</li>', '\n', html, flags=re.IGNORECASE)

# 去掉所有 HTML 标签
text = re.sub(r'<[^>]+>', '', html)

# 清理多余空白
text = re.sub(r'[ \t]+', ' ', text)
text = re.sub(r'\n{3,}', '\n\n', text)
text = text.strip()

# 解码常见 HTML 实体
entities = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&nbsp;': ' '}
for ent, char in entities.items():
    text = text.replace(ent, char)

with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(text)
PYEOF
    ;;
  
  pdf)
    # PDF: 优先 pdftotext，备选 python3
    if command -v pdftotext &>/dev/null; then
      pdftotext -layout "$INPUT" "$OUTPUT"
    else
      # 尝试 python3 + PyPDF2
      python3 - "$INPUT" "$OUTPUT" <<'PYEOF'
import sys
try:
    from PyPDF2 import PdfReader
    reader = PdfReader(sys.argv[1])
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(text.strip())
except ImportError:
    print("错误：需要 pdftotext 或 PyPDF2（pip install PyPDF2）", file=sys.stderr)
    sys.exit(1)
PYEOF
    fi
    ;;
  
  doc|docx)
    # Word: 优先 textutil（macOS），备选 python3 + python-docx
    if [[ "$(uname)" == "Darwin" ]] && command -v textutil &>/dev/null; then
      textutil -convert txt -output "$OUTPUT" "$INPUT"
    else
      python3 - "$INPUT" "$OUTPUT" <<'PYEOF'
import sys
try:
    from docx import Document
    doc = Document(sys.argv[1])
    text = "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(text.strip())
except ImportError:
    print("错误：需要 textutil（macOS）或 python-docx（pip install python-docx）", file=sys.stderr)
    sys.exit(1)
PYEOF
    fi
    ;;
  
  *)
    echo "错误：不支持的文件类型: .$EXT" >&2
    echo "支持: txt, md, markdown, html, htm, pdf, doc, docx" >&2
    exit 1
    ;;
esac

# 验证输出
if [[ ! -s "$OUTPUT" ]]; then
  echo "警告：提取结果为空" >&2
fi
