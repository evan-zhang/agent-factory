#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Report to McKinsey-style HTML Renderer

Key rule:
    Preserve the original Markdown structure. Do NOT enforce fixed chapters.

Usage:
    python report_renderer.py input.md output.html
    python report_renderer.py input.md output.html --title "报告标题"
    python report_renderer.py input.md output.html --asset-dir ./assets
    python report_renderer.py input.md output.html --no-embed-images
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CSS = r"""
:root {
  --navy: #071E41;
  --blue: #0B5CAB;
  --blue-2: #174A7C;
  --cyan: #00A3E0;
  --ink: #111827;
  --text: #243041;
  --muted: #5D6878;
  --line: #D8DEE8;
  --soft: #F6F8FB;
  --white: #FFFFFF;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB",
               "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
  background: #EDEFF3;
  color: var(--text);
  margin: 0;
  line-height: 1.72;
}

.container {
  max-width: 1160px;
  margin: 28px auto;
  background: var(--white);
  padding: 0 0 72px;
  box-shadow: 0 14px 40px rgba(7, 30, 65, 0.12);
  border: 1px solid #E4E8EF;
}

h1 {
  margin: 0;
  padding: 34px 48px 18px;
  font-size: 34px;
  line-height: 1.25;
  color: var(--white);
  background: var(--navy);
  letter-spacing: 0.2px;
  border-bottom: 6px solid var(--cyan);
}

.subtitle {
  margin: 0;
  padding: 18px 48px 22px;
  background: #102B57;
  color: #F4F7FB;
  font-size: 16px;
  border-left: none;
}

.subtitle strong { color: #FFFFFF; }

.toc {
  margin: 30px 48px 26px;
  padding: 22px 24px;
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 0;
}

.toc h2 {
  margin: 0 0 12px;
  padding: 0;
  border: 0;
  color: var(--navy);
  font-size: 20px;
  letter-spacing: 0.5px;
}

.toc ol {
  margin: 0;
  padding-left: 22px;
  columns: 2;
  column-gap: 42px;
}

.toc li {
  break-inside: avoid;
  margin: 4px 0 8px;
  color: var(--muted);
}

.toc a {
  color: var(--blue-2);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}

.toc a:hover { border-bottom-color: var(--blue-2); }

h2 {
  margin: 38px 48px 16px;
  padding: 0 0 10px;
  font-size: 25px;
  color: var(--navy);
  border-bottom: 2px solid var(--navy);
  letter-spacing: 0.2px;
}

h3 {
  margin: 24px 48px 10px;
  font-size: 18px;
  color: var(--blue-2);
  font-weight: 700;
}

h4, h5, h6 {
  margin: 20px 48px 8px;
  color: var(--blue-2);
}

p {
  margin: 10px 48px;
  font-size: 16px;
}

ul, ol {
  margin: 10px 48px 14px;
  padding-left: 22px;
}

li { margin: 5px 0; }
strong { color: var(--navy); }

.flow, pre {
  margin: 14px 48px 20px;
  background: #F8FAFD;
  border: 1px solid var(--line);
  border-left: 5px solid var(--blue);
  padding: 16px 18px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  white-space: pre-wrap;
  color: #16253A;
  font-size: 14px;
  line-height: 1.68;
  overflow-x: auto;
}

code {
  background: #F1F4F8;
  color: #143B6E;
  padding: 2px 5px;
  border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

blockquote {
  margin: 16px 48px 22px;
  padding: 14px 18px;
  background: #F4F7FB;
  border-left: 5px solid var(--cyan);
  color: #243041;
}

.img-wrap {
  margin: 24px 48px 30px;
  padding: 18px;
  text-align: center;
  background: #F7F9FC;
  border: 1px solid var(--line);
}

.img-wrap img {
  max-width: 100%;
  border: 1px solid #CDD5E2;
  box-shadow: 0 8px 22px rgba(7, 30, 65, 0.13);
  background: #FFFFFF;
}

.img-caption {
  color: var(--muted);
  font-size: 13px;
  margin-top: 10px;
}

table {
  border-collapse: collapse;
  width: calc(100% - 96px);
  margin: 16px 48px 26px;
  font-size: 15px;
  border-top: 3px solid var(--navy);
}

th, td {
  border: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}

th {
  background: var(--navy);
  color: #FFFFFF;
  font-weight: 700;
}

tbody tr:nth-child(even) td { background: #F7F9FC; }

tbody td:first-child {
  color: var(--navy);
  font-weight: 700;
  width: 22%;
}

hr {
  border: 0;
  border-top: 1px solid var(--line);
  margin: 28px 48px;
}

.footer {
  margin: 44px 48px 0;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}

.backtop {
  display: inline-block;
  margin: 8px 48px 0;
  color: var(--blue);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}

.backtop:hover { text-decoration: underline; }

@media (max-width: 780px) {
  .container { margin: 0; border: 0; }
  h1 { padding: 26px 24px 14px; font-size: 28px; }
  .subtitle { padding: 16px 24px 18px; }
  .toc, h2, h3, h4, h5, h6, p, ul, ol, .flow, pre, blockquote, .img-wrap, table, hr, .footer, .backtop {
    margin-left: 24px;
    margin-right: 24px;
  }
  .toc ol { columns: 1; }
  table {
    width: calc(100% - 48px);
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .img-wrap { padding: 12px; }
}

@media (max-width: 480px) {
  .container { margin: 0; border: 0; border-radius: 0; }
  h1 {
    padding: 22px 16px 12px;
    font-size: 24px;
    letter-spacing: 0;
  }
  .subtitle { padding: 14px 16px 16px; font-size: 14px; }
  .toc {
    margin: 20px 16px;
    padding: 16px;
  }
  .toc h2 { font-size: 18px; }
  h2 {
    margin: 28px 16px 12px;
    font-size: 21px;
    padding-bottom: 8px;
  }
  h3 {
    margin: 18px 16px 8px;
    font-size: 16px;
  }
  h4, h5, h6 { margin: 16px 16px 6px; }
  p, ul, ol {
    margin: 8px 16px 12px;
  }
  ul, ol { padding-left: 20px; }
  li { margin: 4px 0; }
  .flow, pre {
    margin: 10px 16px 16px;
    padding: 12px 14px;
    font-size: 13px;
  }
  blockquote {
    margin: 12px 16px 16px;
    padding: 10px 14px;
  }
  .img-wrap {
    margin: 16px 16px 22px;
    padding: 10px;
  }
  .img-caption { font-size: 12px; }
  table {
    width: calc(100% - 32px);
    margin: 12px 16px 20px;
    font-size: 13px;
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  th, td { padding: 7px 8px; }
  hr { margin: 20px 16px; }
  .footer {
    margin: 32px 16px 0;
    font-size: 12px;
  }
  .backtop { margin: 6px 16px 0; }
}

@media print {
  body { background: #FFFFFF; }
  .container {
    margin: 0;
    max-width: none;
    box-shadow: none;
    border: 0;
  }
  .backtop { display: none; }
  .fly-nav { display: none !important; }
  h2 { page-break-after: avoid; }
  table, .flow, pre, .img-wrap { page-break-inside: avoid; }
}

/* ── PC 端悬浮导航 ── */
.fly-nav {
  position: fixed;
  top: 50%;
  right: 28px;
  transform: translateY(-50%);
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* toggle button */
.fly-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--navy);
  color: #fff;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(7,30,65,0.25);
  transition: all 0.2s ease;
  margin-left: auto;
}
.fly-nav-btn:hover { background: var(--blue); box-shadow: 0 6px 20px rgba(7,30,65,0.35); transform: scale(1.05); }
.fly-nav-btn:active { transform: scale(0.95); }
.fly-nav-btn svg { width: 22px; height: 22px; fill: currentColor; display: block; }

/* panel */
.fly-nav-panel {
  position: absolute;
  right: 0;
  top: 52px;
  width: 260px;
  max-height: 65vh;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(7,30,65,0.18);
  padding: 14px 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: opacity 0.25s, visibility 0.25s, transform 0.25s;
}
.fly-nav.open .fly-nav-panel {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
.fly-nav-panel::-webkit-scrollbar { width: 5px; }
.fly-nav-panel::-webkit-scrollbar-thumb { background: var(--line); border-radius: 3px; }

/* panel header */
.fly-nav-header {
  padding: 2px 18px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.8px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--line);
  margin-bottom: 6px;
}

/* nav links */
.fly-nav-link {
  display: block;
  padding: 8px 18px 8px 22px;
  color: var(--text);
  text-decoration: none;
  font-size: 13.5px;
  line-height: 1.45;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  word-break: break-word;
}
.fly-nav-link:hover {
  background: var(--soft);
  color: var(--navy);
}
.fly-nav-link.active {
  border-left-color: var(--cyan);
  background: #EBF5FB;
  color: var(--navy);
  font-weight: 600;
}

/* back-to-top inside panel */
.fly-nav-top {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px 6px;
  margin-top: 6px;
  border-top: 1px solid var(--line);
  color: var(--blue-2);
  text-decoration: none;
  font-size: 12.5px;
  font-weight: 600;
}
.fly-nav-top:hover { color: var(--navy); }
.fly-nav-top svg { width: 14px; height: 14px; fill: currentColor; flex-shrink: 0; }

/* reading progress bar */
.fly-nav-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: var(--cyan);
  z-index: 9998;
  transition: width 0.05s linear;
}

/* ===== 移动端（平板 & 手机）===== */
@media (max-width: 780px) {
  .fly-nav {
    right: 16px;
    bottom: 20px;
    top: auto;
    transform: none;
  }
  .fly-nav-btn {
    width: 44px;
    height: 44px;  /* min 44px for touch target */
    border-radius: 50%;
    box-shadow: 0 4px 16px rgba(7,30,65,0.3);
  }
  .fly-nav-btn svg { width: 24px; height: 24px; }
  .fly-nav-panel {
    right: 0;
    top: auto;
    bottom: 56px;
    width: 280px;
    max-height: 50vh;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(7,30,65,0.2);
  }
  .fly-nav-link {
    padding: 10px 18px 10px 22px;  /* bigger touch target */
    font-size: 14px;
  }
  .fly-nav-header { font-size: 11px; }
}

@media (max-width: 480px) {
  .fly-nav {
    right: 12px;
    bottom: 16px;
  }
  .fly-nav-btn {
    width: 44px;
    height: 44px;
    border-radius: 50%;
  }
  .fly-nav-panel {
    right: 0;
    bottom: 52px;
    width: calc(100vw - 40px);
    max-width: 320px;
    max-height: 45vh;
  }
  .fly-nav-link {
    padding: 11px 16px 11px 20px;
    font-size: 14px;
  }
  .fly-nav-top { padding: 10px 16px 6px; }
}

@media print {
  .fly-nav { display: none !important; }
  .fly-nav-progress { display: none !important; }
}
"""


