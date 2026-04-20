#!/usr/bin/env python3
"""Audio transcription using XGJK AI Huiji service with CWork file upload."""
import json
import os
import sys
import time
import uuid
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


def upload_to_qiniu(file_path: str, app_key: str) -> str:
    """Upload file to Qiniu cloud storage and return public URL.

    AI慧记 requires the file URL to be from Qiniu (七牛), not MinIO/CWork.
    This function uploads to Qiniu using the official qiniu SDK.

    Args:
        file_path: Path to local file
        app_key: XGJK appKey

    Returns:
        Public URL accessible by 慧记 service
    """
    import qiniu

    file_path = Path(file_path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get Qiniu upload token
    import requests
    resp = requests.get(
        f"{CWORK_API_URL}/cwork-file/getUploadToken/cwork",
        headers={"appKey": app_key},
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("resultCode") != 1:
        raise Exception(f"Failed to get Qiniu token: {result}")

    token_data = result["data"]
    host = token_data["host"]      # e.g. https://cwork.file.hubmedi.com.cn
    token = token_data["token"]   # Qiniu upload token

    # Generate key: UUID + original extension
    suffix = file_path.suffix.lstrip(".") or "mp3"
    key = f"{uuid.uuid4().hex}.{suffix}"

    print(f"Uploading {file_path.name} to Qiniu ({host})...", file=sys.stderr)

    # Upload via qiniu SDK
    ret, info = qiniu.put_file(token, key, str(file_path), mime_type="audio/mpeg")
    if info.status_code != 200:
        raise Exception(f"Qiniu upload failed: {info.status_code} {info.text}")

    # Public URL for 慧记 service
    file_url = f"{host}/{key}"
    print(f"Uploaded to Qiniu: {file_url}", file=sys.stderr)
    return file_url


def transcribe(audio_file: str, app_key: str) -> str:
    """
    Transcribe audio file using XGJK AI Huiji.

    Steps:
    1. Upload audio to CWork file server
    2. Create Huiji task with file URL
    3. Poll checkSecondSttV2 for completion
    4. Concatenate sttPartList rewriteText as full transcript

    API reference: AI慧记 Open API 接口文档 v1.5 (2026-04-16)
      - startChatByFileUrl: §4.7
      - checkSecondSttV2: §4.2  →  CheckSecondSttV2VO

    Args:
        audio_file: Path to audio file (mp3, m4a, wav, mp4)
        app_key: XGJK appKey for authentication

    Returns:
        Transcribed text (concatenated rewriteText from sttPartList)
    """
    import requests

    # Step 1: Upload to CWork
    file_url = upload_to_qiniu(audio_file, app_key)

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

    # Step 3: Poll for completion via checkSecondSttV2 (not findChat)
    # State: 1=进行中, 2=成功, 3=失败
    max_attempts = 120  # 10 minutes max
    for attempt in range(max_attempts):
        resp = requests.post(
            f"{HUIJI_BASE_URL}/ai-huiji/meetingChat/checkSecondSttV2",
            headers={"appKey": app_key, "Content-Type": "application/json"},
            json={"meetingChatId": task_id},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("resultCode") != 1:
            raise Exception(f"Failed to query Huiji task: {result}")

        data = result.get("data")
        if data is None:
            raise Exception("Huiji returned null data during poll")

        state = data.get("state")

        if state == 2:  # Completed
            stt_part_list = data.get("sttPartList") or []
            # Concatenate rewriteText from each part in order
            text_parts = []
            for part in stt_part_list:
                rt = part.get("rewriteText", "").strip()
                if rt:
                    text_parts.append(rt)
            text = "\n".join(text_parts)
            if not text:
                # Fallback: try tidyText / simpleSummary if sttPartList is empty
                text = data.get("tidyText") or data.get("simpleSummary") or ""
                if not text:
                    raise Exception(
                        "Huiji transcription completed (state=2) but both "
                        "sttPartList and tidyText are empty. "
                        "The audio may exceed the service's length limit."
                    )
            print(f"Transcription completed: {len(text)} chars from {len(stt_part_list)} parts", file=sys.stderr)
            return text
        elif state == 3:  # Error
            err_msg = data.get("errMsg") or "Unknown error"
            raise Exception(f"Huiji transcription failed: {err_msg}")

        # state == 1 (进行中) or unexpected: keep polling
        if (attempt + 1) % 12 == 0:  # Every minute
            progress = data.get("totalProgress", "N/A")
            print(f"Transcribing... ({(attempt + 1) * 5}s / 600s, progress={progress})", file=sys.stderr)

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
