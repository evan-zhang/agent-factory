#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
import fcntl

INVALID_CHARS = r'[\\/:*?"<>|]'
GATEWAY_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def parse_ts(ts: str | None) -> dt.datetime:
    if not ts:
        return now_local()

    raw = str(ts).strip()
    # Python 3.10 does not accept trailing "Z" in fromisoformat().
    # Normalize RFC3339 UTC suffix to +00:00 for cross-version compatibility.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    parsed = dt.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=now_local().tzinfo)
    return parsed.astimezone()


def validate_gateway_name(name: str) -> str:
    if not GATEWAY_RE.match(name):
        raise ValueError("invalid gateway name: only [A-Za-z0-9._-], max 64 chars")
    if name in {".", ".."}:
        raise ValueError("invalid gateway name")
    return name


def normalize_agent_id(agent: str | None) -> str:
    raw = (agent or "unknown-agent").strip()
    if not raw:
        raw = "unknown-agent"
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
    normalized = normalized.strip("._-") or "unknown-agent"
    return normalized[:96]


def resolve_archive_base(archive_root: str, gateway: str, scope_mode: str, agent: str | None) -> tuple[Path, str | None]:
    safe_gateway = validate_gateway_name(gateway)
    root = Path(archive_root).expanduser().resolve()
    if scope_mode == "agent":
        agent_id = normalize_agent_id(agent)
        return root / safe_gateway / "agents" / agent_id, agent_id
    return root / safe_gateway, None


def sanitize_filename(name: str, max_len: int = 200) -> str:
    safe = re.sub(INVALID_CHARS, "_", name).strip()
    if safe.startswith("."):
        safe = f"_{safe[1:]}"
    if not safe:
        safe = "file"
    if len(safe) <= max_len:
        return safe
    stem, dot, suffix = safe.rpartition(".")
    if not dot:
        return safe[:max_len]
    keep = max_len - len(suffix) - 1
    if keep < 1:
        return safe[:max_len]
    return f"{stem[:keep]}.{suffix}"


def format_hms(ts: dt.datetime) -> str:
    return ts.strftime("%H:%M:%S")


def format_day(ts: dt.datetime) -> str:
    return ts.strftime("%Y-%m-%d")


def header_for_day(day: str, gateway: str, agent_id: str | None = None) -> str:
    lines = [
        f"# Chat Log — {day}",
        f"# Gateway: {gateway}",
    ]
    if agent_id:
        lines.append(f"# Agent: {agent_id}")
    lines.extend(["# Mode: append-only", "", "---"])
    return "\n".join(lines) + "\n"


def quote_text(text: str) -> str:
    lines = text.splitlines() or [""]
    return "\n".join(f"> {line}" for line in lines)


def ensure_dirs(base: Path, day: str) -> dict[str, Path]:
    logs = base / "logs"
    inbound = base / "assets" / day / "inbound"
    outbound = base / "assets" / day / "outbound"
    meta = base / "meta"
    for p in (logs, inbound, outbound, meta):
        p.mkdir(parents=True, exist_ok=True)

    log_file = logs / f"{day}.md"
    if not log_file.exists():
        log_file.touch()

    return {
        "logs": logs,
        "inbound": inbound,
        "outbound": outbound,
        "meta": meta,
        "log_file": log_file,
    }


def disk_free_mb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024 * 1024)


def check_disk_space(base: Path, warn_mb: float, min_mb: float) -> None:
    free_mb = disk_free_mb(base)
    if min_mb > 0 and free_mb < min_mb:
        raise OSError(f"disk space too low: {free_mb:.1f}MB < min {min_mb:.1f}MB")
    if warn_mb > 0 and free_mb < warn_mb:
        print(f"[cas][warn] low disk space: {free_mb:.1f}MB < warn {warn_mb:.1f}MB", file=sys.stderr)


def load_state(meta_dir: Path) -> dict:
    state_path = meta_dir / "session-state.json"
    if not state_path.exists():
        return {"session": 0, "lastTs": None, "lastDay": None}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"session": 0, "lastTs": None, "lastDay": None}


