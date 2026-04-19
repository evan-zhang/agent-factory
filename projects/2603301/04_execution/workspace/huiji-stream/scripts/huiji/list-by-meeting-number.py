#!/usr/bin/env python3
"""
list-by-meeting-number.py — 按视频会议号查询慧记记录列表

用法：
  python3 list-by-meeting-number.py <meetingNumber> [--last-ts <ms>] [--json]
"""

import argparse
import json
import time
from datetime import datetime

from pull_core import URL_BY_MEETING_NUMBER, _call_api


def _to_int_or_none(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except Exception:
        return None


def format_ts(ts_ms):
    val = _to_int_or_none(ts_ms)
    if val is None:
        return "-"
    try:
        return datetime.fromtimestamp(val / 1000).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_ms)


def pick_first(item: dict, keys, default=None):
    for k in keys:
        val = item.get(k)
        if val not in (None, ""):
            return val
    return default


def normalize_item(item: dict) -> dict:
    chat_id = pick_first(item, ["meetingChatId", "chatId", "id"], "")
    start = pick_first(item, ["createTime", "startTime", "meetingStartTime", "beginTime"])
    stop = pick_first(item, ["endTime", "stopTime", "meetingEndTime", "finishTime"])
    return {
        "chatId": str(chat_id) if chat_id not in (None, "") else "",
        "open": bool(item.get("open")),
        "isDoneRecordingFile": bool(item.get("isDoneRecordingFile")),
        "start": _to_int_or_none(start),
        "startText": format_ts(start),
        "stop": _to_int_or_none(stop),
        "stopText": format_ts(stop),
        "raw": item,
    }


def main():
    parser = argparse.ArgumentParser(description="按会议号查询慧记记录（listHuiJiIdsByMeetingNumber）")
    parser.add_argument("meeting_number", help="视频会议号（必填）")
    parser.add_argument("--last-ts", type=int, default=None, help="查询时间下限（毫秒时间戳），默认最近10天")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    meeting_number = (args.meeting_number or "").strip()
    if not meeting_number:
        parser.error("meetingNumber 不能为空")

    last_ts = args.last_ts
    if last_ts is None:
        last_ts = int((time.time() - 10 * 24 * 3600) * 1000)

    body = {
        "meetingNumber": meeting_number,
        "lastTs": int(last_ts),
    }

    try:
        result = _call_api(URL_BY_MEETING_NUMBER, body, timeout=30)
    except Exception as e:
        raise RuntimeError(f"调用 listHuiJiIdsByMeetingNumber 失败: {e}")

    if result.get("resultCode") != 1:
        raise RuntimeError(f"listHuiJiIdsByMeetingNumber 失败: {result.get('resultMsg')}")

    items = result.get("data") or []
    normalized = [normalize_item(item) for item in items]

    if args.as_json:
        print(json.dumps({
            "meetingNumber": meeting_number,
            "lastTs": int(last_ts),
            "count": len(normalized),
            "records": [
                {
                    "chatId": it["chatId"],
                    "open": it["open"],
                    "isDoneRecordingFile": it["isDoneRecordingFile"],
                    "start": it["start"],
                    "stop": it["stop"],
                }
                for it in normalized
            ],
        }, ensure_ascii=False, indent=2))
        return

    print("════════════════════════════════════════════════════════")
    print("  按会议号查询慧记记录")
    print("════════════════════════════════════════════════════════")
    print(f"  meetingNumber={meeting_number} lastTs={last_ts} 共 {len(normalized)} 条")
    print("────────────────────────────────────────────────────────")

    if not normalized:
        print("  (无结果)")
    else:
        for idx, it in enumerate(normalized, start=1):
            print(f"  {idx:>2}. chatId            : {it['chatId'] or '-'}")
            print(f"      open             : {it['open']}")
            print(f"      isDoneRecordingFile: {it['isDoneRecordingFile']}")
            print(f"      start            : {it['startText']}")
            print(f"      stop             : {it['stopText']}")
            print("      ─────────────────────────────")

    print("════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
