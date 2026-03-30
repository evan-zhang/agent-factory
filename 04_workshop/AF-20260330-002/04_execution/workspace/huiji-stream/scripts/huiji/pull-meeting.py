#!/usr/bin/env python3
"""
pull-meeting.py — 会议素材镜像器（meeting-id transcript only）

用途：
    基于 meetingChatId（可显式传入，或自动发现）从服务器拉取该会议的全部文本分片，落盘到
    cms-meeting-materials/{meetingChatId}/ 目录。

    - 已结束会议：一次性全量拉取（优先使用二次转写，fallback 到分片原文），收口
    - 进行中会议：增量持续轮询（lastStartTime 游标），检测结束后自动收口

用法：
    python3 pull-meeting.py [meetingChatId] [--auto] [--pick-index <n>] [--prefer-state <0|2>]
                           [--name "会议名称"] [--force] [--interval <秒>] [--timeout <秒>]

参数：
    meetingChatId   可选，慧记会议 ID（兼容旧用法）
    --auto          自动从「我可访问会议」中选择目标 meetingChatId
    --pick-index    配合 --auto 使用，按序号选择（1-based）
    --prefer-state  配合 --auto 使用，优先状态（0=进行中，2=已完成；默认 0）
    --name          可选，会议名称（写入 manifest，便于识别）
    --force         强制重新拉取（忽略 is_fully_pulled 标记）
    --interval      进行中会议的轮询间隔（秒，默认 10，最小 3）
    --timeout       进行中会议的最长等待时间（秒，0=不限，默认 0）

落盘结构：
    cms-meeting-materials/{meetingChatId}/
    ├── manifest.json
    ├── checkpoint.json
    ├── fragments.ndjson
    ├── transcript.txt
    ├── pull.log
    └── .stop

环境变量：
    XG_BIZ_API_KEY    平台 appKey（必填）
"""

import sys
import os
import json
import time
import argparse
import requests
import urllib3
from datetime import datetime
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
API_BASE = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api"
URL_INCREMENTAL = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordListV2"
URL_FULL = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordList"
URL_SECOND_STT = f"{API_BASE}/open-api/ai-huiji/meetingChat/checkSecondSttV2"
URL_CHAT_LIST = f"{API_BASE}/open-api/ai-huiji/meetingChat/chatListByPage"

MAX_RETRIES = 3
RETRY_DELAY = 1
DEFAULT_POLL_INTERVAL = 10   # 秒
MIN_POLL_INTERVAL = 3
IDLE_THRESHOLD_SEC = 60
STATE_MAP = {0: "进行中", 1: "处理中", 2: "已完成", 3: "失败"}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def build_sort_key(state_filter, state, update_time):
    update_num = _to_int_or_none(update_time) or 0
    if state_filter is not None:
        return (0, -update_num)
    ongoing_rank = 0 if state == 0 else 1
    return (ongoing_rank, -update_num)


def resolve_gateway_name() -> str:
    """返回当前 gateway 名称，默认 default。"""
    for key in ("OPENCLAW_GATEWAY", "OPENCLAW_GATEWAY_NAME", "GATEWAY", "GATEWAY_NAME"):
        val = os.environ.get(key)
        if val:
            return str(val).strip()
    return "default"


def resolve_materials_root() -> Path:
    """
    解析会议素材根目录：
      <base>/cms-meeting-materials/<gateway>/

    优先级：
      1) CMS_MEETING_MATERIALS_ROOT（显式基路径）
      2) ~/.openclaw/cms-meeting-materials（默认共享基路径）

    说明：
      - 默认走用户级共享目录，支持多个 agent 共用。
      - 通过 gateway 分桶，避免跨 gateway 混淆。
    """
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()

    gateway = resolve_gateway_name()
    root = base / gateway
    root.mkdir(parents=True, exist_ok=True)
    return root

def build_headers() -> dict:
    app_key = os.environ.get("XG_BIZ_API_KEY")
    if not app_key:
        raise RuntimeError("请设置环境变量 XG_BIZ_API_KEY")
    return {"Content-Type": "application/json", "appKey": app_key}


def _call_api(url: str, body: dict, timeout: int = 60) -> dict:
    headers = build_headers()
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, json=body, headers=headers,
                                 timeout=timeout, verify=False)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"API 请求失败（重试{MAX_RETRIES}次）: {last_err}")


