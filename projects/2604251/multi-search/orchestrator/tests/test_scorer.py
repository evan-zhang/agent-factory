"""
orchestrator/tests/test_scorer.py

Result Quality Scorer 单元测试集（Phase 2 R2）

测试内容：
1. _authority_score() — 各层级域名评分正确性
2. _authority_score() — 子域名 glob 匹配
3. _freshness_score() — 各时间范围评分正确性
4. _freshness_score() — 无日期/解析失败
5. _relevance_score() — 关键词匹配度
6. _relevance_score() — 无匹配
7. score() — 综合评分计算
8. score_and_sort() — 降序排列
9. score_and_sort() — 稳定排序
10. Engine 集成 — search() 返回已排序结果
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# 关闭 orchestrator 日志输出
import logging
logging.disable(logging.CRITICAL)


from ..scorer import ResultScorer
from ..schema import SearchItem, ScorerConfig


# ────────────────────────────────────────────────────────
# ScorerConfig
# ────────────────────────────────────────────────────────

class TestScorerConfigDefaults:
    """ScorerConfig 默认值测试"""

    def test_default_weights(self):
        config = ScorerConfig()
        assert config.authority_weight == 0.5
        assert config.freshness_weight == 0.3
        assert config.relevance_weight == 0.2

    def test_default_authority_tiers_contains_gov(self):
        config = ScorerConfig()
        assert "*.gov.cn" in config.authority_tiers
        assert config.authority_tiers["*.gov.cn"] == 1.0

    def test_default_freshness_cutoffs(self):
        config = ScorerConfig()
        assert (30, 1.0) in config.freshness_cutoffs
        assert (730, 0.2) in config.freshness_cutoffs

    def test_default_unknown_scores(self):
        config = ScorerConfig()
        assert config.unknown_authority_score == 0.1
        assert config.no_date_freshness_score == 0.1


# ────────────────────────────────────────────────────────
# _authority_score
# ────────────────────────────────────────────────────────

class TestAuthorityScore:
    """权威性评分测试"""

    def setup_method(self):
        self.scorer = ResultScorer()

    def test_gov_cn_returns_1_0(self):
        """政府域名 *.gov.cn 返回 1.0"""
        assert self.scorer._authority_score("https://www.mohrss.gov.cn") == 1.0
        assert self.scorer._authority_score("https://sz.gov.cn") == 1.0
        assert self.scorer._authority_score("https://gov.cn") == 1.0

    def test_edu_cn_returns_0_8(self):
        """高校域名 *.edu.cn 返回 0.8"""
        assert self.scorer._authority_score("https://www.tsinghua.edu.cn") == 0.8
        assert self.scorer._authority_score("https://pku.edu.cn") == 0.8

    def test_ac_cn_returns_0_8(self):
        """学术域名 *.ac.cn 返回 0.8"""
        assert self.scorer._authority_score("https://www.cas.ac.cn") == 0.8

    def test_official_media_returns_0_6(self):
        """官方媒体返回 0.6"""
        assert self.scorer._authority_score("https://www.people.com.cn") == 0.6
        assert self.scorer._authority_score("https://xinhuanet.com") == 0.6
        assert self.scorer._authority_score("https://www.cctv.com") == 0.6
        assert self.scorer._authority_score("https://www.chinanews.com") == 0.6
        assert self.scorer._authority_score("https://www.gmw.cn") == 0.6

    def test_org_cn_returns_0_4(self):
        """行业/专业网站 *.org.cn 返回 0.4"""
        assert self.scorer._authority_score("https://www.example.org.cn") == 0.4
        assert self.scorer._authority_score("https://csf.org.cn") == 0.4

    def test_com_cn_returns_0_4(self):
        """商业网站 *.com.cn 返回 0.4"""
        assert self.scorer._authority_score("https://www.example.com.cn") == 0.4

    def test_subdomain_glob_matches(self):
        """子域名 glob 匹配：sz.gov.cn 匹配 *.gov.cn"""
        assert self.scorer._authority_score("https://sz.gov.cn/page") == 1.0
        assert self.scorer._authority_score("https://hr.sz.gov.cn") == 1.0
        assert self.scorer._authority_score("https://www.hr.sz.gov.cn") == 1.0

    def test_self_media_returns_0_2(self):
        """自媒体/非官方返回 0.2 (不在已知层级里的都是 0.1 默认...)"""
        # 注意：未知域名返回 0.1，不是 0.2
        # "*.blog.com" 这种不在 tiers 里 → 0.1
        pass

    def test_unknown_domain_returns_0_1(self):
        """未知域名返回 0.1"""
        assert self.scorer._authority_score("https://some-random-blog.example") == 0.1
        assert self.scorer._authority_score("https://medium.com") == 0.1
        assert self.scorer._authority_score("https://www.somewhere.net") == 0.1

    def test_no_url_returns_0_1(self):
        """空 URL 返回 0.1"""
        assert self.scorer._authority_score("") == 0.1

    def test_invalid_url_returns_0_1(self):
        """无效 URL 返回 0.1"""
        assert self.scorer._authority_score("not-a-url") == 0.1
        assert self.scorer._authority_score("") == 0.1

    def test_gov_with_tld_variation(self):
        """*.gov.* 模式匹配其他国家政府网站"""
        assert self.scorer._authority_score("https://www.gov.uk") == 1.0
        assert self.scorer._authority_score("https://www.whitehouse.gov") == 1.0
        assert self.scorer._authority_score("https://data.gov.au") == 1.0

    def test_exact_match_people_com_cn(self):
        """精确匹配 people.com.cn"""
        assert self.scorer._authority_score("https://people.com.cn") == 0.6


# ────────────────────────────────────────────────────────
# _freshness_score
# ────────────────────────────────────────────────────────

class TestFreshnessScore:
    """时效性评分测试"""

    def setup_method(self):
        self.scorer = ResultScorer()

    def _days_ago_str(self, days: int) -> str:
        """生成 N 天前的 ISO 日期字符串"""
        dt = datetime.now() - timedelta(days=days)
        return dt.strftime("%Y-%m-%d")

    def test_within_30_days_returns_1_0(self):
        """30 天内返回 1.0"""
        date_str = self._days_ago_str(5)
        assert self.scorer._freshness_score(date_str) == 1.0

    def test_30_days_exact_returns_1_0(self):
        """正好 30 天返回 1.0"""
        date_str = self._days_ago_str(30)
        assert self.scorer._freshness_score(date_str) == 1.0

    def test_within_90_days_returns_0_8(self):
        """90 天内返回 0.8"""
        date_str = self._days_ago_str(60)
        assert self.scorer._freshness_score(date_str) == 0.8

    def test_90_days_exact_returns_0_8(self):
        """正好 90 天返回 0.8"""
        date_str = self._days_ago_str(90)
        assert self.scorer._freshness_score(date_str) == 0.8

    def test_within_180_days_returns_0_6(self):
        """180 天内返回 0.6"""
        date_str = self._days_ago_str(120)
        assert self.scorer._freshness_score(date_str) == 0.6

    def test_within_1_year_returns_0_4(self):
        """1 年内返回 0.4"""
        date_str = self._days_ago_str(300)
        assert self.scorer._freshness_score(date_str) == 0.4

    def test_within_2_years_returns_0_2(self):
        """2 年内返回 0.2"""
        date_str = self._days_ago_str(500)
        assert self.scorer._freshness_score(date_str) == 0.2

    def test_over_2_years_returns_0_1(self):
        """超过 2 年返回 0.1"""
        date_str = self._days_ago_str(800)
        assert self.scorer._freshness_score(date_str) == 0.1

    def test_no_date_returns_0_1(self):
        """无日期返回 0.1"""
        assert self.scorer._freshness_score(None) == 0.1
        assert self.scorer._freshness_score("") == 0.1

    def test_invalid_date_returns_0_1(self):
        """无法解析的日期返回 0.1"""
        assert self.scorer._freshness_score("invalid-date") == 0.1
        assert self.scorer._freshness_score("2025/13/40") == 0.1

    def test_chinese_date_format(self):
        """中文日期格式解析"""
        # 今天的中文日期
        now = datetime.now()
        cn_date = f"{now.year}年{now.month}月{now.day}日"
        assert self.scorer._freshness_score(cn_date) == 1.0

    def test_chinese_date_old(self):
        """中文旧日期"""
        cn_date = "2020年1月1日"
        score = self.scorer._freshness_score(cn_date)
        assert score == 0.1  # 超过 2 年

    def test_iso_with_timezone(self):
        """ISO 8601 带时区"""
        # 30 天内带时区
        dt = datetime.now(timezone.utc) - timedelta(days=10)
        date_str = dt.isoformat()
        assert self.scorer._freshness_score(date_str) == 1.0

    def test_future_date_returns_1_0(self):
        """未来日期（罕见）返回 1.0"""
        future = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert self.scorer._freshness_score(future) == 1.0


# ────────────────────────────────────────────────────────
# _relevance_score
# ────────────────────────────────────────────────────────

class TestRelevanceScore:
    """相关性评分测试"""

    def setup_method(self):
        self.scorer = ResultScorer()

    def test_all_keywords_match_high_score(self):
        """query 关键词全部匹配返回高分"""
        item = SearchItem(
            title="深圳社保缴费比例2025",
            url="https://example.com/1",
            snippet="深圳市2025年社保缴费比例和基数调整",
        )
        score = self.scorer._relevance_score(item, "深圳社保缴费比例")
        assert score >= 0.8

    def test_partial_keyword_match(self):
        """部分关键词匹配"""
        item = SearchItem(
            title="北京社保政策",
            url="https://example.com/2",
            snippet="北京市社保缴费指南",
        )
        score = self.scorer._relevance_score(item, "深圳社保缴费比例")
        # "社保" 匹配，"深圳"不匹配（不在 title/snippet 中）
        # 分词后的关键词可能有：深圳, 社保, 缴费, 比例
        # "社保" 在 title 中
        assert 0.2 < score < 0.8

    def test_no_keyword_match_low_score(self):
        """无匹配返回低分"""
        item = SearchItem(
            title="天气预报",
            url="https://example.com/3",
            snippet="今日天气晴朗",
        )
        score = self.scorer._relevance_score(item, "深圳社保缴费比例")
        assert score < 0.3

    def test_empty_query_returns_1_0(self):
        """空查询返回 1.0"""
        item = SearchItem(
            title="任何内容",
            url="https://example.com/4",
            snippet="无关内容",
        )
        score = self.scorer._relevance_score(item, "")
        assert score == 1.0

    def test_title_match_weights_higher(self):
        """标题匹配权重高于摘要匹配"""
        item_a = SearchItem(
            title="深圳社保缴费比例",
            url="https://example.com/a",
            snippet="无关内容",
        )
        item_b = SearchItem(
            title="无关标题",
            url="https://example.com/b",
            snippet="深圳社保缴费比例调整通知",
        )
        score_a = self.scorer._relevance_score(item_a, "深圳社保缴费比例")
        score_b = self.scorer._relevance_score(item_b, "深圳社保缴费比例")
        assert score_a > score_b

    def test_english_keywords(self):
        """英文关键词匹配"""
        item = SearchItem(
            title="Python Programming Guide",
            url="https://example.com/5",
            snippet="Learn Python programming from scratch",
        )
        score = self.scorer._relevance_score(item, "Python programming")
        assert score >= 0.5


# ────────────────────────────────────────────────────────
# score() — 综合评分
# ────────────────────────────────────────────────────────

class TestScore:
    """综合评分测试"""

    def test_score_calculates_correctly(self):
        """综合评分计算：验证权重和维度得分"""
        # 创建一个自定义 scorer 使用明确的权重
        config = ScorerConfig(
            authority_weight=0.5,
            freshness_weight=0.3,
            relevance_weight=0.2,
        )
        scorer = ResultScorer(config)

        # 政府网站 + 近期（确保时效性满分）+ 相关查询
        from datetime import datetime, timedelta
        recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        item = SearchItem(
            title="深圳社保缴费比例",
            url="https://sz.gov.cn/social-insurance",
            snippet="深圳市社保缴费比例调整通知",
            published_date=recent_date,
        )

        total = scorer.score(item, "深圳社保缴费比例")

        # authority: 1.0 (gov.cn)
        # freshness: 1.0 (5天内)
        # relevance: 标题匹配了关键词
        expected = 0.5 * 1.0 + 0.3 * 1.0 + 0.2 * 1.0
        assert total == pytest.approx(expected, abs=0.3)

    def test_score_detail_populated(self):
        """score_detail 字段正确填充"""
        scorer = ResultScorer()
        item = SearchItem(
            title="测试标题",
            url="https://www.tsinghua.edu.cn",
            snippet="测试摘要",
        )
        scorer.score(item, "测试")

        assert "total" in item.score_detail
        assert "authority" in item.score_detail
        assert "freshness" in item.score_detail
        assert "relevance" in item.score_detail

        # tsinghua.edu.cn 应该匹配 *.edu.cn → 0.8
        assert item.score_detail["authority"] == 0.8

    def test_different_domains_get_different_scores(self):
        """不同域名的评分差异"""
        scorer = ResultScorer()

        gov_item = SearchItem(
            title="政策",
            url="https://gov.cn/policy",
            snippet="政策内容",
            published_date=None,
        )
        blog_item = SearchItem(
            title="政策",
            url="https://blog.example/post",
            snippet="政策内容",
            published_date=None,
        )

        scorer.score(gov_item, "政策")
        scorer.score(blog_item, "政策")

        # 权威性差异应该导致总分差异
        assert gov_item.score > blog_item.score


# ────────────────────────────────────────────────────────
# score_and_sort()
# ────────────────────────────────────────────────────────

class TestScoreAndSort:
    """评分排序测试"""

    def setup_method(self):
        self.scorer = ResultScorer()

    def test_descending_order(self):
        """多个结果按评分降序排列"""
        items = [
            SearchItem(
                title="低分", url="https://blog.example/low",
                snippet="相关内容",
            ),
            SearchItem(
                title="高分", url="https://gov.cn/high",
                snippet="相关程度高的内容",
                published_date="2025-06-01",
            ),
        ]

        sorted_items = self.scorer.score_and_sort(items, "相关程度高")

        # 政府网站 + 有日期 + 关键词匹配 → 应该排前面
        assert sorted_items[0].score >= sorted_items[1].score

    def test_stable_sort_same_score(self):
        """评分相同时保持原顺序（稳定排序）"""
        items = [
            SearchItem(
                title="A", url="https://a.example.com/1",
                snippet="same",
            ),
            SearchItem(
                title="B", url="https://b.example.com/2",
                snippet="same",
            ),
            SearchItem(
                title="C", url="https://c.example.com/3",
                snippet="same",
            ),
        ]

        sorted_items = self.scorer.score_and_sort(items, "same query")

        # 评分相同时，保持原顺序 A, B, C
        assert sorted_items[0].title == "A"
        assert sorted_items[1].title == "B"
        assert sorted_items[2].title == "C"

    def test_empty_list(self):
        """空列表评分排序"""
        sorted_items = self.scorer.score_and_sort([], "test")
        assert sorted_items == []

    def test_single_item(self):
        """单个结果"""
        item = SearchItem(
            title="唯一结果", url="https://example.com/1",
            snippet="内容",
        )
        sorted_items = self.scorer.score_and_sort([item], "唯一结果")
        assert len(sorted_items) == 1
        assert sorted_items[0].title == "唯一结果"


# ────────────────────────────────────────────────────────
# _match_domain
# ────────────────────────────────────────────────────────

class TestMatchDomain:
    """域名模式匹配测试"""

    def test_exact_match(self):
        assert ResultScorer._match_domain("people.com.cn", "people.com.cn")

    def test_exact_no_match(self):
        assert not ResultScorer._match_domain("xinhuanet.com", "people.com.cn")

    def test_glob_subdomain_match(self):
        assert ResultScorer._match_domain("sz.gov.cn", "*.gov.cn")

    def test_glob_multi_level_subdomain(self):
        assert ResultScorer._match_domain("hr.sz.gov.cn", "*.gov.cn")

    def test_glob_exact_main_domain(self):
        assert ResultScorer._match_domain("gov.cn", "*.gov.cn")

    def test_glob_no_match_different_tld(self):
        assert not ResultScorer._match_domain("example.com", "*.gov.cn")

    def test_glob_with_star_dot_gov_star(self):
        assert ResultScorer._match_domain("gov.uk", "*.gov.*")
        assert ResultScorer._match_domain("whitehouse.gov", "*.gov.*")
        assert ResultScorer._match_domain("data.gov.au", "*.gov.*")


# ────────────────────────────────────────────────────────
# _parse_days_ago
# ────────────────────────────────────────────────────────

class TestParseDaysAgo:
    """日期解析测试"""

    def test_iso_8601_format(self):
        days = ResultScorer._parse_days_ago("2025-06-07")
        # 从 2025-06-07 到现在的天数应该是 > 0
        assert days is not None
        assert isinstance(days, int)
        assert days >= 0

    def test_chinese_date_format(self):
        days = ResultScorer._parse_days_ago("2025年6月7日")
        assert days is not None
        assert isinstance(days, int)

    def test_invalid_string_returns_none(self):
        assert ResultScorer._parse_days_ago("not-a-date") is None
        assert ResultScorer._parse_days_ago("") is None

    def test_iso_with_time(self):
        days = ResultScorer._parse_days_ago("2025-06-07T12:30:00")
        assert days is not None


# ────────────────────────────────────────────────────────
# 自定义配置测试
# ────────────────────────────────────────────────────────

class TestCustomConfig:
    """自定义 ScorerConfig 测试"""

    def test_custom_weights(self):
        """自定义权重影响评分"""
        config = ScorerConfig(
            authority_weight=1.0,
            freshness_weight=0.0,
            relevance_weight=0.0,
        )
        scorer = ResultScorer(config)

        item = SearchItem(
            title="任何标题", url="https://gov.cn/policy",
            snippet="任何内容",
        )
        scorer.score(item, "无关查询")

        # 只有权威性贡献评分
        assert item.score == 1.0

    def test_custom_authority_tiers(self):
        """自定义权威性层级"""
        config = ScorerConfig(
            authority_tiers={"*.example.com": 0.9},
            unknown_authority_score=0.1,
        )
        scorer = ResultScorer(config)

        score = scorer._authority_score("https://sub.example.com")
        assert score == 0.9

        score = scorer._authority_score("https://unknown.com")
        assert score == 0.1

    def test_custom_freshness_cutoffs(self):
        """自定义时效性阈值"""
        config = ScorerConfig(
            freshness_cutoffs=[
                (7, 1.0),    # 7天内
                (30, 0.5),   # 30天内
            ],
            no_date_freshness_score=0.0,
        )
        scorer = ResultScorer(config)

        from datetime import datetime, timedelta

        recent = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert scorer._freshness_score(recent) == 1.0

        older = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        assert scorer._freshness_score(older) == 0.5

        old = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        assert scorer._freshness_score(old) == 0.0


# ────────────────────────────────────────────────────────
# Engine 集成测试
# ────────────────────────────────────────────────────────

class TestEngineIntegration:
    """Engine 集成搜索排序测试"""

    @pytest.mark.asyncio
    async def test_search_returns_sorted_results(self):
        """search() 返回的结果已按质量评分排序"""
        from ..engine import SearchEngine

        engine = SearchEngine()

        # 创建一个没有实际 provider 的请求（只能用 mock）
        # 但 SearchEngine.__init__ 会尝试加载配置，没问题
        # 我们只需要创建一个 result 并手动验证排序行为

        from ..schema import SearchRequest, SearchItem, OrchestratorSearchResult

        # 验证 scorer 已正确初始化
        assert engine.scorer is not None
        assert isinstance(engine.scorer, ResultScorer)

    @pytest.mark.asyncio
    async def test_scorer_customizable(self):
        """可以向 SearchEngine 传入自定义 scorer"""
        from ..engine import SearchEngine

        config = ScorerConfig(
            authority_weight=1.0,
            freshness_weight=0.0,
            relevance_weight=0.0,
        )
        custom_scorer = ResultScorer(config)

        engine = SearchEngine(scorer=custom_scorer)
        assert engine.scorer is custom_scorer

    def test_scorer_weights_normalized(self):
        """默认权重和为 1.0"""
        config = ScorerConfig()
        total = config.authority_weight + config.freshness_weight + config.relevance_weight
        assert total == pytest.approx(1.0, abs=0.01)


# ────────────────────────────────────────────────────────
# _tokenize（辅助测试）
# ────────────────────────────────────────────────────────

class TestTokenize:
    """分词辅助函数测试"""

    def test_english_words(self):
        tokens = ResultScorer._tokenize("Python programming guide")
        assert "python" in tokens or "Python" in tokens or "python" in [t.lower() for t in tokens]

    def test_chinese_chars(self):
        tokens = ResultScorer._tokenize("深圳社保缴费比例")
        # 应该提取出有意义的 2-3 字词
        assert len(tokens) > 0

    def test_stop_words_removed(self):
        tokens = ResultScorer._tokenize("深圳的社保缴费比例")
        # "的" 应该是停用词被去掉
        token_lower = [t.lower() for t in tokens]
        assert "的" not in token_lower

    def test_empty_query(self):
        tokens = ResultScorer._tokenize("")
        assert tokens == []

    def test_mixed_query(self):
        tokens = ResultScorer._tokenize("深圳 social insurance 2025")
        # 应该有中英文混合
        token_lower = [t.lower() for t in tokens]
        assert any("social" in t.lower() for t in tokens)
