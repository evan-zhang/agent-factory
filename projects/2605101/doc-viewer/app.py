"""
Doc Viewer Service — 上传 Markdown/HTML，返回可查看链接
API:
  POST /upload       — 上传文件或文本
  PUT  /api/{id}     — 更新已有文档
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
import asyncio
import httpx
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, Response
from email.message import Message as _EmailMessage
import multipart.multipart as _mp_mod

# ── 修补 python-multipart 对非 ASCII filename 的 latin-1 编码错误 ──
# python-multipart 的 parse_options_header 将所有参数值用 latin-1 编码
# 中文等 Unicode 字符在 latin-1 编码时触发 UnicodeEncodeError
# 修复：替换为 utf-8 兼容版本


def _utf8_parse_options_header(value):
    """parse_options_header 的 UTF-8 安全版本"""
    if not value:
        return (b"", {})
    if isinstance(value, bytes):
        value = value.decode("latin-1")
    if ";" not in value:
        return (value.lower().strip().encode("latin-1"), {})
    message = _EmailMessage()
    message["content-type"] = value
    params = message.get_params()
    if not params:
        return (value.lower().strip().encode("latin-1"), {})
    ctype = params.pop(0)[0].encode("latin-1")
    options = {}
    for param in params:
        key, val = param
        if isinstance(val, tuple):
            val = val[-1]
        if key == "filename":
            if val[1:3] == ":\\" or val[:2] == "\\\\":
                val = val.split("\\")[-1]
        # 关键修改：用 utf-8 替代 latin-1，支持中文等 Unicode 字符
        options[key.encode("latin-1")] = val.encode("utf-8")
    return ctype, options


_mp_mod.parse_options_header = _utf8_parse_options_header

# 同时 patch starlette.formparsers 中的引用
# Starlette 用 from ... import 导入，创建了本地引用，必须直接替换
try:
    import python_multipart.multipart as _pmp
    _pmp.parse_options_header = _utf8_parse_options_header
except ImportError:
    pass
try:
    import starlette.formparsers as _sfp
    _sfp.parse_options_header = _utf8_parse_options_header
    _orig_user_safe_decode = _sfp._user_safe_decode
    def _patched_user_safe_decode(src, codec):
        # codec 为空时优先 utf-8
        if not codec:
            codec = "utf-8"
        return _orig_user_safe_decode(src, codec)
    _sfp._user_safe_decode = _patched_user_safe_decode
except ImportError:
    pass

import markdown as md_lib

# ── 配置 ──
DATA_DIR = Path(os.getenv("DOC_DATA_DIR", "/data/doc-viewer/data"))
HOST = os.getenv("DOC_HOST", "doc.20100706.xyz")
PORT = int(os.getenv("DOC_PORT", "8080"))
PUBLIC_PORT = int(os.getenv("DOC_PUBLIC_PORT", "0"))
MAX_SIZE = 10 * 1024 * 1024  # 10MB

# 北京时区 (UTC+8)
BJ_TZ = timezone(timedelta(hours=8))

def _bj(dt: datetime) -> datetime:
    """把 UTC datetime 转换为北京时区"""
    return dt.replace(tzinfo=timezone.utc).astimezone(BJ_TZ)

def _fmt_bj(iso_str: str) -> str:
    """把 UTC ISO 字符串转为北京时区格式化字符串"""
    try:
        dt = datetime.fromisoformat(iso_str.rstrip("Z"))
        return _bj(dt).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str[:19].replace("T", " ") if iso_str else "-"

ALLOWED_EXT = {".md", ".markdown", ".html", ".htm"}
RETENTION_DAYS = int(os.getenv("DOC_RETENTION_DAYS", "30"))

# AI 标签配置
AI_BASE_URL = os.getenv("DOC_AI_BASE_URL", "https://api.z.ai/v1")
AI_KEY = os.getenv("DOC_AI_KEY", "")
AI_MODEL = os.getenv("DOC_AI_MODEL", "evanModel")

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _base_url() -> str:
    port = PUBLIC_PORT if PUBLIC_PORT else PORT
    if port == 80:
        return f"http://{HOST}"
    return f"http://{HOST}:{port}"


BASE_URL = _base_url()

app = FastAPI(title="Doc Viewer", version="1.3.0")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """兜底异常处理，避免 multipart 解码等底层错误返回裸 500"""
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {type(exc).__name__}: {exc}"},
    )


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
        "starred": False,
        "tags": [],
    }
    _doc_meta_path(doc_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # 异步 AI 标签生成（不阻塞上传响应）
    try:
        text_preview = content.decode("utf-8", errors="ignore")[:800]
        asyncio.create_task(_generate_tags(doc_id, filename, text_preview))
    except Exception:
        pass

    return meta


async def _generate_tags(doc_id: str, filename: str, content_preview: str) -> None:
    """异步生成 AI 标签，写入 meta.json"""
    if not AI_KEY:
        return
    try:
        prompt = (
            f"请为以下文档生成 2-5 个简短的中文标签（每个标签不超过6个字）。"
            f"只返回标签，用逗号分隔，不要其他内容。\n\n"
            f"文件名：{filename}\n内容摘要：{content_preview[:500]}"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{AI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 60,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            # 解析标签：按逗号/换行分割，过滤空标签
            tags = [t.strip() for t in re.split(r"[，,、\n]", content_text) if t.strip()]
            tags = [t for t in tags if len(t) <= 6][:5]
            if not tags:
                return
            # 写回 meta
            meta = _load_meta(doc_id)
            meta["tags"] = tags
            _doc_meta_path(doc_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    except Exception:
        # AI 生成失败静默忽略，不影响主流程
        pass


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
            meta["bj_time"] = _fmt_bj(meta.get("created_at", ""))
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
    <button id="tb-star" onclick="toggleTbStar()" style="background:none;border:none;cursor:pointer;font-size:1em;padding:0 4px;vertical-align:middle;" title="{starred_label}">{star_icon}</button>
    <a href="/raw/{doc_id}">原始文件</a> ·
    <a href="/api/{doc_id}">API</a> ·
    <button onclick="copyDocLink()" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:13px;padding:0;vertical-align:middle;" title="复制链接">🔗 复制</button> ·
    <a href="/favorites">⭐收藏</a> ·
    <a href="/">首页</a>
  </div>
</div>
<div class="content">
{body}
</div>
<div class="content meta">
  文件: {filename} · 大小: {size} · 格式: {format} · 上传: {created_at}
</div>
<script>
async function toggleTbStar() {{
  var docId = '{doc_id}';
  try {{
    var resp = await fetch('/api/' + docId + '/star', {{ method: 'PUT' }});
    var data = await resp.json();
    var btn = document.getElementById('tb-star');
    if (btn) {{
      btn.textContent = data.starred ? '⭐' : '☆';
      btn.title = data.starred ? '取消收藏' : '收藏';
    }}
  }} catch(e) {{}}
}}
function copyDocLink() {{
  var docId = '{doc_id}';
  navigator.clipboard.writeText(location.origin + '/view/' + docId).then(() => {{
    var btn = event.target;
    var orig = btn.textContent;
    btn.textContent = '已复制!';
    setTimeout(function() {{ btn.textContent = orig; }}, 1500);
  }});
}}
</script>
</body>
</html>"""

