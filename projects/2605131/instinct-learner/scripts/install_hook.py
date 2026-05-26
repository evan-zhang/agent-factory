#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import os
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", "utf-8")

def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _env_path(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _resolve_config_candidates(workspace: Path) -> list[tuple[str, Path]]:
    """
    Return a list of (reason, path) candidates in priority order.

    We intentionally mirror OpenClaw's behavior where possible:
    - OPENCLAW_CONFIG_PATH: full path to config file
    - OPENCLAW_STATE_DIR: config root directory; config file is <state_dir>/openclaw.json
    - OPENCLAW_HOME: affects the default "~" and default config root in OpenClaw,
      so we also honor it for default paths.
    """
    out: list[tuple[str, Path]] = []

    # 0) Explicit config file path
    p = _env_path("OPENCLAW_CONFIG_PATH")
    if p:
        out.append(("env:OPENCLAW_CONFIG_PATH", Path(p).expanduser().resolve()))

    # 1) Explicit state dir -> <state_dir>/openclaw.json
    state_dir = _env_path("OPENCLAW_STATE_DIR")
    if state_dir:
        out.append(
            ("env:OPENCLAW_STATE_DIR", (Path(state_dir).expanduser().resolve() / "openclaw.json"))
        )

    # 2) Derive from workspace path for known wrappers (best-effort)
    # Example: ~/.easyclaw/openclaw/workspace -> ~/.easyclaw/openclaw/openclaw.json
    try:
        parts = workspace.parts
        if ".easyclaw" in parts:
            idx = parts.index(".easyclaw")
            base = Path(*parts[: idx + 1])
            # Typical EasyClaw layout observed: ~/.easyclaw/openclaw/openclaw.json
            out.append(("derived:easyclaw", (base / "openclaw" / "openclaw.json").resolve()))
            # Some wrappers may use a state dir under ~/.easyclaw/openclaw/.openclaw/
            out.append(
                ("derived:easyclaw-state", (base / "openclaw" / ".openclaw" / "openclaw.json").resolve())
            )
    except Exception:
        # best-effort
        pass

    # 3) Default locations. Honor OPENCLAW_HOME when set (OpenClaw prefers it over HOME).
    openclaw_home = _env_path("OPENCLAW_HOME")
    if openclaw_home:
        home = Path(openclaw_home).expanduser().resolve()
        out.append(("env:OPENCLAW_HOME-default", home / ".openclaw" / "openclaw.json"))
    else:
        out.append(("default:~/.openclaw/openclaw.json", (Path.home() / ".openclaw" / "openclaw.json").resolve()))

    # Keep the previously hard-coded EasyClaw path as a low-priority fallback.
    out.append(
        ("fallback:~/.easyclaw/openclaw/openclaw.json", (Path.home() / ".easyclaw" / "openclaw" / "openclaw.json").resolve())
    )

    # De-dup by resolved absolute path while preserving order.
    seen: set[str] = set()
    dedup: list[tuple[str, Path]] = []
    for reason, path in out:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        dedup.append((reason, path))
    return dedup


def _pick_config_path(workspace: Path) -> tuple[Path, str, list[dict[str, str]]]:
    candidates = _resolve_config_candidates(workspace)
    debug = []
    for reason, p in candidates:
        debug.append({"reason": reason, "path": str(p), "exists": str(p.exists()).lower()})
    # Prefer an existing file among candidates; otherwise pick the first candidate (will be created).
    for reason, p in candidates:
        if p.exists():
            return p, reason + " (exists)", debug
    reason, p = candidates[0]
    return p, reason + " (create_if_missing)", debug


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            dst[k] = _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def _init_runtime_instincts(workspace: Path) -> dict[str, Any]:
    """
    Initialize workspace-level instinct storage:
    <workspace>/instincts/*.md
    <workspace>/instincts/archived/*.md
    <workspace>/instincts/index.json
    """
    instincts = (workspace / "instincts").resolve()
    archived = instincts / "archived"
    idx_path = instincts / "index.json"
    instincts.mkdir(parents=True, exist_ok=True)
    archived.mkdir(parents=True, exist_ok=True)
    created_index = False
    if not idx_path.exists():
        _write_json(idx_path, {"by_fingerprint": {}, "by_id": {}})
        created_index = True
    return {
        "instincts_dir": str(instincts),
        "archived_dir": str(archived),
        "index_path": str(idx_path),
        "index_created": created_index,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="安装 instinct-learner workspace hook（可选写配置 + 重启网关）。")
    parser.add_argument("--workspace", required=True, help="OpenClaw workspace 路径")
    parser.add_argument("--hook-dir", default="hooks/instinct-learner", help="相对 workspace 的 hook 安装目录")
    parser.add_argument("--force", action="store_true", help="若 hook 已存在也强制覆盖安装")
    parser.add_argument("--enable-config", action="store_true", help="合并写入 ~/.openclaw/openclaw.json 启用 hook")
    parser.add_argument(
        "--config-path",
        default=None,
        help="OpenClaw 配置文件路径（若不填：优先 env OPENCLAW_CONFIG_PATH / OPENCLAW_STATE_DIR / OPENCLAW_HOME；其次基于 workspace 推断；最后回退到 ~/.openclaw/openclaw.json 等候选）",
    )
    parser.add_argument("--restart-gateway", action="store_true", help="安装后执行 openclaw gateway restart")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    src_hook_root = skill_dir / "references" / "workspace-hook" / "instinct-learner"
    if not src_hook_root.exists():
        raise SystemExit(f"missing bundled hook template: {src_hook_root}")

    workspace = Path(args.workspace).expanduser().resolve()
    dest_hook_root = workspace / args.hook_dir
    dest_hook_root.parent.mkdir(parents=True, exist_ok=True)

    installed = False
    skipped = False
    config_changed = False
    runtime = _init_runtime_instincts(workspace)

    # Copy hook files (idempotent by default; overwrite only with --force)
    if dest_hook_root.exists() and not args.force:
        skipped = True
    else:
        if dest_hook_root.exists():
            shutil.rmtree(dest_hook_root)
        shutil.copytree(src_hook_root, dest_hook_root)
        installed = True

    # Optionally merge config
    config_path_reason = ""
    config_candidates_debug: list[dict[str, str]] = []
    if args.enable_config:
        if args.config_path and str(args.config_path).strip():
            config_path = Path(args.config_path).expanduser().resolve()
            config_path_reason = "arg:--config-path"
            config_candidates_debug = [{"reason": config_path_reason, "path": str(config_path), "exists": str(config_path.exists()).lower()}]
        else:
            config_path, config_path_reason, config_candidates_debug = _pick_config_path(workspace)
        existing = _read_json(config_path)
        desired = {
            "hooks": {
                "internal": {
                    "enabled": True,
                    "entries": {
                        "instinct-learner": {
                            "enabled": True,
                            "k": 5,
                            "extractEveryNMessages": 1,
                            "pruneIntervalHours": 24,
                        }
                    },
                }
            }
        }
        if not isinstance(existing, dict):
            existing = {}
        merged = _deep_merge(dict(existing), desired)
        config_changed = _stable_json(existing) != _stable_json(merged)
        if config_changed:
            _write_json(config_path, merged)

    if args.restart_gateway:
        # Only restart when something actually changed (installed hook or config changed),
        # unless the user forced install.
        should_restart = bool(args.force) or installed or config_changed
        if should_restart:
            try:
                subprocess.run(["openclaw", "gateway", "restart"], check=False)
            except FileNotFoundError:
                print("WARN: openclaw CLI not found on PATH; skip gateway restart")

    print(
        json.dumps(
            {
                "ok": True,
                "installed_to": str(dest_hook_root),
                "installed": installed,
                "skipped_existing": skipped,
                "force": bool(args.force),
                "enable_config": bool(args.enable_config),
                "config_changed": config_changed,
                "config_path": str(
                    (
                        Path(args.config_path).expanduser().resolve()
                        if args.config_path and str(args.config_path).strip()
                        else config_path
                    )
                )
                if args.enable_config
                else "",
                "config_path_reason": config_path_reason if args.enable_config else "",
                "config_candidates": config_candidates_debug if args.enable_config else [],
                "runtime_instincts": runtime,
                "restart_gateway": bool(args.restart_gateway),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