def slugify(text: str, index: int) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text).strip()
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", cleaned)
    return f"sec-{index}-{cleaned[:28]}" if cleaned else f"sec-{index}"


def parse_front_matter(md: str) -> Tuple[Dict[str, str], str]:
    if md.startswith("---\n"):
        end = md.find("\n---", 4)
        if end != -1:
            raw = md[4:end].strip()
            rest = md[end + 4:].lstrip("\n")
            meta: Dict[str, str] = {}
            for line in raw.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            return meta, rest
    return {}, md


def extract_title_and_subtitle(md: str, meta: Dict[str, str], fallback: str) -> Tuple[str, str, str]:
    title = meta.get("title", "").strip()
    subtitle = meta.get("subtitle", "").strip() or meta.get("summary", "").strip()
    lines = md.splitlines()
    new_lines: List[str] = []
    removed_title = False
    removed_subtitle = False

    for line in lines:
        if line.startswith("# ") and not removed_title:
            if not title:
                title = line[2:].strip()
            removed_title = True
            continue
        if line.startswith("> ") and not removed_subtitle and not subtitle:
            subtitle = line[2:].strip()
            removed_subtitle = True
            continue
        elif line.startswith("> ") and not removed_subtitle and subtitle and line[2:].strip() == subtitle:
            removed_subtitle = True
            continue
        new_lines.append(line)

    if not title:
        title = fallback
    return title, subtitle, "\n".join(new_lines).strip()


