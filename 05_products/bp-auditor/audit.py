#!/usr/bin/env python3
"""bp-auditor: generate BP-specific GRV and audit report."""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BP_CLIENT_PATH = Path(__file__).resolve().parent.parent / "bp-manager" / "scripts"
sys.path.insert(0, str(BP_CLIENT_PATH))

try:
    from bp_client import BPClient
except ImportError as exc:
    print(f"Error: cannot import bp_client: {exc}", file=sys.stderr)
    sys.exit(1)


GOAL_CODE_MAP = {
    "G-1": "2000831992328945666",
    "G-1.1": "2000831992475746305",
    "G-1.2": "2000831992622546945",
    "G-1.3": "2000831992769347585",
    "G-2": "2000831992916147202",
    "G-3": "2000831993062947842",
}


RULE_SOURCES = [
    "skills/bp-manager/references/kangzhe-rules.md",
    "skills/bp-manager/references/BP系统业务说明.md",
    "skills/bp-manager/scripts/bp_client.py",
]


@dataclass
class Problem:
    severity: str
    layer: str
    subject_type: str
    subject_code: str
    title: str
    evidence: str
    suggestion: str


def strip_html(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(value: Any) -> str:
    return strip_html(value)


def has_number(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    text = str(value).strip().replace("/", "-")
    if len(text) >= 10:
        text = text[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def split_plan_date_range(value: Optional[str]) -> Tuple[str, str]:
    text = normalize_text(value)
    if not text:
        return "", ""
    for separator in ["~", "至", "—", "–"]:
        if separator in text:
            left, right = text.split(separator, 1)
            return left.strip(), right.strip()
    spaced_dash = re.split(r"\s+-\s+", text, maxsplit=1)
    if len(spaced_dash) == 2:
        return spaced_dash[0].strip(), spaced_dash[1].strip()
    return text, ""


def collect_people(task_users: Optional[Iterable[Dict[str, Any]]]) -> List[str]:
    people: List[str] = []
    for task_user in task_users or []:
        for employee in task_user.get("empList") or []:
            name = normalize_text(employee.get("name"))
            title = normalize_text(employee.get("title"))
            people.append(f"{name}（{title}）" if title else name)
    return [person for person in people if person]


def render_template(template_path: Path, mapping: Dict[str, str]) -> str:
    content = template_path.read_text(encoding="utf-8")
    for key, value in mapping.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    lines = [f"| {' | '.join(headers)} |", f"|{'|'.join(['---'] * len(headers))}|"]
    for row in rows:
        safe_row = [cell.replace("\n", " ") if isinstance(cell, str) else str(cell) for cell in row]
        lines.append(f"| {' | '.join(safe_row)} |")
    return "\n".join(lines)


class BPAuditor:
    def __init__(self) -> None:
        self.client = BPClient()
        self.base_dir = Path(__file__).resolve().parent
        self.today = date.today()
        self.audit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def resolve_bp_id(self, bp_id: Optional[str], goal_code: Optional[str]) -> str:
        if bp_id:
            return bp_id
        if goal_code and goal_code in GOAL_CODE_MAP:
            return GOAL_CODE_MAP[goal_code]
        raise ValueError("请提供 --bp-id，或使用当前映射表中支持的 --goal-code")

    def api_data(self, response: Dict[str, Any], api_name: str) -> Dict[str, Any]:
        if response.get("resultCode") != 1:
            raise RuntimeError(f"{api_name} failed: {response.get('resultMsg') or 'unknown error'}")
        return response.get("data") or {}

    def fetch_goal_detail(self, goal_id: str) -> Dict[str, Any]:
        return self.api_data(self.client.get_goal_detail(goal_id), "get_goal_detail")

    def fetch_kr_detail(self, key_result_id: str) -> Dict[str, Any]:
        return self.api_data(self.client.get_key_result_detail(key_result_id), "get_key_result_detail")

    def fetch_action_detail(self, action_id: str) -> Dict[str, Any]:
        return self.api_data(self.client.get_action_detail(action_id), "get_action_detail")

    def infer_level(self, bp_code: str, group_name: str) -> Dict[str, Any]:
        code = normalize_text(bp_code)
        group = normalize_text(group_name)
        if code.startswith("G-") or "集团" in group:
            return {"name": "集团层级", "expected_layers": 2, "actions_required": False}
        if any(token in group for token in ["中心", "部门", "一级部门", "员工", "个人"]):
            return {"name": group or "组织层级", "expected_layers": 3, "actions_required": True}
        return {"name": group or "默认三层", "expected_layers": 3, "actions_required": True}

    def build_bp_snapshot(self, goal_id: str) -> Dict[str, Any]:
        goal = self.fetch_goal_detail(goal_id)
        key_results = []
        downstream_links: List[Dict[str, Any]] = []

        for kr in goal.get("keyResults") or []:
            kr_id = str(kr.get("id") or "")
            kr_detail = self.fetch_kr_detail(kr_id) if kr_id else kr
            actions = []

            for action in kr_detail.get("actions") or []:
                action_id = str(action.get("id") or "")
                action_detail = self.fetch_action_detail(action_id) if action_id else action
                start_date, end_date = split_plan_date_range(action_detail.get("planDateRange"))
                owners = collect_people(action_detail.get("taskUsers"))
                action_downstream = self.extract_downstream_links(
                    action_detail.get("downTaskList"),
                    source_type="举措",
                    source_code=normalize_text(action_detail.get("fullLevelNumber")) or normalize_text(action.get("fullLevelNumber")),
                    source_name=normalize_text(action_detail.get("name")) or normalize_text(action.get("name")),
                )
                downstream_links.extend(action_downstream)
                actions.append(
                    {
                        "id": action_id,
                        "code": normalize_text(action_detail.get("fullLevelNumber")) or normalize_text(action.get("fullLevelNumber")),
                        "name": normalize_text(action_detail.get("name")) or normalize_text(action.get("name")),
                        "measure_standard": normalize_text(action_detail.get("measureStandard")) or normalize_text(action.get("measureStandard")),
                        "status": normalize_text(action_detail.get("statusDesc")) or normalize_text(action.get("statusDesc")) or "未知",
                        "owners": owners,
                        "plan_start": start_date,
                        "plan_end": end_date,
                        "downstream_count": len(action_downstream),
                    }
                )

            kr_downstream = self.extract_downstream_links(
                kr_detail.get("downTaskList") or kr.get("downTaskList"),
                source_type="KR",
                source_code=normalize_text(kr_detail.get("fullLevelNumber")) or normalize_text(kr.get("fullLevelNumber")),
                source_name=normalize_text(kr_detail.get("name")) or normalize_text(kr.get("name")),
            )
            downstream_links.extend(kr_downstream)
            key_results.append(
                {
                    "id": kr_id,
                    "code": normalize_text(kr_detail.get("fullLevelNumber")) or normalize_text(kr.get("fullLevelNumber")),
                    "name": normalize_text(kr_detail.get("name")) or normalize_text(kr.get("name")),
                    "measure_standard": normalize_text(kr_detail.get("measureStandard")) or normalize_text(kr.get("measureStandard")),
                    "status": normalize_text(kr_detail.get("statusDesc")) or normalize_text(kr.get("statusDesc")) or "未知",
                    "owners": collect_people(kr_detail.get("taskUsers") or kr.get("taskUsers")),
                    "actions": actions,
                    "downstream_count": len(kr_downstream),
                }
            )

        group_name = normalize_text((goal.get("groupInfo") or {}).get("name"))
        bp_code = normalize_text(goal.get("fullLevelNumber"))
        snapshot = {
            "id": str(goal.get("id") or goal_id),
            "code": bp_code or str(goal_id),
            "name": normalize_text(goal.get("name")),
            "description": normalize_text(goal.get("description")),
            "measure_standard": normalize_text(goal.get("measureStandard")),
            "status": normalize_text(goal.get("statusDesc")) or "未知",
            "owners": collect_people(goal.get("taskUsers")),
            "group_name": group_name,
            "upward_refs": self.serialize_refs(goal.get("upwardTaskList")),
            "key_results": key_results,
            "downstream_links": self.deduplicate_links(downstream_links),
        }
        snapshot["level"] = self.infer_level(snapshot["code"], snapshot["group_name"])
        return snapshot

    def extract_downstream_links(
        self,
        raw_links: Optional[Iterable[Dict[str, Any]]],
        source_type: str,
        source_code: str,
        source_name: str,
    ) -> List[Dict[str, Any]]:
        links: List[Dict[str, Any]] = []
        for item in raw_links or []:
            links.append(
                {
                    "source_type": source_type,
                    "source_code": source_code,
                    "source_name": source_name,
                    "target_id": str(item.get("id") or ""),
                    "target_code": normalize_text(item.get("fullLevelNumber")),
                    "target_name": normalize_text(item.get("name")),
                    "target_group": normalize_text((item.get("groupInfo") or {}).get("name")),
                }
            )
        return [link for link in links if link["target_id"]]

    def serialize_refs(self, refs: Optional[Iterable[Dict[str, Any]]]) -> List[Dict[str, str]]:
        result: List[Dict[str, str]] = []
        for item in refs or []:
            result.append(
                {
                    "id": str(item.get("id") or ""),
                    "code": normalize_text(item.get("fullLevelNumber")),
                    "name": normalize_text(item.get("name")),
                }
            )
        return result

    def deduplicate_links(self, links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for link in links:
            key = (link["source_code"], link["target_id"], link["source_type"])
            unique[key] = link
        return list(unique.values())

    def audit(self, snapshot: Dict[str, Any], depth: str) -> Dict[str, Any]:
        problems = self.audit_layer1(snapshot)
        downstream_results: List[Dict[str, Any]] = []

        if depth == "full":
            for link in snapshot["downstream_links"]:
                downstream_result = self.audit_downstream(link)
                downstream_results.append(downstream_result)
                problems.extend(downstream_result["problem_objects"])

        summary = self.build_summary(problems, snapshot, downstream_results, depth)
        return {
            "bp": snapshot,
            "depth": depth,
            "summary": summary,
            "problems": [asdict(problem) for problem in problems],
            "downstream_results": downstream_results,
        }

    def audit_layer1(self, snapshot: Dict[str, Any]) -> List[Problem]:
        problems: List[Problem] = []
        bp_code = snapshot["code"]
        bp_name = snapshot["name"]
        require_actions = snapshot["level"]["actions_required"]

        if not bp_name:
            problems.append(self.problem("P0", "第一层", "目标", bp_code, "目标名称缺失", "目标名称为空", "补齐目标名称，确保可识别"))
        elif len(bp_name) < 8:
            problems.append(self.problem("P1", "第一层", "目标", bp_code, "目标表述偏短", f"目标名称仅 {len(bp_name)} 字：{bp_name}", "改写为更完整的结果状态描述"))

        if not snapshot["measure_standard"]:
            problems.append(self.problem("P0", "第一层", "目标", bp_code, "目标缺少衡量标准", "measureStandard 为空", "补充可验收的衡量标准"))
        elif not has_number(snapshot["measure_standard"]):
            problems.append(self.problem("P1", "第一层", "目标", bp_code, "目标衡量标准缺少量化阈值", snapshot["measure_standard"], "补充数字、阈值或明确验收口径"))

        if not snapshot["owners"]:
            problems.append(self.problem("P1", "第一层", "目标", bp_code, "目标未设置责任人", "taskUsers 为空", "补齐目标责任人或承接人"))

        if not snapshot["code"].startswith("G-") and not snapshot["upward_refs"]:
            problems.append(self.problem("P1", "第一层", "目标", bp_code, "目标缺少上游承接", "upwardTaskList 为空", "补充上游承接关系，明确来源任务"))

        key_results = snapshot["key_results"]
        if not key_results:
            problems.append(self.problem("P0", "第一层", "目标", bp_code, "目标下没有 KR", "keyResults 为空", "至少补充一条关键成果"))

        for key_result in key_results:
            kr_code = key_result["code"] or bp_code
            if not key_result["name"]:
                problems.append(self.problem("P0", "第一层", "KR", kr_code, "KR 名称缺失", "KR 名称为空", "补齐 KR 名称"))
            elif len(key_result["name"]) < 6:
                problems.append(self.problem("P2", "第一层", "KR", kr_code, "KR 表述偏短", key_result["name"], "补充结果状态和对象，增强可验收性"))

            if not key_result["measure_standard"]:
                problems.append(self.problem("P0", "第一层", "KR", kr_code, "KR 缺少衡量标准", "measureStandard 为空", "补充指标、阈值、数据口径"))
            elif not has_number(key_result["measure_standard"]):
                problems.append(self.problem("P1", "第一层", "KR", kr_code, "KR 衡量标准未量化", key_result["measure_standard"], "补充数字或明确阈值"))

            if not key_result["owners"]:
                problems.append(self.problem("P1", "第一层", "KR", kr_code, "KR 未设置责任人", "taskUsers 为空", "补齐 KR 责任人"))

            if require_actions and not key_result["actions"]:
                problems.append(self.problem("P0", "第一层", "KR", kr_code, "KR 缺少关键举措", "actions 为空", "补充可执行举措支撑该 KR"))

            if len(key_result["actions"]) > 6:
                problems.append(self.problem("P2", "第一层", "KR", kr_code, "KR 举措数量偏多", f"当前 {len(key_result['actions'])} 条举措", "检查是否存在拆分过细或重复计功"))

            for action in key_result["actions"]:
                action_code = action["code"] or kr_code
                if not action["name"]:
                    problems.append(self.problem("P0", "第一层", "举措", action_code, "举措名称缺失", "举措名称为空", "补齐具体动作名称"))
                elif len(action["name"]) < 6:
                    problems.append(self.problem("P2", "第一层", "举措", action_code, "举措表述偏短", action["name"], "补充动作、对象、范围或频次"))

                if not action["owners"]:
                    problems.append(self.problem("P1", "第一层", "举措", action_code, "举措未设置责任人", "taskUsers 为空", "补齐举措责任人"))

                if not action["plan_start"] or not action["plan_end"]:
                    problems.append(self.problem("P1", "第一层", "举措", action_code, "举措缺少完整时间边界", f"planDateRange={action['plan_start']}~{action['plan_end']}", "补齐计划开始与结束时间"))
                else:
                    end_date = parse_date(action["plan_end"])
                    if end_date and end_date < self.today and "完成" not in action["status"]:
                        severity = "P0" if (self.today - end_date).days > 30 else "P1"
                        problems.append(self.problem(severity, "第一层", "举措", action_code, "举措已延期", f"计划结束 {action['plan_end']}，当前状态 {action['status']}", "明确延期原因并补充纠偏动作"))

        return problems

    def audit_downstream(self, link: Dict[str, Any]) -> Dict[str, Any]:
        problems: List[Problem] = []
        try:
            snapshot = self.build_bp_snapshot(link["target_id"])
        except Exception as exc:
            problems.append(self.problem("P0", "第二层", "承接BP", link["target_code"] or link["target_id"], "下游 BP 无法读取", str(exc), "确认承接关系与 BP 数据是否可访问"))
            return {
                "link": link,
                "bp": None,
                "problem_objects": problems,
                "problems": [asdict(problem) for problem in problems],
            }

        bp_code = snapshot["code"]
        expected_link = link["source_code"]
        upward_codes = {ref["code"] for ref in snapshot["upward_refs"] if ref["code"]}

        if not snapshot["upward_refs"]:
            problems.append(self.problem("P1", "第二层", "承接BP", bp_code, "下游 BP 未显示上游承接", "upwardTaskList 为空", "补充承接来源，避免链路断裂"))
        elif expected_link and expected_link not in upward_codes:
            problems.append(self.problem("P1", "第二层", "承接BP", bp_code, "下游 BP 承接链路不匹配", f"预期承接 {expected_link}，实际 {', '.join(sorted(upward_codes)) or '空'}", "校准下游 BP 的承接对象"))

        if not snapshot["owners"]:
            problems.append(self.problem("P1", "第二层", "承接BP", bp_code, "下游 BP 未设置责任人", "taskUsers 为空", "补齐下游 BP 责任人"))

        if not snapshot["key_results"]:
            problems.append(self.problem("P0", "第二层", "承接BP", bp_code, "下游 BP 缺少 KR", "keyResults 为空", "补齐关键成果，形成可验收结构"))

        if snapshot["level"]["actions_required"]:
            empty_action_krs = [kr["code"] for kr in snapshot["key_results"] if not kr["actions"]]
            if empty_action_krs:
                problems.append(self.problem("P0", "第二层", "承接BP", bp_code, "下游 KR 缺少举措支撑", ", ".join(empty_action_krs), "为下游 KR 补齐关键举措"))

        result = {
            "link": link,
            "bp": snapshot,
            "problem_objects": problems,
            "problems": [asdict(problem) for problem in problems],
        }
        return result

    def build_summary(
        self,
        problems: List[Problem],
        snapshot: Dict[str, Any],
        downstream_results: List[Dict[str, Any]],
        depth: str,
    ) -> Dict[str, Any]:
        severity_count = {"P0": 0, "P1": 0, "P2": 0}
        for problem in problems:
            severity_count[problem.severity] = severity_count.get(problem.severity, 0) + 1
        overall = "通过"
        if severity_count["P0"]:
            overall = "高风险"
        elif severity_count["P1"]:
            overall = "需优化"

        return {
            "overall": overall,
            "problem_count": len(problems),
            "severity_count": severity_count,
            "layer1_kr_count": len(snapshot["key_results"]),
            "layer1_action_count": sum(len(kr["actions"]) for kr in snapshot["key_results"]),
            "layer2_bp_count": len(downstream_results) if depth == "full" else 0,
        }

    def problem(
        self,
        severity: str,
        layer: str,
        subject_type: str,
        subject_code: str,
        title: str,
        evidence: str,
        suggestion: str,
    ) -> Problem:
        return Problem(severity, layer, subject_type, subject_code, title, evidence, suggestion)

    def render_grv(self, audit_result: Dict[str, Any]) -> str:
        snapshot = audit_result["bp"]
        downstream_links = snapshot["downstream_links"]
        layer2_scope = "仅第一层，不检查下游承接 BP"
        if audit_result["depth"] == "full":
            if downstream_links:
                layer2_scope = " / ".join(
                    f"{link['target_code'] or link['target_name'] or link['target_id']}（承接 {link['source_type']} {link['source_code']}）"
                    for link in downstream_links
                )
            else:
                layer2_scope = "未发现直接下游承接 BP"

        context_rows = [
            ["BP 编码", snapshot["code"]],
            ["BP 名称", snapshot["name"]],
            ["所属分组", snapshot["group_name"] or "未识别"],
            ["责任人", "、".join(snapshot["owners"]) or "未设置"],
            ["上游承接数", str(len(snapshot["upward_refs"]))],
            ["KR 数量", str(len(snapshot["key_results"]))],
            ["举措数量", str(sum(len(kr["actions"]) for kr in snapshot["key_results"]))],
            ["下游承接 BP 数量", str(len(snapshot["downstream_links"]))],
        ]

        mapping = {
            "BP_ID": snapshot["id"],
            "BP_CODE": snapshot["code"],
            "BP_NAME": snapshot["name"],
            "AUDIT_TIME": self.audit_time,
            "LAYER2_SCOPE": layer2_scope,
            "LEVEL_RULE": f"{snapshot['level']['name']}，应拆解到 {snapshot['level']['expected_layers']} 层",
            "EXCLUSIONS": "上游集团 BP 递归、个人能力评估、非 BP 系统外部事实核验",
            "LAYER1_OBJECTIVE_DIMENSIONS": self.dimension_block([
                ("清晰性", "目标名称是否完整且可识别", "名称不能为空，过短记为风险"),
                ("可衡量性", "measureStandard 是否存在且可量化", "缺失为 P0，无数字阈值为 P1"),
                ("责任归属", "是否设置责任人", "未设置为 P1"),
                ("承接关系", "非集团层是否存在上游承接", "缺失为 P1"),
            ]),
            "LAYER1_KR_DIMENSIONS": self.dimension_block([
                ("结果可验收性", "KR 名称与衡量标准是否支撑验收", "缺衡量标准为 P0，未量化为 P1"),
                ("责任人", "KR 是否有明确负责人", "未设置为 P1"),
                ("结构完整性", "三层 BP 的 KR 是否有举措支撑", "应有举措但为空为 P0"),
                ("颗粒度", "举措数量是否失衡", "超过建议上限记为 P2"),
            ]),
            "LAYER1_ACTION_DIMENSIONS": self.dimension_block([
                ("动作明确性", "举措名称是否具体可执行", "名称缺失为 P0，过短为 P2"),
                ("责任归属", "举措是否有责任人", "未设置为 P1"),
                ("时间边界", "是否同时具备计划开始和结束时间", "缺失为 P1"),
                ("延期风险", "到期未完成是否触发风险", "延期 >30 天为 P0，否则 P1"),
            ]),
            "LAYER2_MAPPING_DIMENSIONS": self.dimension_block([
                ("承接存在性", "是否识别到直接下游承接 BP", "无法读取承接 BP 为 P0"),
                ("链路一致性", "下游 upwardTaskList 是否匹配上游来源", "不匹配为 P1"),
            ]),
            "LAYER2_STRUCTURE_DIMENSIONS": self.dimension_block([
                ("目标结构", "下游 BP 是否具备目标与 KR", "无 KR 为 P0"),
                ("三层完整性", "应拆到举措的下游 BP 是否补齐举措", "KR 无举措为 P0"),
            ]),
            "LAYER2_EXECUTION_DIMENSIONS": self.dimension_block([
                ("责任归属", "下游 BP 是否设置责任人", "未设置为 P1"),
                ("执行可行性", "下游是否具备可以推进的任务结构", "结构不完整则升级处理"),
            ]),
            "PROBLEM_TABLE_TEMPLATE": markdown_table(
                ["字段", "说明"],
                [
                    ["问题定位", "层级 / 对象类型 / 编码"],
                    ["证据", "直接引用字段值或缺失情况"],
                    ["整改建议", "给出可执行修复动作"],
                ],
            ),
            "EXECUTION_STEPS": "\n".join([
                "1. 读取目标详情、KR 明细、举措明细。",
                "2. 判定 BP 层级与应有拆解深度。",
                "3. 生成当前 BP 专属 GRV。",
                "4. 执行第一层结构与质量检查。",
                "5. 若为 full 模式，执行第二层承接检查。",
                "6. 汇总 P0 / P1 / P2 问题并生成报告。",
            ]),
            "REPORT_TEMPLATE_FILE": "skills/bp-auditor/report-template.md",
            "BP_CONTEXT": markdown_table(["字段", "值"], context_rows),
        }
        return render_template(self.base_dir / "grv-template.md", mapping)

    def dimension_block(self, rows: List[Tuple[str, str, str]]) -> str:
        return markdown_table(["检查项", "方法", "判定标准"], [[a, b, c] for a, b, c in rows])

    def render_report(self, audit_result: Dict[str, Any], grv_path: Path) -> str:
        snapshot = audit_result["bp"]
        summary = audit_result["summary"]
        problems = audit_result["problems"]
        layer1_rows = []
        for key_result in snapshot["key_results"]:
            layer1_rows.append([
                key_result["code"],
                key_result["name"] or "未命名",
                key_result["measure_standard"] or "未设置",
                str(len(key_result["actions"])),
                "、".join(key_result["owners"]) or "未设置",
            ])

        layer2_rows = []
        for item in audit_result["downstream_results"]:
            link = item["link"]
            bp = item.get("bp")
            issue_count = len(item["problems"])
            layer2_rows.append([
                link["source_type"],
                link["source_code"] or "未识别",
                (bp or {}).get("code") or link["target_code"] or link["target_id"],
                (bp or {}).get("name") or link["target_name"] or "未识别",
                str(issue_count),
            ])

        grouped = {"P0": [], "P1": [], "P2": []}
        for problem in problems:
            grouped.setdefault(problem["severity"], []).append(problem)

        def build_problem_sections(layer_name: str) -> str:
            sections: List[str] = []
            for severity in ["P0", "P1", "P2"]:
                items = [item for item in grouped.get(severity) or [] if item["layer"] == layer_name]
                if not items:
                    continue
                rows = []
                for item in items:
                    rows.append([
                        item["subject_type"],
                        item["subject_code"],
                        item["title"],
                        item["evidence"],
                        item["suggestion"],
                    ])
                sections.append(f"### {severity}\n\n{markdown_table(['对象', '编码', '问题', '证据', '建议'], rows)}")
            return "\n\n".join(sections) if sections else "未发现该层问题。"

        layer1_problem_sections = build_problem_sections("第一层")
        layer2_problem_sections = build_problem_sections("第二层")

        executive_summary = "\n".join([
            f"- 审计结论：{summary['overall']}",
            f"- 问题总数：{summary['problem_count']}（P0={summary['severity_count']['P0']} / P1={summary['severity_count']['P1']} / P2={summary['severity_count']['P2']}）",
            f"- 第一层结构：KR {summary['layer1_kr_count']} 条，举措 {summary['layer1_action_count']} 条",
            f"- 第二层承接：{summary['layer2_bp_count']} 个直接下游 BP",
        ])

        layer1_result = "\n\n".join([
            markdown_table(["KR编码", "KR名称", "衡量标准", "举措数", "责任人"], layer1_rows) if layer1_rows else "未读取到 KR 数据。",
            layer1_problem_sections,
        ])

        if audit_result["depth"] == "full":
            layer2_result = "\n\n".join([
                markdown_table(["承接来源", "来源编码", "下游编码", "下游名称", "问题数"], layer2_rows) if layer2_rows else "未发现直接下游承接 BP。",
                layer2_problem_sections,
            ])
        else:
            layer2_result = "本次仅执行第一层审计。"

        next_actions = self.next_actions(grouped)
        overall_conclusion = self.overall_conclusion(summary)

        mapping = {
            "BP_ID": snapshot["id"],
            "BP_CODE": snapshot["code"],
            "BP_NAME": snapshot["name"],
            "AUDIT_TIME": self.audit_time,
            "AUDIT_DEPTH": "完整两层" if audit_result["depth"] == "full" else "仅第一层",
            "RULE_SOURCES": "、".join(RULE_SOURCES),
            "GRV_PATH": str(grv_path),
            "EXECUTIVE_SUMMARY": executive_summary,
            "LAYER1_RESULT": layer1_result,
            "LAYER2_RESULT": layer2_result,
            "OVERALL_CONCLUSION": overall_conclusion,
            "NEXT_ACTIONS": next_actions,
        }
        return render_template(self.base_dir / "report-template.md", mapping)

    def next_actions(self, grouped: Dict[str, List[Dict[str, Any]]]) -> str:
        lines: List[str] = []
        if grouped.get("P0"):
            lines.append("- 先处理所有 P0：补齐缺失结构、衡量标准与承接链路。")
        if grouped.get("P1"):
            lines.append("- 再处理 P1：完善责任人、时间边界与量化阈值。")
        if grouped.get("P2"):
            lines.append("- 最后处理 P2：优化表述、颗粒度与结构整洁度。")
        if not lines:
            lines.append("- 当前未发现显著问题，建议进入常规跟踪与复核。")
        return "\n".join(lines)

    def overall_conclusion(self, summary: Dict[str, Any]) -> str:
        if summary["severity_count"]["P0"]:
            return "当前 BP 存在高风险结构问题，暂不建议直接作为稳定承接基线，需先完成关键整改。"
        if summary["severity_count"]["P1"]:
            return "当前 BP 主体结构可用，但存在明显设计或执行风险，建议尽快优化后再进入稳定推进。"
        return "当前 BP 结构整体通过，建议继续跟踪执行进度，并在后续迭代中处理表达类优化项。"

    def write_outputs(self, output_dir: Path, audit_result: Dict[str, Any]) -> Dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        grv_path = output_dir / "grv.md"
        report_path = output_dir / "report.md"
        raw_path = output_dir / "raw.json"
        serializable_result = dict(audit_result)
        serializable_result["downstream_results"] = [
            {key: value for key, value in item.items() if key != "problem_objects"}
            for item in audit_result["downstream_results"]
        ]

        grv_path.write_text(self.render_grv(audit_result), encoding="utf-8")
        report_path.write_text(self.render_report(audit_result, grv_path), encoding="utf-8")
        raw_path.write_text(json.dumps(serializable_result, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"grv": grv_path, "report": report_path, "raw": raw_path}


def default_output_dir(snapshot: Dict[str, Any]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_code = re.sub(r"[^A-Za-z0-9._-]+", "-", snapshot["code"] or snapshot["id"])
    return Path("memory") / "bp-audits" / f"{safe_code}-{timestamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate BP-specific GRV and audit report")
    parser.add_argument("--bp-id", help="BP goal id")
    parser.add_argument("--goal-code", help="Goal code, e.g. G-1")
    parser.add_argument("--depth", choices=["layer1", "full"], default="full")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.bp_id and not args.goal_code:
        print("Error: one of --bp-id or --goal-code is required", file=sys.stderr)
        return 2

    auditor = BPAuditor()
    try:
        bp_id = auditor.resolve_bp_id(args.bp_id, args.goal_code)
        snapshot = auditor.build_bp_snapshot(bp_id)
        audit_result = auditor.audit(snapshot, args.depth)
        output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(snapshot)
        paths = auditor.write_outputs(output_dir, audit_result)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({
            "bp_id": bp_id,
            "bp_code": snapshot["code"],
            "output_dir": str(output_dir),
            "files": {key: str(value) for key, value in paths.items()},
            "summary": audit_result["summary"],
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"BP: {snapshot['code']} {snapshot['name']}")
    print(f"结论: {audit_result['summary']['overall']}")
    print(
        "问题: "
        f"P0={audit_result['summary']['severity_count']['P0']} / "
        f"P1={audit_result['summary']['severity_count']['P1']} / "
        f"P2={audit_result['summary']['severity_count']['P2']}"
    )
    print(f"输出目录: {output_dir}")
    print(f"GRV: {paths['grv']}")
    print(f"报告: {paths['report']}")
    print(f"原始数据: {paths['raw']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
