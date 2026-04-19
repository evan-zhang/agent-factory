#!/usr/bin/env python3
"""
huiji / chat-list-by-page 脚本

用途：分页查询当前用户的慧记列表（归属维度）

使用方式：
  python3 scripts/huiji/chat-list-by-page.py [--human] [--state <combineState>] [--body '<json>'] [pageNum pageSize]

  # 基本用法（第0页，每页10条，原始JSON）
  python3 chat-list-by-page.py 0 10

  # 人类可读格式（时间戳自动转换）
  python3 chat-list-by-page.py --human 0 10

  # 只查进行中的会议（combineState=0），一步到位
  python3 chat-list-by-page.py --human --state 0 0 10

  # 只查已完成的会议
  python3 chat-list-by-page.py --human --state 2 0 10

  # 完整参数（JSON body）
  python3 chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"chatType":7,"nameBlur":"周会","minTs":1716345600000}'

  # 人类可读 + JSON body
  python3 chat-list-by-page.py --human --body '{"pageNum":0,"pageSize":10}'

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
from datetime import datetime, timezone, timedelta

API_URL = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/chatListByPage"
MAX_RETRIES = 3
RETRY_DELAY = 1

TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

# combineState 映射
COMBINE_STATE = {0: "进行中", 1: "处理中", 2: "已完成", 3: "失败"}


def ts_to_str(ts_ms):
    """毫秒时间戳 → 人类可读时间"""
    if ts_ms is None:
        return "-"
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return str(ts_ms)


def duration_to_str(ms):
    """毫秒时长 → 人类可读"""
    if ms is None:
        return "-"
    try:
        total_sec = int(ms / 1000)
        h, remainder = divmod(total_sec, 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h}小时{m}分钟"
        elif m > 0:
            return f"{m}分钟{s}秒"
        else:
            return f"{s}秒"
    except (TypeError, ValueError):
        return str(ms)


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


def format_human(result: dict) -> str:
    """将结果转换为人类可读格式"""
    if result.get("resultCode") != 1:
        return f"❌ 请求失败: {result.get('resultMsg', '未知错误')}"

    data = result.get("data", {})
    total = data.get("total", 0)
    items = data.get("pageContent", [])
    state_filter = result.get("_stateFilter")

    # --state 过滤时的无结果提示
    if state_filter is not None and len(items) == 0:
        state_name = COMBINE_STATE.get(state_filter, "指定状态")
        return f"没有{state_name}的会议"

    if state_filter is not None:
        state_name = COMBINE_STATE.get(state_filter, "")
        lines = [f"共 {total} 条{state_name}记录：\n"]
    else:
        lines = [f"共 {total} 条记录：\n"]

    for i, item in enumerate(items, 1):
        name = item.get("name", "（无名称）")
        state = COMBINE_STATE.get(item.get("combineState", -1), "未知")
        create = ts_to_str(item.get("createTime"))
        length = duration_to_str(item.get("meetingLength"))
        chat_id = item.get("originChatId") or item.get("_id", "")

        state_icon = "🟢" if item.get("combineState") == 0 else "✅" if item.get("combineState") == 2 else "⏳"
        lines.append(f"{i}. {state_icon} **{name}**")
        lines.append(f"   开始: {create} | 时长: {length}")
        lines.append(f"   ID: {chat_id}")
        if item.get("simpleSummary"):
            summary = item["simpleSummary"][:80] + "..." if len(item.get("simpleSummary", "")) > 80 else item["simpleSummary"]
            lines.append(f"   摘要: {summary}")
        lines.append("")

    return "\n".join(lines)


def main():
    human = "--human" in sys.argv
    # 解析 --state 参数
    state_filter = None
    args_clean = []
    skip_next = False
    for i, a in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if a == "--state" and i + 2 < len(sys.argv) - 1:
            state_filter = int(sys.argv[i + 2])
            skip_next = True
            continue
        if a != "--human":
            args_clean.append(a)

    if len(args_clean) >= 2 and args_clean[0] == "--body":
        if len(args_clean) < 2:
            print("用法: chat-list-by-page.py [--human] [--state <0|1|2|3>] --body '<json>'", file=sys.stderr)
            sys.exit(1)
        body = json.loads(args_clean[1])
    elif len(args_clean) >= 2:
        body = {"pageNum": int(args_clean[0]), "pageSize": int(args_clean[1])}
    else:
        print("用法: chat-list-by-page.py [--human] [--state <0|1|2|3>] [--body '<json>'] [pageNum pageSize]", file=sys.stderr)
        print("  pageNum 从 0 开始", file=sys.stderr)
        print("  --human: 时间戳自动转换为可读格式", file=sys.stderr)
        print("  --state: 按 combineState 过滤 (0=进行中 1=处理中 2=已完成 3=失败)", file=sys.stderr)
        sys.exit(1)

    result = call_api(body)

    # --state 过滤：从返回结果中只保留指定状态
    if state_filter is not None and result.get("resultCode") == 1:
        all_items = result.get("data", {}).get("pageContent", [])
        total = result.get("data", {}).get("total", 0)
        filtered = [item for item in all_items if item.get("combineState") == state_filter]
        result["data"]["pageContent"] = filtered
        result["data"]["total"] = len(filtered)
        result["_stateFilter"] = state_filter
        result["_originalTotal"] = total

    if human:
        print(format_human(result))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
