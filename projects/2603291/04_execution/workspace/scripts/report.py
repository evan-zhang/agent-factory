"""
report.py
=========
评分报告生成模块。

将评分树（ScoreNode 结构）渲染为 GRV 第五节规定的 Markdown 格式报告，
输出到 output/[组织名]-[日期]-report.md。
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据结构定义（纯 dict，无外部依赖）
# ---------------------------------------------------------------------------

# ScoreNode 结构（在代码中以 dict 表示）：
# {
#   "id": str,                  # bpId 或 personId
#   "name": str,                # BP 标题 / 人名
#   "type": "bp" | "person",
#   "score": float,
#   "score_source": "ai_original" | "manual_adjusted" | "cascade_updated" | "no_undertaker" | "ai_failed",
#   "adjusted_from": float | None,   # 人工调整前的原始分
#   "adjust_reason": str | None,
#   "confidence": float | None,
#   "reason": str,              # 评分理由
#   "tags": list[str],          # 如 ["内容不完整", "低置信度", "无承接"]
#   "children": list[ScoreNode],
#   "parent_ratio": float | None,  # 占上级分值池的比例
#   "org_path": str,            # 完整路径，如 "产品中心 → 部门A → 员工甲"
#   "source_bp_ids": list[str], # 得分来源的 bpId（用于个人汇总表）
# }


def build_tags(node: dict, confidence_threshold: float = 0.70) -> list[str]:
    """
    根据节点状态构建标注标签列表。

    :param node: ScoreNode dict
    :param confidence_threshold: 低置信度阈值
    :return: 标签列表
    """
    tags = list(node.get("tags", []))

    score_source = node.get("score_source", "")
    if score_source == "no_undertaker":
        if "无承接" not in tags:
            tags.append("无承接")
    elif score_source == "ai_failed":
        if "AI评分失败，需人工" not in tags:
            tags.append("AI评分失败，需人工")

    confidence = node.get("confidence")
    if confidence is not None and confidence < confidence_threshold:
        label = f"低置信度: {confidence:.2f}"
        if not any("低置信度" in t for t in tags):
            tags.append(label)

    if node.get("score_source") == "manual_adjusted":
        tags.append(f"人工调整，原AI评分{node.get('adjusted_from', '?')}分")

    return tags


def _render_tag_str(tags: list[str]) -> str:
    """将标签列表渲染为行内标注字符串，如 `[内容不完整]` `[低置信度: 0.62]`。"""
    if not tags:
        return ""
    return " " + " ".join(f"`[{t}]`" for t in tags)


def _render_score_label(node: dict) -> str:
    """
    渲染分值旁的来源标注，如 `[AI原始]` / `[人工调整，原AI评分28.0分，原因：...]`。

    :param node: ScoreNode dict
    :return: 标注字符串
    """
    source = node.get("score_source", "ai_original")
    if source == "manual_adjusted":
        orig = node.get("adjusted_from", "?")
        reason = node.get("adjust_reason", "")
        return f" [人工调整，原AI评分{orig}分，原因：{reason}]"
    elif source == "cascade_updated":
        return " [AI原始，联动更新自上级调整]"
    elif source == "ai_original":
        return " [AI原始]"
    elif source == "no_undertaker":
        return " [无承接]"
    elif source == "ai_failed":
        return " [AI评分失败，需人工]"
    return ""


def render_score_tree(nodes: list[dict], confidence_threshold: float = 0.70, depth: int = 1) -> str:
    """
    递归渲染评分树为 Markdown 文本。

    :param nodes: 同层 ScoreNode 列表
    :param confidence_threshold: 低置信度阈值
    :param depth: 当前层级（决定标题级别，从2开始，最深用列表）
    :return: Markdown 字符串
    """
    lines = []
    heading = "#" * min(depth + 2, 6)  # H3~H6

    for node in nodes:
        score = node.get("score", 0.0)
        name = node.get("name", node.get("id", "未知"))
        node_type = node.get("type", "bp")
        tags = build_tags(node, confidence_threshold)
        tag_str = _render_tag_str(tags)
        score_label = _render_score_label(node)
        ratio = node.get("parent_ratio")
        ratio_str = f"（占池子 {ratio * 100:.0f}%）" if ratio is not None else ""
        reason = node.get("reason", "")
        children = node.get("children", [])

        if node_type == "person":
            # 个人层：用列表项
            lines.append(f"- **{name}** — **{score:.1f}分**{score_label}{tag_str}")
            if reason:
                lines.append(f"  > {reason}")
        else:
            # 组织/BP 层：用标题
            bp_id = node.get("id", "")
            lines.append(f"{heading} {bp_id}《{name}》— **{score:.1f}分**{score_label}{tag_str}")
            if reason:
                lines.append(f"> {reason}")
            
            # 显示关键成果（KR）
            key_results = node.get("key_results", [])
            if key_results:
                lines.append("")
                lines.append("**关键成果（KR）：**")
                for kr in key_results:
                    lines.append(f"- {kr}")
            
            lines.append("")

            if children:
                lines.append("**承接方：**")
                lines.append("")
                lines.append(render_score_tree(children, confidence_threshold, depth + 1))

        lines.append("")

    return "\n".join(lines)


def collect_persons(nodes: list[dict]) -> list[dict]:
    """
    从评分树中递归收集所有个人层节点，并按人名汇总总分。

    :param nodes: ScoreNode 列表（任意层级）
    :return: 按人名汇总的个人得分列表 [{"name": str, "total_score": float, "bp_count": int, "source_bps": list}]
    """
    # 先收集所有 person 节点
    persons_map = {}  # {人名: {"total_score": float, "bp_count": int, "bp_names": list}}
    
    def collect(node):
        if node.get("type") == "person":
            name = node.get("name", "未知")
            score = node.get("score", 0.0)
            source_bp_ids = node.get("source_bp_ids", [])
            if name not in persons_map:
                persons_map[name] = {"total_score": 0.0, "bp_count": 0, "bp_names": [], "bp_ids": []}
            persons_map[name]["total_score"] += score
            persons_map[name]["bp_count"] += 1
            persons_map[name]["bp_ids"].extend(source_bp_ids)
        for child in node.get("children", []):
            collect(child)
    
    for node in nodes:
        collect(node)
    
    # 转换为列表并按总分降序排列
    result = []
    for name, data in persons_map.items():
        result.append({
            "name": name,
            "total_score": round(data["total_score"], 1),
            "bp_count": data["bp_count"],
            "source_bp_ids": list(set(data["bp_ids"])),
        })
    result.sort(key=lambda x: x["total_score"], reverse=True)
    return result


def collect_pending_items(nodes: list[dict], confidence_threshold: float = 0.70) -> list[str]:
    """
    从评分树中收集所有待人工确认项。

    :param nodes: ScoreNode 列表
    :param confidence_threshold: 低置信度阈值
    :return: 待确认项描述列表
    """
    items = []
    for node in nodes:
        node_id = node.get("id", "?")
        name = node.get("name", "?")
        confidence = node.get("confidence")
        tags = node.get("tags", [])
        score = node.get("score", 0.0)

        if confidence is not None and confidence < confidence_threshold:
            items.append(
                f"- [ ] `{node_id}`《{name}》AI置信度 {confidence:.2f}，"
                f"分值 {score:.1f}分 `[低置信度: {confidence:.2f}]`"
            )
        if "AI评分失败，需人工" in tags or node.get("score_source") == "ai_failed":
            items.append(f"- [ ] `{node_id}`《{name}》AI评分失败，需人工赋分 `[AI评分失败，需人工]`")
        if "无承接" in tags or node.get("score_source") == "no_undertaker":
            items.append(
                f"- [ ] `{node_id}`《{name}》无承接方，分值 {score:.1f} 分未继续下分 `[无承接]`"
            )
        if "内容不完整" in " ".join(tags):
            items.append(f"- [ ] `{node_id}`《{name}》BP内容不完整，已给最低分 `[内容不完整]`")

        # 递归子节点
        items.extend(collect_pending_items(node.get("children", []), confidence_threshold))

    return items


def generate_report(
    org_name: str,
    period_name: str,
    score_tree: list[dict],
    confidence_threshold: float = 0.70,
    output_dir: str = "output",
    version: str = "v1（待人工确认）",
) -> str:
    """
    生成完整的评分报告 Markdown 文件，写入 output/ 目录。

    :param org_name: 组织名称
    :param period_name: BP 周期名称
    :param score_tree: 评分树（ScoreNode 列表）
    :param confidence_threshold: 低置信度阈值
    :param output_dir: 输出目录路径
    :param version: 报告版本字符串
    :return: 输出文件路径
    """
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%Y-%m-%d %H:%M")

    # 计算顶层总分（理论上应 = 100）
    total_score = sum(n.get("score", 0.0) for n in score_tree)

    # 渲染评分树
    tree_md = render_score_tree(score_tree, confidence_threshold, depth=1)

    # 个人得分汇总表
    persons = collect_persons(score_tree)
    person_rows = ""
    if persons:
        rows = []
        for p in persons:
            bp_ids = p.get("source_bp_ids", [])
            # 截取 BP ID 前8位用于显示
            bp_display = ", ".join(bid[:8] for bid in bp_ids) if bp_ids else "—"
            rows.append(
                f"| {p.get('name', '?')} | {p.get('total_score', 0.0):.1f}分 "
                f"| {p.get('bp_count', 0)}个BP | {bp_display} |"
            )
        person_rows = "\n".join(rows)
    else:
        person_rows = "| （无个人层数据） | — | — | — |"

    # 待人工确认项
    pending = collect_pending_items(score_tree, confidence_threshold)
    pending_md = "\n".join(pending) if pending else "（无待确认项，所有评分AI置信度均达标）"

    report_md = f"""# BP价值评分报告