def save_state(meta_dir: Path, state: dict) -> None:
    state_path = meta_dir / "session-state.json"
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=meta_dir,
            prefix="session-state.",
            suffix=".tmp",
        ) as tf:
            tf.write(json.dumps(state, ensure_ascii=False, indent=2))
            tf.flush()
            os.fsync(tf.fileno())
            tmp_name = tf.name
        Path(tmp_name).replace(state_path)
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.remove(tmp_name)


@contextmanager
def file_lock(lock_path: Path, timeout_seconds: int = 5):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lockf:
        start = time.monotonic()
        acquired = False
        while not acquired:
            try:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                if timeout_seconds is not None and (time.monotonic() - start) >= timeout_seconds:
                    raise TimeoutError(f"lock wait timeout after {timeout_seconds}s: {lock_path}")
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def append_locked(path: Path, content: str, timeout_seconds: int = 5) -> None:
    lock_path = path.with_suffix(path.suffix + ".lock")
    with file_lock(lock_path, timeout_seconds=timeout_seconds):
        with open(path, "a", encoding="utf-8") as out:
            out.write(content)


def ensure_log_header(log_file: Path, day: str, gateway: str, agent_id: str | None, lock_timeout_seconds: int = 5) -> None:
    if log_file.stat().st_size != 0:
        return
    append_locked(log_file, header_for_day(day, gateway, agent_id), timeout_seconds=lock_timeout_seconds)


def maybe_session_header(state: dict, ts: dt.datetime, force_new: bool, timeout_min: int) -> str:
    day = format_day(ts)
    if force_new:
        state["session"] = int(state.get("session", 0)) + 1
        return f"\n## Session #{state['session']} — {format_hms(ts)}\n\n"

    if not state.get("lastTs") or state.get("lastDay") != day:
        state["session"] = int(state.get("session", 0)) + 1
        return f"\n## Session #{state['session']} — {format_hms(ts)}\n\n"

    try:
        last = dt.datetime.fromisoformat(state["lastTs"])
    except Exception:
        state["session"] = int(state.get("session", 0)) + 1
        return f"\n## Session #{state['session']} — {format_hms(ts)}\n\n"

    if ts - last > dt.timedelta(minutes=timeout_min):
        state["session"] = int(state.get("session", 0)) + 1
        return f"\n## Session #{state['session']} — {format_hms(ts)}\n\n"

    return ""


def direction_label(direction: str) -> tuple[str, str]:
    d = direction.lower()
    if d in ("in", "inbound"):
        return "INBOUND", "inbound"
    if d in ("out", "outbound"):
        return "OUTBOUND", "outbound"
    raise ValueError("direction must be inbound|outbound|in|out")


def build_message_block(direction_upper: str, sender: str, text: str, ts: dt.datetime, session_prefix: str = "") -> str:
    return (
        f"{session_prefix}"
        f"**[{direction_upper}]** {format_hms(ts)} | {sender}\n"
        f"{quote_text(text)}\n\n"
    )


def archive_asset(paths: dict[str, Path], base: Path, direction_folder: str, source: Path, ts: dt.datetime, max_asset_mb: float) -> tuple[Path, str]:
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"source file not found: {source}")

    if max_asset_mb > 0:
        size_mb = source.stat().st_size / (1024 * 1024)
        if size_mb > max_asset_mb:
            raise ValueError(f"asset too large: {size_mb:.2f}MB > {max_asset_mb}MB")

    orig_name = sanitize_filename(source.name)
    direction_short = "in" if direction_folder == "inbound" else "out"
    stamp = ts.strftime("%Y-%m-%d-%H-%M-%S")
    milli = f"{int(ts.microsecond / 1000):03d}"
    target_name = f"{direction_short}-{stamp}-{milli}-{orig_name}"

    target_dir = paths[direction_folder]
    target = target_dir / target_name
    if target.exists():
        target = target_dir / f"{direction_short}-{stamp}-{milli}-{os.getpid()}-{orig_name}"

    shutil.copy2(source, target)

    rel = target.relative_to(base)
    size = target.stat().st_size
    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"

    block = (
        f"**[ASSET]** {format_hms(ts)} | {direction_short} | {orig_name}\n"
        f"> Path: {rel.as_posix()}\n"
        f"> Size: {size} bytes | MIME: {mime}\n\n"
    )
    return target, block


