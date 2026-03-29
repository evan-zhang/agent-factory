"""
scorer.py
=========
AI评分引擎。

提供两类评分能力：
1. 同级BP权重评分（peer scoring）：为N个同层BP分配100分权重
2. 分值池分配（pool distribution）：将上级BP分值池按贡献度分配给承接方

依赖：
- 环境变量 SCORER_MODEL（默认 gpt-4o）
- 环境变量 SCORER_API_KEY（OpenAI 兼容 API key）
- config/scoring_weights.yaml（由调用方加载后传入）
"""

import json
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SCORER_MODEL = os.environ.get("SCORER_MODEL", "gpt-4o")
SCORER_API_KEY = os.environ.get("SCORER_API_KEY", "")
SCORER_API_BASE = os.environ.get("SCORER_API_BASE", "https://api.openai.com/v1")


# ---------------------------------------------------------------------------
# LLM 调用基础设施
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, retry_count: int = 3) -> Optional[str]:
    """
    调用 LLM（OpenAI 兼容格式），返回模型文本响应。

    :param prompt: 完整的用户提示词
    :param retry_count: 失败重试次数
    :return: 模型返回的文本，失败时返回 None
    """
    url = f"{SCORER_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SCORER_API_KEY}",
    }
    payload = {
        "model": SCORER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,  # 低温度保证评分稳定性
    }

    for attempt in range(1, retry_count + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("LLM调用失败（第%d次/%d次）: %s", attempt, retry_count, e)
            if attempt < retry_count:
                time.sleep(2 ** attempt)  # 指数退避

    logger.error("LLM调用全部失败，已达最大重试次数 %d", retry_count)
    return None


def _parse_json_from_response(text: str) -> Optional[dict]:
    """
    从 LLM 返回文本中提取 JSON 块。

    LLM 可能在 JSON 前后包含 markdown 代码块标记，需剥离后解析。

    :param text: LLM 原始返回文本
    :return: 解析后的 dict，失败时返回 None
    """
    # 剥离 markdown 代码块
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # 去掉首行（```json 或 ```）和末行（```）
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        stripped = inner.strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        logger.error("JSON解析失败: %s\n原文: %s", e, text[:500])
        return None


# ---------------------------------------------------------------------------
# 格式化辅助函数
# ---------------------------------------------------------------------------

def _format_bp_for_prompt(bp: dict, index: int) -> str:
    """
    将单个 BP 详情格式化为 Prompt 中的文本块。

    :param bp: BP 详情字典（含 bpId, objective, keyResults, measures）
    :param index: 序号（从1开始）
    :return: 格式化文本
    """
    bp_id = bp.get("bpId", f"BP-{index}")
    objective = bp.get("objective", "（无目标描述）")

    krs = bp.get("keyResults", [])
    kr_text = "\n".join(
        f"  - KR{i+1}: {kr.get('description', '')}（目标：{kr.get('target', '无量化目标')}）"
        for i, kr in enumerate(krs)
    ) or "  （无KR）"

    measures = bp.get("measures", [])
    measure_text = "\n".join(
        f"  - 举措{i+1}: {m.get('description', '')}（承接方：{', '.join(d.get('name', '') for d in m.get('taskDepts', []) if d.get('role') == 'undertaker') or '无'}）"
        for i, m in enumerate(measures)
    ) or "  （无举措）"

    return (
        f"### BP {index}（ID: {bp_id}）\n"
        f"**目标**: {objective}\n"
        f"**关键成果（KR）**:\n{kr_text}\n"
        f"**核心举措**:\n{measure_text}"
    )


def _format_undertaker_for_prompt(undertaker_bp: dict, index: int) -> str:
    """
    将承接方BP格式化为 Prompt 文本块。

    :param undertaker_bp: 承接方的 BP 详情字典
    :param index: 序号
    :return: 格式化文本
    """
    return _format_bp_for_prompt(undertaker_bp, index)


# ---------------------------------------------------------------------------
# 同级 BP 权重评分
# ---------------------------------------------------------------------------

def score_peer_bps(
    org_name: str,
    period_name: str,
    bp_list: list[dict],
    parent_bp: Optional[dict],
    weights: dict,
    retry_count: int = 3,
) -> Optional[dict]:
    """
    对同一组织下的 N 个同级 BP 进行相对权重评分，总分 = 100。

    :param org_name: 组织名称
    :param period_name: BP 周期名称
    :param bp_list: 同级 BP 详情列表（每项含 bpId, objective, keyResults, measures）
    :param parent_bp: 上级 BP 信息（可为 None）
    :param weights: peer_scoring 权重字典，如 {strategic_alignment: 0.4, ...}
    :param retry_count: LLM 重试次数
    :return: LLM 返回的评分结果 dict，或 None（失败）
    """
    n = len(bp_list)
    if n == 0:
        return None

    # 构造上级BP文本
    if parent_bp:
        parent_text = (
            f"- 目标: {parent_bp.get('objective', '无')}\n"
            f"- KR: {'; '.join(kr.get('description', '') for kr in parent_bp.get('keyResults', []))}\n"
            f"- 举措: {'; '.join(m.get('description', '') for m in parent_bp.get('measures', []))}"
        )
    else:
        parent_text = "（无上级BP，当前为顶层组织BP）"

    # 格式化 BP 列表
    formatted_bps = "\n\n".join(_format_bp_for_prompt(bp, i + 1) for i, bp in enumerate(bp_list))

    # 构造 Prompt（完整复现 GRV 3.2 中的示例，填充权重变量）
    prompt = f"""你是一个企业BP（Business Plan）价值评估专家，熟悉OKR/BP管理体系。

## 任务
以下是「{org_name}」在「{period_name}」的 {n} 个BP目标，请评估它们的相对重要性，为每个BP分配分值。

## 评分规则
1. 总分固定为100分，{n}个BP共同分配，每个BP最低得1分
2. 按以下4个维度综合评估（维度权重由配置文件提供）：
   - **战略对齐度**（权重：{weights.get('strategic_alignment', 0.4)}）：与组织核心战略/上级BP的关联紧密程度
   - **成果可衡量性**（权重：{weights.get('measurability', 0.2)}）：KR的量化程度和可验收性
   - **举措覆盖度**（权重：{weights.get('measure_coverage', 0.2)}）：举措能否支撑目标达成
   - **影响面**（权重：{weights.get('impact_scope', 0.2)}）：影响范围和协同复杂度
3. 每个维度按0-10分打分，最终加权得分归一化到100分总池

## 重要提示
- 这是相对排序，不是绝对评价
- 不要因BP文字写得好看就给高分，关注实质内容
- 如果某个BP内容严重不完整，单独标注，但仍给出评分
- 若某BP举措承诺的完成时间节点已过期但未交付，在「举措覆盖度」和「成果可衡量性」维度中扣分，理由中注明
- BP内容质量极差（目标空洞/KR无量化/举措缺失）的，正常参与评分，但在reason中明确说明内容缺陷

## 上级BP信息（参考）
{parent_text}

## 待评估的BP列表

{formatted_bps}

## 输出格式（严格遵守，方便程序解析）
```json
{{
  "scores": [
    {{
      "bp_id": "<bp_id>",
      "score": 28,
      "confidence": 0.85,
      "reason": "一句话说明评分依据",
      "dimension_scores": {{
        "strategic_alignment": 8,
        "measurability": 7,
        "measure_coverage": 6,
        "impact_scope": 7
      }}
    }}
  ],
  "total": 100,
  "notes": "整体评分说明（如有特殊情况）"
}}
```"""

    raw = _call_llm(prompt, retry_count=retry_count)
    if raw is None:
        return None

    result = _parse_json_from_response(raw)
    if result is None:
        return None

    # 规范化：确保总分 = 100（允许 < 0.1 误差，否则强制归一化）
    result = _normalize_peer_scores(result, min_score=1.0)
    return result


def _normalize_peer_scores(result: dict, min_score: float = 1.0) -> dict:
    """
    归一化同级BP评分，保证总分 = 100，每个BP分值 ≥ min_score。

    :param result: LLM返回的评分结构
    :param min_score: 单个BP最低分
    :return: 归一化后的评分结构
    """
    scores = result.get("scores", [])
    if not scores:
        return result

    # 强制最低分
    for s in scores:
        if s.get("score", 0) < min_score:
            s["score"] = min_score

    total = sum(s.get("score", 0) for s in scores)
    if abs(total - 100.0) < 0.1:
        result["total"] = 100.0
        return result

    # 按比例归一化到 100
    factor = 100.0 / total
    for i, s in enumerate(scores):
        s["score"] = round(s["score"] * factor, 1)

    # 修正尾差（最后一个BP吸收浮点误差）
    adjusted_total = sum(s["score"] for s in scores)
    diff = round(100.0 - adjusted_total, 1)
    if scores:
        scores[-1]["score"] = round(scores[-1]["score"] + diff, 1)

    result["total"] = 100.0
    return result


# ---------------------------------------------------------------------------
# 分值池分配（承接方贡献度评分）
# ---------------------------------------------------------------------------

def score_undertakers(
    parent_bp: dict,
    undertaker_bps: list[dict],
    pool_score: float,
    weights: dict,
    retry_count: int = 3,
) -> Optional[dict]:
    """
    评估多个承接方对上级BP的贡献度，按比例分配分值池。

    :param parent_bp: 上级 BP 详情
    :param undertaker_bps: 承接方 BP 详情列表
    :param pool_score: 当前分值池（上级BP得分）
    :param weights: pool_distribution 权重字典
    :param retry_count: LLM 重试次数
    :return: LLM 返回的分配结果 dict，或 None（失败）
    """
    n = len(undertaker_bps)
    if n == 0:
        return None

    if n == 1:
        # 单一承接方：100% 分配，无需 AI 比较
        bp = undertaker_bps[0]
        return {
            "allocations": [{
                "undertaker_id": bp.get("bpId", ""),
                "ratio": 1.0,
                "score": pool_score,
                "confidence": 1.0,
                "reason": "唯一承接方，获得100%分值池",
            }],
            "total_ratio": 1.0,
            "total_score": pool_score,
            "notes": "单一承接方，无需AI比较",
        }

    parent_obj = parent_bp.get("objective", "（无）")
    parent_krs = "; ".join(kr.get("description", "") for kr in parent_bp.get("keyResults", []))
    parent_measures = "; ".join(m.get("description", "") for m in parent_bp.get("measures", []))

    formatted_undertakers = "\n\n".join(
        _format_undertaker_for_prompt(bp, i + 1) for i, bp in enumerate(undertaker_bps)
    )

    prompt = f"""你是一个企业BP价值评估专家。

## 任务
上级BP「{parent_bp.get('objective', '（无标题）')}」（分值池：{pool_score}分）有 {n} 个承接方，
请评估每个承接方BP对上级BP的贡献度，分配分值。

## 评分规则
1. {n}个承接方共同分配 {pool_score} 分，每个承接方最低得0.5分
2. 按以下3个维度综合评估：
   - **目标承接准确性**（权重：{weights.get('target_accuracy', 0.45)}）：下级目标是否真实对应上级举措意图
   - **成果对上级贡献**（权重：{weights.get('outcome_contribution', 0.35)}）：成果能否直接推动上级目标实现
   - **举措完整性**（权重：{weights.get('measure_completeness', 0.20)}）：举措是否完整覆盖所承接范围

## 上级BP信息
- 目标：{parent_obj}
- 关键成果（KR）：{parent_krs}
- 核心举措：{parent_measures}

## 承接方BP列表

{formatted_undertakers}

## 输出格式（严格遵守）
```json
{{
  "allocations": [
    {{
      "undertaker_id": "<undertaker_id>",
      "ratio": 0.45,
      "score": {pool_score * 0.45:.1f},
      "confidence": 0.80,
      "reason": "承接准确，成果指标直接映射上级KR"
    }}
  ],
  "total_ratio": 1.0,
  "total_score": {pool_score},
  "notes": "特殊情况说明"
}}
```"""

    raw = _call_llm(prompt, retry_count=retry_count)
    if raw is None:
        return None

    result = _parse_json_from_response(raw)
    if result is None:
        return None

    # 归一化：确保分配总分 = pool_score
    result = _normalize_pool_allocations(result, pool_score=pool_score, min_score=0.5)
    return result


def _normalize_pool_allocations(result: dict, pool_score: float, min_score: float = 0.5) -> dict:
    """
    归一化分值池分配结果，保证总分 = pool_score，每个承接方分值 ≥ min_score。

    :param result: LLM 返回的分配结构
    :param pool_score: 总分值池
    :param min_score: 最低分
    :return: 归一化后的分配结构
    """
    allocations = result.get("allocations", [])
    if not allocations:
        return result

    # 强制最低分
    for a in allocations:
        if a.get("score", 0) < min_score:
            a["score"] = min_score

    total = sum(a.get("score", 0) for a in allocations)
    if abs(total - pool_score) < 0.1:
        # 修正 ratio
        for a in allocations:
            a["ratio"] = round(a["score"] / pool_score, 4)
        result["total_score"] = pool_score
        result["total_ratio"] = 1.0
        return result

    # 按比例归一化
    factor = pool_score / total
    for a in allocations:
        a["score"] = round(a["score"] * factor, 1)
        a["ratio"] = round(a["score"] / pool_score, 4)

    # 修正尾差
    adjusted_total = sum(a["score"] for a in allocations)
    diff = round(pool_score - adjusted_total, 1)
    if allocations:
        allocations[-1]["score"] = round(allocations[-1]["score"] + diff, 1)
        allocations[-1]["ratio"] = round(allocations[-1]["score"] / pool_score, 4)

    result["total_score"] = pool_score
    result["total_ratio"] = 1.0
    return result


# ---------------------------------------------------------------------------
# 批量处理辅助
# ---------------------------------------------------------------------------

def batch_score_peer_bps(
    org_name: str,
    period_name: str,
    bp_list: list[dict],
    parent_bp: Optional[dict],
    weights: dict,
    batch_size: int = 10,
    retry_count: int = 3,
) -> Optional[dict]:
    """
    当 BP 数量 > batch_size 时，分批调用 AI 评分，合并后归一化。

    :param org_name: 组织名称
    :param period_name: BP 周期名称
    :param bp_list: 同级 BP 详情列表
    :param parent_bp: 上级 BP 信息
    :param weights: peer_scoring 权重字典
    :param batch_size: 每批最大 BP 数量（默认 10）
    :param retry_count: LLM 重试次数
    :return: 合并后的评分结果 dict，或 None（全部失败）
    """
    if len(bp_list) <= batch_size:
        return score_peer_bps(org_name, period_name, bp_list, parent_bp, weights, retry_count)

    # 分批处理
    all_scores = []
    batches = [bp_list[i:i + batch_size] for i in range(0, len(bp_list), batch_size)]
    logger.info("BP数量 %d > %d，分 %d 批处理", len(bp_list), batch_size, len(batches))

    for batch_idx, batch in enumerate(batches):
        logger.info("处理第 %d/%d 批（%d个BP）", batch_idx + 1, len(batches), len(batch))
        batch_result = score_peer_bps(
            org_name, period_name, batch, parent_bp, weights, retry_count
        )
        if batch_result is None:
            logger.error("第 %d 批评分失败", batch_idx + 1)
            # 为失败批次生成占位评分
            for bp in batch:
                all_scores.append({
                    "bp_id": bp.get("bpId", ""),
                    "score": 5.0,  # 临时均分
                    "confidence": 0.0,
                    "reason": "[AI评分失败，需人工]",
                    "dimension_scores": {},
                })
        else:
            all_scores.extend(batch_result.get("scores", []))

    if not all_scores:
        return None

    # 合并后重新归一化到100分
    combined = {"scores": all_scores, "total": 100.0, "notes": "[分批处理]"}
    combined = _normalize_peer_scores(combined, min_score=1.0)
    return combined
