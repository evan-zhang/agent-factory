#!/usr/bin/env python3
"""
huiji-stream / event-processor.py

语义事件处理器：消费 events 表中未处理事件，驱动实时速记流和滚动摘要。

职责：
  - APPEND：追加新文本到 fullText
  - REPLACE：静默替换旧文本，标注"已校正"，保留 original_text
  - 每 45 秒触发滚动摘要（调用 Summarizer.generate()，写入 SQLite）

Phase B 变更：
  - 导入 Summarizer，process_events() 触发摘要时自动调用 Summarizer.generate()
  - get_fragments() 返回时对已校正片段附带 original_text 字段
  - _load_from_db() 去重强化：同一 segment_id 同时有 APPEND(v1)+REPLACE(v2) 时，
    fragment 文本使用 corrected_text，original_text 保留原始文本

使用方式（供 poll-scheduler.py 调用）：
  from event_processor import EventProcessor
  processor = EventProcessor(storage_dir="/path/to/.cache/huiji")
  result = processor.process_events(meeting_chat_id)
  # result = {full_text, new_fragments, updated_fragments, summary_trigger, latest_summary}
"""

import json
import time
import sqlite3
import re
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DB_NAME = "huiji_stream.db"
SUMMARY_INTERVAL_MS = 45_000  # 滚动摘要触发间隔（45 秒）


# ---------------------------------------------------------------------------
# 事件处理器
# ---------------------------------------------------------------------------
class EventProcessor:
    """
    消费 APPEND / REPLACE / DELETE 事件，维护实时文本和摘要。

    内存中维护一个 {meeting_chat_id: MeetingState} 的字典，
    由 poll-scheduler.py 在同一个进程内管理生命周期。
    """

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(self.storage_dir / DB_NAME)
        # 内存状态：meeting_chat_id -> MeetingState
        self._states: dict[str, "MeetingState"] = {}

    def process_events(self, meeting_chat_id: str) -> dict:
        """
        拉取未处理事件，应用到内存状态，返回更新后的状态摘要。

        Phase B：若 summary_trigger=True，自动调用 Summarizer.generate() 并持久化摘要。

        触发滚动摘要的条件：距上次摘要 >= SUMMARY_INTERVAL_MS
        """
        from stream_sync import StreamSync

        syncer = StreamSync(self.storage_dir)
        events = syncer.get_unprocessed_events(meeting_chat_id)
        if not events:
            return self._get_current_view(meeting_chat_id)

        state = self._get_state(meeting_chat_id)
        processed_ids = []
        new_fragments = []
        updated_fragments = []

        for evt in events:
            seg_id = evt["segment_id"]
            version = evt["version"]
            payload = json.loads(evt["payload"])
            event_type = evt["event_type"]

            if event_type == "APPEND":
                # 追加新片段到 fullText
                state.add_fragment(seg_id, payload)
                new_fragments.append(payload)
            elif event_type == "REPLACE":
                # 静默替换：标注"已校正"，保留 original_text
                state.replace_fragment(seg_id, payload)
                updated_fragments.append(payload)
            elif event_type == "DELETE":
                state.delete_fragment(seg_id)

            processed_ids.append(evt["id"])

        # 更新摘要触发计时
        state.update_summary_timer()

        # 标记已处理
        if processed_ids:
            syncer.mark_processed(processed_ids)

        should_summary = state.should_trigger_summary()
        latest_summary = None

        if should_summary:
            state.mark_summary_triggered()
            # Phase B：调用 Summarizer 产出并持久化摘要卡片
            latest_summary = self._run_summarizer(meeting_chat_id, state)

        return {
            "meeting_chat_id": meeting_chat_id,
            "full_text": state.get_full_text(),
            "fragments": state.get_fragments(),
            "new_fragments": new_fragments,
            "updated_fragments": updated_fragments,
            "summary_trigger": should_summary,
            "last_summary_triggered_at": state.last_summary_triggered_at,
            "latest_summary": latest_summary,
        }

    def get_current_view(self, meeting_chat_id: str) -> dict:
        """返回当前内存中的视图（不消费事件）。"""
        return self._get_current_view(meeting_chat_id)

    def trigger_summary(self, meeting_chat_id: str) -> dict:
        """
        手动触发滚动摘要更新（在 T+45s 窗口到期时由 poll-scheduler.py 调用）。
        返回摘要内容（包含 Summarizer 产出的结构化卡片）。
        """
        state = self._get_state(meeting_chat_id)
        state.mark_summary_triggered()
        # Phase B：调用 Summarizer
        summary_card = self._run_summarizer(meeting_chat_id, state)
        return {
            "meeting_chat_id": meeting_chat_id,
            "current_text": state.get_full_text(),
            "fragment_count": len(state.fragments),
            "topics": state.extract_topics(),
            "action_items": state.extract_action_items(),
            "summary_card": summary_card,
        }

    def get_latest_summary(self, meeting_chat_id: str) -> Optional[dict]:
        """从 SQLite 读取最新摘要卡片（供 get_current_text 附带返回）。"""
        try:
            from summarizer import Summarizer
            s = Summarizer(self.db_path)
            return s.get_latest(meeting_chat_id)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    def _run_summarizer(self, meeting_chat_id: str, state: "MeetingState") -> Optional[dict]:
        """调用 Summarizer.generate()，失败时返回 None（best-effort）。"""
        try:
            from summarizer import Summarizer
            s = Summarizer(self.db_path)
            return s.generate(meeting_chat_id, state.get_fragments())
        except Exception:
            return None

    def _get_current_view(self, meeting_chat_id: str) -> dict:
        state = self._get_state(meeting_chat_id)
        return {
            "meeting_chat_id": meeting_chat_id,
            "full_text": state.get_full_text(),
            "fragments": state.get_fragments(),
            "new_fragments": [],
            "updated_fragments": [],
            "summary_trigger": False,
            "last_summary_triggered_at": state.last_summary_triggered_at,
            "latest_summary": None,
        }

    def _get_state(self, meeting_chat_id: str) -> "MeetingState":
        if meeting_chat_id not in self._states:
            self._states[meeting_chat_id] = MeetingState(self.db_path, meeting_chat_id)
        return self._states[meeting_chat_id]


