"""
adjuster.py
===========
人工调整模块。

实现 GRV 第六节的 adjust 命令逻辑：
- 修改指定 BP 的分值
- 按"原始AI比例"等比缩放同层其他 BP
- 递归联动更新下级分值池
- 标注调整来源
"""

import copy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 原始比例管理
# ---------------------------------------------------------------------------

def extract_original_ratios(score_tree: list[dict], layer_id: str) -> dict:
    """
    从评分树的某一层提取 AI 原始比例，格式为 {bp_id: ratio}。

    比例 = 该 BP 得分 / 该层总分。
    只记录 AI 原始评分（score_source == "ai_original"）的 BP；
    已被人工调整的 BP 在计算剩余分时会被跳过。

    :param score_tree: 该层的 ScoreNode 列表
    :param layer_id: 该层的唯一标识（如 "产品中心-2026Q1"），用于 session 存储 key
    :return: {bp_id: original_ratio}
    """
    total = sum(n.get("score", 0.0) for n in score_tree)
    if total <= 0:
        logger.warning("层级 %s 总分为0，无法提取原始比例", layer_id)
        return {}

    ratios = {}
    for node in score_tree:
        bp_id = node.get("id", "")
        ratios[bp_id] = node.get("score", 0.0) / total
    return ratios


def build_original_ratios_session(score_tree: list[dict], parent_id: str = "root") -> dict:
    """
    递归遍历评分树，为每一层构建原始比例 session 状态。

    :param score_tree: ScoreNode 列表（任意层级）
    :param parent_id: 当前层的父节点 ID（用作 key）
    :return: {layer_key: {bp_id: ratio}} 嵌套 dict
    """
    session = {}
    if not score_tree:
        return session

    layer_key = parent_id
    session[layer_key] = extract_original_ratios(score_tree, layer_key)

    for node in score_tree:
        children = node.get("children", [])
        if children:
            child_session = build_original_ratios_session(children, parent_id=node.get("id", ""))
            session.update(child_session)

    return session


# ---------------------------------------------------------------------------
# 核心调整逻辑
# ---------------------------------------------------------------------------

def adjust_bp_score(
    score_tree: list[dict],
    bp_id: str,
    new_score: float,
    reason: str,
    original_ratios_session: dict,
    parent_id: str = "root",
) -> tuple[list[dict], bool]:
    """
    在评分树中找到指定 BP，修改其分值，并对同层其他 BP 按原始比例等比缩放。
    同时递归联动更新下级分值池。

    :param score_tree: 当前层 ScoreNode 列表（原地修改副本）
    :param bp_id: 要调整的 BP ID
    :param new_score: 新的分值（用户指定）
    :param reason: 调整理由
    :param original_ratios_session: 每层的原始比例 session dict
    :param parent_id: 当前层父节点 ID（用于 session key 查找）
    :return: (更新后的 score_tree, 是否找到并调整成功)
    """
    tree = copy.deepcopy(score_tree)

    # 在当前层查找目标 BP
    target_idx = None
    for i, node in enumerate(tree):
        if node.get("id") == bp_id:
            target_idx = i
            break

    if target_idx is not None:
        # 找到目标 BP，执行调整
        target_node = tree[target_idx]
        original_score = target_node.get("score", 0.0)
        layer_key = parent_id

        # 记录人工调整信息
        target_node["score_source"] = "manual_adjusted"
        target_node["adjusted_from"] = original_score
        target_node["adjust_reason"] = reason
        target_node["score"] = round(new_score, 1)

        # 计算当前层总分（调整前）
        layer_total = sum(n.get("score", 0.0) for n in score_tree)

        # 获取本层原始比例
        layer_ratios = original_ratios_session.get(layer_key, {})

        # 识别"尚未被人工指定"的 BP
        manually_adjusted_ids = {
            n.get("id") for n in tree
            if n.get("score_source") == "manual_adjusted" and n.get("id") != bp_id
        }
        unadjusted_nodes = [
            n for n in tree
            if n.get("id") != bp_id and n.get("id") not in manually_adjusted_ids
        ]

        remaining_score = layer_total - new_score
        manual_total = sum(n.get("score", 0.0) for n in tree if n.get("id") in manually_adjusted_ids)
        remaining_for_unadjusted = remaining_score - manual_total

        if unadjusted_nodes:
            # 按原始比例等比分配剩余分
            unadjusted_ratio_sum = sum(
                layer_ratios.get(n.get("id"), 1.0 / len(unadjusted_nodes))
                for n in unadjusted_nodes
            )

            if unadjusted_ratio_sum <= 0:
                # 无法按比例分配，均分
                each = remaining_for_unadjusted / len(unadjusted_nodes)
                for n in unadjusted_nodes:
                    n["score"] = round(each, 1)
            else:
                for n in unadjusted_nodes:
                    ratio = layer_ratios.get(n.get("id"), 1.0 / len(unadjusted_nodes))
                    n["score"] = round(remaining_for_unadjusted * (ratio / unadjusted_ratio_sum), 1)
                    n["score_source"] = "cascade_updated"

            # 修正尾差
            _fix_rounding_error(tree, layer_total)

        elif manually_adjusted_ids:
            # 所有 BP 均已被手动指定
            current_total = sum(n.get("score", 0.0) for n in tree)
            if abs(current_total - layer_total) > 0.1:
                raise ValueError(
                    f"所有BP均已手动指定，但总分 {current_total:.1f} ≠ {layer_total:.1f}，"
                    "请修正分值使总和等于上级分值池。"
                )

        # 联动更新下级分值池：递归重算目标BP的子节点
        new_pool = target_node["score"]
        if target_node.get("children"):
            target_node["children"] = _cascade_update_children(
                target_node["children"], new_pool, original_ratios_session, bp_id
            )

        return tree, True

    # 未在当前层找到，递归向下搜索
    for node in tree:
        children = node.get("children", [])
        if children:
            updated_children, found = adjust_bp_score(
                children, bp_id, new_score, reason,
                original_ratios_session, parent_id=node.get("id", "")
            )
            if found:
                node["children"] = updated_children
                return tree, True

    return tree, False


