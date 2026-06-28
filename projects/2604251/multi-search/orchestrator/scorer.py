"""
orchestrator/scorer.py

Result Quality Scorer 模块（Phase 2 R2）。

本模块负责：
- 对搜索结果按三个维度（权威性/时效性/相关性）加权评分
- 替代按 provider 顺序排列，改为质量降序排列
- 支持通过 ScorerConfig 调整权重和评分策略
"""

import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import logging

from .schema import SearchItem, ScorerConfig

logger = logging.getLogger("orchestrator.scorer")

# 中文停用词列表
_STOP_WORDS = frozenset({
    "的", "了", "是", "在", "和", "与", "及", "或", "也", "还",
    "有", "就", "都", "而", "且", "但", "但", "被", "把", "对",
    "从", "到", "以", "为", "上", "下", "中", "之", "其", "它",
    "他", "她", "们", "这", "那", "哪", "什么", "如何", "怎么",
    "一个", "这个", "那个", "这些", "那些", "每个", "一些",
    "不", "没", "很", "太", "更", "最", "非常",
    "将", "要", "会", "可以", "能", "应该", "必须", "需要",
    "我", "你", "您", "我们", "你们", "他们",
    "请", "让", "给", "向", "把", "被", "叫", "让",
    "吧", "吗", "呢", "啊", "哦", "嗯", "嘛",
    "已经", "正在", "着", "了", "过",
})


