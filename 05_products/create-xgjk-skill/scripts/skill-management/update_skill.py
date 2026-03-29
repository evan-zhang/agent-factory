#!/usr/bin/env python3
"""
更新已有 Skill

用途：更新已注册 Skill 的信息（名称、描述、下载地址等）

使用方式：
  python3 create-xgjk-skill/scripts/skill-management/update_skill.py --code <code> [--name <name>] [--description <desc>] [--download-url <url>] [--label <label>] [--version <ver>] [--internal]

参数说明：
  --code          Skill 唯一标识（必须）
  --name          新的 Skill 名称
  --description   新的描述
  --download-url  新的下载地址
  --label         新的标签
  --version       版本号
  --internal      标记为内部 Skill

环境变量：
  XG_USER_TOKEN  — access-token（必须）
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import ssl

API_URL = "https://sg-cwork-api.mediportal.com.cn/im/skill/update"


def call_api(token: str, payload: dict) -> dict:
    """更新 Skill 信息"""
    headers = {
        "access-token": token,
        "Content-Type": "application/json",
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")

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

    parser = argparse.ArgumentParser(description="更新已有 Skill")
    parser.add_argument("--code", required=True, help="Skill 唯一标识")
    parser.add_argument("--name", default="", help="新的 Skill 名称")
    parser.add_argument("--description", default="", help="新的描述")
    parser.add_argument("--download-url", default="", help="新的下载地址")
    parser.add_argument("--label", default="", help="新的标签")
    parser.add_argument("--version", type=int, default=0, help="版本号")
    parser.add_argument("--internal", action="store_true", help="标记为内部 Skill")
    args = parser.parse_args()

    payload = {
        "code": args.code,
    }
    if args.name:
        payload["name"] = args.name
    if args.description:
        payload["description"] = args.description
    if args.download_url:
        payload["downloadUrl"] = args.download_url
    if args.label:
        payload["label"] = args.label
    if args.version:
        payload["version"] = args.version
    if args.internal:
        payload["isInternal"] = True

    result = call_api(token, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
