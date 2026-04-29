#!/usr/bin/env python3
"""
Video archiver for link-archivist.

Downloads video files to archive directory when:
  - mode is "full"
  - video_archive_dir is configured
  - URL is a supported video platform (YouTube / Douyin)

Usage:
  # Download video (Phase 2, before archive_id is known)
  python3 video_archive.py --url "<url>" --platform youtube|douyin --mode full

  # Rename temp file to final archive path (Phase 5)
  python3 video_archive.py --rename --temp "<temp_path>" --archive-id "K-260429-003"

  # Check if video archiving is available
  python3 video_archive.py --check
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def load_config() -> dict:
    """Load config from standard paths."""
    for config_file in [
        Path.home() / ".openclaw" / "link-archivist-config.json",
        Path.home() / ".hermes" / "link-archivist-config.json",
        Path.home() / ".config" / "link-archivist-config.json",
    ]:
        if config_file.exists():
            try:
                return json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
    return {}


def get_archive_dir(config: dict) -> Path | None:
    """Return video_archive_dir as Path, or None if not configured."""
    raw = config.get("video_archive_dir", "")
    if not raw:
        return None
    p = Path(raw).expanduser()
    return p if p.is_dir() else None


def run_cmd(cmd: str, timeout: int = 300, check: bool = True) -> str:
    """Execute shell command, return stdout."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed (rc={result.returncode}): {result.stderr[:500]}"
        )
    return result.stdout.strip()


def download_youtube(url: str, output_path: str) -> dict:
    """Download YouTube video at 720p using yt-dlp."""
    cmd = (
        f'yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" '
        f'--merge-output-format mp4 -o "{output_path}" '
        f'--no-playlist --no-warnings "{url}"'
    )
    run_cmd(cmd, timeout=600)

    if not os.path.exists(output_path):
        raise RuntimeError("yt-dlp completed but output file not found")

    size = os.path.getsize(output_path)
    return {"ok": True, "path": output_path, "size_mb": round(size / 1048576, 1)}


def download_douyin(url: str, output_path: str) -> dict:
    """
    Download Douyin video.
    Uses the same parse_with_python logic from douyin_process.py.
    Best-effort: if it fails, return ok=False (no blocking).
    """
    try:
        import requests
    except ImportError:
        return {"ok": False, "error": "requests not installed"}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Referer": "https://www.douyin.com/",
    }

    # Follow redirects to get real URL
    try:
        resp = requests.get(url, headers=headers, timeout=30,
                            allow_redirects=True, verify=False)
        real_url = resp.url
    except Exception as e:
        return {"ok": False, "error": f"Failed to resolve URL: {e}"}

    # Extract video ID
    vid_match = re.search(r'/video/(\d+)', real_url)
    video_id = vid_match.group(1) if vid_match else ""

    if not video_id:
        return {"ok": False, "error": f"Cannot extract video ID from: {real_url}"}

    download_url = (
        f"https://aweme.snssdk.com/aweme/v1/play/"
        f"?video_id={video_id}&ratio=720p&line=0"
    )

    try:
        dl_resp = requests.get(
            download_url, headers=headers, timeout=120,
            stream=True, verify=False
        )
        dl_resp.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

    except Exception as e:
        return {"ok": False, "error": f"Download failed: {e}"}

    size = os.path.getsize(output_path)
    if size < 10000:
        os.remove(output_path)
        return {"ok": False, "error": f"File too small ({size} bytes), likely failed"}

    return {"ok": True, "path": output_path, "size_mb": round(size / 1048576, 1)}


def do_download(url: str, platform: str, config: dict) -> dict:
    """Download video to a temp file inside video_archive_dir date subfolder."""
    archive_dir = get_archive_dir(config)
    if not archive_dir:
        return {"ok": False, "error": "video_archive_dir not configured or not a directory"}

    today = datetime.now().strftime("%Y-%m-%d")
    date_dir = archive_dir / today
    date_dir.mkdir(parents=True, exist_ok=True)

    # Temp filename
    timestamp = datetime.now().strftime("%H%M%S")
    temp_name = f"_temp_{timestamp}.mp4"
    temp_path = str(date_dir / temp_name)

    try:
        if platform == "youtube":
            result = download_youtube(url, temp_path)
        elif platform == "douyin":
            result = download_douyin(url, temp_path)
        else:
            return {"ok": False, "error": f"Unsupported platform: {platform}"}
    except Exception as e:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"ok": False, "error": str(e)}

    result["temp_path"] = temp_path
    result["platform"] = platform
    return result


def do_rename(temp_path: str, archive_id: str, config: dict) -> dict:
    """Rename temp video to final archive path: {video_archive_dir}/{date}/{archive_id}.mp4"""
    archive_dir = get_archive_dir(config)
    if not archive_dir:
        return {"ok": False, "error": "video_archive_dir not configured"}

    src = Path(temp_path)
    if not src.exists():
        return {"ok": False, "error": f"Temp file not found: {temp_path}"}

    # Extract date from path (parent dir name is YYYY-MM-DD)
    date_str = src.parent.name
    final_name = f"{archive_id}.mp4"
    final_path = src.parent / final_name

    shutil.move(str(src), str(final_path))

    return {
        "ok": True,
        "path": str(final_path),
        "size_mb": round(final_path.stat().st_size / 1048576, 1),
    }


def do_check(config: dict) -> dict:
    """Check if video archiving is available."""
    raw = config.get("video_archive_dir", "")
    if not raw:
        return {"ok": True, "available": False, "reason": "video_archive_dir not configured"}

    p = Path(raw).expanduser()
    if not p.exists():
        return {"ok": True, "available": False, "reason": f"directory does not exist: {p}"}
    if not p.is_dir():
        return {"ok": True, "available": False, "reason": f"not a directory: {p}"}

    return {"ok": True, "available": True, "video_archive_dir": str(p)}


def main() -> int:
    args = sys.argv[1:]

    config = load_config()

    # Mode: --check
    if "--check" in args:
        result = do_check(config)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # Mode: --rename
    if "--rename" in args:
        temp_path = ""
        archive_id = ""
        i = 0
        while i < len(args):
            if args[i] == "--temp" and i + 1 < len(args):
                temp_path = args[i + 1]
                i += 2
            elif args[i] == "--archive-id" and i + 1 < len(args):
                archive_id = args[i + 1]
                i += 2
            else:
                i += 1

        if not temp_path or not archive_id:
            print(json.dumps({
                "ok": False,
                "error": "usage: video_archive.py --rename --temp <path> --archive-id <id>"
            }, ensure_ascii=False))
            return 1

        result = do_rename(temp_path, archive_id, config)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1

    # Mode: download
    url = ""
    platform = ""
    mode = ""
    i = 0
    while i < len(args):
        if args[i] == "--url" and i + 1 < len(args):
            url = args[i + 1]
            i += 2
        elif args[i] == "--platform" and i + 1 < len(args):
            platform = args[i + 1]
            i += 2
        elif args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            i += 2
        else:
            i += 1

    if not url:
        print(json.dumps({
            "ok": False,
            "error": "usage: video_archive.py --url <url> --platform youtube|douyin --mode full"
        }, ensure_ascii=False))
        return 1

    if mode != "full":
        print(json.dumps({"ok": True, "skipped": True, "reason": f"mode={mode}, only full triggers download"}))
        return 0

    result = do_download(url, platform, config)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