def normalize_meeting_chat_id(item: dict) -> str:
    origin = item.get("originChatId")
    if origin:
        return str(origin)
    raw_id = str(item.get("_id") or "")
    if "__" in raw_id:
        return raw_id.split("__", 1)[0]
    return raw_id


def extract_meetings(raw_data) -> list:
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        for key in ("records", "list", "rows", "items", "data"):
            val = raw_data.get(key)
            if isinstance(val, list):
                return val
    return []


def list_accessible_meetings(page_num: int = 0, page_size: int = 20, state_filter=None) -> list:
    body = {"pageNum": page_num, "pageSize": page_size}
    if state_filter is not None:
        body["state"] = state_filter

    result = _call_api(URL_CHAT_LIST, body, timeout=30)
    if result.get("resultCode") != 1:
        raise RuntimeError(f"chatListByPage 失败: {result.get('resultMsg')}")
    data = extract_meetings(result.get("data"))

    normalized = []
    for item in data:
        state = item.get("combineState")
        update_time = item.get("updateTime")
        normalized.append({
            "meetingChatId": normalize_meeting_chat_id(item),
            "meetingName": item.get("chatName") or item.get("meetingName") or "",
            "state": state,
            "stateText": STATE_MAP.get(state, str(state)),
            "updateTime": _to_int_or_none(update_time) or 0,
            "updateTimeText": format_ts(update_time),
            "sort_key": list(build_sort_key(state_filter, state, update_time)),
            "raw": item,
        })

    normalized.sort(key=lambda m: tuple(m.get("sort_key") or [9, 0]))
    for idx, m in enumerate(normalized, start=1):
        m["index"] = idx
    return normalized


def choose_meeting_from_accessible(prefer_state: int = 0, pick_index: int = None):
    meetings = list_accessible_meetings(0, 20, state_filter=None)
    if not meetings:
        return None, meetings, []

    preferred = [m for m in meetings if m.get("state") == prefer_state]
    candidates = preferred if preferred else meetings

    if pick_index is not None:
        if pick_index < 1 or pick_index > len(candidates):
            return None, meetings, candidates
        return candidates[pick_index - 1], meetings, candidates

    return candidates[0], meetings, candidates


def build_auto_pick_error(prefer_state: int, pick_index: int = None) -> str:
    base = [
        "--auto 模式下未找到可用会议，无法确定 meetingChatId。",
        "建议先查看可访问会议：",
        "  python3 scripts/huiji/list-my-meetings.py 0 20",
        "然后再执行拉取：",
    ]
    if pick_index is not None:
        base.append(
            f"  python3 scripts/huiji/pull-meeting.py --auto --prefer-state {prefer_state} --pick-index <序号>"
        )
    else:
        base.append(
            f"  python3 scripts/huiji/pull-meeting.py --auto --prefer-state {prefer_state}"
        )
    return "\n".join(base)