# HTML 文件预览注入工具栏
HTML_TOOLBAR = """
<script>
(function() {{
  var bar = document.createElement('div');
  bar.id = 'dv-toolbar';
  bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:rgba(255,255,255,0.92);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid #e5e5e5;padding:8px 20px;font:13px -apple-system,BlinkMacSystemFont,sans-serif;color:#888;display:flex;justify-content:space-between;align-items:center;transition:transform 0.3s ease,opacity 0.3s ease;';
  bar.innerHTML = '<span>📄 {filename} <span style="color:#bbb;margin:0 8px;">·</span> {size} <span style="color:#bbb;margin:0 8px;">·</span> {created_at}</span><div><button id="tb-star" onclick="toggleTbStar()" style="background:none;border:none;cursor:pointer;font-size:1em;padding:0 4px;" title="收藏">{star_icon}</button><button onclick="copyDocLink()" style="background:none;border:none;cursor:pointer;font-size:1em;padding:0 4px;" title="复制链接">🔗</button><a href="/raw/{doc_id}" style="color:#888;text-decoration:none;margin-left:8px;">原始文件</a><a href="/favorites" style="color:#888;text-decoration:none;margin-left:8px;">⭐收藏</a><a href="/" style="color:#888;text-decoration:none;margin-left:8px;">首页</a></div>';
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

async function copyDocLink() {{
  var docId = '{doc_id}';
  navigator.clipboard.writeText(location.origin + '/view/' + docId).then(function() {{
    var btn = document.querySelector('[onclick="copyDocLink()"]');
    if (btn) {{
      var orig = btn.textContent;
      btn.textContent = '已复制!';
      setTimeout(function() {{ btn.textContent = orig; }}, 1500);
    }}
  }});
}}

async function toggleTbStar() {{
  var docId = '{doc_id}';
  try {{
    var resp = await fetch('/api/' + docId + '/star', {{ method: 'PUT' }});
    var data = await resp.json();
    var btn = document.getElementById('tb-star');
    if (btn) {{
      btn.textContent = data.starred ? '⭐' : '☆';
      btn.title = data.starred ? '取消收藏' : '收藏';
    }}
  }} catch(e) {{}}
}}
</script>
"""