def cmd_init(args: argparse.Namespace) -> None:
    gateway = validate_gateway_name(args.gateway)
    base, agent_id = resolve_archive_base(args.archive_root, gateway, args.scope_mode, args.agent)
    ts = parse_ts(args.timestamp)
    day = format_day(ts)
    paths = ensure_dirs(base, day)
    check_disk_space(base, args.disk_warn_mb, args.disk_min_mb)
    ensure_log_header(paths["log_file"], day, gateway, agent_id, args.lock_timeout_sec)
    print(f"Initialized: {base}")


def cmd_record_message(args: argparse.Namespace) -> None:
    gateway = validate_gateway_name(args.gateway)
    base, agent_id = resolve_archive_base(args.archive_root, gateway, args.scope_mode, args.agent)
    ts = parse_ts(args.timestamp)
    day = format_day(ts)
    paths = ensure_dirs(base, day)
    log_file = paths["log_file"]
    meta_dir = paths["meta"]

    check_disk_space(base, args.disk_warn_mb, args.disk_min_mb)

    direction_upper, _ = direction_label(args.direction)
    text = args.text or ""
    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    sender = args.sender or ("User" if direction_upper == "INBOUND" else "Assistant")

    state_lock = meta_dir / "session-state.lock"
    with file_lock(state_lock, timeout_seconds=args.lock_timeout_sec):
        ensure_log_header(log_file, day, gateway, agent_id, args.lock_timeout_sec)

        state = load_state(meta_dir)
        session = maybe_session_header(state, ts, args.new_session, args.session_timeout_min)
        block = build_message_block(direction_upper, sender, text, ts, session_prefix=session)

        append_locked(log_file, block, timeout_seconds=args.lock_timeout_sec)
        state["lastTs"] = ts.isoformat()
        state["lastDay"] = day
        save_state(meta_dir, state)

    print(f"Logged message: {log_file}")


def cmd_record_asset(args: argparse.Namespace) -> None:
    gateway = validate_gateway_name(args.gateway)
    base, agent_id = resolve_archive_base(args.archive_root, gateway, args.scope_mode, args.agent)
    ts = parse_ts(args.timestamp)
    day = format_day(ts)
    paths = ensure_dirs(base, day)

    check_disk_space(base, args.disk_warn_mb, args.disk_min_mb)

    ensure_log_header(paths["log_file"], day, gateway, agent_id, args.lock_timeout_sec)

    _, direction_folder = direction_label(args.direction)
    source = Path(args.source).expanduser()

    target, block = archive_asset(paths, base, direction_folder, source, ts, args.max_asset_mb)
    append_locked(paths["log_file"], block, timeout_seconds=args.lock_timeout_sec)

    print(f"Archived asset: {target}")