# ---------------------------------------------------------------------------
# MeetingState — 单场会议的内存状态
# ---------------------------------------------------------------------------
class MeetingState:
    """
    管理单场会议的实时文本状态：
      - fragments: {seg_id -> {startTime, text, realTime, corrected, original_text?}}
      - full_text: 按 startTime 排序拼接的全文
      - last_summary_triggered_at: 上次摘要触发时间

    Phase B 去重强化：
      _load_from_db() 恢复时，同一 segment_id 若同时有 APPEND(v1)+REPLACE(v2)，
      最终 fragment 只保留 REPLACE 的文本（corrected_text），original_text 保留原始文本。
    """

    def __init__(self, db_path: str, meeting_chat_id: str):
        self.db_path = db_path
        self.meeting_chat_id = meeting_chat_id
        self.fragments: dict[str, dict] = {}
        self.last_event_at: int = int(time.time() * 1000)
        self.last_summary_triggered_at: int = int(time.time() * 1000)
        self._load_from_db()

    def _load_from_db(self) -> None:
        """
        启动时从 DB 恢复已有片段（避免重启丢状态）。

        Phase B 去重强化：
          - 按 id ASC 顺序处理，确保 APPEND 先于 REPLACE
          - 同一 segment_id 有 APPEND(v1) 且后续有 REPLACE(v2)：
              fragment.text       = REPLACE 的 corrected_text
              fragment.corrected  = True
              fragment.original_text = APPEND 的原始 text
          - 只有 APPEND(v1)，无 REPLACE：
              fragment.text       = APPEND 的 text
              fragment.corrected  = False
              fragment.original_text = 不设置（None）
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT segment_id, payload, event_type, version FROM events
                WHERE meeting_chat_id=? AND event_type IN ('APPEND','REPLACE')
                ORDER BY id ASC
                """,
                (self.meeting_chat_id,),
            ).fetchall()

        for row in rows:
            frag = json.loads(row["payload"])
            seg_id = row["segment_id"]
            event_type = row["event_type"]

            if event_type == "APPEND":
                # 初始化（若不存在）；APPEND 应先出现（按 id ASC）
                if seg_id not in self.fragments:
                    self.fragments[seg_id] = {
                        **frag,
                        "corrected": False,
                        "original_text": None,
                        # 保留 APPEND 原始文本，供后续 REPLACE 使用
                        "_raw_text": frag.get("text"),
                    }
            elif event_type == "REPLACE":
                if seg_id in self.fragments:
                    original = self.fragments[seg_id].get("_raw_text") or self.fragments[seg_id].get("text")
                    self.fragments[seg_id]["corrected"] = True
                    self.fragments[seg_id]["text"] = frag.get("text")
                    self.fragments[seg_id]["original_text"] = original
                else:
                    # 极罕见：只有 REPLACE 无 APPEND（兼容性处理）
                    self.fragments[seg_id] = {
                        **frag,
                        "corrected": True,
                        "original_text": None,
                        "_raw_text": None,
                    }

        # 清理内部临时字段
        for seg_id in self.fragments:
            self.fragments[seg_id].pop("_raw_text", None)

    def add_fragment(self, seg_id: str, payload: dict) -> None:
        """追加新片段（APPEND 事件）。"""
        self.fragments[seg_id] = {
            **payload,
            "corrected": False,
            "original_text": None,
        }

    def replace_fragment(self, seg_id: str, payload: dict) -> None:
        """替换片段文本（REPLACE 事件），保留 original_text。"""
        if seg_id in self.fragments:
            original = self.fragments[seg_id].get("text")
            self.fragments[seg_id]["corrected"] = True
            self.fragments[seg_id]["text"] = payload.get("text")
            self.fragments[seg_id]["original_text"] = original
        else:
            # 兼容性：REPLACE 先于 APPEND 到达（理论上不该发生）
            self.fragments[seg_id] = {
                **payload,
                "corrected": True,
                "original_text": None,
            }

    def delete_fragment(self, seg_id: str) -> None:
        self.fragments.pop(seg_id, None)

    def get_fragments(self) -> list[dict]:
        """
        按 startTime 排序返回所有片段。

        Phase B：已校正片段附带 original_text 字段，用于展示"原文 → 校正后"对比。
        返回格式：
          {
            "startTime": 120034,
            "realTime": 1716349200000,
            "text": "校正后文本（若有）或原始文本",
            "corrected": True/False,
            "original_text": "原始文本（仅 corrected=True 时有值）"
          }
        """
        sorted_frags = sorted(
            self.fragments.values(),
            key=lambda f: f.get("startTime") or 0,
        )
        result = []
        for f in sorted_frags:
            corrected = f.get("corrected", False)
            entry = {
                "startTime": f.get("startTime"),
                "realTime": f.get("realTime"),
                "text": f.get("text") or "",
                "corrected": corrected,
            }
            # Phase B：仅 corrected=True 时附带 original_text
            if corrected:
                entry["original_text"] = f.get("original_text")
            result.append(entry)
        return result

    def get_full_text(self) -> str:
        """拼接全文，用于 LLM 摘要。"""
        parts = []
        for frag in self.get_fragments():
            text = frag["text"]
            if frag.get("corrected"):
                parts.append(f"[已校正] {text}")
            else:
                parts.append(text)
        return "\n".join(parts)

    def update_summary_timer(self) -> None:
        """记录有新事件的时间（不影响摘要触发计时）。"""
        self.last_event_at = int(time.time() * 1000)

    def should_trigger_summary(self) -> bool:
        """距上次触发摘要 >= 45s 就触发，与是否有新事件无关。"""
        elapsed = int(time.time() * 1000) - self.last_summary_triggered_at
        return elapsed >= SUMMARY_INTERVAL_MS

    def mark_summary_triggered(self) -> None:
        """触发摘要后调用，更新触发时间。"""
        self.last_summary_triggered_at = int(time.time() * 1000)

    def extract_topics(self) -> list[str]:
        """
        基于片段文本做简单话题提取（关键字统计）。
        后续可替换为 LLM 调用或 Summarizer 的主题提取。
        """
        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "这个", "那个", "什么", "怎么", "为什么", "可以",
        }
        all_text = self.get_full_text()
        words = re.findall(r"[\w\u4e00-\u9fff]{2,}", all_text)
        freq: dict[str, int] = {}
        for w in words:
            w = w.lower()
            if w not in stop_words:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: -x[1])
        return [w for w, _ in sorted_words[:10]]

    def extract_action_items(self) -> list[dict]:
        """
        基于片段文本做待办提取（正则匹配）。
        后续可替换为 Summarizer 的行动项提取。
        """
        action_patterns = [
            r"(.{2,10})负责(.+?)(?:。|$)",
            r"(.{2,10})做(.+?)(?:。|$)",
            r"(待办|TODO|行动项)[:：]?\s*(.+?)(?:。|$)",
        ]
        items = []
        text = self.get_full_text()
        for pat in action_patterns:
            for m in re.finditer(pat, text):
                items.append({"text": m.group(0), "raw": m.group(0)})
        return items[:10]
