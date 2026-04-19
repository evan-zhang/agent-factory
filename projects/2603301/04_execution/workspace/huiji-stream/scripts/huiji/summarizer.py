#!/usr/bin/env python3
"""
huiji-stream / summarizer.py — 轻量滚动摘要引擎

职责：
  - 每 45s 接收当前全文（片段列表），产出结构化摘要卡片
  - 不依赖外部 LLM API（避免网络故障影响主流程）
  - 摘要持久化到 SQLite summaries 表（meeting_chat_id PRIMARY KEY，覆盖更新）

摘要卡片格式：
  {
    "topics": ["议题1", "议题2", ...],       # 关键词/主题提取（正则+频率）
    "decisions": ["决策1", ...],             # 匹配决策句式
    "action_items": [                        # 待办提取（人名 + 动词 + 事项）
      {"text": "...", "assignee": "..."},
      ...
    ],
    "summary_text": "...",                   # 最近 10 条片段拼接，不超过 500 字
    "fragment_count": 42,
    "generated_at": 1716349200000
  }

使用方式（供 event-processor.py / poll-scheduler.py 调用）：
  from summarizer import Summarizer
  summarizer = Summarizer(db_path="/path/to/huiji_stream.db")
  card = summarizer.generate(meeting_chat_id, fragments)
"""

import json
import re
import sqlite3
import time
from typing import Optional

# ---------------------------------------------------------------------------
# 停用词表（中文高频功能词，不作为主题词）
# ---------------------------------------------------------------------------
_STOP_WORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
    "都", "一", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "那", "但",
    "这个", "那个", "什么", "怎么", "为什么", "可以", "因为",
    "所以", "如果", "还是", "然后", "已经", "现在", "一下", "一些",
    "非常", "比较", "应该", "需要", "能够", "进行", "通过", "方面",
    "问题", "情况", "工作", "时候", "时间", "地方", "知道", "觉得",
    "认为", "感觉", "希望", "表示", "我们", "他们", "它们", "大家",
    "他", "她", "它", "他的", "她的", "们", "来", "没", "把",
    "被", "与", "及", "对", "从", "以", "于", "其", "将",
    "之", "而", "又", "或", "且", "各", "该", "此", "其他",
    "今天", "明天", "昨天", "一个", "两个", "三个", "很多", "一样",
    "主要", "基本", "相关", "具体", "不是", "还有", "只是", "就是",
    "这样", "那样", "然而", "但是", "不过", "可能", "应当", "必须",
    "已校正",
}

# ---------------------------------------------------------------------------
# 决策句匹配模式
# ---------------------------------------------------------------------------
_DECISION_PATTERNS = [
    re.compile(r"([^。！？\n]{4,80}(?:决定|确定|同意|通过|批准|同意|达成)[^。！？\n]{0,40})"),
    re.compile(r"([^。！？\n]{0,20}(?:大家|会议|我们)(?:一致|决定|同意|确认)[^。！？\n]{4,60})"),
    re.compile(r"([^。！？\n]{0,20}(?:已|将|下一步)[^。！？\n]{4,60})"),
]

# ---------------------------------------------------------------------------
# 行动项匹配模式（"[人名](负责|跟进|提交|完成|处理)[事项]"）
# ---------------------------------------------------------------------------
_ACTION_PATTERN = re.compile(
    r"([^，。！？\n、]{2,8})"          # 人名/组织（2~8字）
    r"(?:来?)"                         # 可选"来"
    r"(负责|跟进|提交|完成|处理|负责人|推进|落实|确认|安排)"  # 动词
    r"([^，。！？\n]{2,30})"           # 事项（2~30字）
)


