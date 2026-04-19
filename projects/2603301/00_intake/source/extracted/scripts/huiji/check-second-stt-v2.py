#!/usr/bin/env python3
"""
huiji / check-second-stt-v2 脚本

用途：查询已结束会议的改写原文状态；成功时 sttPartList 常含优于会中分片的原文（可能有发言人区分）

使用方式：
  python3 scripts/huiji/check-second-stt-v2.py [--body '<json>'] <meetingChatId>

  # 基本用法
  python3 check-second-stt-v2.py abc123

  # JSON body
  python3 check-second-stt-v2.py --body '{"meetingChatId":"abc123"}'

环境变量：
  XG_BIZ_API_KEY   — appKey（必须）
  XG_USER_TOKEN    — access-token（可选，增强鉴权）
"""

import sys
import os
import json
import urllib.request
import ssl
import time

API_URL = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/checkSecondSttV2"
MAX_RETRIES = 3
RETRY_DELAY = 1


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("XG_USER_TOKEN")
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if token:
        headers["access-token"] = token
    if app_key:
        headers["appKey"] = app_key
    if not token and not app_key:
        print("错误: 请至少设置 XG_USER_TOKEN 或 XG_BIZ_API_KEY", file=sys.stderr)
        sys.exit(1)
    return headers


def call_api(body: dict) -> dict:
    headers = build_headers()
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    print(f"错误: 请求失败（重试{MAX_RETRIES}次）: {last_err}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--body":
        if len(sys.argv) < 3:
            print("用法: check-second-stt-v2.py --body '<json>'", file=sys.stderr)
            sys.exit(1)
        body = json.loads(sys.argv[2])
    elif len(sys.argv) >= 2:
        body = {"meetingChatId": sys.argv[1]}
    else:
        print("用法: check-second-stt-v2.py [--body '<json>'] <meetingChatId>", file=sys.stderr)
        sys.exit(1)
    result = call_api(body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
