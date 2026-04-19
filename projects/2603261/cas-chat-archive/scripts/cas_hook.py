#!/usr/bin/env python3
"""OpenClaw Gateway post-response hook for CAS chat archiving."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cmd(cmd: list[str], label: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        stderr = (result.stderr or "").strip()
        return True, stderr
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        return False, f"{label} failed (exit {e.returncode}): {stderr}"
    except OSError as e:
        return False, f"{label} OS error: {e}"


def resolve_allowed_attachment_roots(gateway: str) -> list[Path]:
    roots: list[Path] = []

    gw_root = Path("~/.openclaw/gateways").expanduser() / gateway
    defaults = [
        gw_root / "uploads",
        gw_root / "state" / "media" / "inbound",
        gw_root / "state" / "media" / "outbound",
    ]
    for p in defaults:
        roots.append(p.resolve())

    extra = os.getenv("CAS_ALLOWED_ATTACHMENT_ROOTS", "").strip()
    if extra:
        for part in extra.split(os.pathsep):
            p = part.strip()
            if p:
                roots.append(Path(p).expanduser().resolve())

    return roots


def is_allowed_attachment(path_str: str, roots: list[Path]) -> bool:
    try:
        path = Path(path_str).expanduser().resolve()
    except Exception:
        return False

    for root in roots:
        try:
            if path.is_relative_to(root):
                return True
        except Exception:
            if str(path).startswith(str(root) + os.sep):
                return True
    return False


def filter_payload(payload: dict, roots: list[Path]) -> tuple[dict, list[str]]:
    errors: list[str] = []

    inbound = payload.get("inbound", {}) or {}
    outbound = payload.get("outbound", {}) or {}

    def filter_attachments(items: list) -> list[str]:
        allowed: list[str] = []
        for attachment in items or []:
            if not isinstance(attachment, str) or not attachment:
                continue
            if is_allowed_attachment(attachment, roots):
                allowed.append(attachment)
            else:
                errors.append(f"blocked attachment outside allowed roots: {attachment}")
        return allowed

    clean_payload = {
        "timestamp": payload.get("timestamp"),
        "inbound": {
            "sender": os.getenv("OPENCLAW_USER_ID", "User"),
            "text": inbound.get("text") if isinstance(inbound.get("text"), str) else "",
            "attachments": filter_attachments(inbound.get("attachments", [])),
        },
        "outbound": {
            "sender": "Assistant",
            "text": outbound.get("text") if isinstance(outbound.get("text"), str) else "",
            "attachments": filter_attachments(outbound.get("attachments", [])),
        },
    }

    return clean_payload, errors


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(f"Failed to parse hook input: {e}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("Invalid hook payload: expected object", file=sys.stderr)
        return 1

    gateway = os.getenv("OPENCLAW_GATEWAY_NAME", "default")
    archive_root = os.getenv("CAS_ARCHIVE_ROOT", "~/.openclaw/chat-archive")
    disk_warn_mb = os.getenv("CAS_DISK_WARN_MB", "500")
    disk_min_mb = os.getenv("CAS_DISK_MIN_MB", "200")
    max_asset_mb = os.getenv("CAS_MAX_ASSET_MB", "100")
    strict_mode = os.getenv("CAS_STRICT_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}

    allowed_roots = resolve_allowed_attachment_roots(gateway)
    clean_payload, block_errors = filter_payload(payload, allowed_roots)

    script_dir = Path(__file__).parent
    cas_script = script_dir / "cas_archive.py"
    if not cas_script.exists():
        print(f"CAS script not found: {cas_script}", file=sys.stderr)
        return 1

    # One subprocess call for whole turn (perf improvement).
    temp_payload_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as tf:
            tf.write(json.dumps(clean_payload, ensure_ascii=False))
            temp_payload_path = tf.name

        cmd = [
            sys.executable,
            str(cas_script),
            "--archive-root",
            archive_root,
            "record-bundle",
            "--gateway",
            gateway,
            "--payload-file",
            temp_payload_path,
            "--disk-warn-mb",
            str(disk_warn_mb),
            "--disk-min-mb",
            str(disk_min_mb),
            "--max-asset-mb",
            str(max_asset_mb),
        ]

        ok, msg = run_cmd(cmd, "record-bundle")
        if msg:
            print(msg, file=sys.stderr)

        for err in block_errors:
            print(err, file=sys.stderr)

        # Default fail-soft: never disrupt user flow for archival failures.
        # Set CAS_STRICT_MODE=true if you want hard-fail behavior.
        if not ok:
            return 1 if strict_mode else 0

        if block_errors:
            return 1 if strict_mode else 0

        return 0

    finally:
        if temp_payload_path:
            try:
                os.remove(temp_payload_path)
            except OSError:
                pass


if __name__ == "__main__":
    sys.exit(main())