class ResultScorer:
    """
    搜索结果质量评分器。

    对 SearchItem 按三个维度加权评分：
    1. 权威性 (authority) — 基于 URL 域名评估来源可信度
    2. 时效性 (freshness) — 基于 published_date 评估信息新鲜度
    3. 相关性 (relevance) — 基于关键词覆盖度评估与查询的匹配度

    评分后按综合得分降序排列，替代按 provider 顺序排列。

    Usage:
        scorer = ResultScorer()
        scored_items = scorer.score_and_sort(items, query)
    """

    def __init__(self, config: Optional[ScorerConfig] = None):
        """
        初始化评分器。

        Args:
            config: 评分配置（如果为 None，使用默认配置）
        """
        self.config = config or ScorerConfig()
        logger.debug(
            f"ResultScorer 初始化完成 "
            f"weights=authority:{self.config.authority_weight} "
            f"freshness:{self.config.freshness_weight} "
            f"relevance:{self.config.relevance_weight}"
        )

    def score(self, item: SearchItem, query: str) -> float:
        """
        对单个结果项计算综合评分。

        同时更新 item.score_detail 记录各维度得分。

        Args:
            item: 搜索结果项
            query: 原始搜索查询

        Returns:
            综合评分（0.0 - 1.0）
        """
        auth_score = self._authority_score(item.url)
        fresh_score = self._freshness_score(item.published_date)
        relev_score = self._relevance_score(item, query)

        total = (
            self.config.authority_weight * auth_score
            + self.config.freshness_weight * fresh_score
            + self.config.relevance_weight * relev_score
        )

        # 记录评分明细
        item.score_detail = {
            "total": round(total, 4),
            "authority": round(auth_score, 4),
            "freshness": round(fresh_score, 4),
            "relevance": round(relev_score, 4),
        }

        # 同时更新主 score 字段
        item.score = total

        logger.debug(
            f"评分完成 url={item.url[:60]} "
            f"total={total:.4f} "
            f"authority={auth_score:.4f} "
            f"freshness={fresh_score:.4f} "
            f"relevance={relev_score:.4f}"
        )

        return total

    def score_and_sort(
        self,
        items: List[SearchItem],
        query: str,
    ) -> List[SearchItem]:
        """
        对所有结果评分后降序排列。

        排序是稳定的：评分相同时保持原顺序。

        Args:
            items: 搜索结果项列表
            query: 原始搜索查询

        Returns:
            按评分降序排列的结果列表
        """
        for item in items:
            self.score(item, query)

        # 稳定排序（评分相同时保持原顺序）
        sorted_items = sorted(items, key=lambda x: x.score, reverse=True)

        top_info = f"top_score={sorted_items[0].score:.4f}" if sorted_items else "top_score=N/A"
        logger.debug(
            f"评分排序完成 items={len(items)} "
            f"{top_info}"
        )

        return sorted_items

    # ────────────────────────────────────────────────────────
    # 权威性评分
    # ────────────────────────────────────────────────────────

    def _authority_score(self, url: str) -> float:
        """
        基于域名计算权威性评分。

        评分规则：
        - tier_1 (1.0): 政府官网 *.gov.cn, *.gov.*
        - tier_2 (0.8): 学术/高校 *.edu.cn, *.ac.cn
        - tier_3 (0.6): 官方媒体 people.com.cn, xinhuanet.com 等
        - tier_4 (0.4): 行业/专业网站 *.org.cn, *.com.cn（非新闻）
        - tier_5 (0.2): 自媒体/非官方 — 其余所有
        - unknown (0.1): 无法解析域名的

        Args:
            url: 搜索结果 URL

        Returns:
            权威性评分（0.0 - 1.0）
        """
        if not url or not isinstance(url, str):
            return self.config.unknown_authority_score

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return self.config.unknown_authority_score
        except Exception:
            return self.config.unknown_authority_score

        # 转换为小写做匹配
        hostname = hostname.lower()

        for pattern, score in self.config.authority_tiers.items():
            if self._match_domain(hostname, pattern):
                return score

        return self.config.unknown_authority_score

    @staticmethod
    def _match_domain(hostname: str, pattern: str) -> bool:
        """
        域名模式匹配。

        支持三种模式：
        - 精确+子域名匹配: "people.com.cn" → 精确匹配域名或任意子域名
        - glob 匹配: "*.gov.cn" → 匹配任意子域名 + 主域名
        - glob + 通配 TLD: "*.gov.*" → 匹配任意子域名 + "gov" + 任意 TLD

        Args:
            hostname: 域名（如 "sz.gov.cn", "www.people.com.cn"）
            pattern: 模式（如 "*.gov.cn", "people.com.cn"）

        Returns:
            是否匹配
        """
        if not hostname:
            return False

        hostname = hostname.lower()
        pattern = pattern.lower()

        if pattern.startswith("*."):
            suffix = pattern[2:]  # 去掉 "*."

            # 处理 *.gov.* 模式
            if suffix.endswith(".*"):
                # 中间部分（如 "gov"）必须作为一个域名级别出现
                middle = suffix[:-2]  # 去掉 ".*"
                parts = hostname.split(".")
                return middle in parts

            # 普通 glob 模式：匹配任意子域名 + 主域名
            # 主域名本身匹配（如 gov.cn 匹配 *.gov.cn）
            if hostname == suffix:
                return True
            # 子域名匹配（如 sz.gov.cn 匹配 *.gov.cn）
            if hostname.endswith("." + suffix):
                return True
            return False
        else:
            # 精确匹配或子域名匹配
            if hostname == pattern:
                return True
            # 子域名匹配（如 www.people.com.cn 匹配 people.com.cn）
            if hostname.endswith("." + pattern):
                return True
            return False

    # ────────────────────────────────────────────────────────
    # 时效性评分
    # ────────────────────────────────────────────────────────

    def _freshness_score(self, published_date: Optional[str]) -> float:
        """
        基于发布日期计算时效性评分。

        支持的日期格式：
        - ISO 8601: "2025-06-07"
        - 中文日期: "2025年6月7日"
        - 其他格式解析失败时返回 0.1

        评分阈值（可配置）：
        - 30 天内: 1.0
        - 90 天内: 0.8
        - 180 天内: 0.6
        - 1 年内: 0.4
        - 2 年内: 0.2
        - 超过 2 年或无日期: 0.1

        Args:
            published_date: 发布日期字符串

        Returns:
            时效性评分（0.0 - 1.0）
        """
        if not published_date:
            return self.config.no_date_freshness_score

        days_ago = self._parse_days_ago(published_date)
        if days_ago is None:
            return self.config.no_date_freshness_score

        for cutoff, score in self.config.freshness_cutoffs:
            if days_ago <= cutoff:
                return score

        return self.config.no_date_freshness_score

    @staticmethod
    def _parse_days_ago(date_str: str) -> Optional[int]:
        """
        解析日期字符串并计算距今的天数。

        支持的格式：
        - ISO 8601: "2025-06-07" 或 "2025-06-07T12:00:00"
        - 中文日期: "2025年6月7日"

        Args:
            date_str: 日期字符串

        Returns:
            距今的天数，解析失败返回 None
        """
        from datetime import datetime, timezone
        import re

        date_str = date_str.strip()

        # 尝试 ISO 8601（带时间部分）
        try:
            dt = datetime.fromisoformat(date_str)
            now = datetime.now(timezone.utc if dt.tzinfo else None)
            delta = now - dt
            # 处理未来日期（罕见但可能发生）
            if delta.days < 0:
                return 0
            return delta.days
        except (ValueError, TypeError):
            pass

        # 尝试中文日期格式 "2025年6月7日"
        cn_match = re.match(
            r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
            date_str,
        )
        if cn_match:
            year, month, day = int(cn_match.group(1)), int(cn_match.group(2)), int(cn_match.group(3))
            try:
                dt = datetime(year, month, day)
                now = datetime.now()
                delta = now - dt
                if delta.days < 0:
                    return 0
                return delta.days
            except (ValueError, TypeError):
                pass

        # 尝试 "YYYY-MM" 格式（只有年月）
        ym_match = re.match(r"(\d{4})[-/](\d{1,2})$", date_str)
        if ym_match:
            year, month = int(ym_match.group(1)), int(ym_match.group(2))
            try:
                from datetime import timedelta
                dt = datetime(year, month, 1)
                now = datetime.now()
                delta = now - dt
                if delta.days < 0:
                    return 0
                return delta.days
            except (ValueError, TypeError):
                pass

        # 解析失败
        logger.debug(f"日期解析失败 date_str='{date_str}'")
        return None

    # ────────────────────────────────────────────────────────
    # 相关性评分
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(query: str) -> List[str]:
        """
        对查询进行分词并去掉停用词。

        支持中英文混合查询。

        Args:
            query: 搜索查询字符串

        Returns:
            关键词列表（已去停用词）
        """
        if not query:
            return []

        # 英文分词：按空格/标点分割
        # 中文分词：按字符分割
        tokens = []
        # 提取英文单词
        en_tokens = re.findall(r"[a-zA-Z0-9]+(?:[._+#-][a-zA-Z0-9]+)*", query)
        tokens.extend(en_tokens)

        # 提取中文字符（去除停用词）
        cn_chars = re.findall(r"[\u4e00-\u9fff]", query)
        # 将连续的中文字符组成短语（2-4 字词）
        cn_text = "".join(cn_chars)

        # 简单分词：尝试 3-gram 和 2-gram，然后单字
        # 先处理 3 字词（如果有更好的分词库可以替换）
        # 这里使用简单的滑动窗口
        cn_tokens = set()
        # 2-gram
        for i in range(len(cn_text) - 1):
            token = cn_text[i:i + 2]
            if token not in _STOP_WORDS and len(token.strip()) == 2:
                cn_tokens.add(token)
        # 3-gram（覆盖更大的语义单元）
        for i in range(len(cn_text) - 2):
            token = cn_text[i:i + 3]
            if token not in _STOP_WORDS and len(token.strip()) == 3:
                cn_tokens.add(token)

        tokens.extend(cn_tokens)

        # 过滤停用词
        tokens = [t for t in tokens if t.lower() not in _STOP_WORDS and t.strip()]

        return tokens

    def _relevance_score(self, item: SearchItem, query: str) -> float:
        """
        基于关键词覆盖度计算相关性评分。

        计算方式：
        1. 对 query 分词（去掉停用词），得到关键词列表
        2. 检查每个关键词在 title 和 snippet 中是否出现
        3. title 匹配权重 1.0，snippet 匹配权重 0.5
        4. 最终评分 = clamp(match_ratio, 0, 1)

        Args:
            item: 搜索结果项
            query: 原始搜索查询

        Returns:
            相关性评分（0.0 - 1.0）
        """
        keywords = self._tokenize(query)
        if not keywords:
            return 1.0  # 空查询无法判断相关性，返回最高分

        title_lower = (item.title or "").lower()
        snippet_lower = (item.snippet or "").lower()

        title_matches = 0
        snippet_matches = 0

        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in title_lower:
                title_matches += 1
            elif kw_lower in snippet_lower:
                snippet_matches += 1

        total_possible = len(keywords)
        match_ratio = (title_matches + snippet_matches * 0.5) / total_possible

        return max(0.0, min(1.0, match_ratio))


__all__ = ["ResultScorer"]
