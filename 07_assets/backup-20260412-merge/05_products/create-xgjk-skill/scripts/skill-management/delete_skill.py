#!/usr/bin/env python3
"""
下架（删除）Skill

用途：将已发布的 Skill 下架

使用方式：
  python3 create-xgjk-skill/scripts/skill-management/delete_skill.py --id <skill-id> [--reason <下架原因>]

参数说明：
  --id       Skill ID（必须）
  --reason   下架原因（可选）

环境变量：
  XG_USER_TOKEN  — access-token（必须）
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
import ssl

API_URL = "https://sg-cwork-api.mediportal.com.cn/im/skill/delete"


def call_api(token: str, skill_id: str, reason: str = "") -> dict:
    """下架 Skill"""
    headers = {
        "access-token": token,
        "Content-Type": "application/json",
    }

    params = {"id": skill_id}
    if reason:
        params["deleteSkill"] = reason

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=b"", headers=headers, method="POST")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    token = os.environ.get("XG_USER_TOKEN")

    if not token:
        print("错误: 请设置环境变量 XG_USER_TOKEN", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="下架（删除）Skill")
    parser.add_argument("--id", required=True, help="Skill ID")
    parser.add_argument("--reason", default="", help="下架原因")
    args = parser.parse_args()

    result = call_api(token, args.id, args.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
