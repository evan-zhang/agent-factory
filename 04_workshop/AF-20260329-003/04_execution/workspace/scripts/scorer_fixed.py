# scorer.py 修复版片段

def _format_bp_for_prompt(bp: dict, index: int) -> str:
    """
    将单个 BP 详情格式化为 Prompt 中的文本块。

    :param bp: BP 详情字典（API 返回: id, name, keyResults[].actions）
    :param index: 序号（从1开始）
    :return: 格式化文本
    """
    # API 返回字段: id (非 bpId), name (非 objective)
    bp_id = bp.get("id", "") or bp.get("bpId", f"BP-{index}")
    objective = bp.get("name", "") or bp.get("objective", "（无目标描述）")
    
    # 清理 HTML 标签
    def clean_html(text):
        if not text:
            return ""
        return text.replace("<p>", "").replace("</p>", "").replace("<span>", "").replace("</span>", "").strip()[:80]

    krs = bp.get("keyResults", []) or []
    kr_text = "\n".join(
        f"  - KR{i+1}: {clean_html(kr.get('name', '') or kr.get('description', ''))}"
        for i, kr in enumerate(krs)
    ) or "  （无KR）"

    # 从 keyResults[].actions 中提取举措（而非顶层 measures）
    all_measures = []
    for kr in krs:
        actions = kr.get("actions", []) or []
        for a in actions:
            undertakers = []
            for td in (a.get("taskDepts", []) or []):
                if td.get("role") == "undertaker":
                    for dept in (td.get("deptList", []) or []):
                        undertakers.append(dept.get("name", ""))
            action_name = clean_html(a.get("name", ""))
            if action_name or undertakers:
                all_measures.append({
                    "name": action_name,
                    "undertakers": undertakers
                })

    # 兼容旧格式：如果顶层有 measures 字段
    if not all_measures:
        for m in bp.get("measures", []) or []:
            undertakers = [d.get("name", "") for d in (m.get("taskDepts", []) or []) if d.get("role") == "undertaker"]
            all_measures.append({
                "name": m.get("description", "") or m.get("name", ""),
                "undertakers": undertakers
            })

    measure_text = "\n".join(
        f"  - 举措{i+1}: {m['name'] or '（无名称）'}（承接方：{', '.join(m['undertakers']) or '无'}）"
        for i, m in enumerate(all_measures)
    ) or "  （无举措）"

    return (
        f"### BP {index}（ID: {bp_id}）\n"
        f"**目标**: {objective}\n"
        f"**关键成果（KR）**:\n{kr_text}\n"
        f"**核心举措**:\n{measure_text}"
    )
