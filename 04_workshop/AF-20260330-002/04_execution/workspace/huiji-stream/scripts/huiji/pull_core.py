#!/usr/bin/env python3
"""
pull_core.py — huiji pull 核心逻辑（短任务优先）
"""

import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api"
URL_INCREMENTAL = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordListV2"
URL_FULL = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordList"
URL_SECOND_STT = f"{API_BASE}/open-api/ai-huiji/meetingChat/checkSecondSttV2"
URL_BY_MEETING_NUMBER = f"{API_BASE}/open-api/ai-huiji/meetingChat/listHuiJiIdsByMeetingNumber"

DEFAULT_INTERVAL = 120
ALLOWED_INTERVALS = {60, 120, 180}
LOCK_TTL_SECONDS = 150
MAX_LIFETIME_SECONDS = 10 * 3600
CIRCUIT_OPEN_SECONDS = 15 * 60
BACKOFF_STEPS = [30, 60, 120, 300]


class ApiCallError(RuntimeError):
    def __init__(self, message: str, http_status=None):
        super().__init__(message)
        self.http_status = http_status


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_epoch() -> int:
    return int(time.time())


def resolve_gateway_name(gateway=None) -> str:
    if gateway:
        return str(gateway).strip()
    for key in ("OPENCLAW_GATEWAY", "OPENCLAW_GATEWAY_NAME", "GATEWAY", "GATEWAY_NAME"):
        val = os.environ.get(key)
        if val:
            return str(val).strip()
    return "default"


def resolve_materials_root(gateway=None) -> Path:
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()
    root = base / resolve_gateway_name(gateway)
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_headers() -> dict:
    app_key = os.environ.get("XG_BIZ_API_KEY")
    if not app_key:
        raise RuntimeError("请设置环境变量 XG_BIZ_API_KEY")
    return {"Content-Type": "application/json", "appKey": app_key}


def _call_api(url: str, body: dict, timeout: int = 60) -> dict:
    headers = build_headers()
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout, verify=False)
        if resp.status_code >= 400:
            msg = resp.text[:300]
            raise ApiCallError(f"HTTP {resp.status_code}: {msg}", http_status=resp.status_code)
        return resp.json()
    except requests.exceptions.RequestException as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        raise ApiCallError(f"network_error: {e}", http_status=status)


def resolve_meeting_chat_id_by_number(meeting_number: str, last_ts=None) -> dict:
    if not meeting_number:
        raise RuntimeError("meeting_number 不能为空")
    if last_ts is None:
        last_ts = int((time.time() - 10 * 24 * 3600) * 1000)

    result = _call_api(URL_BY_MEETING_NUMBER, {
        "meetingNumber": str(meeting_number),
        "lastTs": int(last_ts),
    }, timeout=30)
    if result.get("resultCode") != 1:
        raise RuntimeError(f"listHuiJiIdsByMeetingNumber 失败: {result.get('resultMsg')}")

    data = result.get("data") or []
    if not data:
        raise RuntimeError(f"meetingNumber={meeting_number} 未查询到 meetingChatId")

    picked = sorted(data, key=lambda x: x.get("createTime") or 0, reverse=True)[0]
    chat_id = picked.get("meetingChatId")
    if not chat_id:
        raise RuntimeError("返回结果缺少 meetingChatId")

    return {
        "meetingNumber": str(meeting_number),
        "meetingChatId": str(chat_id),
        "open": bool(picked.get("open")),
    }