def _fix_rounding_error(tree: list[dict], expected_total: float) -> None:
    """
    修正浮点误差：将尾差加到最后一个未被手动调整的 BP。

    :param tree: 当前层 ScoreNode 列表（原地修改）
    :param expected_total: 期望总分
    """
    current_total = sum(n.get("score", 0.0) for n in tree)
    diff = round(expected_total - current_total, 1)
    if abs(diff) < 0.01:
        return

    # 找最后一个 cascade_updated 节点吸收误差
    for node in reversed(tree):
        if node.get("score_source") in ("cascade_updated", "ai_original"):
            node["score"] = round(node["score"] + diff, 1)
            break


def _cascade_update_children(
    children: list[dict],
    new_pool: float,
    original_ratios_session: dict,
    parent_id: str,
) -> list[dict]:
    """
    当上级 BP 分值发生变化时，按原始比例重新缩放所有子节点分值。

    :param children: 子节点列表
    :param new_pool: 新的分值池（上级 BP 新分值）
    :param original_ratios_session: 原始比例 session
    :param parent_id: 父节点 ID
    :return: 更新后的子节点列表
    """
    layer_ratios = original_ratios_session.get(parent_id, {})
    if not layer_ratios:
        # 没有原始比例，按当前分值等比缩放
        old_total = sum(c.get("score", 0.0) for c in children)
        if old_total <= 0:
            return children
        factor = new_pool / old_total
        updated = []
        for child in children:
            c = copy.deepcopy(child)
            c["score"] = round(c.get("score", 0.0) * factor, 1)
            c["score_source"] = "cascade_updated"
            # 递归更新子节点的下级
            if c.get("children"):
                c["children"] = _cascade_update_children(
                    c["children"], c["score"], original_ratios_session, c.get("id", "")
                )
            updated.append(c)
        return updated

    updated = []
    ratio_sum = sum(layer_ratios.get(c.get("id", ""), 0.0) for c in children)
    if ratio_sum <= 0:
        ratio_sum = 1.0

    for child in children:
        c = copy.deepcopy(child)
        ratio = layer_ratios.get(c.get("id", ""), 1.0 / len(children))
        c["score"] = round(new_pool * (ratio / ratio_sum), 1)
        c["score_source"] = "cascade_updated"
        if c.get("children"):
            c["children"] = _cascade_update_children(
                c["children"], c["score"], original_ratios_session, c.get("id", "")
            )
        updated.append(c)

    # 修正尾差
    _fix_rounding_error(updated, new_pool)
    return updated


def validate_tree_score_conservation(
    score_tree: list[dict],
    expected_total: float = 100.0,
    tolerance: float = 0.1,
) -> tuple[bool, list[str]]:
    """
    验证评分树的分值守恒性：每层子节点之和 ≤ 父节点分值（允许 tolerance 误差）。

    :param score_tree: 评分树根节点列表
    :param expected_total: 根层期望总分
    :param tolerance: 允许误差
    :return: (通过/失败, 错误描述列表)
    """
    errors = []

    # 校验根层
    root_total = sum(n.get("score", 0.0) for n in score_tree)
    if abs(root_total - expected_total) > tolerance:
        errors.append(f"根层总分 {root_total:.1f} ≠ {expected_total:.1f}")

    def _check(nodes: list[dict]):
        for node in nodes:
            children = node.get("children", [])
            if children:
                child_total = sum(c.get("score", 0.0) for c in children)
                parent_score = node.get("score", 0.0)
                if abs(child_total - parent_score) > tolerance:
                    errors.append(
                        f"节点 {node.get('id')}（{node.get('name')}）"
                        f"子节点总分 {child_total:.1f} ≠ 父节点 {parent_score:.1f}"
                    )
                _check(children)

    _check(score_tree)
    return len(errors) == 0, errors
