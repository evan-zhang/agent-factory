#!/usr/bin/env python3
"""
list-my-meetings.py — 列出当前 appKey 可访问的会议列表

用途：
    调用 chatListByPage 接口，列出当前 appKey 可访问会议。

用法：
    python3 list-my-meetings.py [page_num] [page_size] [--state {0,1,2,3}] [--name-blur 关键词] [--json]
"""

import os
import json
import time
import argparse
import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api"
URL_CHAT_LIST = f"{API_BASE}/open-api/ai-huiji/meetingChat/chatListByPage"

MAX_RETRIES = 3
RETRY_DELAY = 1
STATE_MAP = {
    0: "进行中",
    1: "处理中",
    2: "已完成",
    3: "失败",
}


def build_headers() -> dict:
    app_key = os.environ.get("XG_BIZ_API_KEY")
    if not app_key:
        raise RuntimeError("请设置环境变量 XG_BIZ_API_KEY")
    return {"Content-Type": "application/json", "appKey": app_key}


def _call_api(url: str, body: dict, timeout: int = 30) -> dict:
    headers = build_headers()
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=timeout, verify=False)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"API 请求失败（重试{MAX_RETRIES}次）: {last_err}")


def normalize_id_fields(item: dict) -> dict:
    raw_id = str(item.get("_id") or "")
    origin_chat_id = item.get("originChatId")
    has_suffix = "__" in raw_id

    if origin_chat_id not in (None, ""):
        normalized = str(origin_chat_id)
        applied = normalized != raw_id
    elif has_suffix:
        normalized = raw_id.split("__", 1)[0]
        applied = True
    else:
        normalized = raw_id
        applied = False

    return {
        "rawId": raw_id or None,
        "originChatId": str(origin_chat_id) if origin_chat_id not in (None, "") else None,
        "normalizedMeetingChatId": normalized,
        "idNormalizationApplied": bool(applied),
        "suffixTruncated": has_suffix,
    }


def format_ts(ts_ms):
    if ts_ms in (None, ""):
        return "-"
    try:
        ms = int(ts_ms)
        return datetime.fromtimestamp(ms / 1000).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_ms)


