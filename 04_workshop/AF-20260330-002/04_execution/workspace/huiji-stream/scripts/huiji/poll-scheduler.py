#!/usr/bin/env python3
"""
huiji-stream / poll-scheduler.py

自适应轮询调度器：管理一场或多场会议的实时轮询。

策略：
  - 会议活跃（近 10 秒有新片段） → interval = 2s
  - 会议静默（30 秒无新片段）    → interval = 8s
  - 断连检测（连续 3 次失败）   → 指数退避（2→4→8→16→30s，上限）
  - 断连恢复：全量校验（对比本地 vs 远端片段数）
  - 限制：同时监控 ≤ 3 场会议

Phase B 变更：
  - _do_poll() 检测到 summary_trigger=True 时，调用 EventProcessor.trigger_summary()
    触发 Summarizer.generate()，产出并持久化结构化摘要卡片
  - get_current_text() 返回值中附带 latest_summary（来自 Summarizer 的最新摘要卡片）

使用方式（供 OpenClaw Skill 命令调用）：
  from poll_scheduler import PollScheduler
  scheduler = PollScheduler(storage_dir="/path/to/.cache/huiji")

  # 启动监控
  scheduler.start_stream("huijiXgMt_xxx")

  # 停止监控
  scheduler.stop_stream("huijiXgMt_xxx")

  # 查看状态
  status = scheduler.stream_status()
  print(json.dumps(status, ensure_ascii=False))

  # 查看当前全文 + 最新摘要
  text_view = scheduler.get_current_text("huijiXgMt_xxx")
  # {ok, full_text, latest_summary, fragment_count, ...}
"""

import json
import time
import threading
import sys
import sqlite3
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DB_NAME = "huiji_stream.db"

# 轮询间隔
INTERVAL_ACTIVE = 2.0   # 近 10 秒有新片段
INTERVAL_SILENT = 8.0    # 30 秒无新片段

# 断连恢复
MAX_CONSECUTIVE_FAILS = 3
BACKOFF_STEPS = [2, 4, 8, 16, 30]  # 秒，上限 30s
BACKOFF_MAX = 30

# 最大并发监控数
MAX_STREAMS = 3

# 全局轮询线程
_poll_thread: Optional[threading.Thread] = None
_poll_running = False


