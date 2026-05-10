"""
Doc Viewer Service — 上传 Markdown/HTML，返回可查看链接
API:
  POST /upload       — 上传文件或文本
  GET  /view/{id}    — 渲染查看
  GET  /raw/{id}     — 原始内容
  GET  /api/{id}     — JSON 元信息
  GET  /api/list     — 所有文档列表
  DELETE /api/{id}   — 删除文档
"""

import os
import hashlib
import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
import markdown as md_lib

# ── 配置 ──
DATA_DIR = Path(os.getenv("DOC_DATA_DIR", "/data/doc-viewer/data"))
HOST = os.getenv("DOC_HOST", "doc.20100706.xyz")
PORT = int(os.getenv("DOC_PORT", "8080"))
PUBLIC_PORT = int(os.getenv("DOC_PUBLIC_PORT", "0"))
MAX_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {".md", ".markdown", ".html", ".htm", ".txt"}
RETENTION_DAYS = int(os.getenv("DOC_RETENTION_DAYS", "30"))

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _base_url() -> str:
    port = PUBLIC_PORT if PUBLIC_PORT else PORT
    if port == 80:
        return f"http://{HOST}"
    return f"http://{HOST}:{port}"


BASE_URL = _base_url()

app = FastAPI(title="Doc Viewer", version="1.1.0")


# ── 工具函数 ──
def _doc_path(doc_id: str, suffix: str = "") -> Path:
    safe_id = doc_id.replace("/", "").replace("..", "")
    return DATA_DIR / f"{safe_id}{suffix}"


def _doc_meta_path(doc_id: str) -> Path:
    return _doc_path(doc_id, ".meta.json")


def _doc_content_path(doc_id: str) -> Path:
    return _doc_path(doc_id, ".content")