class MeetingStore:
    def __init__(self, meeting_chat_id: str, gateway=None):
        self.gateway = resolve_gateway_name(gateway)
        self.meeting_chat_id = meeting_chat_id
        self.dir = resolve_materials_root(self.gateway) / meeting_chat_id
        self.dir.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.dir / "manifest.json"
        self.checkpoint_path = self.dir / "checkpoint.json"
        self.fragments_path = self.dir / "fragments.ndjson"
        self.transcript_path = self.dir / "transcript.txt"
        self.log_path = self.dir / "pull.log"
        self.stop_path = self.dir / ".stop"
        self.lock_path = self.dir / ".pull.lock"

    def log(self, msg: str, level: str = "INFO"):
        line = f"[{now_iso()}] [{level}] {msg}"
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
            "started_at": now_iso(),
            "stopped_at": None,
            "stopped_reason": None,
            "consecutive_empty_polls": 0,
            "consecutive_failures": 0,
            "circuit_open_until": None,
            "last_error": None,
            "next_retry_after": None,
            "lock": {},
        }

    def save_manifest(self, manifest: dict):
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

    def save_checkpoint(self, last_start_time):
        tmp = self.checkpoint_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"last_start_time": last_start_time, "updated_at": now_iso()}, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.checkpoint_path)

    def load_dedup_keys(self) -> set:
        keys = set()
        if not self.fragments_path.exists():
            return keys
        try:
            with open(self.fragments_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    keys.add((obj.get("_segment_id"), obj.get("_version", 1)))
        except Exception:
            return keys
        return keys

    def append_fragments(self, frags: list, version: int = 1) -> int:
        dedup = self.load_dedup_keys()
        new_count = 0
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
        return new_count

    def rebuild_transcript(self) -> int:
        if not self.fragments_path.exists():
            return 0
        seen = {}
        with open(self.fragments_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                seg_id = obj.get("_segment_id")
                ver = obj.get("_version", 1)
                if seg_id not in seen or ver > seen[seg_id].get("_version", 1):
                    seen[seg_id] = obj

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

    def should_stop(self) -> bool:
        return self.stop_path.exists()

    def clear_stop(self):
        try:
            self.stop_path.unlink(missing_ok=True)
        except Exception:
            pass


@dataclass
class LockHandle:
    acquired: bool
    reason: str = ""
    lock_path: str = ""


def acquire_lock(store: MeetingStore, ttl_seconds: int = LOCK_TTL_SECONDS) -> LockHandle:
    now = now_epoch()
    payload = {
        "gateway": store.gateway,
        "meeting_chat_id": store.meeting_chat_id,
        "lock_key": f"{store.gateway}:{store.meeting_chat_id}",
        "pid": os.getpid(),
        "acquired_at": now,
        "expires_at": now + ttl_seconds,
    }

    for _ in range(2):
        try:
            fd = os.open(store.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            return LockHandle(True, lock_path=str(store.lock_path))
        except FileExistsError:
            try:
                existing = json.loads(store.lock_path.read_text(encoding="utf-8"))
                exp = int(existing.get("expires_at") or 0)
            except Exception:
                exp = 0
            if exp <= now:
                try:
                    store.lock_path.unlink(missing_ok=True)
                except Exception:
                    pass
                continue
            return LockHandle(False, reason="locked", lock_path=str(store.lock_path))
    return LockHandle(False, reason="locked", lock_path=str(store.lock_path))


def release_lock(store: MeetingStore):
    try:
        store.lock_path.unlink(missing_ok=True)
    except Exception:
        pass


def fetch_incremental(meeting_chat_id: str, last_start_time=None) -> list:
    body = {"meetingChatId": meeting_chat_id}
    if last_start_time is not None:
        body["lastStartTime"] = last_start_time
    result = _call_api(URL_INCREMENTAL, body)
    if result.get("resultCode") != 1:
        raise RuntimeError(f"splitRecordListV2 失败: {result.get('resultMsg')}")
    return [f for f in (result.get("data") or []) if f.get("startTime") is not None]


def fetch_full(meeting_chat_id: str) -> list:
    result = _call_api(URL_FULL, {"meetingChatId": meeting_chat_id})
    if result.get("resultCode") != 1:
        raise RuntimeError(f"splitRecordList 失败: {result.get('resultMsg')}")
    return [f for f in (result.get("data") or []) if f.get("startTime") is not None]


def detect_runtime_status(meeting_chat_id: str) -> str:
    result = _call_api(URL_SECOND_STT, {"meetingChatId": meeting_chat_id}, timeout=30)
    if result.get("resultCode") != 1:
        return "unknown"
    state = result.get("state")
    if state == 2:
        return "completed"
    if state == 0:
        return "active"
    return "non_active"


def pull_completed(store: MeetingStore, manifest: dict):
    all_frags = fetch_full(store.meeting_chat_id)
    store.append_fragments(all_frags, version=1)
    if all_frags:
        store.save_checkpoint(max(f.get("startTime") or 0 for f in all_frags))
    total = store.rebuild_transcript()
    manifest["status"] = "completed"
    manifest["is_fully_pulled"] = True
    manifest["fragment_count"] = total
    manifest["stopped_at"] = now_iso()
    manifest["stopped_reason"] = "meeting_completed"


def classify_error(exc: Exception):
    if isinstance(exc, ApiCallError):
        code = exc.http_status
        if code == 429 or (code and code >= 500):
            return "retryable", f"http_{code}"
        if code and 400 <= code < 500:
            return "terminal", f"http_{code}"
        return "retryable", "network"
    msg = str(exc).lower()
    if "timeout" in msg or "connection" in msg or "network" in msg:
        return "retryable", "network"
    return "retryable", "unknown"


def run_pull_once(meeting_chat_id: str, gateway=None, name="", force=False, lock_ttl=LOCK_TTL_SECONDS) -> dict:
    store = MeetingStore(meeting_chat_id=meeting_chat_id, gateway=gateway)
    manifest = store.load_manifest()
    if name and not manifest.get("name"):
        manifest["name"] = name
    if not manifest.get("started_at"):
        manifest["started_at"] = now_iso()

    lock = acquire_lock(store, ttl_seconds=lock_ttl)
    if not lock.acquired:
        manifest["lock"] = {
            "lock_key": f"{store.gateway}:{store.meeting_chat_id}",
            "acquired": False,
            "lock_path": lock.lock_path,
            "ttl_seconds": lock_ttl,
            "checked_at": now_iso(),
        }
        store.save_manifest(manifest)
        return {
            "status": "skipped",
            "skipped_locked": True,
            "meeting_chat_id": meeting_chat_id,
            "materials_dir": str(store.dir),
        }

    try:
        manifest["lock"] = {
            "lock_key": f"{store.gateway}:{store.meeting_chat_id}",
            "acquired": True,
            "lock_path": lock.lock_path,
            "ttl_seconds": lock_ttl,
            "checked_at": now_iso(),
        }

        if manifest.get("is_fully_pulled") and not force:
            store.save_manifest(manifest)
            return {"status": "skipped", "reason": "already_fully_pulled", "meeting_chat_id": meeting_chat_id}

        circuit_until = manifest.get("circuit_open_until")
        if circuit_until:
            try:
                if datetime.fromisoformat(circuit_until).timestamp() > time.time():
                    store.save_manifest(manifest)
                    return {
                        "status": "skipped",
                        "skipped_circuit_open": True,
                        "meeting_chat_id": meeting_chat_id,
                        "circuit_open_until": circuit_until,
                    }
            except Exception:
                pass

        try:
            started_at_epoch = int(datetime.fromisoformat(manifest["started_at"]).timestamp())
        except Exception:
            started_at_epoch = now_epoch()
            manifest["started_at"] = now_iso()
        if now_epoch() - started_at_epoch > MAX_LIFETIME_SECONDS:
            manifest["status"] = "stopped"
            manifest["stopped_at"] = now_iso()
            manifest["stopped_reason"] = "ttl_exceeded_10h"
            store.save_manifest(manifest)
            return {"status": "stopped", "stopped_reason": manifest["stopped_reason"], "meeting_chat_id": meeting_chat_id}

        if store.should_stop():
            store.clear_stop()
            manifest["status"] = "stopped"
            manifest["stopped_at"] = now_iso()
            manifest["stopped_reason"] = "manual_stop_flag"
            store.save_manifest(manifest)
            return {"status": "stopped", "stopped_reason": manifest["stopped_reason"], "meeting_chat_id": meeting_chat_id}

        checkpoint = store.load_checkpoint()
        last_start_time = checkpoint.get("last_start_time")

        try:
            frags = fetch_incremental(meeting_chat_id, last_start_time)
            runtime_status = detect_runtime_status(meeting_chat_id)
            manifest["consecutive_failures"] = 0
            manifest["circuit_open_until"] = None
            manifest["next_retry_after"] = None
            manifest["last_error"] = None
        except Exception as e:
            err_kind, err_code = classify_error(e)
            manifest["consecutive_failures"] = int(manifest.get("consecutive_failures") or 0) + 1
            manifest["last_error"] = f"{err_kind}:{err_code}:{e}"
            if err_kind == "terminal":
                manifest["status"] = "failed"
                manifest["stopped_at"] = now_iso()
                manifest["stopped_reason"] = f"terminal_fail_{err_code}"
                store.save_manifest(manifest)
                return {"status": "failed", "terminal": True, "reason": manifest["stopped_reason"], "meeting_chat_id": meeting_chat_id}

            idx = min(manifest["consecutive_failures"] - 1, len(BACKOFF_STEPS) - 1)
            backoff = BACKOFF_STEPS[idx] + random.randint(0, 5)
            manifest["next_retry_after"] = datetime.fromtimestamp(time.time() + backoff).astimezone().isoformat(timespec="seconds")
            if manifest["consecutive_failures"] >= 5:
                manifest["circuit_open_until"] = datetime.fromtimestamp(time.time() + CIRCUIT_OPEN_SECONDS).astimezone().isoformat(timespec="seconds")
            store.save_manifest(manifest)
            return {
                "status": "skipped",
                "retryable_error": True,
                "meeting_chat_id": meeting_chat_id,
                "backoff_seconds": backoff,
                "circuit_open_until": manifest.get("circuit_open_until"),
            }

        new_count = store.append_fragments(frags, version=1)
        if frags:
            store.save_checkpoint(max(f.get("startTime") or 0 for f in frags))

        total = store.rebuild_transcript()
        manifest["fragment_count"] = total

        if runtime_status == "completed":
            pull_completed(store, manifest)
            store.save_manifest(manifest)
            return {
                "status": "completed",
                "meeting_chat_id": meeting_chat_id,
                "new_fragments": new_count,
                "fragment_count": manifest.get("fragment_count", 0),
                "checkpoint": store.load_checkpoint().get("last_start_time"),
            }

        if new_count == 0 and runtime_status != "active":
            manifest["consecutive_empty_polls"] = int(manifest.get("consecutive_empty_polls") or 0) + 1
        else:
            manifest["consecutive_empty_polls"] = 0

        if int(manifest.get("consecutive_empty_polls") or 0) >= 3 and runtime_status != "active":
            manifest["status"] = "stopped"
            manifest["stopped_at"] = now_iso()
            manifest["stopped_reason"] = "empty_polls_non_active_3"
            store.save_manifest(manifest)
            return {
                "status": "stopped",
                "meeting_chat_id": meeting_chat_id,
                "stopped_reason": manifest["stopped_reason"],
                "new_fragments": new_count,
                "fragment_count": manifest.get("fragment_count", 0),
            }

        manifest["status"] = "ongoing" if runtime_status in ("active", "non_active", "unknown") else runtime_status
        manifest["is_fully_pulled"] = False
        store.save_manifest(manifest)

        return {
            "status": "ok",
            "meeting_chat_id": meeting_chat_id,
            "new_fragments": new_count,
            "fragment_count": manifest.get("fragment_count", 0),
            "runtime_status": runtime_status,
            "checkpoint": store.load_checkpoint().get("last_start_time"),
            "materials_dir": str(store.dir),
        }
    finally:
        release_lock(store)