# ---------------------------------------------------------------------------
# 轮询调度器
# ---------------------------------------------------------------------------
class PollScheduler:
    """
    管理多场会议的实时轮询任务。

    内存中维护 {meeting_chat_id: _StreamState}。
    在一个后台线程中顺序轮询所有活跃会议。
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(self.storage_dir / DB_NAME)
        self._streams: dict[str, "_StreamState"] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # 公共 API（供 Skill 命令调用）
    # ------------------------------------------------------------------
    def start_stream(self, meeting_chat_id: str, name: str = "") -> dict:
        """
        启动一场会议的实时监控。
        返回 {"ok": True} 或 {"ok": False, "error": "..."}
        """
        with self._lock:
            if len(self._streams) >= MAX_STREAMS:
                return {
                    "ok": False,
                    "error": f"已达同时监控上限（{MAX_STREAMS}场），请先停止一场"
                }
            if meeting_chat_id in self._streams:
                return {"ok": True, "already_running": True}

            from stream_sync import StreamSync
            from event_processor import EventProcessor

            syncer = StreamSync(self.storage_dir)
            processor = EventProcessor(self.storage_dir)

            state = _StreamState(
                meeting_chat_id=meeting_chat_id,
                name=name,
                syncer=syncer,
                processor=processor,
            )
            self._streams[meeting_chat_id] = state
            self._ensure_thread()
            return {"ok": True}

    def stop_stream(self, meeting_chat_id: str) -> dict:
        """停止一场会议的监控。"""
        with self._lock:
            if meeting_chat_id in self._streams:
                del self._streams[meeting_chat_id]
            return {"ok": True}

    def stream_status(self) -> dict:
        """返回所有监控流的状态。"""
        with self._lock:
            result = {
                "active_count": len(self._streams),
                "max_streams": MAX_STREAMS,
                "streams": [],
            }
            for mid, state in self._streams.items():
                result["streams"].append({
                    "meeting_chat_id": mid,
                    "name": state.name,
                    "status": state.status,
                    "interval": state.interval,
                    "last_sync_at": state.last_sync_at,
                    "fragment_count": state.fragment_count,
                    "consecutive_fails": state.consecutive_fails,
                    "backoff_level": state.backoff_level,
                })
            return result

    def get_current_text(self, meeting_chat_id: str) -> dict:
        """
        返回当前实时全文（供展示层调用）。

        Phase B：附带 latest_summary（最新摘要卡片，若无则为 None）。
        返回格式：
          {
            "ok": True,
            "meeting_chat_id": "...",
            "name": "...",
            "full_text": "...",
            "latest_summary": {摘要卡片} 或 None,
            "fragment_count": 42,
            "status": "active",
            "last_sync_at": 1716349200000
          }
        """
        with self._lock:
            if meeting_chat_id not in self._streams:
                return {"ok": False, "error": "未在监控中"}
            state = self._streams[meeting_chat_id]

        view = state.processor.get_current_view(meeting_chat_id)
        # Phase B：从 EventProcessor 获取最新摘要（从 SQLite 读取）
        latest_summary = state.processor.get_latest_summary(meeting_chat_id)

        return {
            "ok": True,
            "meeting_chat_id": meeting_chat_id,
            "name": state.name,
            "full_text": view["full_text"],
            "latest_summary": latest_summary,
            "fragment_count": state.fragment_count,
            "status": state.status,
            "last_sync_at": state.last_sync_at,
        }

    def poll_once(self, meeting_chat_id: str) -> dict:
        """
        对一场会议执行一次轮询（同步调用，返回结果）。
        供外部测试或手动触发使用。
        """
        with self._lock:
            if meeting_chat_id not in self._streams:
                return {"ok": False, "error": "未在监控中"}
            state = self._streams[meeting_chat_id]
        return self._do_poll(state)

    # ------------------------------------------------------------------
    # 后台轮询线程
    # ------------------------------------------------------------------
    def _ensure_thread(self) -> None:
        global _poll_thread, _poll_running
        if _poll_running:
            return
        _poll_running = True
        _poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        _poll_thread.start()

    def _poll_loop(self) -> None:
        global _poll_running
        while _poll_running:
            # 复制一份 stream 列表，释放锁
            with self._lock:
                streams_snapshot = list(self._streams.values())
            if not streams_snapshot:
                time.sleep(1)
                continue

            for state in streams_snapshot:
                try:
                    self._do_poll(state)
                except Exception as e:
                    state.record_fail(str(e))

                # 根据状态决定下次间隔
                interval = state.interval
                time.sleep(interval)

    def _do_poll(self, state: "_StreamState") -> dict:
        """
        执行一次同步轮询。

        Phase B：若 view["summary_trigger"]=True，
          调用 EventProcessor.trigger_summary() → Summarizer.generate()
          确保摘要被生成并持久化（即使 process_events 内部已触发，此处作双重保险）。
        """
        try:
            from stream_sync import StreamSync

            syncer = StreamSync(self.storage_dir)

            # 断连恢复后先做全量校验
            if state.was_recovering:
                local_count, remote_count = syncer.full_rollback_recovery(state.meeting_chat_id)
                state.was_recovering = False  # 重置标志

            events = syncer.sync(state.meeting_chat_id)
            view = state.processor.process_events(state.meeting_chat_id)

            # Phase B：摘要触发串联
            # process_events() 内部已调用 Summarizer，此处通过 trigger_summary()
            # 做显式串联，确保摘要写入 SQLite（防止内部静默失败时遗漏）
            summary_data = None
            if view.get("summary_trigger"):
                try:
                    summary_data = state.processor.trigger_summary(state.meeting_chat_id)
                except Exception:
                    pass

            # 更新流状态
            state.record_success(
                fragment_count=len(view.get("fragments", [])),
                has_new=len(view.get("new_fragments", [])) > 0,
            )

            return {
                "ok": True,
                "meeting_chat_id": state.meeting_chat_id,
                "new_fragments": len(view.get("new_fragments", [])),
                "updated_fragments": len(view.get("updated_fragments", [])),
                "summary_trigger": view.get("summary_trigger", False),
                "fragment_count": len(view.get("fragments", [])),
                "full_text_preview": view.get("full_text", "")[:200],
                "latest_summary": summary_data.get("summary_card") if summary_data else view.get("latest_summary"),
            }

        except Exception as e:
            state.record_fail(str(e))
            return {
                "ok": False,
                "meeting_chat_id": state.meeting_chat_id,
                "error": str(e),
            }


# ---------------------------------------------------------------------------
# _StreamState — 单场会议的轮询状态
# ---------------------------------------------------------------------------
class _StreamState:
    """
    维护单场会议的轮询上下文：
      - interval：当前轮询间隔
      - status：active / recovering / failed
      - consecutive_fails：连续失败次数
      - backoff_level：退避级别（0=正常）
      - last_sync_at：上次成功同步时间
      - last_new_fragment_at：上次有新片段的时间
      - fragment_count：当前片段数
      - was_recovering：上次是否处于恢复状态（用于触发全量校验）
    """

    def __init__(
        self,
        meeting_chat_id: str,
        name: str,
        syncer,
        processor,
    ):
        self.meeting_chat_id = meeting_chat_id
        self.name = name
        self.syncer = syncer
        self.processor = processor
        self.interval = INTERVAL_ACTIVE
        self.status = "active"
        self.consecutive_fails = 0
        self.backoff_level = 0
        self.last_sync_at: Optional[int] = None
        self.last_new_fragment_at: Optional[int] = None
        self.fragment_count = 0
        self.was_recovering: bool = False  # 上次是否处于恢复状态

    def record_success(
        self,
        fragment_count: int,
        has_new: bool,
    ) -> None:
        """成功同步后更新状态。"""
        now_ms = int(time.time() * 1000)
        # Phase A W-04：恢复成功后设置 was_recovering 标志（已在 _do_poll 调用前完成）
        # 此处检查是否刚从恢复状态成功，更新 was_recovering（供下次 _do_poll 用）
        if self.consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            self.was_recovering = True
        else:
            self.was_recovering = False
        self.consecutive_fails = 0
        self.backoff_level = 0
        self.last_sync_at = now_ms
        self.status = "active"
        self.fragment_count = fragment_count
        if has_new:
            self.last_new_fragment_at = now_ms
            self.interval = INTERVAL_ACTIVE
        else:
            self._maybe_increase_interval(now_ms)

    def record_fail(self, error: str) -> None:
        """失败后进入断连恢复流程。"""
        self.consecutive_fails += 1
        if self.consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            self._apply_backoff()

    def _maybe_increase_interval(self, now_ms: int) -> None:
        """近 30 秒无新片段，切换到静默间隔。"""
        if self.last_new_fragment_at is None:
            self.interval = INTERVAL_ACTIVE
            return
        silent_ms = 30_000
        if now_ms - self.last_new_fragment_at > silent_ms:
            self.interval = INTERVAL_SILENT

    def _apply_backoff(self) -> None:
        """指数退避，恢复成功后自动降回正常间隔。"""
        self.status = "recovering"
        self.backoff_level = min(self.backoff_level + 1, len(BACKOFF_STEPS) - 1)
        self.interval = BACKOFF_STEPS[self.backoff_level]