**组织**：{org_name}
**BP周期**：{period_name}
**评分时间**：{time_str}
**总分**：{total_score:.1f} 分
**报告版本**：{version}

---

## 评分树

{tree_md}

---

## 个人得分汇总

| 姓名 | 总分 | BP数量 | 来源BP(前8位) |
|---|---|---|---|
{person_rows}

---

## 待人工确认项

以下评分AI置信度 < {confidence_threshold:.2f}，建议人工复核：

{pending_md}

---

*本报告由AI生成，置信度仅供参考。最终以人工确认版本（confirmed.md）为准。*
*评分不代表绩效结论，激励决策由管理者综合判断。*
"""

    # 写入文件
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{org_name}-{date_str}-report.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_md)

    logger.info("评分报告已生成: %s", filepath)
    return filepath


def generate_confirmed_report(
    report_path: str,
    bonus_section: str = "",
) -> str:
    """
    基于 report.md 生成 confirmed.md（只读，带确认时间戳）。

    :param report_path: 原始报告路径（*-report.md）
    :param bonus_section: 奖金系数合理性审查章节 Markdown 文本（由 bonus_checker 提供）
    :return: confirmed 文件路径
    """
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 替换版本号为已确认
    content = content.replace("v1（待人工确认）", f"v1（已确认，{now}）")

    # 追加奖金系数审查章节（如有）
    if bonus_section:
        content = content.rstrip() + "\n\n" + bonus_section.strip() + "\n"

    # 追加确认标记
    content += f"\n---\n\n> **⚠️ 此文件为最终确认版本（{now}），不可再修改。如需更新，请重新运行 run 命令生成新版本。**\n"

    confirmed_path = report_path.replace("-report.md", "-confirmed.md")
    with open(confirmed_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("已生成确认报告: %s", confirmed_path)
    return confirmed_path


def load_score_tree_from_report(report_path: str) -> Optional[dict]:
    """
    从已生成的报告文件旁加载评分树（JSON 缓存文件）。

    评分树以 JSON 格式缓存在 *-tree.json，与 *-report.md 并存。

    :param report_path: 报告文件路径
    :return: 评分树 dict，或 None
    """
    tree_path = report_path.replace("-report.md", "-tree.json")
    if not os.path.exists(tree_path):
        logger.warning("评分树缓存文件不存在: %s", tree_path)
        return None
    with open(tree_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_score_tree(report_path: str, tree_data: dict) -> None:
    """
    将评分树以 JSON 格式缓存到磁盘（供 adjust 命令后重新渲染）。

    :param report_path: 报告文件路径（用于派生 JSON 路径）
    :param tree_data: 包含 score_tree 和 session 状态的 dict
    """
    tree_path = report_path.replace("-report.md", "-tree.json")
    with open(tree_path, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)
    logger.info("评分树缓存已保存: %s", tree_path)