def _render_favorites_page() -> str:
    """生成收藏页 HTML"""
    docs = _list_all_docs()
    starred = [d for d in docs if d.get("starred", False)]
    starred.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # 聚合所有标签及出现次数
    tag_counts = defaultdict(int)
    for d in starred:
        for t in d.get("tags", []):
            tag_counts[t] += 1
    all_tags = sorted(tag_counts.items(), key=lambda x: -x[1])

    # 生成分组列表 HTML
    def file_card(doc, show_tags=True):
        fmt = doc.get("format", "text")
        icon = "📝" if fmt == "markdown" else "🌐" if fmt == "html" else "📄"
        fname = doc.get("filename", doc["id"])
        size = _human_size(doc.get("size", 0))
        try:
            dt = datetime.fromisoformat(doc["created_at"].rstrip("Z"))
            time_str = _bj(dt).strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = ""
        doc_id = doc["id"]
        tags_html = ""
        if show_tags and doc.get("tags"):
            tags_html = "<div class=\"file-tags\">" + "".join(
                f'<span class="tag">{t}</span>' for t in doc["tags"]
            ) + "</div>"
        return f'''
  <a href="/view/{doc_id}" class="file-card">
    <div class="file-icon">{icon}</div>
    <div class="file-info">
      <div class="file-name">{fname}</div>
      <div class="file-meta">{size} · {time_str}</div>
      {tags_html}
    </div>
    <button class="star-btn starred" onclick="toggleStar(event, '{doc_id}', false)" title="取消收藏">⭐</button>
  </a>'''

    list_html = ""
    if not starred:
        list_html = '<div class="empty">暂无收藏内容，给文档点个星标吧 ↑</div>'
    else:
        # 按天分组
        groups = defaultdict(list)
        for doc in starred:
            date_key = doc.get("created_at", "")[:10]
            groups[date_key].append(doc)
        for date_key in sorted(groups.keys(), reverse=True):
            items = groups[date_key]
            today_s = datetime.utcnow().strftime("%Y-%m-%d")
            yesterday_s = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            if date_key == today_s:
                label = "今天"
            elif date_key == yesterday_s:
                label = "昨天"
            else:
                label = date_key
            list_html += f'<div class="date-group">'
            list_html += f'  <div class="date-label">{label}</div>'
            for doc in items:
                list_html += file_card(doc)
            list_html += '</div>'

    # 标签云 HTML
    if all_tags:
        tags_cloud_html = '<div class="tags-cloud">'
        tags_cloud_html += f'<button class="tag-btn active" onclick="filterTag('')">全部</button>'
        for tag, count in all_tags:
            tags_cloud_html += f'<button class="tag-btn" onclick="filterTag(\'{tag}\')">{tag} <span class="tag-count">{count}</span></button>'
        tags_cloud_html += '</div>'
    else:
        tags_cloud_html = ''

    total = len(starred)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⭐ 收藏 — Doc Viewer</title>
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
    --star-color: #f59e0b;
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
      --star-color: #f59e0b;
      --green: #34d399;
      --shadow: 0 1px 3px rgba(0,0,0,0.2);
      --shadow-lg: 0 4px 16px rgba(0,0,0,0.3);
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; }}

  .navbar {{
    background: var(--card); border-bottom: 1px solid var(--border);
    padding: 16px 24px; display: flex; justify-content: space-between; align-items: center;
    position: sticky; top: 0; z-index: 100;
  }}
  .navbar h1 {{ font-size: 1.15em; font-weight: 600; }}
  .navbar h1 span {{ color: var(--star-color); }}
  .stats {{ color: var(--muted); font-size: 13px; }}

  .main {{ max-width: 720px; margin: 0 auto; padding: 24px 16px; }}

  .tags-cloud {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px;
    padding: 16px; background: var(--card); border-radius: var(--radius);
    box-shadow: var(--shadow);
  }}
  .tag-btn {{
    padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border);
    background: var(--card); color: var(--text); font-size: 13px; cursor: pointer;
    transition: all 0.2s; display: inline-flex; align-items: center; gap: 4px;
  }}
  .tag-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
  .tag-btn.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .tag-count {{ font-size: 11px; opacity: 0.7; }}

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
  .file-tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }}
  .tag {{
    padding: 2px 8px; border-radius: 10px;
    background: var(--accent-light); color: var(--accent);
    font-size: 0.75em;
  }}
  .star-btn {{
    background: none; border: none; font-size: 1.1em;
    cursor: pointer; padding: 4px 6px; border-radius: 6px;
    transition: transform 0.15s; flex-shrink: 0;
  }}
  .star-btn:hover {{ transform: scale(1.2); }}
  .icon-btn {{
    background: none; border: none; font-size: 1.1em;
    cursor: pointer; padding: 4px 6px; border-radius: 6px;
    transition: transform 0.15s; flex-shrink: 0;
  }}
  .icon-btn:hover {{ transform: scale(1.2); }}

  .empty {{
    text-align: center; color: var(--muted); padding: 48px 32px; font-size: 0.95em;
  }}

  @media (max-width: 600px) {{
    .main {{ padding: 16px 12px; }}
    .navbar {{ padding: 12px 16px; }}
  }}