def _save_doc(content: bytes, filename: str, content_type: str) -> dict:
    doc_id = uuid.uuid4().hex[:12]
    now = datetime.utcnow().isoformat() + "Z"

    ext = Path(filename).suffix.lower() if filename else ""
    if ext in (".md", ".markdown") or content_type and "markdown" in content_type:
        fmt = "markdown"
    elif ext in (".html", ".htm") or content_type and "html" in content_type:
        fmt = "html"
    elif ext == ".txt":
        fmt = "text"
    else:
        text = content.decode("utf-8", errors="ignore")
        if "<html" in text.lower() or "<!doctype html" in text.lower():
            fmt = "html"
        else:
            fmt = "markdown"

    _doc_content_path(doc_id).write_bytes(content)

    meta = {
        "id": doc_id,
        "filename": filename,
        "format": fmt,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest()[:16],
        "created_at": now,
        "expires_at": _expiry_time(now, RETENTION_DAYS),
        "url": f"{BASE_URL}/view/{doc_id}",
        "raw_url": f"{BASE_URL}/raw/{doc_id}",
    }
    _doc_meta_path(doc_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def _expiry_time(iso_now: str, days: int) -> str:
    t = datetime.fromisoformat(iso_now.rstrip("Z"))
    return (t + timedelta(days=days)).isoformat() + "Z"


def _load_meta(doc_id: str) -> dict:
    p = _doc_meta_path(doc_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return json.loads(p.read_text())


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _list_all_docs() -> list:
    """扫描数据目录，返回所有文档元信息，按时间倒序"""
    docs = []
    for p in DATA_DIR.glob("*.meta.json"):
        try:
            meta = json.loads(p.read_text())
            docs.append(meta)
        except Exception:
            pass
    docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return docs


# ── HTML 页面模板 ──

# 公共头部样式（VIEW_TEMPLATE 用）
VIEW_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{ --bg: #fafafa; --card: #fff; --border: #e5e5e5; --text: #333; --muted: #888; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #1a1a1a; --card: #242424; --border: #333; --text: #e0e0e0; --muted: #999; }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.7; }}
  .header {{ background: var(--card); border-bottom: 1px solid var(--border);
             padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; }}
  .header a {{ color: var(--muted); text-decoration: none; font-size: 13px; }}
  .header a:hover {{ color: var(--text); }}
  .content {{ max-width: 860px; margin: 0 auto; padding: 32px 24px; }}
  .content h1 {{ font-size: 1.8em; margin: 1em 0 0.5em; }}
  .content h2 {{ font-size: 1.4em; margin: 1em 0 0.4em; }}
  .content h3 {{ font-size: 1.15em; margin: 0.8em 0 0.3em; }}
  .content p {{ margin: 0.6em 0; }}
  .content pre {{ background: var(--card); border: 1px solid var(--border);
                 border-radius: 6px; padding: 16px; overflow-x: auto; margin: 1em 0; }}
  .content code {{ font-family: "SF Mono", "Fira Code", monospace; font-size: 0.9em; }}
  .content :not(pre) > code {{ background: var(--card); border: 1px solid var(--border);
                                padding: 2px 6px; border-radius: 3px; }}
  .content blockquote {{ border-left: 3px solid var(--border); margin: 1em 0;
                         padding: 0.5em 1em; color: var(--muted); }}
  .content img {{ max-width: 100%; border-radius: 6px; }}
  .content table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  .content th, .content td {{ border: 1px solid var(--border); padding: 8px 12px; text-align: left; }}
  .content th {{ background: var(--card); }}
  .content ul, .content ol {{ padding-left: 1.5em; margin: 0.5em 0; }}
  .content a {{ color: #4f94cd; }}
  .meta {{ color: var(--muted); font-size: 12px; margin-top: 2em; padding-top: 1em;
           border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="header">
  <span>📄 {title}</span>
  <div>
    <a href="/raw/{doc_id}">原始文件</a> ·
    <a href="/api/{doc_id}">API</a> ·
    <a href="/">首页</a>
  </div>
</div>
<div class="content">
{body}
</div>
<div class="content meta">
  文件: {filename} · 大小: {size} · 格式: {format} · 上传: {created_at}
</div>
</body>
</html>"""

# HTML 文件预览注入工具栏
HTML_TOOLBAR = """
<script>
(function() {{
  var bar = document.createElement('div');
  bar.id = 'dv-toolbar';
  bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:rgba(255,255,255,0.92);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid #e5e5e5;padding:8px 20px;font:13px -apple-system,BlinkMacSystemFont,sans-serif;color:#888;display:flex;justify-content:space-between;align-items:center;transition:transform 0.3s ease,opacity 0.3s ease;';
  bar.innerHTML = '<span>📄 {filename} <span style="color:#bbb;margin:0 8px;">·</span> {size} <span style="color:#bbb;margin:0 8px;">·</span> {created_at}</span><div><a href="/raw/{doc_id}" style="color:#888;text-decoration:none;margin-left:16px;">原始文件</a><a href="/" style="color:#888;text-decoration:none;margin-left:16px;">首页</a></div>';
  document.body.prepend(bar);
  document.body.style.paddingTop = '44px';

  var lastY = window.scrollY;
  var hideTimer = null;

  function showBar() {{
    bar.style.transform = 'translateY(0)';
    bar.style.opacity = '1';
    document.body.style.paddingTop = '44px';
  }}

  function hideBar() {{
    bar.style.transform = 'translateY(-100%)';
    bar.style.opacity = '0';
    document.body.style.paddingTop = '0';
  }}

  // 滚动时：向下滚隐藏，向上滚显示
  window.addEventListener('scroll', function() {{
    var y = window.scrollY;
    if (y > lastY && y > 60) {{
      hideBar();
    }} else {{
      showBar();
    }}
    lastY = y;

    // 停止滚动 3 秒后自动隐藏
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() {{
      if (window.scrollY > 60) hideBar();
    }}, 3000);
  }}, {{ passive: true }});

  // 点击页面空白处临时显示
  document.addEventListener('click', function(e) {{
    if (e.target === document.body || e.target.tagName === 'DIV' || e.target.tagName === 'MAIN') {{
      showBar();
      clearTimeout(hideTimer);
      hideTimer = setTimeout(function() {{
        if (window.scrollY > 60) hideBar();
      }}, 3000);
    }}
  }});
}})();
</script>
"""


def _render_home_page() -> str:
    """生成主页 HTML（含文件列表）"""
    docs = _list_all_docs()

    # 按天分组
    groups = defaultdict(list)
    for doc in docs:
        try:
            dt = datetime.fromisoformat(doc["created_at"].rstrip("Z"))
            date_key = dt.strftime("%Y-%m-%d")
        except Exception:
            date_key = "未知日期"
        groups[date_key].append(doc)

    # 生成文件列表 HTML
    if not groups:
        list_html = '<div class="empty">暂无文档，上传第一个文件吧 ↑</div>'
    else:
        parts = []
        for date_key in sorted(groups.keys(), reverse=True):
            items = groups[date_key]
            # 日期标题
            today = datetime.utcnow().strftime("%Y-%m-%d")
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            if date_key == today:
                label = "今天"
            elif date_key == yesterday:
                label = "昨天"
            else:
                label = date_key

            parts.append(f'<div class="date-group">')
            parts.append(f'  <div class="date-label">{label}</div>')
            for doc in items:
                fmt = doc.get("format", "text")
                icon = "📝" if fmt == "markdown" else "🌐" if fmt == "html" else "📄"
                fname = doc.get("filename", doc["id"])
                size = _human_size(doc.get("size", 0))
                try:
                    dt = datetime.fromisoformat(doc["created_at"].rstrip("Z"))
                    time_str = dt.strftime("%H:%M")
                except Exception:
                    time_str = ""
                doc_id = doc["id"]
                parts.append(f"""  <a href="/view/{doc_id}" class="file-card">
    <div class="file-icon">{icon}</div>
    <div class="file-info">
      <div class="file-name">{fname}</div>
      <div class="file-meta">{size} · {fmt} · {time_str}</div>
    </div>
  </a>""")
            parts.append('</div>')
        list_html = "\n".join(parts)

    # 统计
    total = len(docs)
    total_size = sum(d.get("size", 0) for d in docs)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Doc Viewer</title>
<style>
  :root {{
    --bg: #f5f7fa;
    --card: #fff;
    --border: #e8ecf1;
    --text: #1a1a2e;
    --muted: #8892a4;
    --accent: #4361ee;
    --accent-light: rgba(67,97,238,0.08);
    --accent-hover: #3a56d4;
    --green: #10b981;
    --shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 4px 16px rgba(0,0,0,0.08);
    --radius: 12px;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0f1117;
      --card: #1a1d27;
      --border: #2a2e3a;
      --text: #e4e6ed;
      --muted: #6b7280;
      --accent: #6381ff;
      --accent-light: rgba(99,129,255,0.1);
      --accent-hover: #7a94ff;
      --green: #34d399;
      --shadow: 0 1px 3px rgba(0,0,0,0.2);
      --shadow-lg: 0 4px 16px rgba(0,0,0,0.3);
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; }}

  /* 顶部导航 */
  .navbar {{
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky; top: 0; z-index: 100;
  }}
  .navbar h1 {{ font-size: 1.15em; font-weight: 600; }}
  .navbar h1 span {{ color: var(--accent); }}
  .stats {{ color: var(--muted); font-size: 13px; }}

  /* 主内容区 */
  .main {{ max-width: 720px; margin: 0 auto; padding: 24px 16px; }}

  /* 上传区 */
  .upload-section {{
    background: var(--card);
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 32px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 32px;
    box-shadow: var(--shadow);
  }}
  .upload-section:hover, .upload-section.dragover {{
    border-color: var(--accent);
    background: var(--accent-light);
  }}
  .upload-icon {{ font-size: 2em; margin-bottom: 8px; }}
  .upload-title {{ font-size: 1em; font-weight: 500; margin-bottom: 4px; }}
  .upload-hint {{ color: var(--muted); font-size: 13px; }}

  /* Tab 切换 */
  .tabs {{
    display: flex; gap: 0; margin-bottom: 24px; background: var(--card);
    border-radius: 10px; padding: 4px; box-shadow: var(--shadow);
  }}
  .tab {{
    flex: 1; padding: 10px 16px; border-radius: 8px;
    cursor: pointer; color: var(--muted); font-size: 14px; font-weight: 500;
    transition: all 0.2s; text-align: center; border: none; background: none;
  }}
  .tab.active {{
    background: var(--accent); color: #fff;
    box-shadow: 0 2px 8px rgba(67,97,238,0.3);
  }}

  /* 文本输入区 */
  .text-area {{
    width: 100%; height: 160px; background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px; font-family: "SF Mono", "Fira Code", monospace;
    font-size: 14px; color: var(--text); resize: vertical; margin-bottom: 12px;
    transition: border-color 0.2s;
  }}
  .text-area:focus {{ outline: none; border-color: var(--accent); }}

  /* 按钮 */
  .btn-row {{ display: flex; gap: 8px; align-items: center; }}
  .btn {{
    background: var(--accent); color: #fff; border: none; padding: 10px 24px;
    border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer;
    transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px;
  }}
  .btn:hover {{ background: var(--accent-hover); transform: translateY(-1px); }}
  .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}
  .btn-outline {{
    background: transparent; color: var(--accent); border: 1px solid var(--accent);
  }}
  .btn-outline:hover {{ background: var(--accent-light); }}

  select {{
    padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border);
    background: var(--card); color: var(--text); font-size: 14px;
  }}

  /* 上传结果 */
  .result {{
    margin-top: 16px; padding: 14px 18px; background: var(--accent-light);
    border: 1px solid var(--accent); border-radius: 10px;
    display: none; word-break: break-all;
  }}
  .result.show {{ display: block; }}
  .result strong {{ color: var(--green); }}
  .result a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
  .result a:hover {{ text-decoration: underline; }}
  .copy-btn {{
    background: var(--accent); color: #fff; border: none; padding: 4px 12px;
    border-radius: 6px; font-size: 12px; cursor: pointer; margin-left: 8px;
  }}

  /* 文件列表区 */
  .section-title {{
    font-size: 0.8em; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;
    padding-bottom: 8px; border-bottom: 1px solid var(--border);
  }}

  .date-group {{ margin-bottom: 24px; }}
  .date-label {{
    font-size: 0.85em; font-weight: 600; color: var(--muted);
    margin-bottom: 8px; padding-left: 4px;
  }}

  .file-card {{
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px; background: var(--card);
    border: 1px solid var(--border); border-radius: var(--radius);
    margin-bottom: 6px; text-decoration: none; color: var(--text);
    transition: all 0.15s ease; box-shadow: var(--shadow);
  }}
  .file-card:hover {{
    border-color: var(--accent); transform: translateX(4px);
    box-shadow: var(--shadow-lg);
  }}
  .file-icon {{
    width: 40px; height: 40px; border-radius: 10px;
    background: var(--accent-light); display: flex; align-items: center;
    justify-content: center; font-size: 1.3em; flex-shrink: 0;
  }}
  .file-info {{ flex: 1; min-width: 0; }}
  .file-name {{
    font-size: 0.95em; font-weight: 500; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }}
  .file-meta {{ font-size: 0.8em; color: var(--muted); margin-top: 2px; }}

  .empty {{
    text-align: center; color: var(--muted); padding: 32px; font-size: 0.95em;
  }}

  .hidden {{ display: none; }}

  /* 响应式 */
  @media (max-width: 600px) {{
    .main {{ padding: 16px 12px; }}
    .navbar {{ padding: 12px 16px; }}
    .upload-section {{ padding: 24px 16px; }}
  }}
</style>
</head>
<body>

<!-- 顶部导航 -->
<div class="navbar">
  <h1>📄 <span>Doc</span> Viewer</h1>
  <div class="stats">{total} 个文档 · {_human_size(total_size)}</div>
</div>

<div class="main">

  <!-- Tab 切换 -->
  <div class="tabs">
    <div class="tab active" onclick="switchTab('file')">📁 上传文件</div>
    <div class="tab" onclick="switchTab('text')">✏️ 粘贴文本</div>
  </div>

  <!-- 文件上传 -->
  <div id="file-tab">
    <form id="upload-form" enctype="multipart/form-data">
      <div class="upload-section" id="dropzone">
        <div class="upload-icon">⬆️</div>
        <div class="upload-title">拖拽文件到此处，或点击选择</div>
        <div class="upload-hint">支持 .md .html .htm .txt · 最大 10MB</div>
        <input type="file" name="file" id="file-input" accept=".md,.markdown,.html,.htm,.txt" style="display:none">
      </div>
      <div class="btn-row">
        <button type="submit" class="btn" id="upload-btn">🚀 上传并获取链接</button>
      </div>
    </form>
  </div>

  <!-- 文本上传 -->
  <div id="text-tab" class="hidden">
    <form id="text-form">
      <textarea class="text-area" name="content" placeholder="在此粘贴 Markdown 或 HTML 内容..."></textarea>
      <div class="btn-row">
        <select name="format">
          <option value="auto">自动检测</option>
          <option value="markdown">Markdown</option>
          <option value="html">HTML</option>
        </select>
        <button type="submit" class="btn">🚀 提交并获取链接</button>
      </div>
    </form>
  </div>

  <!-- 上传结果 -->
  <div id="result" class="result">
    <strong>✅ 上传成功</strong><br>
    <span>预览链接: <a id="view-link" href="" target="_blank"></a>
    <button class="copy-btn" onclick="copyLink()">复制</button></span>
  </div>

  <!-- 文件列表 -->
  <div style="margin-top: 36px;">
    <div class="section-title">📂 所有文档</div>
    {list_html}
  </div>

</div>

<script>
function switchTab(tab) {{
  document.querySelectorAll('.tab').forEach((t, i) => {{
    t.classList.toggle('active', (tab === 'file' ? i === 0 : i === 1));
  }});
  document.getElementById('file-tab').classList.toggle('hidden', tab !== 'file');
  document.getElementById('text-tab').classList.toggle('hidden', tab !== 'text');
}}

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
dropzone.onclick = () => fileInput.click();
dropzone.ondragover = (e) => {{ e.preventDefault(); dropzone.classList.add('dragover'); }};
dropzone.ondragleave = () => dropzone.classList.remove('dragover');
dropzone.ondrop = (e) => {{
  e.preventDefault(); dropzone.classList.remove('dragover');
  fileInput.files = e.dataTransfer.files;
}};

async function handleUpload(formData) {{
  const btn = document.querySelector('.btn[disabled]') || document.getElementById('upload-btn');
  const origText = btn.textContent;
  btn.textContent = '⏳ 上传中...'; btn.disabled = true;
  try {{
    const resp = await fetch('/upload', {{ method: 'POST', body: formData }});
    const data = await resp.json();
    if (data.url) {{
      document.getElementById('view-link').href = data.url;
      document.getElementById('view-link').textContent = data.url;
      document.getElementById('result').classList.add('show');
      // 1秒后刷新页面以更新列表
      setTimeout(() => location.reload(), 1500);
    }} else {{
      alert(data.detail || '上传失败');
    }}
  }} catch(err) {{ alert('上传出错: ' + err.message); }}
  finally {{ btn.textContent = origText; btn.disabled = false; }}
}}

document.getElementById('upload-form').onsubmit = (e) => {{
  e.preventDefault();
  handleUpload(new FormData(e.target));
}};

document.getElementById('text-form').onsubmit = (e) => {{
  e.preventDefault();
  handleUpload(new FormData(e.target));
}};

function copyLink() {{
  const link = document.getElementById('view-link').href;
  navigator.clipboard.writeText(link).then(() => {{
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '已复制!'; setTimeout(() => btn.textContent = '复制', 1500);
  }});
}}
</script>
</body>
</html>"""


# ── 路由 ──
@app.get("/", response_class=HTMLResponse)
async def index():
    return _render_home_page()


@app.post("/upload")
async def upload_doc(
    file: UploadFile = File(default=None),
    content: str = Form(default=""),
    format: str = Form(default="auto"),
):
    """上传文档 — 支持文件上传或文本粘贴"""
    if file and file.filename:
        raw = await file.read()
        if len(raw) > MAX_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        filename = file.filename or "untitled.md"
        meta = _save_doc(raw, filename, file.content_type or "")
    elif content.strip():
        raw = content.encode("utf-8")
        filename = f"paste.{format}" if format != "auto" else "paste.md"
        meta = _save_doc(raw, filename, f"text/{format}" if format != "auto" else "")
    else:
        raise HTTPException(status_code=400, detail="No file or content provided")

    return JSONResponse(meta)


@app.get("/view/{doc_id}", response_class=HTMLResponse)
async def view_doc(doc_id: str):
    """渲染查看文档"""
    meta = _load_meta(doc_id)
    content_path = _doc_content_path(doc_id)
    raw = content_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    fmt = meta.get("format", "markdown")

    if fmt == "html":
        return HTMLResponse(text)

    # Markdown / Text
    if fmt == "markdown":
        body = md_lib.markdown(text, extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br"])
    else:
        body = f"<pre>{text}</pre>"

    title = meta.get("filename", doc_id)
    return VIEW_TEMPLATE.format(
        title=title,
        doc_id=doc_id,
        body=body,
        filename=meta.get("filename", "-"),
        size=_human_size(meta.get("size", 0)),
        format=fmt,
        created_at=meta.get("created_at", "-"),
    )


@app.get("/raw/{doc_id}")
async def raw_doc(doc_id: str):
    """返回原始内容"""
    meta = _load_meta(doc_id)
    content_path = _doc_content_path(doc_id)
    raw = content_path.read_bytes()

    fmt = meta.get("format", "markdown")
    if fmt == "html":
        ct = "text/html; charset=utf-8"
    elif fmt == "markdown":
        ct = "text/markdown; charset=utf-8"
    else:
        ct = "text/plain; charset=utf-8"

    return PlainTextResponse(raw, media_type=ct)


@app.get("/api/{doc_id}")
async def api_meta(doc_id: str):
    """获取文档元信息"""
    meta = _load_meta(doc_id)
    return JSONResponse(meta)


@app.get("/api/list")
async def api_list():
    """获取所有文档列表"""
    return JSONResponse(_list_all_docs())


@app.delete("/api/{doc_id}")
async def delete_doc(doc_id: str):
    """删除文档"""
    meta = _load_meta(doc_id)
    _doc_content_path(doc_id).unlink(missing_ok=True)
    _doc_meta_path(doc_id).unlink(missing_ok=True)
    return JSONResponse({"status": "deleted", "id": doc_id})


# ── 启动入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
