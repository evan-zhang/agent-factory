#!/usr/bin/env python3
"""
上传文件到七牛云存储

用途：获取七牛上传凭证 → 上传文件 → 返回下载地址

使用方式：
  python3 create-xgjk-skill/scripts/skill-management/upload_to_qiniu.py <file-path> [--file-key <key>] [--corp-id <id>]

参数说明：
  file-path     要上传的文件路径（必须）
  --file-key    七牛文件 key（可选，默认为 时间戳-文件名）
  --corp-id     企业 ID（可选，也可通过环境变量 XG_CORP_ID 设置）

环境变量：
  XG_USER_TOKEN  — access-token（必须，用于获取七牛上传凭证）
  XG_CORP_ID     — 企业 ID（可选，也可通过 --corp-id 参数传入）

示例：
  python3 create-xgjk-skill/scripts/skill-management/upload_to_qiniu.py ./im-robot.zip
  python3 create-xgjk-skill/scripts/skill-management/upload_to_qiniu.py ./im-robot.zip --file-key "skills/im-robot-v1.zip"

输出：
  成功时输出下载地址到 stdout，可直接作为 register_skill.py 的 --download-url 参数。
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
import ssl
import io

# 七牛上传凭证接口
QINIU_AUTH_URL = "https://sg-cwork-api.mediportal.com.cn/ai-business/qiNiu/getSimpleUploadCredentials"

# 七牛上传地址（z2 区域）
QINIU_UPLOAD_URL = "https://up-z2.qiniup.com/"


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_qiniu_token(access_token: str, file_key: str, corp_id: str = "") -> dict:
    """
    获取七牛上传凭证，返回 {token, domain}。
    与前端逻辑一致：先 GET，GET 不支持则 fallback 到 POST。
    """
    ctx = _ssl_context()

    # ── 尝试 GET ──（与前端一致，corpId 始终传，即使为空）
    query_params = {"fileKey": file_key, "corpId": corp_id}
    get_url = f"{QINIU_AUTH_URL}?{urllib.parse.urlencode(query_params)}"

    headers = {
        "access-token": access_token,
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(get_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("data") and data["data"].get("token") and data["data"].get("domain"):
            return data["data"]
        # GET 返回但数据不完整，检查是否是 method not supported
        msg = (data.get("resultMsg") or data.get("detailMsg") or "").lower()
        if "not supported" not in msg and "method not allowed" not in msg:
            raise RuntimeError(f"获取七牛凭证失败 (GET): {json.dumps(data, ensure_ascii=False)}")
    except urllib.error.HTTPError as e:
        if e.code != 405:
            raise

    # ── Fallback POST ──
    print("GET 方式不支持，尝试 POST ...", file=sys.stderr)
    post_body = {"fileKey": file_key, "corpId": corp_id}
    body_bytes = json.dumps(post_body).encode("utf-8")

    req = urllib.request.Request(QINIU_AUTH_URL, data=body_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not data.get("data") or not data["data"].get("token"):
        raise RuntimeError(f"获取七牛凭证失败 (POST): {json.dumps(data, ensure_ascii=False)}")

    return data["data"]


def upload_file(qiniu_token: str, file_key: str, file_path: str) -> bool:
    """通过 multipart/form-data 上传文件到七牛"""
    boundary = f"----PythonBoundary{int(time.time() * 1000)}"

    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_data = f.read()

    # 手动构造 multipart body
    body = io.BytesIO()

    # token 字段
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="token"\r\n\r\n')
    body.write(f"{qiniu_token}\r\n".encode())

    # key 字段
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="key"\r\n\r\n')
    body.write(f"{file_key}\r\n".encode())

    # file 字段
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode())
    body.write(b"Content-Type: application/octet-stream\r\n\r\n")
    body.write(file_data)
    body.write(b"\r\n")

    # 结束
    body.write(f"--{boundary}--\r\n".encode())

    body_bytes = body.getvalue()

    upload_url = QINIU_UPLOAD_URL
    ctx = _ssl_context()

    req = urllib.request.Request(
        upload_url,
        data=body_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body_bytes)),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=300) as resp:
            resp_body = resp.read().decode("utf-8")
            status = resp.getcode()
            if status != 200:
                raise RuntimeError(f"七牛上传失败 (HTTP {status}): {resp_body}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        # 七牛区域重定向：错误信息中包含 "please use <host>"
        import re
        region_match = re.search(r'please use\s+([a-z0-9.-]+)', error_body, re.IGNORECASE)
        if region_match:
            new_host = region_match.group(1)
            new_url = f"https://{new_host}/"
            print(f"区域重定向: {new_url}", file=sys.stderr)
            req2 = urllib.request.Request(
                new_url,
                data=body_bytes,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(body_bytes)),
                },
                method="POST",
            )
            with urllib.request.urlopen(req2, context=ctx, timeout=300) as resp2:
                if resp2.getcode() != 200:
                    raise RuntimeError(f"七牛上传失败（重定向后）: {resp2.read().decode('utf-8')}")
        else:
            raise RuntimeError(f"七牛上传失败 (HTTP {e.code}): {error_body}")

    return True


def main():
    token = os.environ.get("XG_USER_TOKEN")
    if not token:
        print("错误: 请设置环境变量 XG_USER_TOKEN", file=sys.stderr)
        sys.exit(1)

    corp_id = os.environ.get("XG_CORP_ID", "")

    parser = argparse.ArgumentParser(description="上传文件到七牛云存储")
    parser.add_argument("file_path", help="要上传的文件路径")
    parser.add_argument("--file-key", default="", help="七牛文件 key（默认自动生成）")
    parser.add_argument("--corp-id", default="", help="企业 ID（也可通过 XG_CORP_ID 环境变量设置）")
    args = parser.parse_args()

    corp_id = args.corp_id or corp_id

    file_path = os.path.abspath(args.file_path)
    if not os.path.isfile(file_path):
        print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    file_name = os.path.basename(file_path)
    file_key = args.file_key or f"{int(time.time() * 1000)}-{file_name}"

    # Step 1: 获取七牛上传凭证
    print(f"[1/2] 获取七牛上传凭证 (fileKey={file_key}) ...", file=sys.stderr)
    creds = get_qiniu_token(token, file_key, corp_id)
    qiniu_token = creds["token"]
    domain = creds["domain"]
    print(f"[1/2] 凭证获取成功，domain={domain}", file=sys.stderr)

    # Step 2: 上传文件
    size_kb = os.path.getsize(file_path) / 1024
    print(f"[2/2] 上传 {file_name} ({size_kb:.1f} KB) ...", file=sys.stderr)
    upload_file(qiniu_token, file_key, file_path)

    # 构造下载地址
    base_url = domain if domain.startswith("http") else f"https://{domain}"
    base_url = base_url.rstrip("/")
    download_url = f"{base_url}/{file_key}"

    print(f"[2/2] 上传成功!", file=sys.stderr)
    print(f"下载地址: {download_url}", file=sys.stderr)

    # 输出下载地址到 stdout（方便管道）
    print(download_url)


if __name__ == "__main__":
    main()
