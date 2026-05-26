from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


FRONTMATTER_RE = re.compile(r"^---\s*$([\s\S]*?)^---\s*$", re.MULTILINE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def safe_read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return default


def safe_write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, "utf-8")
    tmp.replace(path)


def compute_fingerprint(trigger: str, action: str) -> str:
    normalized = (trigger.strip() + "\n" + action.strip()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()[:16]


def parse_frontmatter_md(text: str) -> dict[str, Any]:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, Any] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                out[key] = []
            else:
                out[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")]
            continue
        if val.lower() in ("true", "false"):
            out[key] = val.lower() == "true"
            continue
        try:
            if "." in val:
                out[key] = float(val)
            else:
                out[key] = int(val)
            continue
        except Exception:
            pass
        out[key] = val.strip('"').strip("'")
    return out


def render_frontmatter_md(frontmatter: dict[str, Any]) -> str:
    lines: list[str] = ["---"]
    for key in sorted(frontmatter.keys()):
        val = frontmatter[key]
        if isinstance(val, list):
            rendered = "[" + ", ".join(str(x) for x in val) + "]"
        elif isinstance(val, bool):
            rendered = "true" if val else "false"
        else:
            rendered = str(val)
        lines.append(f"{key}: {rendered}")
    lines.append("---")
    return "\n".join(lines)


def upsert_frontmatter_md(original: str, patch: dict[str, Any]) -> str:
    current = parse_frontmatter_md(original)
    merged = {**current, **patch}
    body = original
    m = FRONTMATTER_RE.search(original)
    if m:
        body = original[m.end() :].lstrip("\n")
    fm = render_frontmatter_md(merged)
    return fm + "\n\n" + body


@dataclass(frozen=True)
class Instinct:
    path: Path
    frontmatter: dict[str, Any]
    title: str
    trigger: str
    action: str

    @property
    def id(self) -> str:
        v = self.frontmatter.get("id")
        return str(v) if v else self.path.stem

    @property
    def status(self) -> str:
        v = self.frontmatter.get("status")
        return str(v).lower() if v else "active"

    @property
    def confidence(self) -> float:
        try:
            return float(self.frontmatter.get("confidence", 0.6))
        except Exception:
            return 0.6

    @property
    def tags(self) -> list[str]:
        v = self.frontmatter.get("tags")
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    @property
    def last_used(self) -> str | None:
        v = self.frontmatter.get("last_used")
        return str(v) if v else None


def resolve_data_dir(base_dir: Path, data_dir: str | None = None) -> Path:
    """
    Resolve the directory that stores instinct data (instincts/*.md + instincts/index.json).

    Priority:
    1) explicit CLI arg `--data-dir`
    2) env INSTINCT_LEARNER_DATA_DIR
    3) default: <base_dir>/instincts (PRD default)
    """
    if data_dir and str(data_dir).strip():
        return Path(str(data_dir)).expanduser().resolve()
    env_dir = (os.environ.get("INSTINCT_LEARNER_DATA_DIR") or "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return base_dir / "instincts"


def instincts_dir(base_dir: Path, data_dir: str | None = None) -> Path:
    return resolve_data_dir(base_dir, data_dir)


def archived_dir(base_dir: Path, data_dir: str | None = None) -> Path:
    return instincts_dir(base_dir, data_dir) / "archived"


def index_path(base_dir: Path, data_dir: str | None = None) -> Path:
    return instincts_dir(base_dir, data_dir) / "index.json"


def ensure_dirs(base_dir: Path, data_dir: str | None = None) -> None:
    instincts_dir(base_dir, data_dir).mkdir(parents=True, exist_ok=True)
    archived_dir(base_dir, data_dir).mkdir(parents=True, exist_ok=True)


def read_config(base_dir: Path, override_path: str | None = None) -> dict[str, Any]:
    path = Path(override_path).resolve() if override_path else base_dir / "config.json"
    return safe_read_json(path, {})


def list_instinct_files(base_dir: Path, data_dir: str | None = None) -> list[Path]:
    ensure_dirs(base_dir, data_dir)
    return sorted(instincts_dir(base_dir, data_dir).glob("*.md"))


def read_instinct(path: Path) -> Instinct:
    text = path.read_text("utf-8", errors="replace")
    fm = parse_frontmatter_md(text)
    title = fm.get("title") if isinstance(fm.get("title"), str) else path.stem
    lines = text.splitlines()
    section = None
    buf: list[str] = []
    sections: dict[str, str] = {}
    for line in lines:
        if line.strip().startswith("## "):
            if section:
                sections[section] = "\n".join(buf).strip()
            section = line.strip()[3:].strip().lower()
            buf = []
        elif section:
            buf.append(line)
    if section:
        sections[section] = "\n".join(buf).strip()
    trigger = sections.get("触发条件", "") or sections.get("trigger", "")
    action = sections.get("行动建议", "") or sections.get("action", "")
    return Instinct(path=path, frontmatter=fm, title=str(title), trigger=trigger, action=action)


def load_index(base_dir: Path, data_dir: str | None = None) -> dict[str, Any]:
    return safe_read_json(index_path(base_dir, data_dir), {"by_fingerprint": {}, "by_id": {}})


def save_index(base_dir: Path, idx: dict[str, Any], data_dir: str | None = None) -> None:
    safe_write_text_atomic(index_path(base_dir, data_dir), json.dumps(idx, ensure_ascii=False, indent=2))


def rank_instincts(query: str, instincts: Iterable[Instinct]) -> list[Instinct]:
    q = query.lower().strip()
    q_terms = [t for t in re.split(r"\W+", q) if t]

    def score(inst: Instinct) -> float:
        hay = " ".join([inst.title, inst.trigger, inst.action, " ".join(inst.tags)]).lower()
        hits = sum(1 for t in q_terms if t in hay)
        return hits * 10.0 + inst.confidence

    return sorted(instincts, key=score, reverse=True)


def days_since_iso(ts: str | None) -> int | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None
    delta = utc_now() - dt.astimezone(timezone.utc)
    return max(0, int(delta.total_seconds() // 86400))


def next_instinct_filename(base_dir: Path, data_dir: str | None = None) -> Path:
    ensure_dirs(base_dir, data_dir)
    today = utc_now().astimezone(timezone.utc).date().isoformat()
    existing = sorted(instincts_dir(base_dir, data_dir).glob(f"{today}-*.md"))
    n = len(existing) + 1
    return instincts_dir(base_dir, data_dir) / f"{today}-{n:03d}.md"


def build_instinct_markdown(params: dict[str, Any]) -> str:
    fm = {
        "id": params["id"],
        "created": params["created"],
        "confidence": params.get("confidence", 0.6),
        "times_used": params.get("times_used", 0),
        "times_validated": params.get("times_validated", 0),
        "last_used": params.get("last_used", ""),
        "tags": params.get("tags", []),
        "status": params.get("status", "active"),
        "title": params.get("title", params["id"]),
        "fingerprint": params["fingerprint"],
    }
    body = "\n".join(
        [
            "## 触发条件",
            params["trigger"].strip(),
            "",
            "## 行动建议",
            params["action"].strip(),
            "",
            "## 证据",
            params.get("evidence", "- (自动生成：暂无证据样例)"),
            "",
        ]
    )
    return render_frontmatter_md(fm) + "\n\n" + body


def simple_extract_candidate(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    correction_keywords = ("你说错", "不对", "应该", "正确", "别这样", "不要这样", "不是")
    failure_keywords = ("失败", "报错", "错误", "不行", "无法", "不工作", "卡住", "timeout")
    success_keywords = ("成功", "解决", "修复", "可以了", "已完成", "搞定", "work", "worked")

    for msg in reversed(messages[-10:]):
        role = (msg.get("role") or "").lower()
        content = str(msg.get("content") or "")
        if role != "user":
            continue
        if any(k in content for k in correction_keywords):
            trigger = "当用户指出回答不准确/方向错误时"
            action = "优先复述用户纠正点并更新方案；不要争辩；必要时回到最小可行验证。"
            return {
                "title": "用户纠正优先",
                "trigger": trigger,
                "action": action,
                "tags": ["correction", "alignment"],
                "evidence": f"- {utc_now_iso()}: 用户纠正：{content[:120]}",
            }

    recent = messages[-12:] if len(messages) > 12 else messages
    assistant_texts = [str(m.get("content") or "") for m in recent if str(m.get("role") or "").lower() == "assistant"]
    if len(assistant_texts) >= 2:
        saw_failure = any(any(k in t for k in failure_keywords) for t in assistant_texts[:-1])
        saw_success = any(k in assistant_texts[-1] for k in success_keywords)
        if saw_failure and saw_success:
            trigger = "当某种方法/方案尝试失败或报错时"
            action = "快速切换到可行的备选方案（降级/替代实现），并明确说明变更点；避免在同一路径反复重试。"
            return {
                "title": "失败后快速切换方案",
                "trigger": trigger,
                "action": action,
                "tags": ["fallback", "recovery"],
                "evidence": f"- {utc_now_iso()}: 近期对话出现“失败/报错”后又出现“成功/解决”的自报告",
            }

    return None