</style>
</head>
<body>

<div class="navbar">
  <h1>⭐ <span>收藏</span></h1>
  <div class="stats">{total} 个收藏</div>
</div>

<div class="main">
  {tags_cloud_html}

  <div id="file-list">
    {list_html}
  </div>
</div>

<script>
let currentTag = '';

function filterTag(tag) {{
  currentTag = tag;
  document.querySelectorAll('.tag-btn').forEach(btn => {{
    const isActive = (tag === '' && btn.textContent.includes('全部')) || btn.textContent.startsWith(tag + ' ');
    btn.classList.toggle('active', tag === '' ? btn.textContent.includes('全部') : btn.textContent.startsWith(tag + ' '));
  }});
  loadFavorites();
}}

async function loadFavorites() {{
  const url = currentTag ? '/api/favorites?tag=' + encodeURIComponent(currentTag) : '/api/favorites';
  const resp = await fetch(url);
  const data = await resp.json();
  const docs = data.docs || [];
  const listEl = document.getElementById('file-list');
  if (!docs.length) {{
    listEl.innerHTML = '<div class="empty">该标签下暂无收藏内容</div>';
    return;
  }}
  // 按天分组
  const groups = {{}};
  docs.forEach(doc => {{
    const dk = doc.bj_time ? doc.bj_time.slice(0, 10) : '';
    if (!groups[dk]) groups[dk] = [];
    groups[dk].push(doc);
  }});
  let html = '';
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  Object.keys(groups).sort().reverse().forEach(dateKey => {{
    const label = dateKey === today ? '今天' : dateKey === yesterday ? '昨天' : dateKey;
    html += `<div class="date-group"><div class="date-label">${{label}}</div>`;
    groups[dateKey].forEach(doc => {{
      const icon = doc.format === 'markdown' ? '📝' : doc.format === 'html' ? '🌐' : '📄';
      const size = doc.size ? formatSize(doc.size) : '';
      const time = doc.bj_time ? doc.bj_time.slice(11) : '';
      const tagsHtml = doc.tags && doc.tags.length
        ? `<div class="file-tags">${{doc.tags.map(t => `<span class="tag">${{t}}</span>`).join('')}}</div>`
        : '';
      html += `<a href="/view/${{doc.id}}" class="file-card">
        <div class="file-icon">${{icon}}</div>
        <div class="file-info">
          <div class="file-name">${{doc.filename || doc.id}}</div>
          <div class="file-meta">${{size}} · ${{time}}</div>
          ${{tagsHtml}}
        </div>
        <button class="star-btn starred" onclick="toggleStar(event, doc.id, false)" title="取消收藏">⭐</button>
      </a>`;
    }});
    html += '</div>';
  }});
  listEl.innerHTML = html;
}}

