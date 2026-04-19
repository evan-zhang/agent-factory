#!/usr/bin/env python3
"""
huiji-stream / stream-sync.py

核心同步引擎：增量拉取 + checkpoint 管理 + 事件生成

职责：
  - 增量拉取：调用 splitRecordListV2，用 lastStartTime 作游标
  - Checkpoint 管理：SQLite 存储（meetingChatId / lastSegmentId / lastStartTime）
  - 事件生成：APPEND / REPLACE / DELETE
  - 幂等键：meeting_id + segment_id + version
  - 鉴权：AppKey Header，环境变量 XG_BIZ_API_KEY
  - 生产域名：sg-al-ai-voice-assistant.mediportal.com.cn/api

使用方式（供 poll-scheduler.py 调用，非独立运行）：
  from stream_sync import StreamSync
  syncer = StreamSync(storage_dir="/path/to/.cache/huiji")
  events = syncer.sync(meeting_chat_id)
  # events = [{event_type, segment_id, version, payload, ...}, ...]
"""

import sys
import os
import json
import time
import sqlite3
import requests
import urllib3
from pathlib import Path
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
API_BASE = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api"
API_URL = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordListV2"
CHECK_SECOND_API = f"{API_BASE}/open-api/ai-huiji/meetingChat/checkSecondSttV2"
CHECK_FULL_API = f"{API_BASE}/open-api/ai-huiji/meetingChat/splitRecordList"
MAX_RETRIES = 3
RETRY_DELAY = 1
DB_NAME = "huiji_stream.db"


# ---------------------------------------------------------------------------
# 鉴权 Header
# ---------------------------------------------------------------------------
def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    app_key = os.environ.get("XG_BIZ_API_KEY")
    if not app_key:
        raise RuntimeError("请设置环境变量 XG_BIZ_API_KEY")
    headers["appKey"] = app_key
    return headers


# ---------------------------------------------------------------------------
# HTTP 调用
# ---------------------------------------------------------------------------
def _call_api(url: str, body: dict, timeout: int = 60) -> dict:
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