def _to_int_or_none(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except Exception:
        return None


def format_duration_ms(ms):
    val = _to_int_or_none(ms)
    if val is None:
        return "-"
    seconds = max(0, val // 1000)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}小时{m}分钟{s}秒"
    if m > 0:
        return f"{m}分钟{s}秒"
    return f"{s}秒"


def extract_meetings(raw_data) -> list:
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        for key in ("pageContent", "records", "list", "rows", "items", "data"):
            val = raw_data.get(key)
            if isinstance(val, list):
                return val
    return []


def pick_first(item: dict, keys, default=None):
    for k in keys:
        val = item.get(k)
        if val not in (None, ""):
            return val
    return default


def build_sort_key(state_filter, state, update_time):
    update_num = _to_int_or_none(update_time) or 0
    if state_filter is not None:
        return (0, -update_num)
    ongoing_rank = 0 if state == 0 else 1
    return (ongoing_rank, -update_num)


def normalize_item(item: dict, state_filter=None) -> dict:
    state_code = item.get("combineState")
    update_time = item.get("updateTime")
    create_time = pick_first(item, ["createTime", "createdTime", "gmtCreate"])
    owner_name = pick_first(item, ["creatorName", "ownerName", "userName", "createUserName", "nickname"])
    meeting_number = pick_first(item, ["meetingNumber", "meetingNo", "conferenceNo", "confNo"])
    meeting_length_ms = pick_first(item, ["meetingLength", "duration", "meetingDuration", "durationMs"])
    id_info = normalize_id_fields(item)

    return {
        "meetingChatId": id_info["normalizedMeetingChatId"],
        "rawId": id_info["rawId"],
        "originChatId": id_info["originChatId"],
        "normalizedMeetingChatId": id_info["normalizedMeetingChatId"],
        "idNormalizationApplied": id_info["idNormalizationApplied"],
        "suffixTruncated": id_info["suffixTruncated"],
        "meetingName": item.get("chatName") or item.get("meetingName") or item.get("name") or "",
        "state": state_code,
        "stateText": STATE_MAP.get(state_code, str(state_code)),
        "updateTime": _to_int_or_none(update_time),
        "updateTimeText": format_ts(update_time),
        "createTime": _to_int_or_none(create_time),
        "createTimeText": format_ts(create_time),
        "ownerName": owner_name,
        "meetingNumber": str(meeting_number) if meeting_number not in (None, "") else None,
        "meetingLengthMs": _to_int_or_none(meeting_length_ms),
        "meetingLengthText": format_duration_ms(meeting_length_ms),
        "sort_key": list(build_sort_key(state_filter, state_code, update_time)),
        "raw": item,
    }


def pick_recommended(meetings: list):
    if not meetings:
        return None
    ongoing = next((m for m in meetings if m.get("state") == 0), None)
    if ongoing:
        return ongoing
    completed = next((m for m in meetings if m.get("state") == 2), None)
    if completed:
        return completed
    return meetings[0]


def main():
    parser = argparse.ArgumentParser(description="列出当前 appKey 可访问会议（chatListByPage）")
    parser.add_argument("page_num", nargs="?", type=int, default=0, help="页码（从 0 开始，默认 0）")
    parser.add_argument("page_size", nargs="?", type=int, default=20, help="每页条数（默认 20）")
    parser.add_argument("--state", type=int, choices=[0, 1, 2, 3], help="按状态过滤：0进行中 1处理中 2已完成 3失败")
    parser.add_argument("--name-blur", default="", help="会议名称模糊搜索关键词")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    body = {
        "pageNum": args.page_num,
        "pageSize": args.page_size,
    }
    if args.state is not None:
        body["state"] = args.state
    if args.name_blur:
        body["nameBlur"] = args.name_blur

    result = _call_api(URL_CHAT_LIST, body)
    if result.get("resultCode") != 1:
        raise RuntimeError(f"chatListByPage 失败: {result.get('resultMsg')}")

    meetings = extract_meetings(result.get("data"))
    normalized = [normalize_item(item, state_filter=args.state) for item in meetings]
    normalized.sort(key=lambda m: tuple(m.get("sort_key") or [9, 0]))

    for idx, m in enumerate(normalized, start=1):
        m["index"] = idx

    recommended = pick_recommended(normalized)

    if args.as_json:
        print(json.dumps({
            "page_num": args.page_num,
            "page_size": args.page_size,
            "count": len(normalized),
            "state_filter": args.state,
            "meetings": [
                {
                    "index": m.get("index"),
                    "meetingName": m.get("meetingName"),
                    "meetingChatId": m.get("meetingChatId"),
                    "rawId": m.get("rawId"),
                    "originChatId": m.get("originChatId"),
                    "normalizedMeetingChatId": m.get("normalizedMeetingChatId"),
                    "idNormalizationApplied": m.get("idNormalizationApplied"),
                    "state": m.get("state"),
                    "stateText": m.get("stateText"),
                    "updateTime": m.get("updateTime"),
                    "updateTimeText": m.get("updateTimeText"),
                    "createTime": m.get("createTime"),
                    "createTimeText": m.get("createTimeText"),
                    "ownerName": m.get("ownerName"),
                    "meetingNumber": m.get("meetingNumber"),
                    "meetingLengthMs": m.get("meetingLengthMs"),
                    "meetingLengthText": m.get("meetingLengthText"),
                    "sort_key": m.get("sort_key"),
                }
                for m in normalized
            ],
            "recommended": {
                "index": recommended.get("index"),
                "meetingChatId": recommended.get("meetingChatId"),
                "meetingName": recommended.get("meetingName"),
                "state": recommended.get("state"),
                "stateText": recommended.get("stateText"),
                "updateTimeText": recommended.get("updateTimeText"),
            } if recommended else None,
        }, ensure_ascii=False, indent=2))
        return

    print("════════════════════════════════════════════════════════")
    print("  我可访问的会议（chatListByPage）")
    print("════════════════════════════════════════════════════════")
    print(f"  page_num={args.page_num} page_size={args.page_size} 共 {len(normalized)} 条")
    if args.state is not None:
        print(f"  state={args.state} ({STATE_MAP.get(args.state, '-')})")
        print("  排序: 按更新时间倒序")
    else:
        print("  排序: 进行中优先 → 更新时间倒序")
    if args.name_blur:
        print(f"  name_blur={args.name_blur}")
    print("────────────────────────────────────────────────────────")

    if not normalized:
        print("  (无结果)")
    else:
        for m in normalized:
            print(f"  {m['index']:>2}. {m['meetingName'] or '-'}")
            print(f"      meetingChatId: {m['meetingChatId'] or '-'}")
            if m.get("suffixTruncated") and m.get("rawId") and m.get("meetingChatId"):
                print(f"      ID 归一化     : {m['rawId']} -> {m['meetingChatId']}")
            print(f"      状态         : {m['stateText']}")
            print(f"      更新时间     : {m['updateTimeText']}")
            print(f"      创建时间     : {m['createTimeText']}")
            print(f"      录制人/发起人: {m['ownerName'] or '-'}")
            print(f"      会议号       : {m['meetingNumber'] or '-'}")
            print(f"      会议时长     : {m['meetingLengthText']}")
            print("      ─────────────────────────────")

        print("────────────────────────────────────────────────────────")
        if recommended:
            print(
                f"  推荐候选: #{recommended['index']} {recommended.get('meetingName') or '-'} "
                f"| {recommended.get('stateText')} | {recommended.get('updateTimeText')}"
            )
            print(f"  拉取示例: python3 scripts/huiji/pull-meeting.py --auto --pick-index {recommended['index']}")

    print("════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
