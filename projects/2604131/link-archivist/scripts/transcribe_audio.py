#!/usr/bin/env python3
"""Audio transcription using XGJK AI Huiji service with CWork file upload."""
import json
import os
import sys
import time
from pathlib import Path

# Configuration
HUIJI_BASE_URL = os.getenv("XGJK_HUIJI_BASE_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
CWORK_API_URL = os.getenv("XGJK_CWORK_API_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
APP_KEY = os.getenv("XGJK_APP_KEY")


def load_app_key() -> str | None:
    """Load appKey from config file or environment."""
    if APP_KEY:
        return APP_KEY

    config_paths = [
        Path.home() / ".openclaw" / "link-archivist-config.json",
        Path.home() / ".hermes" / "link-archivist-config.json",
        Path.home() / ".config" / "link-archivist-config.json",
    ]
    for config_file in config_paths:
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text(encoding="utf-8"))
                if "xgjk_app_key" in config:
                    return config["xgjk_app_key"]
            except (json.JSONDecodeError, OSError):
                continue
    return None


def upload_to_cwork(file_path: str, app_key: str) -> str:
    """Upload file to CWork file server and get download URL.

    API: POST /cwork-file/uploadWholeFile (multipart/form-data)
    Reference: 基础服务 API 文档 4.1

    Args:
        file_path: Path to local file

    Returns:
        Download URL (valid for 1 hour)
    """
    import requests

    file_path = Path(file_path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Uploading {file_path.name} to CWork...", file=sys.stderr)

    # Upload using multipart/form-data
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/octet-stream")}
        resp = requests.post(
            f"{CWORK_API_URL}/cwork-file/uploadWholeFile",
            headers={"appKey": app_key},
            files=files,
            timeout=300
        )
    resp.raise_for_status()
    result = resp.json()

    if result.get("resultCode") != 1:
        raise Exception(f"Failed to upload file: {result}")

    resource_id = result["data"]

    # Get download URL
    resp = requests.get(
        f"{CWORK_API_URL}/cwork-file/getDownloadInfo",
        headers={"appKey": app_key},
        params={"resourceId": resource_id},
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("resultCode") != 1:
        raise Exception(f"Failed to get download URL: {result}")

    download_url = result["data"]["downloadUrl"]
    print(f"Uploaded: {download_url}", file=sys.stderr)
    return download_url


def transcribe(audio_file: str, app_key: str) -> str:
    """
    Transcribe audio file using XGJK AI Huiji.

    Steps:
    1. Upload audio to CWork file server
    2. Create Huiji task with file URL
    3. Poll for completion
    4. Return transcribed text

    Args:
        audio_file: Path to audio file (mp3, m4a, wav, mp4)
        app_key: XGJK appKey for authentication

    Returns:
        Transcribed text (tidyText or simpleSummary)
    """
    import requests

    # Step 1: Upload to CWork
    file_url = upload_to_cwork(audio_file, app_key)

    # Step 2: Create Huiji task
    file_ext = Path(audio_file).suffix.lstrip(".")
    print(f"Creating Huiji task...", file=sys.stderr)
    resp = requests.post(
        f"{HUIJI_BASE_URL}/ai-huiji/meetingChat/startChatByFileUrl",
        headers={"appKey": app_key, "Content-Type": "application/json"},
        json={"fileUrl": file_url, "fileExt": file_ext},
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("resultCode") != 1:
        raise Exception(f"Failed to create Huiji task: {result}")

    task_id = result["data"]["_id"]
    print(f"Huiji task created: {task_id}", file=sys.stderr)

    # Step 3: Poll for completion
    max_attempts = 120  # 10 minutes max
    for attempt in range(max_attempts):
        resp = requests.post(
            f"{HUIJI_BASE_URL}/ai-huiji/meetingChat/findChat",
            headers={"appKey": app_key, "Content-Type": "application/json"},
            json={"meetingChatId": task_id},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("resultCode") != 1:
            raise Exception(f"Failed to query Huiji task: {result}")

        data = result["data"]
        state = data.get("recordState")

        if state == 2:  # Completed
            tidy_text = data.get("tidyText")
            simple_summary = data.get("simpleSummary")
            text = tidy_text or simple_summary or ""
            print(f"Transcription completed: {len(text)} chars", file=sys.stderr)
            return text
        elif state == 3:  # Error
            error_msg = data.get("errorMsg", "Unknown error")
            raise Exception(f"Huiji transcription failed: {error_msg}")

        if (attempt + 1) % 12 == 0:  # Every minute
            print(f"Transcribing... ({(attempt + 1) * 5}s / 600s)", file=sys.stderr)

        time.sleep(5)

    raise Exception("Transcription timeout (10 minutes)")


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: transcribe_audio.py <audio_file> [app_key]"}, ensure_ascii=False))
        return 1

    audio_file = sys.argv[1]
    app_key = sys.argv[2] if len(sys.argv) > 2 else load_app_key()

    if not app_key:
        print(json.dumps({
            "ok": False,
            "error": "XGJK appKey not found. Set XGJK_APP_KEY environment variable or add 'xgjk_app_key' to config file."
        }, ensure_ascii=False))
        return 1

    try:
        text = transcribe(audio_file, app_key)
        print(json.dumps({"ok": True, "text": text}, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