# ---------------------------------------------------------------------------
# SQLite 数据库初始化
# ---------------------------------------------------------------------------
def init_db(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                meeting_chat_id TEXT PRIMARY KEY,
                last_segment_id TEXT,
                last_start_time INTEGER,
                last_poll_at INTEGER,
                status TEXT DEFAULT 'active'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_chat_id TEXT,
                event_type TEXT,
                segment_id TEXT,
                version INTEGER DEFAULT 1,
                payload TEXT,
                processed INTEGER DEFAULT 0,
                created_at INTEGER,
                UNIQUE(meeting_chat_id, segment_id, version)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                meeting_chat_id TEXT PRIMARY KEY,
                summary_text TEXT,
                action_items TEXT,
                topics TEXT,
                updated_at INTEGER
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# StreamSync 主类
# ---------------------------------------------------------------------------
class StreamSync:
    """
    会议实时同步引擎。

    幂等键：meeting_chat_id + segment_id + version
    - APPEND：version=1，新分片
    - REPLACE：version=2，二次转写
    - DELETE：version=1，平台删除
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(self.storage_dir / DB_NAME)
        init_db(self.db_path)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------
    def sync(self, meeting_chat_id: str, force_full: bool = False) -> list[dict]:
        """
        对一场会议执行增量同步，返回新增事件列表。

        Args:
            meeting_chat_id: 慧记 ID
            force_full: True 时跳过 checkpoint，全量拉取（用于断连恢复）

        Returns:
            list of event dicts, each containing:
                event_type: APPEND | REPLACE | DELETE
                segment_id:  平台返回的 startTime 作为分片 ID
                version:     1（一转/DELETE）或 2（二次转写）
                payload:     JSON string of the fragment
                created_at:  Unix ms
        """
        checkpoint = self._load_checkpoint(meeting_chat_id)
        last_start_time = None if force_full else checkpoint.get("last_start_time")
        last_segment_id = checkpoint.get("last_segment_id")

        # --- 1. 增量拉取新片段（APPEND 事件） ---
        new_fragments = self._fetch_incremental(meeting_chat_id, last_start_time)

        # --- 2. 检查二次转写（REPLACE 事件）---
        replace_events = self._check_second_stt(meeting_chat_id)

        # --- 3. 生成事件，写入 DB ---
        events = []

        for frag in new_fragments:
            seg_id = str(frag.get("startTime"))
            # 幂等：跳过已存在的 version=1 记录
            if self._event_exists(meeting_chat_id, seg_id, version=1):
                continue
            event = self._make_event(
                meeting_chat_id,
                event_type="APPEND",
                segment_id=seg_id,
                version=1,
                payload=json.dumps(frag, ensure_ascii=False),
            )
            events.append(event)
            # 更新 checkpoint 游标
            last_start_time = frag.get("startTime")
            last_segment_id = seg_id

        for repl_frag in replace_events:
            seg_id = str(repl_frag.get("startTime"))
            # 幂等：version=2
            if self._event_exists(meeting_chat_id, seg_id, version=2):
                continue
            event = self._make_event(
                meeting_chat_id,
                event_type="REPLACE",
                segment_id=seg_id,
                version=2,
                payload=json.dumps(repl_frag, ensure_ascii=False),
            )
            events.append(event)

        # --- 4. 持久化 checkpoint ---
        if last_start_time is not None or last_segment_id is not None:
            self._save_checkpoint(
                meeting_chat_id,
                last_segment_id=last_segment_id,
                last_start_time=last_start_time,
            )

        return events

    def get_unprocessed_events(self, meeting_chat_id: str) -> list[dict]:
        """返回未处理的事件列表（供 event-processor.py 调用）。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM events
                WHERE meeting_chat_id=? AND processed=0
                ORDER BY created_at ASC, id ASC
                """,
                (meeting_chat_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_processed(self, event_ids: list[int]) -> None:
        """标记事件为已处理。"""
        if not event_ids:
            return
        placeholders = ",".join("?" * len(event_ids))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE events SET processed=1 WHERE id IN ({placeholders})",
                event_ids,
            )
            conn.commit()

    def full_rollback_recovery(self, meeting_chat_id: str) -> tuple[int, int]:
        """
        断连恢复：全量拉取，对比本地 vs 远端片段数。
        返回 (local_count, remote_count)。
        """
        remote_fragments = self._fetch_full(meeting_chat_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            local_rows = conn.execute(
                """
                SELECT segment_id, version FROM events
                WHERE meeting_chat_id=? AND event_type='APPEND'
                """,
                (meeting_chat_id,),
            ).fetchall()
        local_ids = {r["segment_id"] for r in local_rows}
        remote_ids = {str(f.get("startTime")) for f in remote_fragments}
        missing = remote_ids - local_ids
        # 补发缺失的 APPEND 事件
        for frag in remote_fragments:
            seg_id = str(frag.get("startTime"))
            if seg_id in missing:
                self._write_event(
                    meeting_chat_id,
                    "APPEND",
                    seg_id,
                    version=1,
                    payload=json.dumps(frag, ensure_ascii=False),
                )
        # 更新 checkpoint 到最大 startTime
        if remote_fragments:
            max_frag = max(remote_fragments, key=lambda f: f.get("startTime") or 0)
            self._save_checkpoint(
                meeting_chat_id,
                last_segment_id=str(max_frag.get("startTime")),
                last_start_time=max_frag.get("startTime"),
            )
        return len(local_ids), len(remote_ids)

    def get_meeting_status(self, meeting_chat_id: str) -> dict:
        """返回当前监控状态（供 stream-status 命令使用）。"""
        checkpoint = self._load_checkpoint(meeting_chat_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            unprocessed = conn.execute(
                "SELECT COUNT(*) as c FROM events WHERE meeting_chat_id=? AND processed=0",
                (meeting_chat_id,),
            ).fetchone()["c"]
            total = conn.execute(
                "SELECT COUNT(*) as c FROM events WHERE meeting_chat_id=?",
                (meeting_chat_id,),
            ).fetchone()["c"]
        return {
            "meeting_chat_id": meeting_chat_id,
            "status": checkpoint.get("status", "unknown"),
            "last_start_time": checkpoint.get("last_start_time"),
            "last_poll_at": checkpoint.get("last_poll_at"),
            "unprocessed_events": unprocessed,
            "total_events": total,
        }

    # ------------------------------------------------------------------
    # 私有方法
    # ------------------------------------------------------------------
    def _fetch_incremental(self, meeting_chat_id: str, last_start_time: Optional[int]) -> list[dict]:
        """调用 splitRecordListV2，增量拉取新分片。"""
        body = {"meetingChatId": meeting_chat_id}
        if last_start_time is not None:
            body["lastStartTime"] = last_start_time
        result = _call_api(API_URL, body)
        if result.get("resultCode") != 1:
            raise RuntimeError(f"splitRecordListV2 失败: {result.get('resultMsg')}")
        data = result.get("data") or []
        # 过滤掉 startTime 为 null 的分片
        return [f for f in data if f.get("startTime") is not None]

    def _fetch_full(self, meeting_chat_id: str) -> list[dict]:
        """调用 splitRecordList，全量拉取（用于断连恢复）。"""
        body = {"meetingChatId": meeting_chat_id}
        result = _call_api(CHECK_FULL_API, body)
        if result.get("resultCode") != 1:
            raise RuntimeError(f"splitRecordList（全量）失败: {result.get('resultMsg')}")
        return result.get("data") or []

    def _check_second_stt(self, meeting_chat_id: str) -> list[dict]:
        """
        调用 checkSecondSttV2，检测二次转写状态。
        state=2 时返回改写分片列表（REPLACE 事件来源）。
        """
        body = {"meetingChatId": meeting_chat_id}
        try:
            result = _call_api(CHECK_SECOND_API, body, timeout=30)
        except Exception:
            return []
        if result.get("resultCode") != 1:
            return []
        state = result.get("state")
        if state != 2:
            return []
        stt_list = result.get("sttPartList") or []
        return [f for f in stt_list if f.get("startTime") is not None]

    def _load_checkpoint(self, meeting_chat_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE meeting_chat_id=?",
                (meeting_chat_id,),
            ).fetchone()
        return dict(row) if row else {}

    def _save_checkpoint(
        self,
        meeting_chat_id: str,
        last_segment_id: Optional[str],
        last_start_time: Optional[int],
    ) -> None:
        now = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (meeting_chat_id, last_segment_id, last_start_time, last_poll_at, status)
                VALUES (?, ?, ?, ?, 'active')
                ON CONFLICT(meeting_chat_id)
                DO UPDATE SET
                    last_segment_id=excluded.last_segment_id,
                    last_start_time=excluded.last_start_time,
                    last_poll_at=excluded.last_poll_at
                """,
                (meeting_chat_id, last_segment_id, last_start_time, now),
            )
            conn.commit()

    def _event_exists(self, meeting_chat_id: str, segment_id: str, version: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT 1 FROM events WHERE meeting_chat_id=? AND segment_id=? AND version=?",
                (meeting_chat_id, segment_id, version),
            ).fetchone()
        return row is not None

    def _write_event(
        self,
        meeting_chat_id: str,
        event_type: str,
        segment_id: str,
        version: int,
        payload: str,
    ) -> None:
        now = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO events (meeting_chat_id, event_type, segment_id, version, payload, processed, created_at)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                    """,
                    (meeting_chat_id, event_type, segment_id, version, payload, now),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # 幂等键冲突，已存在
                pass

    def _make_event(
        self,
        meeting_chat_id: str,
        event_type: str,
        segment_id: str,
        version: int,
        payload: str,
    ) -> dict:
        now = int(time.time() * 1000)
        self._write_event(meeting_chat_id, event_type, segment_id, version, payload)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id FROM events WHERE meeting_chat_id=? AND segment_id=? AND version=?",
                (meeting_chat_id, segment_id, version),
            ).fetchone()
        event_id = row["id"] if row else None
        return {
            "event_type": event_type,
            "segment_id": segment_id,
            "version": version,
            "payload": payload,
            "created_at": now,
            "id": event_id,
        }