# ---------------------------------------------------------------------------
# Summarizer 主类
# ---------------------------------------------------------------------------
class Summarizer:
    """
    轻量滚动摘要引擎。

    不依赖外部 LLM API，基于正则+词频实现：
      - 主题提取：关键词频率排序
      - 决策识别：正则匹配决策句式
      - 行动项抽取：正则匹配"人名+动词+事项"
      - 摘要文本：最近 10 条片段拼接，截断至 500 字
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------
    def generate(self, meeting_chat_id: str, fragments: list[dict]) -> dict:
        """
        对当前片段列表产出结构化摘要卡片，并持久化到 SQLite。

        Args:
            meeting_chat_id: 会议 ID
            fragments: 当前所有片段（来自 MeetingState.get_fragments()）
                       每项格式: {startTime, realTime, text, corrected, original_text?}

        Returns:
            摘要卡片 dict，格式见模块文档
        """
        now_ms = int(time.time() * 1000)

        # 拼接全文（用于主题/决策/行动项提取）
        full_text = self._build_full_text(fragments)

        # 产出各结构化字段
        topics = self._extract_topics(full_text)
        decisions = self._extract_decisions(full_text)
        action_items = self._extract_action_items(full_text)
        summary_text = self._build_summary_text(fragments)

        card = {
            "topics": topics,
            "decisions": decisions,
            "action_items": action_items,
            "summary_text": summary_text,
            "fragment_count": len(fragments),
            "generated_at": now_ms,
        }

        # 持久化
        self._save(meeting_chat_id, card)

        return card

    def get_latest(self, meeting_chat_id: str) -> Optional[dict]:
        """
        从 SQLite 读取最新摘要卡片。
        若无记录，返回 None。
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM summaries WHERE meeting_chat_id=?",
                (meeting_chat_id,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_card(row)

    # ------------------------------------------------------------------
    # 内部：摘要生成
    # ------------------------------------------------------------------
    def _build_full_text(self, fragments: list[dict]) -> str:
        """拼接全部片段文本（用于提取）。"""
        return "".join(f.get("text", "") for f in fragments)

    def _extract_topics(self, text: str, top_n: int = 8) -> list[str]:
        """
        基于词频提取主题词（排除停用词）。
        切词方式：正则提取 2~8 字中文词组。
        """
        # 提取 2~8 字的中文词组（CJK 统一表意文字范围）
        words = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
        freq: dict[str, int] = {}
        for w in words:
            if w not in _STOP_WORDS:
                freq[w] = freq.get(w, 0) + 1

        # 按频率排序，过滤掉只出现 1 次的词
        sorted_words = sorted(freq.items(), key=lambda x: -x[1])
        return [w for w, cnt in sorted_words if cnt >= 2][:top_n]

    def _extract_decisions(self, text: str, max_items: int = 8) -> list[str]:
        """
        基于正则识别决策句（决定/确定/同意/通过/批准 等关键词）。
        """
        found = []
        seen: set[str] = set()

        for pat in _DECISION_PATTERNS:
            for m in pat.finditer(text):
                sentence = m.group(1).strip()
                # 去重（精确匹配），限制长度
                normalized = sentence[:60]
                if normalized not in seen and len(sentence) >= 6:
                    seen.add(normalized)
                    found.append(sentence[:80])
                if len(found) >= max_items:
                    break
            if len(found) >= max_items:
                break

        return found

    def _extract_action_items(self, text: str, max_items: int = 10) -> list[dict]:
        """
        基于正则提取待办项。
        匹配模式：([^，。]{2,8})(负责|跟进|提交|完成|处理)([^，。]{2,20})
        """
        items = []
        seen: set[str] = set()

        for m in _ACTION_PATTERN.finditer(text):
            assignee = m.group(1).strip()
            verb = m.group(2).strip()
            task = m.group(3).strip()
            full_text = m.group(0).strip()

            # 去重
            key = f"{assignee}|{task[:20]}"
            if key in seen:
                continue
            seen.add(key)

            items.append({
                "text": full_text,
                "assignee": assignee,
                "verb": verb,
                "task": task,
            })

            if len(items) >= max_items:
                break

        return items

    def _build_summary_text(self, fragments: list[dict], max_frags: int = 10, max_chars: int = 500) -> str:
        """
        取最近 max_frags 条片段拼接，总长度不超过 max_chars 字。
        用于快速呈现"最近在讨论什么"。
        """
        if not fragments:
            return ""

        # 取最近 N 条（按 startTime 排序后取尾部）
        recent = fragments[-max_frags:]
        parts = []
        total = 0
        for frag in recent:
            text = frag.get("text", "")
            if not text:
                continue
            remaining = max_chars - total
            if remaining <= 0:
                break
            chunk = text[:remaining]
            parts.append(chunk)
            total += len(chunk)

        return "".join(parts)

    # ------------------------------------------------------------------
    # 内部：SQLite 持久化
    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        """确保 summaries 表存在（补充 decisions 列，兼容 Phase A 的旧表）。"""
        with sqlite3.connect(self.db_path) as conn:
            # 先确保表存在（与 stream-sync.py 保持一致）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    meeting_chat_id TEXT PRIMARY KEY,
                    summary_text TEXT,
                    action_items TEXT,
                    topics TEXT,
                    updated_at INTEGER
                )
            """)
            # 尝试添加 decisions 列（若已存在会报 OperationalError，忽略即可）
            try:
                conn.execute("ALTER TABLE summaries ADD COLUMN decisions TEXT")
            except Exception:
                pass
            conn.commit()

    def _save(self, meeting_chat_id: str, card: dict) -> None:
        """将摘要卡片写入 SQLite，覆盖更新（UPSERT）。"""
        now_ms = card["generated_at"]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO summaries
                    (meeting_chat_id, summary_text, action_items, topics, decisions, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(meeting_chat_id)
                DO UPDATE SET
                    summary_text=excluded.summary_text,
                    action_items=excluded.action_items,
                    topics=excluded.topics,
                    decisions=excluded.decisions,
                    updated_at=excluded.updated_at
                """,
                (
                    meeting_chat_id,
                    card.get("summary_text", ""),
                    json.dumps(card.get("action_items", []), ensure_ascii=False),
                    json.dumps(card.get("topics", []), ensure_ascii=False),
                    json.dumps(card.get("decisions", []), ensure_ascii=False),
                    now_ms,
                ),
            )
            conn.commit()

    def _row_to_card(self, row) -> dict:
        """将 SQLite row 反序列化为摘要卡片 dict。"""
        action_items = []
        topics = []
        decisions = []
        try:
            action_items = json.loads(row["action_items"] or "[]")
        except Exception:
            pass
        try:
            topics = json.loads(row["topics"] or "[]")
        except Exception:
            pass
        try:
            # decisions 列可能在旧数据库中不存在
            decisions = json.loads(row["decisions"] or "[]") if "decisions" in row.keys() else []
        except Exception:
            pass
        return {
            "topics": topics,
            "decisions": decisions,
            "action_items": action_items,
            "summary_text": row["summary_text"] or "",
            "fragment_count": 0,  # DB 中未存储，返回占位值
            "generated_at": row["updated_at"] or 0,
        }