def cmd_record_bundle(args: argparse.Namespace) -> None:
    gateway = validate_gateway_name(args.gateway)

    payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be JSON object")

    bundle_agent = args.agent or payload.get("agent")
    base, agent_id = resolve_archive_base(args.archive_root, gateway, args.scope_mode, bundle_agent)

    ts = parse_ts(args.timestamp or payload.get("timestamp"))
    day = format_day(ts)
    paths = ensure_dirs(base, day)
    log_file = paths["log_file"]
    meta_dir = paths["meta"]

    check_disk_space(base, args.disk_warn_mb, args.disk_min_mb)

    inbound = payload.get("inbound", {}) or {}
    outbound = payload.get("outbound", {}) or {}

    state_lock = meta_dir / "session-state.lock"
    with file_lock(state_lock, timeout_seconds=args.lock_timeout_sec):
        ensure_log_header(log_file, day, gateway, agent_id, args.lock_timeout_sec)

        state = load_state(meta_dir)
        blocks: list[str] = []
        has_message = False
        first_message = True

        inbound_text = inbound.get("text")
        if isinstance(inbound_text, str) and inbound_text:
            has_message = True
            session_prefix = maybe_session_header(state, ts, args.new_session, args.session_timeout_min) if first_message else ""
            first_message = False
            sender = inbound.get("sender") or "User"
            blocks.append(build_message_block("INBOUND", sender, inbound_text, ts, session_prefix=session_prefix))

        for attachment in inbound.get("attachments", []) or []:
            if isinstance(attachment, str) and attachment:
                _, block = archive_asset(paths, base, "inbound", Path(attachment).expanduser(), ts, args.max_asset_mb)
                blocks.append(block)

        outbound_text = outbound.get("text")
        if isinstance(outbound_text, str) and outbound_text:
            has_message = True
            session_prefix = maybe_session_header(state, ts, args.new_session, args.session_timeout_min) if first_message else ""
            first_message = False
            sender = outbound.get("sender") or "Assistant"
            blocks.append(build_message_block("OUTBOUND", sender, outbound_text, ts, session_prefix=session_prefix))

        for attachment in outbound.get("attachments", []) or []:
            if isinstance(attachment, str) and attachment:
                _, block = archive_asset(paths, base, "outbound", Path(attachment).expanduser(), ts, args.max_asset_mb)
                blocks.append(block)

        if blocks:
            append_locked(log_file, "".join(blocks), timeout_seconds=args.lock_timeout_sec)

        if has_message:
            state["lastTs"] = ts.isoformat()
            state["lastDay"] = day
            save_state(meta_dir, state)

    print(f"Logged bundle: {log_file}")


def add_common_tuning(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lock-timeout-sec", type=int, default=5)
    parser.add_argument("--disk-warn-mb", type=float, default=500)
    parser.add_argument("--disk-min-mb", type=float, default=200)


def add_scope(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scope-mode", choices=["gateway", "agent"], default="gateway")
    parser.add_argument("--agent", help="agent/session scope id when scope-mode=agent")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CAS chat archive append-only logger")
    p.add_argument("--archive-root", default="~/.openclaw/chat-archive", help="archive root directory")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize archive directories and day log")
    p_init.add_argument("--gateway", required=True)
    p_init.add_argument("--timestamp", help="ISO timestamp")
    add_scope(p_init)
    add_common_tuning(p_init)
    p_init.set_defaults(func=cmd_init)

    p_msg = sub.add_parser("record-message", help="append inbound/outbound message")
    p_msg.add_argument("--gateway", required=True)
    p_msg.add_argument("--direction", required=True, help="inbound|outbound|in|out")
    p_msg.add_argument("--sender", help="sender display name")
    p_msg.add_argument("--text", help="message text")
    p_msg.add_argument("--text-file", help="path to text file")
    p_msg.add_argument("--timestamp", help="ISO timestamp")
    p_msg.add_argument("--new-session", action="store_true", help="force new session header")
    p_msg.add_argument("--session-timeout-min", type=int, default=30)
    add_scope(p_msg)
    add_common_tuning(p_msg)
    p_msg.set_defaults(func=cmd_record_message)

    p_asset = sub.add_parser("record-asset", help="copy asset and append asset block")
    p_asset.add_argument("--gateway", required=True)
    p_asset.add_argument("--direction", required=True, help="inbound|outbound|in|out")
    p_asset.add_argument("--source", required=True, help="source file path")
    p_asset.add_argument("--timestamp", help="ISO timestamp")
    p_asset.add_argument("--max-asset-mb", type=float, default=100)
    add_scope(p_asset)
    add_common_tuning(p_asset)
    p_asset.set_defaults(func=cmd_record_asset)

    p_bundle = sub.add_parser("record-bundle", help="record full inbound/outbound payload in one process")
    p_bundle.add_argument("--gateway", required=True)
    p_bundle.add_argument("--payload-file", required=True, help="json file path with inbound/outbound payload")
    p_bundle.add_argument("--timestamp", help="override ISO timestamp")
    p_bundle.add_argument("--new-session", action="store_true", help="force new session header")
    p_bundle.add_argument("--session-timeout-min", type=int, default=30)
    p_bundle.add_argument("--max-asset-mb", type=float, default=100)
    add_scope(p_bundle)
    add_common_tuning(p_bundle)
    p_bundle.set_defaults(func=cmd_record_bundle)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