# ---------------------------------------------------------------------------
# 落盘工具
# ---------------------------------------------------------------------------
class MeetingStore:
    """管理单场会议的落盘目录。"""

    def __init__(self, base_dir: Path, meeting_chat_id: str):
        self.meeting_chat_id = meeting_chat_id
        self.dir = base_dir / meeting_chat_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.dir / "manifest.json"
        self.checkpoint_path = self.dir / "checkpoint.json"
        self.fragments_path = self.dir / "fragments.ndjson"
        self.transcript_path = self.dir / "transcript.txt"
        self.log_path = self.dir / "pull.log"
        self.stop_path = self.dir / ".stop"

    def log(self, msg: str, level: str = "INFO") -> None:
        ts = now_iso()
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def load_manifest(self) -> dict:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "meeting_chat_id": self.meeting_chat_id,
            "name": "",
            "status": "unknown",
            "is_fully_pulled": False,
            "fragment_count": 0,
            "last_sync": None,
            "created_at": now_iso(),
        }

    def save_manifest(self, manifest: dict) -> None:
        manifest["last_sync"] = now_iso()
        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.manifest_path)

    def load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"last_start_time": None, "updated_at": None}

    def save_checkpoint(self, last_start_time) -> None:
        data = {"last_start_time": last_start_time, "updated_at": now_iso()}
        tmp = self.checkpoint_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.checkpoint_path)

    def load_dedup_keys(self) -> set:
        keys = set()
        if not self.fragments_path.exists():
            return keys
        try:
            with open(self.fragments_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        keys.add((obj.get("_segment_id"), obj.get("_version", 1)))
                    except Exception:
                        pass
        except Exception:
            pass
        return keys

    def append_fragments(self, frags: list, version: int = 1) -> int:
        dedup = self.load_dedup_keys()
        new_count = 0
        try:
            with open(self.fragments_path, "a", encoding="utf-8") as f:
                for frag in frags:
                    seg_id = str(frag.get("startTime"))
                    key = (seg_id, version)
                    if key in dedup:
                        continue
                    record = {
                        "_meeting_chat_id": self.meeting_chat_id,
                        "_segment_id": seg_id,
                        "_version": version,
                        "_appended_at": now_iso(),
                        **frag,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    dedup.add(key)
                    new_count += 1
        except Exception as e:
            self.log(f"append_fragments 失败: {e}", "ERROR")
        return new_count

    def rebuild_transcript(self) -> int:
        if not self.fragments_path.exists():
            return 0
        try:
            seen = {}
            with open(self.fragments_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        seg_id = obj.get("_segment_id")
                        ver = obj.get("_version", 1)
                        if seg_id not in seen or ver > seen[seg_id].get("_version", 1):
                            seen[seg_id] = obj
                    except Exception:
                        pass

            sorted_frags = sorted(seen.values(), key=lambda x: x.get("startTime") or 0)
            lines = []
            for frag in sorted_frags:
                text = frag.get("text") or ""
                start_ms = frag.get("startTime")
                if start_ms is not None:
                    mins, secs = divmod(start_ms // 1000, 60)
                    hrs, mins = divmod(mins, 60)
                    ts_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    ts_str = "??"
                lines.append(f"[{ts_str}] {text}")

            tmp = self.transcript_path.with_suffix(".txt.tmp")
            tmp.write_text("\n".join(lines), encoding="utf-8")
            tmp.replace(self.transcript_path)
            return len(lines)
        except Exception as e:
            self.log(f"rebuild_transcript 失败: {e}", "ERROR")
            return 0

    def should_stop(self) -> bool:
        return self.stop_path.exists()

    def clear_stop(self) -> None:
        try:
            self.stop_path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# API 调用
# ---------------------------------------------------------------------------
def fetch_incremental(meeting_chat_id: str, last_start_time=None) -> list:
    body = {"meetingChatId": meeting_chat_id}
    if last_start_time is not None:
        body["lastStartTime"] = last_start_time
    result = _call_api(URL_INCREMENTAL, body)
    if result.get("resultCode") != 1:
        raise RuntimeError(f"splitRecordListV2 失败: {result.get('resultMsg')}")
    data = result.get("data") or []
    return [f for f in data if f.get("startTime") is not None]


def fetch_full(meeting_chat_id: str) -> list:
    result = _call_api(URL_FULL, {"meetingChatId": meeting_chat_id})
    if result.get("resultCode") != 1:
        raise RuntimeError(f"splitRecordList 失败: {result.get('resultMsg')}")
    return [f for f in (result.get("data") or []) if f.get("startTime") is not None]


def fetch_second_stt(meeting_chat_id: str):
    try:
        result = _call_api(URL_SECOND_STT, {"meetingChatId": meeting_chat_id}, timeout=30)
        if result.get("resultCode") != 1:
            return None
        state = result.get("state")
        if state != 2:
            return None
        stt_list = [f for f in (result.get("sttPartList") or []) if f.get("startTime") is not None]
        return stt_list if stt_list else None
    except Exception:
        return None


def detect_meeting_status(meeting_chat_id: str) -> str:
    try:
        result = _call_api(URL_SECOND_STT, {"meetingChatId": meeting_chat_id}, timeout=30)
        if result.get("resultCode") == 1:
            state = result.get("state")
            if state == 2:
                return "completed"
            if state in (1, 3):
                return "completed"
        return "ongoing"
    except Exception:
        return "ongoing"


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------
def pull_completed(store: MeetingStore, manifest: dict) -> None:
    meeting_chat_id = store.meeting_chat_id
    store.log("检测到会议已结束，执行全量拉取…")

    stt_frags = fetch_second_stt(meeting_chat_id)
    if stt_frags:
        store.log(f"二次转写可用，共 {len(stt_frags)} 个分片（version=2）")
        new_v2 = store.append_fragments(stt_frags, version=2)
        store.log(f"新增二次转写分片 {new_v2} 条")
        try:
            v1_frags = fetch_full(meeting_chat_id)
            new_v1 = store.append_fragments(v1_frags, version=1)
            store.log(f"同步原始分片（v1）{new_v1} 条")
        except Exception as e:
            store.log(f"拉取 v1 分片失败（非致命）: {e}", "WARN")
    else:
        store.log("二次转写暂不可用，使用全量分片原文（version=1）")
        v1_frags = fetch_full(meeting_chat_id)
        store.log(f"全量分片共 {len(v1_frags)} 个")
        new_v1 = store.append_fragments(v1_frags, version=1)
        store.log(f"新增分片 {new_v1} 条")

    all_frags = fetch_full(meeting_chat_id)
    if all_frags:
        max_start = max(f.get("startTime") or 0 for f in all_frags)
        store.save_checkpoint(max_start)

    total = store.rebuild_transcript()
    store.log(f"transcript.txt 重建完成，共 {total} 行")

    manifest["status"] = "completed"
    manifest["is_fully_pulled"] = True
    manifest["fragment_count"] = total
    store.save_manifest(manifest)
    store.log("已结束会议全量拉取完成，is_fully_pulled=true ✅")


def pull_ongoing(store: MeetingStore, manifest: dict, interval: int, timeout_sec: int) -> None:
    meeting_chat_id = store.meeting_chat_id
    store.log(f"检测到会议进行中，启动增量轮询（interval={interval}s）…")
    if timeout_sec > 0:
        store.log(f"最长等待 {timeout_sec}s 后自动退出")

    checkpoint = store.load_checkpoint()
    last_start_time = checkpoint.get("last_start_time")
    start_ts = time.time()
    idle_since = time.time()
    consecutive_errors = 0

    while True:
        if store.should_stop():
            store.log("检测到 .stop 标记，安全退出增量轮询")
            store.clear_stop()
            manifest["status"] = "ongoing"
            manifest["is_fully_pulled"] = False
            store.save_manifest(manifest)
            return

        if timeout_sec > 0 and (time.time() - start_ts) > timeout_sec:
            store.log(f"已达到最长等待时间 {timeout_sec}s，退出轮询")
            manifest["status"] = "ongoing"
            store.save_manifest(manifest)
            return

        try:
            new_frags = fetch_incremental(meeting_chat_id, last_start_time)
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            store.log(f"增量拉取失败（第{consecutive_errors}次）: {e}", "ERROR")
            backoff = min(2 ** consecutive_errors, 30)
            store.log(f"等待 {backoff}s 后重试…")
            time.sleep(backoff)
            continue

        if new_frags:
            new_count = store.append_fragments(new_frags, version=1)
            if new_count > 0:
                store.log(f"新增分片 {new_count} 条（共拉到 {len(new_frags)} 条）")
                max_start = max(f.get("startTime") or 0 for f in new_frags)
                last_start_time = max_start
                store.save_checkpoint(last_start_time)
                total = store.rebuild_transcript()
                manifest["fragment_count"] = total
                store.save_manifest(manifest)
                idle_since = time.time()
            else:
                store.log(f"拉到 {len(new_frags)} 条但全部重复，无新数据")
        else:
            store.log("无新分片")

        meeting_status = "ongoing"
        try:
            meeting_status = detect_meeting_status(meeting_chat_id)
        except Exception as e:
            store.log(f"检测会议状态失败: {e}", "WARN")

        if meeting_status == "completed":
            store.log("检测到会议已结束，执行收口拉取…")
            try:
                pull_completed(store, manifest)
            except Exception as e:
                store.log(f"收口拉取失败: {e}", "ERROR")
                manifest["status"] = "completed"
                manifest["is_fully_pulled"] = False
                store.save_manifest(manifest)
            return

        idle_sec = time.time() - idle_since
        sleep_sec = min(interval * 2, 30) if idle_sec > IDLE_THRESHOLD_SEC else interval
        store.log(f"等待 {sleep_sec}s 后继续…")

        elapsed = 0
        while elapsed < sleep_sec:
            time.sleep(min(1, sleep_sec - elapsed))
            elapsed += 1
            if store.should_stop():
                break


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="会议素材镜像器：拉取指定 meetingChatId 的全部文本素材")
    parser.add_argument("meeting_chat_id", nargs="?", default=None, help="慧记会议 ID（可选；未提供时可配合 --auto）")
    parser.add_argument("--auto", action="store_true", help="自动从我可访问会议中选择目标 meetingChatId")
    parser.add_argument("--pick-index", type=int, default=None, help="配合 --auto：按序号选择候选会议（1-based）")
    parser.add_argument("--prefer-state", type=int, choices=[0, 2], default=0,
                        help="配合 --auto：优先状态（0=进行中，2=已完成，默认 0）")
    parser.add_argument("--name", default="", help="会议名称（可选）")
    parser.add_argument("--force", action="store_true", help="强制重新拉取，忽略 is_fully_pulled 标记")
    parser.add_argument("--interval", type=int, default=DEFAULT_POLL_INTERVAL,
                        help=f"进行中会议的轮询间隔（秒，默认 {DEFAULT_POLL_INTERVAL}）")
    parser.add_argument("--timeout", type=int, default=0, help="进行中会议的最长等待时间（秒，0=不限）")
    args = parser.parse_args()

    meeting_chat_id = args.meeting_chat_id

    if not meeting_chat_id and not args.auto:
        parser.error("必须提供 meeting_chat_id，或使用 --auto 自动发现。")

    auto_selected = None
    if args.auto and not meeting_chat_id:
        selected, all_items, candidates = choose_meeting_from_accessible(args.prefer_state, args.pick_index)
        if not selected:
            print(build_auto_pick_error(args.prefer_state, args.pick_index), file=sys.stderr)
            if all_items:
                print("\n可访问会议候选：", file=sys.stderr)
                for item in candidates:
                    print(
                        f"  {item.get('index')}. {item.get('meetingChatId')} | "
                        f"{item.get('meetingName') or '-'} | {item.get('stateText')} | "
                        f"{item.get('updateTimeText')}",
                        file=sys.stderr,
                    )
            sys.exit(2)

        meeting_chat_id = selected["meetingChatId"]
        auto_selected = selected

    interval = max(MIN_POLL_INTERVAL, args.interval)

    base_dir = resolve_materials_root()
    store = MeetingStore(base_dir, meeting_chat_id)

    if auto_selected:
        store.log(
            f"--auto 自动选择: {auto_selected.get('meetingName') or '-'} | "
            f"{auto_selected.get('stateText')} | {auto_selected.get('updateTimeText')} "
            f"(meetingChatId={meeting_chat_id}, pick_index={auto_selected.get('index')})"
        )

    store.log(f"=== pull-meeting 启动 | meetingChatId={meeting_chat_id} ===")

    manifest = store.load_manifest()
    if args.name:
        manifest["name"] = args.name
    elif auto_selected and auto_selected.get("meetingName") and not manifest.get("name"):
        manifest["name"] = auto_selected.get("meetingName")

    if manifest.get("is_fully_pulled") and not args.force:
        store.log("manifest.is_fully_pulled=true，已完成跳过。如需重新拉取请加 --force")
        print(json.dumps({
            "status": "skipped",
            "reason": "already_fully_pulled",
            "meeting_chat_id": meeting_chat_id,
            "fragment_count": manifest.get("fragment_count", 0),
        }, ensure_ascii=False, indent=2))
        return

    store.clear_stop()

    store.log("检测会议状态…")
    try:
        status = detect_meeting_status(meeting_chat_id)
    except Exception as e:
        store.log(f"检测会议状态异常: {e}，默认视为 ongoing", "WARN")
        status = "ongoing"

    store.log(f"会议状态: {status}")
    manifest["status"] = status

    if status == "completed":
        pull_completed(store, manifest)
    else:
        pull_ongoing(store, manifest, interval, args.timeout)

    manifest = store.load_manifest()
    print(json.dumps({
        "meeting_chat_id": meeting_chat_id,
        "status": manifest.get("status"),
        "is_fully_pulled": manifest.get("is_fully_pulled"),
        "fragment_count": manifest.get("fragment_count"),
        "last_sync": manifest.get("last_sync"),
        "materials_dir": str(store.dir),
        "auto_selected": bool(auto_selected),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