function formatSize(n) {{
  if (n < 1024) return n + ' B';
  if (n < 1024*1024) return (n/1024).toFixed(1) + ' KB';
  return (n/1024/1024).toFixed(1) + ' MB';
}}

async function toggleStar(event, docId, reload=true) {{
  event.preventDefault();
  event.stopPropagation();
  try {{
    const resp = await fetch('/api/' + docId + '/star', {{ method: 'PUT' }});
    const data = await resp.json();
    if (reload && !data.starred) {{
      // 取消收藏后刷新列表
      loadFavorites();
    }} else if (reload) {{
      loadFavorites();
    }}
  }} catch(err) {{ console.error(err); }}
}}
</script>
</body>
</html>'''


def _render_home_page() -> str:
    """生成主页 HTML（含文件列表，默认显示最近3天）"""
    docs = _list_all_docs()

    # 按天分组
    groups = defaultdict(list)
    for doc in docs:
        try:
            dt = datetime.fromisoformat(doc["created_at"].rstrip("Z"))
            date_key = _bj(dt).strftime("%Y-%m-%d")
        except Exception:
            date_key = "未知日期"
        groups[date_key].append(doc)

    sorted_dates = sorted(groups.keys(), reverse=True)
    # 默认显示最近3天
    initial_dates = sorted_dates[:3]
    initial_docs = []
    for dk in initial_dates:
        initial_docs.extend(groups[dk])
    has_more = len(sorted_dates) > 3

    # 生成文件列表 HTML（只显示初始3天）
    if not initial_docs:
        list_html = '<div class="empty">暂无文档，上传第一个文件吧 ↑</div>'
    else:
        parts = []
        for date_key in initial_dates:
            items = groups.get(date_key, [])
            # 日期标题
            today = datetime.now(BJ_TZ).strftime("%Y-%m-%d")
            yesterday = (datetime.now(BJ_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
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
                    time_str = _bj(dt).strftime("%H:%M")
                except Exception:
                    time_str = ""
                doc_id = doc["id"]
                starred = doc.get("starred", False)
                star_icon = "⭐" if starred else "☆"
                star_class = "starred" if starred else ""
                starred_label = "取消收藏" if starred else "收藏"
                tags = doc.get("tags", [])
                tags_html = ""
                if tags:
                    tags_html = "<div class=\"file-tags\">" + "".join(f'<span class=\"tag\">{t}</span>' for t in tags) + "</div>"
                parts.append(f'''<a href="/view/{doc_id}" class="file-card">
    <div class="file-icon">{icon}</div>
    <div class="file-info">
      <div class="file-name">{fname}</div>
      <div class="file-meta">{size} · {fmt} · {time_str}</div>
      {tags_html}
    </div>
    <input type="file" id="update-file-{doc_id}" style="display:none" onchange="doUpdate('{doc_id}', this.files[0])"><button class="icon-btn" onclick="openUpdate('{doc_id}')" title="更新文件">📤</button>
    <button class="icon-btn" onclick="copyUrl('/raw/{doc_id}', this)" title="复制链接">🔗</button>
    <button class="star-btn {star_class}" onclick="toggleStar(event, '{doc_id}')" title="{starred_label}">{star_icon}</button>
  </a>''')
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
    --star-color: #f59e0b;
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
      --star-color: #f59e0b;
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
  .upload-section:hover {{ border-color: var(--accent); }}
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
  <div>
    <a href="/favorites" style="color: var(--star-color, #f59e0b); text-decoration: none; font-size: 13px; margin-right: 12px;">⭐ 收藏</a>
    <span class="stats">{total} 个文档 · {_human_size(total_size)}</span>
  </div>
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
        <div class="upload-title">点击选择文件，或直接提交（使用上次选择的文件）</div>
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
    <div id="load-more-wrap" style="text-align:center;margin-top:16px;{('' if has_more else ' display:none')}">
      <button class="btn" id="load-more-btn" onclick="loadMore()">📜 查看更多</button>
    </div>
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

const fileInput = document.getElementById('file-input');
document.getElementById('dropzone').onclick = () => fileInput.click();

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

function copyUrl(url, btn) {{
  navigator.clipboard.writeText(url).then(() => {{
    const orig = btn.textContent;
    btn.textContent = '已复制!';
    setTimeout(() => btn.textContent = orig, 1500);
  }});
}}

function copyLink() {{
  const link = document.getElementById('view-link').href;
  const btn = document.querySelector('.copy-btn');
  navigator.clipboard.writeText(link).then(() => {{
    const orig = btn.textContent;
    btn.textContent = '已复制!';
    setTimeout(() => btn.textContent = orig, 1500);
  }});
}}

// 加载更多
let offsetDays = 3;
let hasMore = {str(has_more).lower()};

async function loadMore() {{
  const btn = document.getElementById('load-more-btn');
  btn.textContent = '⏳ 加载中...';
  btn.disabled = true;
  try {{
    const resp = await fetch(`/api/list/page?days=7&' + offsetDays`);
    const data = await resp.json();
    const groups = data.groups || [];
    if (!groups.length) {{
      document.getElementById('load-more-wrap').style.display = 'none';
      hasMore = false;
      return;
    }}
    // 追加到文件列表
    let html = '';
    groups.forEach(g => {{
      html += `<div class="date-group"><div class="date-label">${{g.date}}</div>`;
      g.items.forEach(doc => {{
        const icon = doc.format === 'markdown' ? '📝' : doc.format === 'html' ? '🌐' : '📄';
        const size = doc.size ? formatSize(doc.size) : '';
        const time = doc.created_at ? new Date(doc.created_at).toLocaleTimeString('zh-CN', {{hour:'2-digit',minute:'2-digit'}}) : '';
        const starred = doc.starred || false;
        const starIcon = starred ? '⭐' : '☆';
        const starClass = starred ? 'starred' : '';
        const tags = doc.tags || [];
        const tagsHtml = tags.length ? `<div class="file-tags">${{tags.map(t => `<span class="tag">${{t}}</span>`).join('')}}</div>` : '';
        html += `<a href="/view/${{doc.id}}" class="file-card">
  <div class="file-icon">${{icon}}</div>
  <div class="file-info">
    <div class="file-name">${{doc.filename || doc.id}}</div>
    <div class="file-meta">${{size}} · ${{doc.format}} · ${{time}}</div>
    ${{tagsHtml}}
  </div>
  <input type="file" id="update-file-${{doc.id}}" style="display:none" onchange="doUpdate(doc.id, this.files[0])"><button class="icon-btn" onclick="openUpdate(doc.id)" title="更新文件">📤</button>
  <button class="icon-btn" onclick="copyUrl('/raw/' + doc.id, this)" title="复制链接">🔗</button>
  <button class="star-btn" onclick="toggleStar(event, doc.id)" title="{{starIcon ? '取消收藏' : '收藏'}}">{{starIcon}}</button>
</a>`;
      }});
      html += '</div>';
    }});
    // 插入到加载更多按钮之前
    const wrap = document.getElementById('load-more-wrap');
    const div = document.createElement('div');
    div.innerHTML = html;
    wrap.parentNode.insertBefore(div, wrap);
    offsetDays += 7;
    if (!data.has_more) {{
      wrap.style.display = 'none';
      hasMore = false;
    }} else {{
      btn.textContent = '📜 查看更多';
      btn.disabled = false;
    }}
  }} catch(err) {{
    alert('加载失败: ' + err.message);
    btn.textContent = '📜 查看更多';
    btn.disabled = false;
  }}
}}

function formatSize(n) {{
  if (n < 1024) return n + ' B';
  if (n < 1024*1024) return (n/1024).toFixed(1) + ' KB';
  return (n/1024/1024).toFixed(1) + ' MB';
}}

async function toggleStar(event, docId) {{
  event.preventDefault();
  event.stopPropagation();
  try {{
    const resp = await fetch('/api/' + docId + '/star', {{ method: 'PUT' }});
    const data = await resp.json();
    document.querySelectorAll(`.star-btn[onclick*="' + docId + '"]`).forEach(btn => {{
      btn.textContent = data.starred ? '⭐' : '☆';
      btn.className = `star-btn ${{data.starred ? 'starred' : ''}}`;
      btn.title = data.starred ? '取消收藏' : '收藏';
    }});
  }} catch(err) {{ console.error(err); }}
}}

// ── 更新上传 ──
function openUpdate(docId) {{
  console.log('openUpdate clicked:', docId);
  const input = document.getElementById('update-file-' + docId);
  if (input) {{ input.click(); }} else {{ console.error('input not found'); }}
}}
async function doUpdate(docId, file) {{
  if (!file) return;
  try {{
    const form = new FormData();
    form.append('file', file);
    const resp = await fetch('/api/' + docId, {{ method: 'PUT', body: form }});
    if (!resp.ok) throw new Error(await resp.text());
    alert('更新成功！');
    location.reload();
  }} catch(e) {{
    alert('更新失败: ' + e.message);
  }}
}}
</script>

<!-- 动态生成的更新上传 input（通过 JS 插入每个卡片） -->
</body>
</html>"""


# ── 路由 ──
@app.get("/", response_class=HTMLResponse)
async def index():
    html = _render_home_page()
    return Response(content=html.encode("utf-8"), media_type="text/html")


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

        # 处理文件名编码：兼容中文等非 ASCII 字符
        try:
            filename = file.filename or "untitled.md"
            # 确保 filename 是有效的 str
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="replace")
        except Exception:
            filename = "untitled.md"

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXT))}")
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
        starred = meta.get("starred", False)
        toolbar = HTML_TOOLBAR.format(
            filename=meta.get("filename", "-"),
            size=_human_size(meta.get("size", 0)),
            created_at=_fmt_bj(meta.get("created_at", "")),
            doc_id=doc_id,
            star_icon="⭐" if starred else "☆",
        )
        if "</body>" in text:
            text = text.replace("</body>", toolbar + "</body>", 1)
        else:
            text += toolbar
        return Response(content=text.encode("utf-8"), media_type="text/html")

    # Markdown / Text
    if fmt == "markdown":
        body = md_lib.markdown(text, extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br"])
    else:
        body = f"<pre>{text}</pre>"

    title = meta.get("filename", doc_id)
    starred = meta.get("starred", False)
    html = VIEW_TEMPLATE.format(
        title=title,
        doc_id=doc_id,
        body=body,
        filename=meta.get("filename", "-"),
        size=_human_size(meta.get("size", 0)),
        format=fmt,
        created_at=_fmt_bj(meta.get("created_at", "")),
        starred_label=("取消收藏" if starred else "收藏"),
        star_icon=("⭐" if starred else "☆"),
    )
    return Response(content=html.encode("utf-8"), media_type="text/html")


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


@app.get("/api/list")
async def api_list():
    """获取所有文档列表"""
    return JSONResponse(_list_all_docs())


@app.get("/api/{doc_id}")
async def api_meta(doc_id: str):
    """获取文档元信息"""
    meta = _load_meta(doc_id)
    return JSONResponse(meta)


@app.put("/api/{doc_id}")
async def update_doc(
    doc_id: str,
    file: UploadFile = File(default=None),
    content: str = Form(default=""),
    format: str = Form(default="auto"),
):
    """更新已有文档 — 支持文件上传或文本粘贴，保留 doc_id 和链接不变"""
    meta = _load_meta(doc_id)

    if file and file.filename:
        raw = await file.read()
        if len(raw) > MAX_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        try:
            filename = file.filename or meta.get("filename", "untitled.md")
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="replace")
        except Exception:
            filename = meta.get("filename", "untitled.md")
    elif content.strip():
        raw = content.encode("utf-8")
        filename = meta.get("filename", "paste.md")
    else:
        raise HTTPException(status_code=400, detail="No file or content provided")

    # 覆盖内容
    _doc_content_path(doc_id).write_bytes(raw)

    # 判断格式
    ext = Path(filename).suffix.lower() if filename else ""
    if ext in (".md", ".markdown") or format == "markdown":
        fmt = "markdown"
    elif ext in (".html", ".htm") or format == "html":
        fmt = "html"
    elif ext == ".txt":
        fmt = "text"
    else:
        # 保留原格式
        fmt = meta.get("format", "markdown")

    # 更新元信息（保留 id、created_at、url、expires_at）
    now = datetime.utcnow().isoformat() + "Z"
    meta["filename"] = filename
    meta["format"] = fmt
    meta["size"] = len(raw)
    meta["sha256"] = hashlib.sha256(raw).hexdigest()[:16]
    meta["updated_at"] = now

    _doc_meta_path(doc_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return JSONResponse(meta)


@app.delete("/api/{doc_id}")
async def delete_doc(doc_id: str):
    """删除文档"""
    meta = _load_meta(doc_id)
    _doc_content_path(doc_id).unlink(missing_ok=True)
    _doc_meta_path(doc_id).unlink(missing_ok=True)
    return JSONResponse({"status": "deleted", "id": doc_id})


@app.put("/api/{doc_id}/star")
async def toggle_star(doc_id: str):
    """切换星标状态"""
    meta = _load_meta(doc_id)
    meta["starred"] = not meta.get("starred", False)
    _doc_meta_path(doc_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return JSONResponse(meta)


@app.get("/api/list/page")
async def api_list_page(
    days: int = Query(default=3),
    offset_days: int = Query(default=0),
):
    """
    分页获取文档列表。
    - offset_days: 从今天往前偏移多少天开始
    - days: 取多少天的数据
    """
    all_docs = _list_all_docs()
    today = datetime.now(BJ_TZ).date()
    cutoff = (today - timedelta(days=offset_days)).isoformat()
    cutoff_prev = (today - timedelta(days=offset_days + days)).isoformat()

    # 取在 [cutoff_prev, cutoff) 区间内的文档
    window = [d for d in all_docs if cutoff_prev <= d.get("created_at", "")[:10] < cutoff]
    # 判断是否还有更多（是否有文档不在当前窗口内）
    window_ids = {d["id"] for d in window}
    has_more = any(d["id"] not in window_ids for d in all_docs)

    # 按天分组
    groups = defaultdict(list)
    for doc in window:
        date_key = doc["created_at"][:10]
        groups[date_key].append(doc)

    result_parts = []
    for date_key in sorted(groups.keys(), reverse=True):
        items = groups[date_key]
        today_s = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday_s = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        if date_key == today_s:
            label = "今天"
        elif date_key == yesterday_s:
            label = "昨天"
        else:
            label = date_key
        result_parts.append({"date": label, "date_key": date_key, "items": items})

    return JSONResponse({"groups": result_parts, "has_more": has_more})


@app.get("/api/favorites")
async def api_favorites(tag: str = Query(default="")):
    """获取星标文件列表，可按标签过滤"""
    all_docs = _list_all_docs()
    starred = [d for d in all_docs if d.get("starred", False)]
    if tag:
        starred = [d for d in starred if tag in d.get("tags", [])]
    # 按时间倒序
    starred.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return JSONResponse({"docs": starred})


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page():
    """收藏页 HTML"""
    html = _render_favorites_page()
    return Response(content=html.encode("utf-8"), media_type="text/html")


# ── 启动入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
