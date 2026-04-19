#!/usr/bin/env python3
"""Audio transcription using XGJK AI Huiji service.

Flow:
1. Get Qiniu upload token from CWork file service
2. Upload audio to Qiniu using SDK
3. Call startChatByFileUrl to create Huiji task
4. Poll checkSecondSttV2 for transcription result

Official API docs: https://github.com/xgjk/dev-guide (AI慧记 API说明 v1.4)
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

BASE_URL = os.getenv("XGJK_BASE_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
# 七牛空间外链域名（从官方文档示例推断）
QINIU_BUCKET_DOMAIN = os.getenv("XGJK_QINIU_DOMAIN", "https://filegpt-hn.file.mediportal.com.cn")


def load_app_key() -> str | None:
    """Load appKey from config file or environment."""
    env_key = os.getenv("XGJK_APP_KEY")
    if env_key:
        return env_key

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


def get_qiniu_upload_token(app_key: str) -> dict:
    """Get Qiniu upload token from CWork file service.
    
    API: GET /cwork-file/getUploadToken/cwork
    Returns: {"token": "...", ...}
    """
    import requests

    resp = requests.get(
        f"{BASE_URL}/cwork-file/getUploadToken/cwork",
        headers={"appKey": app_key},
        timeout=10
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("resultCode") != 1:
        raise Exception(f"Failed to get upload token: {result}")

    return result["data"]


def upload_to_qiniu(file_path: str, token: str) -> str:
    """Upload file to Qiniu using SDK.
    
    Returns: Qiniu key (used to construct public URL)
    """
    from qiniu import put_file_v2

    file_path = Path(file_path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.suffix  # e.g. ".mp3"
    key = f"{uuid.uuid4()}{ext}"

    print(f"Uploading {file_path.name} to Qiniu...", file=sys.stderr)
    ret, info = put_file_v2(token, key, str(file_path), version="v2")

    if ret is None:
        raise Exception(f"Qiniu upload failed: {info}")

    print(f"Uploaded to Qiniu key: {key}", file=sys.stderr)
    return key


def create_huiji_task(file_url: str, file_ext: str, app_key: str) -> str:
    """Create Huiji transcription task.
    
    API: POST /ai-huiji/meetingChat/startChatByFileUrl
    Returns: meetingChatId
    """
    import requests

    print(f"Creating Huiji task...", file=sys.stderr)
    resp = requests.post(
        f"{BASE_URL}/ai-huiji/meetingChat/startChatByFileUrl",
        headers={"appKey": app_key, "Content-Type": "application/json"},
        json={"fileUrl": file_url, "fileExt": file_ext},
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("resultCode") != 1:
        raise Exception(f"Failed to create Huiji task: {result}")

    data = result["data"]
    task_id = data["_id"]
    state = data.get("recordState")
    print(f"Huiji task created: {task_id}, state: {state}", file=sys.stderr)
    return task_id


def poll_transcription(task_id: str, app_key: str, timeout: int = 600) -> str:
    """Poll for transcription completion.
    
    API: POST /ai-huiji/meetingChat/checkSecondSttV2
    Returns: transcribed text (改写文本拼接)
    """
    import requests

    max_attempts = timeout // 5
    for attempt in range(max_attempts):
        resp = requests.post(
            f"{BASE_URL}/ai-huiji/meetingChat/checkSecondSttV2",
            headers={"appKey": app_key, "Content-Type": "application/json"},
            json={"meetingChatId": task_id},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("resultCode") != 1:
            raise Exception(f"Failed to check transcription: {result}")

        data = result["data"]
        state = data.get("state")

        # state: 1=进行中, 2=成功, 3=失败
        if state == 2:
            # Extract rewritten text from sttPartList
            parts = data.get("sttPartList", [])
            texts = []
            for part in sorted(parts, key=lambda p: p.get("startTime", 0)):
                text = part.get("rewriteText", "")
                if text:
                    texts.append(text)
            full_text = "\n".join(texts)
            print(f"Transcription completed: {len(full_text)} chars", file=sys.stderr)
            return full_text
        elif state == 3:
            error_msg = data.get("errMsg", "Unknown error")
            raise Exception(f"Transcription failed: {error_msg}")

        # Still processing (state == 1 or None)
        if (attempt + 1) % 12 == 0:  # Every minute
            progress = data.get("totalProgress", 0)
            print(f"Transcribing... progress={progress}% ({(attempt + 1) * 5}s / {timeout}s)", file=sys.stderr)

        time.sleep(5)

    raise Exception(f"Transcription timeout ({timeout}s)")


def transcribe(audio_file: str, app_key: str) -> str:
    """Full transcription pipeline.
    
    Args:
        audio_file: Path to audio file (mp3, m4a, wav, mp4)
        app_key: XGJK appKey
    
    Returns:
        Transcribed text
    """
    file_path = Path(audio_file).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = file_path.suffix.lstrip(".")  # "mp3", "m4a", etc.

    # Step 1: Get Qiniu upload token
    token_data = get_qiniu_upload_token(app_key)
    qiniu_token = token_data["token"]

    # Step 2: Upload to Qiniu
    key = upload_to_qiniu(file_path, qiniu_token)
    file_url = f"{QINIU_BUCKET_DOMAIN}/{key}"

    # Step 3: Create Huiji task
    task_id = create_huiji_task(file_url, file_ext, app_key)

    # Step 4: Poll for result
    text = poll_transcription(task_id, app_key)
    return text


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "error": "usage: transcribe_audio.py <audio_file> [app_key]"
        }, ensure_ascii=False))
        return 1

    audio_file = sys.argv[1]
    app_key = sys.argv[2] if len(sys.argv) > 2 else load_app_key()

    if not app_key:
        print(json.dumps({
            "ok": False,
            "error": "XGJK appKey not found. Set XGJK_APP_KEY env var or add 'xgjk_app_key' to config."
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