def escape_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def image_to_html(alt: str, src: str, md_dir: Path, asset_dir: Optional[Path], embed: bool) -> str:
    candidates = []
    p = Path(src)
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(md_dir / p)
        if asset_dir:
            candidates.append(asset_dir / p)
            candidates.append(asset_dir / p.name)

    found = next((c for c in candidates if c.exists()), None)
    alt_e = html.escape(alt or "图片")
    if found and embed:
        mime = "image/png"
        ext = found.suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif ext == ".webp":
            mime = "image/webp"
        elif ext == ".gif":
            mime = "image/gif"
        data = base64.b64encode(found.read_bytes()).decode("utf-8")
        src_attr = f"data:{mime};base64,{data}"
    elif found:
        src_attr = html.escape(str(found))
    else:
        src_attr = html.escape(src)

    return (
        f'<div class="img-wrap">'
        f'<img src="{src_attr}" alt="{alt_e}" />'
        f'<div class="img-caption">{alt_e}</div>'
        f'</div>'
    )


def convert_markdown(md: str, md_dir: Path, asset_dir: Optional[Path], embed_images: bool) -> Tuple[str, List[Tuple[str, str]]]:
    lines = md.splitlines()
    html_parts: List[str] = []
    toc: List[Tuple[str, str]] = []
    i = 0
    section_index = 0
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_lists()
            lang = stripped[3:].strip()
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            code = html.escape("\n".join(code_lines))
            cls = "flow" if lang in ("text", "flow", "") else ""
            if cls:
                html_parts.append(f'<div class="{cls}">{code}</div>')
            else:
                html_parts.append(f"<pre><code>{code}</code></pre>")
            continue

        if not stripped:
            close_lists()
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            close_lists()
            html_parts.append("<hr />")
            i += 1
            continue

        m = re.match(r"^(#{2,6})\s+(.+)$", line)
        if m:
            close_lists()
            level = len(m.group(1))
            raw_title = m.group(2).strip()
            title = escape_inline(raw_title)
            if level == 2:
                section_index += 1
                sid = slugify(raw_title, section_index)
                toc.append((sid, re.sub(r"<[^>]+>", "", title)))
                html_parts.append(f'<h2 id="{sid}">{title}</h2>')
            else:
                html_parts.append(f"<h{level}>{title}</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            close_lists()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            quote_html = "<br />".join(escape_inline(x) for x in quote_lines)
            html_parts.append(f"<blockquote>{quote_html}</blockquote>")
            continue

        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[i + 1]):
            close_lists()
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            html_parts.append("<table><thead><tr>" + "".join(f"<th>{escape_inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            for row in rows:
                html_parts.append("<tr>" + "".join(f"<td>{escape_inline(c)}</td>" for c in row) + "</tr>")
            html_parts.append("</tbody></table>")
            continue

        img_m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if img_m:
            close_lists()
            html_parts.append(image_to_html(img_m.group(1), img_m.group(2), md_dir, asset_dir, embed_images))
            i += 1
            continue

        ul_m = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if ul_m:
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{escape_inline(ul_m.group(1).strip())}</li>")
            i += 1
            continue

        ol_m = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ol_m:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{escape_inline(ol_m.group(1).strip())}</li>")
            i += 1
            continue

        close_lists()
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith("#") or nxt.startswith(">") or nxt.startswith("```") or re.match(r"^\s*[-*+]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i]):
                break
            if "|" in lines[i] and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}:?", lines[i+1]):
                break
            if re.match(r"!\[([^\]]*)\]\(([^)]+)\)", nxt):
                break
            para.append(nxt)
            i += 1

        paragraph = " ".join(para)
        paragraph = re.sub(
            r"!\[([^\]]*)\]\(([^)]+)\)",
            lambda m: image_to_html(m.group(1), m.group(2), md_dir, asset_dir, embed_images),
            paragraph,
        )
        if paragraph.startswith('<div class="img-wrap">'):
            html_parts.append(paragraph)
        else:
            html_parts.append(f"<p>{escape_inline(paragraph)}</p>")

    close_lists()
    return "\n".join(html_parts), toc


def build_toc(toc: List[Tuple[str, str]]) -> str:
    if not toc:
        return ""
    items = "\n".join(f'<li><a href="#{sid}">{html.escape(title)}</a></li>' for sid, title in toc)
    return f'<div class="toc"><h2>目录</h2><ol>{items}</ol></div>'


def add_backtop_links(body: str) -> str:
    return re.sub(r"(</h2>)", r"\1", body)


def build_fly_nav(toc: List[Tuple[str, str]]) -> str:
    if not toc:
        return ""
    links = "\n".join(
        f'<a class="fly-nav-link" href="#{sid}" data-target="{sid}">{html.escape(title)}</a>'
        for sid, title in toc
    )
    return f"""<div class="fly-nav" id="flyNav">
  <button class="fly-nav-btn" id="flyNavBtn" aria-label="导航目录">
    <svg viewBox="0 0 24 24"><path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/></svg>
  </button>
  <div class="fly-nav-panel" id="flyNavPanel">
    <div class="fly-nav-header">目录导航</div>
    {links}
    <a class="fly-nav-top" href="#top">
      <svg viewBox="0 0 24 24"><path d="M12 4l-8 8h5v8h6v-8h5z"/></svg>
      回到顶部
    </a>
  </div>
</div>
<div class="fly-nav-progress" id="flyNavProgress"></div>
"""


FLY_NAV_JS = r"""
<script>
(function(){
  var nav = document.getElementById('flyNav');
  var btn = document.getElementById('flyNavBtn');
  var panel = document.getElementById('flyNavPanel');
  var progress = document.getElementById('flyNavProgress');
  var links = panel ? panel.querySelectorAll('.fly-nav-link') : [];
  var sections = [];

  /* collect section elements */
  links.forEach(function(a){
    var t = document.getElementById(a.getAttribute('data-target'));
    if (t) sections.push({el: t, link: a});
  });

  /* toggle */
  btn.addEventListener('click', function(e){
    e.stopPropagation();
    nav.classList.toggle('open');
  });
  document.addEventListener('click', function(e){
    if (!nav.contains(e.target)) nav.classList.remove('open');
  });
  panel.addEventListener('click', function(e){
    if (e.target.classList.contains('fly-nav-link')) nav.classList.remove('open');
  });

  /* scroll spy + progress */
  function onScroll(){
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    var docH = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = docH > 0 ? (scrollTop / docH * 100) + '%' : '0%';

    var active = null;
    for (var i = sections.length - 1; i >= 0; i--){
      if (sections[i].el.getBoundingClientRect().top <= 120) { active = sections[i]; break; }
    }
    links.forEach(function(a){ a.classList.remove('active'); });
    if (active) active.link.classList.add('active');
  }
  window.addEventListener('scroll', onScroll, {passive: true});
  onScroll();
})();
</script>
"""


def render_html(title: str, subtitle: str, body: str, toc_html: str) -> str:
    subtitle_html = f'<div class="subtitle">{escape_inline(subtitle)}</div>' if subtitle else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="container">
    <h1 id="top">{html.escape(title)}</h1>
    {subtitle_html}
    {toc_html}
    {body}
    <div class="footer">样式版本：咨询汇报风格（深蓝 / 黑白灰 / 少量强调色）</div>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument("output", nargs="?", help="Output HTML file")
    parser.add_argument("--title", default="", help="Override report title")
    parser.add_argument("--subtitle", default="", help="Override subtitle")
    parser.add_argument("--asset-dir", default="", help="Directory for local images")
    parser.add_argument("--no-embed-images", action="store_true", help="Do not embed images as base64")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Input file not found: {in_path}", file=sys.stderr)
        return 1

    md = in_path.read_text(encoding="utf-8")
    meta, md = parse_front_matter(md)
    title, subtitle, md_body = extract_title_and_subtitle(md, meta, in_path.stem)

    if args.title:
        title = args.title
    if args.subtitle:
        subtitle = args.subtitle

    asset_dir = Path(args.asset_dir) if args.asset_dir else None
    body_html, toc = convert_markdown(md_body, in_path.parent, asset_dir, not args.no_embed_images)
    toc_html = build_toc(toc)
    toc_data = toc  # keep reference for fly nav
    fly_nav = build_fly_nav(toc_data)
    final_html = render_html(title, subtitle, body_html, toc_html)

    # inject fly nav + JS before </body>
    final_html = final_html.replace('</body>', fly_nav + FLY_NAV_JS + '</body>')

    out_path = Path(args.output) if args.output else in_path.with_name(in_path.stem + "_麦肯锡风格.html")
    out_path.write_text(final_html, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
