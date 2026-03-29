#!/usr/bin/env python3
"""
CAS Chat Archive - Publishing Script

Dual channel:
1) ClawHub public registry
2) Company internal skill marketplace
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SKILL_NAME = "cas-chat-archive"
SKILL_DIR = Path(__file__).parent.parent.resolve()
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
ALLOWED_TOP_FILES = {"SKILL.md"}
ALLOWED_TOP_DIRS = {"scripts", "references", "assets", "hooks"}
REQUIRED_ARCHIVE_ENTRIES = {
    "SKILL.md",
    "scripts/cas_archive.py",
    "hooks/cas-chat-archive-auto/HOOK.md",
    "hooks/cas-chat-archive-auto/handler.ts",
}


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def validate_version(version: str) -> bool:
    return bool(SEMVER_RE.match(version))


def validate_skill() -> bool:
    missing: list[str] = []
    for rel in REQUIRED_ARCHIVE_ENTRIES:
        if not (SKILL_DIR / rel).exists():
            missing.append(rel)

    if missing:
        print(f"Error: Required files missing: {', '.join(missing)}", file=sys.stderr)
        return False

    print("✓ Skill structure validated")
    return True


def iter_pack_files() -> list[Path]:
    files: list[Path] = []

    # top-level files: only SKILL.md
    for f in ALLOWED_TOP_FILES:
        p = SKILL_DIR / f
        if p.exists() and p.is_file():
            files.append(p)

    # top-level dirs: scripts/references/assets (if present)
    for d in ALLOWED_TOP_DIRS:
        root = SKILL_DIR / d
        if not root.exists() or not root.is_dir():
            continue
        for path in root.rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if path.suffix == ".pyc":
                continue
            if path.is_file() and not path.name.startswith("."):
                files.append(path)

    return files


def validate_archive_entries(skill_file: Path) -> None:
    with zipfile.ZipFile(skill_file, "r") as zf:
        names = set(zf.namelist())

    missing = sorted(REQUIRED_ARCHIVE_ENTRIES - names)
    if missing:
        raise RuntimeError(f"packaged skill missing required entries: {', '.join(missing)}")


def package_skill(output_dir: Path, version: str) -> Path:
    skill_file = output_dir / f"{SKILL_NAME}-{version}.skill"
    if skill_file.exists():
        skill_file.unlink()

    pack_files = iter_pack_files()
    if not pack_files:
        raise RuntimeError("No files to package")

    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in pack_files:
            arcname = file_path.relative_to(SKILL_DIR)
            zf.write(file_path, arcname)

    validate_archive_entries(skill_file)
    print(f"✓ Packaged: {skill_file}")
    return skill_file


def publish_to_clawhub(version: str, changelog: str) -> bool:
    print("\n=== Publishing to ClawHub ===")
    try:
        cmd = [
            "clawhub",
            "publish",
            str(SKILL_DIR),
            "--slug",
            SKILL_NAME,
            "--name",
            "CAS Chat Archive",
            "--version",
            version,
            "--changelog",
            changelog,
        ]
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print(f"ClawHub publish failed: {result.stderr}", file=sys.stderr)
            return False

        print(f"✓ Published to ClawHub: {SKILL_NAME} v{version}")
        return True
    except FileNotFoundError:
        print("Error: clawhub CLI not found. Install with: npm i -g clawhub", file=sys.stderr)
        return False


def publish_to_internal(skill_file: Path, version: str, changelog: str, allow_mock: bool) -> bool:
    print("\n=== Publishing to Internal Marketplace ===")

    internal_registry = os.getenv("CAS_INTERNAL_REGISTRY", "").strip()
    if not internal_registry:
        if allow_mock:
            print("Warning: CAS_INTERNAL_REGISTRY not set. Mock publish allowed.", file=sys.stderr)
            print(f"✓ [MOCK] Published to internal marketplace: {SKILL_NAME} v{version}")
            return True
        print("Error: CAS_INTERNAL_REGISTRY not set. Refusing fake success.", file=sys.stderr)
        return False

    try:
        internal_dir = Path(internal_registry).expanduser().resolve() / SKILL_NAME / version
        internal_dir.mkdir(parents=True, exist_ok=True)

        dest_file = internal_dir / f"{SKILL_NAME}.skill"
        shutil.copy2(skill_file, dest_file)

        metadata = {
            "name": SKILL_NAME,
            "version": version,
            "changelog": changelog,
            "published_at": datetime.now().isoformat(),
            "published_by": os.getenv("USER", "unknown"),
        }
        (internal_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"✓ Published to internal marketplace: {dest_file}")
        return True
    except Exception as e:
        print(f"Internal publish failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish CAS Chat Archive skill")
    parser.add_argument("--channel", choices=["clawhub", "internal", "both"], default="both", help="publishing channel")
    parser.add_argument("--version", required=True, help="version number (e.g., 1.0.0)")
    parser.add_argument("--changelog", default="", help="changelog message")
    parser.add_argument("--dry-run", action="store_true", help="validate and package only")
    parser.add_argument("--allow-mock-internal", action="store_true", help="allow mock internal publish when registry env is missing")

    args = parser.parse_args()

    if not validate_version(args.version):
        print("Error: version must match semver, e.g. 1.0.0", file=sys.stderr)
        return 1

    if not validate_skill():
        return 1

    output_dir = SKILL_DIR / "dist"
    output_dir.mkdir(exist_ok=True)
    skill_file = package_skill(output_dir, args.version)

    if args.dry_run:
        print(f"\n✓ Dry run complete. Package at: {skill_file}")
        return 0

    success = True

    if args.channel in ["clawhub", "both"]:
        if not publish_to_clawhub(args.version, args.changelog):
            success = False

    if args.channel in ["internal", "both"]:
        if not publish_to_internal(skill_file, args.version, args.changelog, args.allow_mock_internal):
            success = False

    if success:
        print(f"\n✓ Publishing complete: {SKILL_NAME} v{args.version}")
        return 0

    print("\n✗ Publishing failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
