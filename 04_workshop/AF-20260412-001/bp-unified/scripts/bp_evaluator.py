#!/usr/bin/env python3
"""
bp-evaluator - BP Evaluation Script v2.3
Full BP evaluation with two-layer structure, P0/P1/P2 problem grading,
and 6 deep analysis capabilities.

v2.3 报告结构重组：从"按维度组织"改为"按BP组织"，两层结构清晰。
  - 第一层：G-1自身评估
  - 第二层：6个下游BP各一节，节内按维度展开

Deep Analysis Capabilities (v2.2+):
  §3.1 举措过期时间线（下游BP）- Initiative expiry timeline (downstream BPs)
  §3.2 责任人能力匹配  - Owner capability matching
  §3.3 口径一致性检查  - Caliber consistency (G-layer vs downstream)
  §3.4 因果链追溯      - Initiative→income causal chain
  §3.5 个人BP核对      - Personal BP verification (TBD placeholder)
  §3.6 目标设计有效性  - Target design validity
"""

import argparse
import json
import re
import subprocess
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── BP Client ────────────────────────────────────────────────────────────────
BP_CLIENT_PATH = Path(__file__).parent.parent.parent / "bp-manager" / "scripts"
sys.path.insert(0, str(BP_CLIENT_PATH))
try:
    from bp_client import BPClient
except ImportError:
    print("Error: cannot import bp_client", file=sys.stderr)
    sys.exit(1)

# ── CWork Search Emp ────────────────────────────────────────────────────────
CWORK_SEARCH_EMP_PATH = (
    Path(__file__).parent.parent.parent
    / "cms-cwork" / "scripts" / "cwork-search-emp.py"
)

# Goal code → BP ID mapping
GOAL_CODE_MAP = {
    "G-1":   "2000831992328945666",
    "G-1.1": "2000831992475746305",
    "G-1.2": "2000831992622546945",
    "G-1.3": "2000831992769347585",
    "G-2":   "2000831992916147202",
    "G-3":   "2000831993062947842",
}

# ─────────────────────────────────────────────────────────────────────────────
# Keyword tables
# ─────────────────────────────────────────────────────────────────────────────

ACTION_TYPE_KEYWORDS = {
    "销售类": ["销售", "签单", "回款", "转化", "客户", "市场", "渠道", "商机", "报价", "中标"],
    "产品类": ["产品", "功能", "迭代", "开发", "设计", "需求", "PRD", "方案", "需求分析"],
    "运营类": ["运营", "活动", "用户", "留存", "促活", "DAU", "MAU", "内容", "增长"],
    "技术类": ["研发", "系统", "架构", "数据", "算法", "模型", "平台", "安全", "IT"],
    "支撑类": ["培训", "赋能", "支撑", "协调", "对接", "流程", "体系", "规范", "资料包", "文档"],
    "流程类": ["周报", "双周会", "月度会", "复盘", "汇报", "总结", "检查", "例会", "会议"],
}

TITLE_DEPT_KEYWORDS = {
    "销售": ["销售", "客户", "市场", "渠道", "BD", "商务", "客户成功"],
    "产品": ["产品", "需求", "设计", "UX", "UI", "PD"],
    "技术": ["研发", "开发", "算法", "数据", "工程", "技术", "IT", "架构师"],
    "运营": ["运营", "用户", "内容", "活动", "增长"],
    "职能": ["HR", "行政", "财务", "法务", "人力", "HRBP"],
    "高层": ["总监", "总经理", "VP", "副总裁", "COO", "CTO", "CEO"],
    "AI":   ["AI", "人工智能", "大模型", "LLM", "模型"],
}

MEASURE_KEYWORD_TABLE = {
    "收入":     ["收入", "营收", "销售额", "回款", "GMV", "订单金额", "实收"],
    "毛利":     ["毛利", "毛利润", "毛利率"],
    "客户数":   ["客户", "客户数", "客户量", "用户数", "用户量"],
    "新增客户": ["新增客户", "新客户", "新增用户", "新用户"],
    "转化率":   ["转化率", "转化", "成功率", "通过率", "签单率"],
    "DAU":      ["DAU", "日活", "日活跃"],
    "MAU":      ["MAU", "月活", "月活跃"],
    "留存率":   ["留存率", "留存", "复购率"],
}

DIRECT_REVENUE_KW  = ["签单", "收入", "回款", "销售", "转化", "签约", "中标", "新增收入"]
SUPPORT_KW         = ["培训", "赋能", "支撑", "协同", "资料包", "方案", "文档", "培训赋能"]
PROCESS_KW         = ["周报", "双周会", "月度会", "复盘", "会议", "例会", "汇报", "总结"]
REVENUE_MEASURE_KW = ["收入", "回款", "签约", "转化", "销售", "实收"]

DIMENSION_PATTERN = r"(.{0,12}的|.{0,12}区域|.{0,12}产品线|.{0,12}业务线|.{0,12}部门|.{0,12}类型)"
UNIT_PATTERN      = r"(万元|亿元|万|个|人|%|％|美元|人民币)?"

MAINTENANCE_KW = ["维持", "保持", "不低于", "不高于", "稳定在", "守住", "控在"]
STABILITY_MEAS = ["故障率", "流失率", "投诉率", "事故", "宕机", "差错率", "响应时长"]


# ─────────────────────────────────────────────────────────────────────────────
# v2.3 新增：BP审计结果数据结构
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BPAuditResult:
    """对单个BP的完整审计结果（v2.3 按BP组织报告的核心数据结构）"""
    bp_id: str = ""
    bp_code: str = ""
    bp_name: str = ""
    upstream_kr: str = ""          # 承接上游KR编码，如 "G-1.1"
    owner: str = ""
    goal_assessment: dict = field(default_factory=dict)   # 目标对齐性
    kr_assessments: list = field(default_factory=list)    # KR层评估列表
    initiative_assessments: list = field(default_factory=list)  # 举措评估列表
    caliber_check: str = ""        # 口径一致性检查结论
    owner_match: str = ""          # owner匹配结论（如适用）
    problems: list = field(default_factory=list)           # 本BP问题列表


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', str(text)).strip()


def extract_numbers(text: str) -> List[float]:
    return [float(m) for m in re.findall(r'-?\d+\.?\d*', text)]


def call_cwork_search_emp(name: str, verbose: bool = False) -> Optional[Dict[str, str]]:
    """Call cwork-search-emp.py to get employee title and department."""
    if not CWORK_SEARCH_EMP_PATH.exists():
        return None
    cmd = [sys.executable, str(CWORK_SEARCH_EMP_PATH), "--name", name]
    if verbose:
        cmd.append("--verbose")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return None
        try:
            data = json.loads(result.stdout.strip().split("\n")[-1])
        except (json.JSONDecodeError, IndexError):
            out = result.stdout
            title_m = re.search(r'"title"\s*:\s*"([^"]+)"', out)
            dept_m  = re.search(r'"department"\s*:\s*"([^"]+)"', out)
            emp_m   = re.search(r'"empId"\s*:\s*"([^"]+)"', out)
            if title_m or dept_m:
                data = {
                    "title":      title_m.group(1) if title_m else "",
                    "department": dept_m.group(1)  if dept_m  else "",
                    "empId":      emp_m.group(1)   if emp_m   else "",
                }
            else:
                data = None
        if not data:
            return None
        inside = data.get("inside", [])
        if isinstance(inside, list) and inside:
            emp = inside[0]
            return {"title": emp.get("title", ""), "department": emp.get("department", ""),
                    "empId": emp.get("empId", "")}
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 1: 举措过期时间线
# ─────────────────────────────────────────────────────────────────────────────

def initiative_expiry_analysis(actions: List[dict], current_date: date = None) -> List[dict]:
    """Analyze action deadline expiry timeline."""
    if current_date is None:
        current_date = date.today()
    findings = []
    for action in actions:
        deadline_str = strip_html(action.get("deadline", ""))
        if not deadline_str:
            continue
        try:
            deadline = datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        delta_days = (current_date - deadline).days
        if delta_days >= 60:
            severity = "P0"
        elif delta_days >= 30:
            severity = "P1"
        elif delta_days >= 1:
            severity = "P2"
        else:
            severity = "PASS"
        findings.append({
            "code": action.get("fullLevelNumber", action.get("code", "N/A")),
            "name": strip_html(action.get("name", "")),
            "deadline": deadline_str[:10],
            "overdue_days": delta_days,
            "severity": severity,
        })
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 2: 责任人能力匹配
# ─────────────────────────────────────────────────────────────────────────────

def keyword_based_match(action_title: str, owner_title: str, owner_dept: str) -> Tuple[str, str]:
    """Keyword table fallback for owner-capability matching."""
    action_lower = action_title.lower()
    title_lower  = owner_title.lower()
    dept_lower   = owner_dept.lower()
    action_types = set()
    for category, keywords in ACTION_TYPE_KEYWORDS.items():
        if any(kw in action_lower for kw in keywords):
            action_types.add(category)
    capability_cats = set()
    for category, keywords in TITLE_DEPT_KEYWORDS.items():
        if any(kw in title_lower or kw in dept_lower for kw in keywords):
            capability_cats.add(category)
    if not action_types:
        return "WEAK", "无法识别举措类型，按弱匹配处理"
    if action_types & capability_cats:
        overlap = action_types & capability_cats
        return "MATCH", f"职能匹配：举措类型({list(overlap)[0]}) 在 title/部门中有对应关键词"
    return "MISMATCH", "举措类型与责任人title/部门无直接关联"


def owner_match_analysis(actions: List[dict], use_llm: bool = False) -> List[dict]:
    """Analyze owner capability matching using cwork-search-emp + keyword fallback."""
    findings = []
    for action in actions:
        code = action.get("fullLevelNumber", action.get("code", "N/A"))
        name = strip_html(action.get("name", ""))
        task_users = action.get("taskUsers", [])
        owners = []
        for tu in task_users:
            for emp in tu.get("empList", []):
                owners.append(emp.get("name", ""))
        if not owners:
            findings.append({"code": code, "owner": "未分配", "title": "", "department": "",
                             "severity": "P0", "reason": "举措未分配责任人", "confidence": "HIGH"})
            continue
        for owner_name in owners:
            emp_info = call_cwork_search_emp(owner_name, verbose=True)
            title, department = (emp_info.get("title", ""), emp_info.get("department", "")) if emp_info else ("", "")
            match_type, reason = keyword_based_match(name, title, department)
            severity = "P0" if match_type == "MISMATCH" else ("P1" if match_type == "WEAK" else "PASS")
            findings.append({"code": code, "owner": owner_name, "title": title,
                             "department": department, "severity": severity,
                             "reason": reason, "confidence": "HIGH" if emp_info else "MEDIUM"})
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 3: 口径一致性
# ─────────────────────────────────────────────────────────────────────────────

def regex_extract_measure(measure_text: str) -> dict:
    """Regex + keyword table fallback for measure word extraction."""
    measure_text = strip_html(measure_text)
    if not measure_text:
        return {"measure_word": "", "qualifier": "全量", "unit": "", "confidence": "LOW", "category": ""}
    unit_match = re.search(UNIT_PATTERN, measure_text)
    unit = unit_match.group(1) if unit_match else ""
    found_measure, found_category = "", ""
    for category, keywords in MEASURE_KEYWORD_TABLE.items():
        for kw in keywords:
            if kw in measure_text and len(kw) > len(found_measure):
                found_measure, found_category = kw, category
    dim_match = re.search(DIMENSION_PATTERN, measure_text)
    qualifier = dim_match.group(0).strip("的") if dim_match else "全量"
    return {"measure_word": found_measure, "qualifier": qualifier, "unit": unit,
            "confidence": "HIGH" if found_measure else "LOW", "category": found_category}


def check_caliber_consistency(parent_measure: dict, child_measure: dict) -> dict:
    """Check caliber consistency between parent and child measureStandard."""
    DIMENSION_CONFLICT = {
        ("收入", "客户数"), ("毛利", "客户数"), ("DAU", "收入"), ("转化率", "毛利"),
        ("收入", "新增客户"), ("毛利", "新增客户"),
    }
    MEASURE_ALIAS = {
        "新增客户": "客户数", "新客户": "客户数", "新增用户": "客户数",
        "客户": "客户数", "用户数": "客户数", "用户": "客户数",
    }
    p_word, c_word = parent_measure.get("measure_word", ""), child_measure.get("measure_word", "")
    p_qual, c_qual = parent_measure.get("qualifier", "全量"), child_measure.get("qualifier", "全量")
    # Normalize aliases for conflict detection
    p_norm = MEASURE_ALIAS.get(p_word, p_word)
    c_norm = MEASURE_ALIAS.get(c_word, c_word)
    if (p_norm, c_norm) in DIMENSION_CONFLICT and p_norm and c_norm:
        return {"consistent": False, "severity": "P0",
                "reason": f"量纲矛盾：父层='{p_word}' vs 子层='{c_word}'", "confidence": "HIGH"}
    if p_word == c_word and p_word:
        if p_qual not in ("全量", "") and c_qual in ("全量", ""):
            return {"consistent": False, "severity": "P0",
                    "reason": f"口径泛化：父层限定'{p_qual}{p_word}'，子层泛化为全量",
                    "confidence": parent_measure.get("confidence", "MEDIUM")}
        if p_qual != c_qual and p_qual not in ("全量", "") and c_qual not in ("全量", ""):
            return {"consistent": False, "severity": "P1",
                    "reason": f"口径部分差异：父层='{p_qual}{p_word}' vs 子层='{c_qual}{c_word}'",
                    "confidence": "MEDIUM"}
    if p_word == c_word:
        return {"consistent": True, "severity": "PASS", "reason": "口径一致", "confidence": "HIGH"}
    if not p_word or not c_word:
        return {"consistent": False, "severity": "P1",
                "reason": "无法判定口径一致性（度量词提取置信度低）", "confidence": "LOW"}
    return {"consistent": True, "severity": "PASS", "reason": "口径一致", "confidence": "MEDIUM"}


def caliber_consistency_analysis(parent_bp: dict, child_bps: List[dict]) -> List[dict]:
    """Analyze caliber consistency between G-layer KR measureStandard and downstream BP."""
    findings = []
    parent_measure = strip_html(parent_bp.get("measureStandard", ""))
    p_ext = regex_extract_measure(parent_measure)
    for child_bp in child_bps:
        code          = child_bp.get("fullLevelNumber", child_bp.get("code", "N/A"))
        child_measure = strip_html(child_bp.get("measureStandard", ""))
        child_name    = strip_html(child_bp.get("name", ""))
        c_ext         = regex_extract_measure(child_measure)
        result        = check_caliber_consistency(p_ext, c_ext)
        findings.append({
            "code": code, "child_name": child_name,
            "parent_measure": parent_measure, "child_measure": child_measure,
            "parent_keywords": f"{p_ext['qualifier']} {p_ext['measure_word']}".strip(),
            "child_keywords":  f"{c_ext['qualifier']} {c_ext['measure_word']}".strip(),
            "consistent": result["consistent"], "severity": result["severity"],
            "reason": result["reason"], "confidence": result["confidence"],
        })
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 4: 举措→收入因果链追溯
# ─────────────────────────────────────────────────────────────────────────────

def keyword_intent_classify(action_text: str, kr_measure: str) -> dict:
    """Keyword-based initiative intent classification (fallback when LLM unavailable)."""
    text_lower, measure_lower = action_text.lower(), kr_measure.lower()
    if any(kw in text_lower for kw in DIRECT_REVENUE_KW):
        surface_type = "直接创收类"
    elif any(kw in text_lower for kw in PROCESS_KW):
        surface_type = "流程类"
    elif any(kw in text_lower for kw in SUPPORT_KW):
        surface_type = "支撑类"
    else:
        surface_type = "未分类"
    is_revenue_measure = any(w in measure_lower for w in REVENUE_MEASURE_KW)
    if surface_type == "直接创收类":
        causal_chain, severity = "完整", "PASS"
    elif surface_type == "支撑类" and is_revenue_measure:
        causal_chain, severity = "断裂", "P0"
    elif surface_type == "流程类":
        causal_chain, severity = "间接", "P1"
    elif surface_type == "支撑类":
        causal_chain, severity = "间接", "P1"
    else:
        causal_chain, severity = "无法判定", "P1"
    return {"surface_type": surface_type, "causal_chain": causal_chain,
            "severity": severity, "confidence": "LOW",
            "disclaimer": "本判定基于关键词匹配，误判率较高，建议人工复核"}


def initiative_income_chain_analysis(actions: List[dict], kr_measure: str,
                                     use_llm: bool = False) -> List[dict]:
    """Analyze whether each action can trace a causal chain to income."""
    findings = []
    for action in actions:
        code = action.get("fullLevelNumber", action.get("code", "N/A"))
        name = strip_html(action.get("name", ""))
        desc = strip_html(action.get("description", ""))
        text = f"{name} {desc}"
        result = keyword_intent_classify(text, kr_measure)
        if result["severity"] == "P0":
            reason = f"举措类型为'{result['surface_type']}'，与收入指标间因果链断裂"
        elif result["severity"] == "P1":
            reason = f"举措类型为'{result['surface_type']}'，因果链为间接传导"
        else:
            reason = f"举措类型为'{result['surface_type']}'，因果链完整"
        findings.append({"code": code, "name": name, "surface_type": result["surface_type"],
                          "causal_chain": result["causal_chain"], "severity": result["severity"],
                          "reason": reason, "confidence": result["confidence"],
                          "disclaimer": result.get("disclaimer", "")})
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 5: 个人BP核对 (TBD placeholder)
# ─────────────────────────────────────────────────────────────────────────────

def personal_bp_verification(owner_name: str, action_content: str) -> dict:
    """TBD placeholder — personal BP verification. BP system API not yet confirmed."""
    return {"owner": owner_name, "action": action_content, "status": "TBD",
            "severity": "TBD",
            "reason": "个人BP核对功能在 v2.2 中标注为 TBD，待 BP 系统 API 就绪后实现",
            "confidence": "N/A"}


# ─────────────────────────────────────────────────────────────────────────────
# Deep Analysis 6: 目标设计有效性
# ─────────────────────────────────────────────────────────────────────────────

def is_maintenance_objective(kr_data: dict) -> bool:
    """判断 measure 是否为维持型目标（目标是保持当前水平，不追求增长）。"""
    measure_text = strip_html(kr_data.get("measureStandard", ""))
    if any(kw in measure_text for kw in MAINTENANCE_KW):
        return True
    if any(m in measure_text for m in STABILITY_MEAS):
        numbers = extract_numbers(measure_text)
        if len(numbers) >= 2:
            baseline, target = numbers[0], numbers[1]
            if baseline != 0 and abs(target - baseline) / abs(baseline) < 0.01:
                return True
        elif len(numbers) == 1:
            return True
    return False


def target_design_validity(kr_data: dict) -> dict:
    """Check whether a KR's target design is valid."""
    measure_text = strip_html(kr_data.get("measureStandard", ""))
    numbers = extract_numbers(measure_text)
    is_maintenance = is_maintenance_objective(kr_data)
    if not numbers:
        return {"valid": False, "severity": "P1", "detail": "无法提取目标值",
                "is_maintenance": is_maintenance, "confidence": "LOW"}
    baseline, target = (numbers[0], numbers[1]) if len(numbers) >= 2 else (0, numbers[0])
    change_pct = (target - baseline) / abs(baseline) * 100 if baseline != 0 else (100 if target > 0 else 0)
    is_negative_metric = any(m in measure_text for m in STABILITY_MEAS)
    if is_maintenance:
        return {"valid": True, "severity": "PASS",
                "detail": f"维持型目标：目标值={target}，变化幅度={change_pct:.1f}%",
                "is_maintenance": True, "confidence": "HIGH"}
    if is_negative_metric and target > baseline:
        return {"valid": False, "severity": "P0",
                "detail": f"指标反向：{measure_text} 应降低但目标设为{target}（当前{baseline}）",
                "is_maintenance": False, "confidence": "HIGH"}
    if change_pct <= 0:
        return {"valid": False, "severity": "P0",
                "detail": f"目标值≤基准值（目标={target}，基准={baseline}，变化={change_pct:.1f}%），非维持型目标设计失效",
                "is_maintenance": False, "confidence": "HIGH"}
    if change_pct > 500:
        return {"valid": False, "severity": "P1",
                "detail": f"目标增长{change_pct:.0f}% 过于激进，建议分阶段设定",
                "is_maintenance": False, "confidence": "HIGH"}
    return {"valid": True, "severity": "PASS",
            "detail": f"目标设计合理：目标={target}，增长={change_pct:.1f}%",
            "is_maintenance": False, "confidence": "HIGH"}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def collect_child_bps(bp_data: dict) -> List[dict]:
    child_bps = []
    for kr in bp_data.get("keyResults", []):
        for child in kr.get("downTaskList", []):
            child_bps.append(child)
    return child_bps


def collect_upward_tasks(bp_data: dict) -> List[dict]:
    upward = bp_data.get("upwardTaskList", [])
    for task in upward:
        task["_bp_code"] = bp_data.get("fullLevelNumber", "")
    return upward


# ─────────────────────────────────────────────────────────────────────────────
# Main Evaluator Class
# ─────────────────────────────────────────────────────────────────────────────

class BPEvaluatorV2:
    def __init__(self, enable_deep_analysis: bool = True, use_llm: bool = False,
                 severity_threshold: str = "P2"):
        self.client          = BPClient()
        self.problems        = []
        self.deep_findings   = []
        self.timestamp       = datetime.now()
        self.enable_deep     = enable_deep_analysis
        self.use_llm         = use_llm
        self.severity_thresh = severity_threshold
        self._sev_order      = {"P0": 0, "P1": 1, "P2": 2, "PASS": 3, "TBD": 3}

    def _sev_score(self, s: str) -> int:
        return self._sev_order.get(s, 3)

    def _filter_sev(self, findings: List[dict]) -> List[dict]:
        thresh = self._sev_score(self.severity_thresh)
        return [f for f in findings if self._sev_score(f.get("severity", "PASS")) <= thresh]

    def strip_html(self, text: str) -> str:
        return strip_html(text)

    def evaluate_objective(self, bp_data: dict) -> List[dict]:
        problems = []
        name = strip_html(bp_data.get("name", ""))
        if not name or len(name) < 5:
            problems.append({"level": "P0", "dimension": "objective-clarity",
                              "item": bp_data.get("goalCode", "N/A"),
                              "problem": "Objective description empty or too short",
                              "suggestion": "Provide clear objective description"})
        measure = strip_html(bp_data.get("measureStandard", ""))
        if not measure:
            problems.append({"level": "P0", "dimension": "objective-measurability",
                             "item": bp_data.get("goalCode", "N/A"),
                             "problem": "No measure standard",
                             "suggestion": "Add quantifiable measure standard"})
        upward = bp_data.get("upwardTaskList", [])
        if not upward:
            problems.append({"level": "P1", "dimension": "objective-alignment",
                             "item": bp_data.get("goalCode", "N/A"),
                             "problem": "No upstream dependency",
                             "suggestion": "Confirm alignment with upper-level strategy"})
        return problems

    def evaluate_kr(self, kr_data: dict, bp_code: str) -> List[dict]:
        problems = []
        kr_code = kr_data.get("fullLevelNumber", "N/A")
        status   = kr_data.get("statusDesc", "unknown")
        measure  = strip_html(kr_data.get("measureStandard", ""))
        if not measure:
            problems.append({"level": "P0", "dimension": "kr-smart", "item": kr_code,
                             "problem": "KR has no measure standard",
                             "suggestion": "Add quantifiable measure standard (SMART)"})
        elif len(measure) < 10:
            problems.append({"level": "P1", "dimension": "kr-smart", "item": kr_code,
                             "problem": f"Measure too brief: {measure}",
                             "suggestion": "Detail with specific values and timeframes"})
        task_users = kr_data.get("taskUsers", [])
        owners = [u["name"] for emp in task_users for u in emp.get("empList", [])]
        if not owners:
            problems.append({"level": "P0", "dimension": "kr-owner-match", "item": kr_code,
                             "problem": "KR has no owner",
                             "suggestion": "Assign a clear owner to this KR"})
        action_count = kr_data.get("actionCount", 0)
        child_bps    = kr_data.get("downTaskList", [])
        if not (action_count > 0 or child_bps):
            problems.append({"level": "P0", "dimension": "kr-support", "item": kr_code,
                             "problem": "KR has neither actions nor child BP - cannot execute",
                             "suggestion": "Add actions or establish downstream BP"})
        if status == "未启动":
            problems.append({"level": "P1", "dimension": "kr-status", "item": kr_code,
                             "problem": "KR status is not started",
                             "suggestion": "Confirm if KR needs activation"})
        # §3.6 目标设计有效性
        if self.enable_deep and measure:
            validity = target_design_validity(kr_data)
            if validity["severity"] not in ("PASS", "TBD"):
                self.deep_findings.append({
                    "type": "target-design-validity", "code": kr_code,
                    "severity": validity["severity"],
                    "title": f"KR目标设计{'无效' if not validity['valid'] else '有效'}",
                    "detail": validity["detail"],
                    "is_maintenance": validity.get("is_maintenance", False),
                    "confidence": validity.get("confidence", "MEDIUM"),
                })
        return problems

    def parse_date_range(self, date_range_str: str) -> Tuple[Optional[str], Optional[str]]:
        """从'2026-01-01 ~ 2026-01-30'格式提取开始和截止日期"""
        if not date_range_str:
            return None, None
        match = re.search(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})', date_range_str)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def get_all_initiatives_downstream(self, bp_id: str, visited: set = None) -> List[dict]:
        """获取下游所有举措详情（递归遍历所有下游BP的KR下的举措）"""
        if visited is None:
            visited = set()
        if bp_id in visited:
            return []
        visited.add(bp_id)

        all_initiatives = []
        bp_result = self.client.get_goal_detail(bp_id)
        if bp_result.get('resultCode') != 1:
            return []

        bp_data = bp_result.get('data', {})
        bp_code = bp_data.get('fullLevelNumber', '')
        key_results = bp_data.get('keyResults', [])

        for kr in key_results:
            kr_id = kr.get('id')
            kr_detail = self.client.get_key_result_detail(kr_id)
            kr_data = kr_detail.get('data', {})
            # actions在kr_data里是嵌套的
            actions = kr_data.get('actions', [])
            for action in actions:
                action_copy = dict(action)
                action_copy['kr_id'] = kr_id
                action_copy['kr_name'] = self.strip_html(kr_data.get('name', ''))
                action_copy['bp_id'] = bp_id
                action_copy['bp_code'] = bp_code
                all_initiatives.append(action_copy)

            # 递归获取下游BP
            downstream = kr.get('downTaskList') or []
            for child in downstream:
                child_id = child.get('id')
                if child_id:
                    child_initiatives = self.get_all_initiatives_downstream(child_id, visited)
                    all_initiatives.extend(child_initiatives)

        return all_initiatives

    def analyze_initiative_expiry(self, initiatives: List[dict]) -> List[dict]:
        """分析举措过期情况，计算过期天数和严重度"""
        today = datetime.now().date()
        results = []

        for init in initiatives:
            plan_start, plan_end = self.parse_date_range(init.get('planDateRange', ''))
            if not plan_end:
                continue

            try:
                end_date = datetime.strptime(plan_end, '%Y-%m-%d').date()
                days_diff = (today - end_date).days
                status = init.get('statusDesc', '未知')
                name = self.strip_html(init.get('name', ''))
                owners = [u['name'] for emp in init.get('taskUsers', [])
                        for u in emp.get('empList', [])]
                kr_name = init.get('kr_name', '')
                code = init.get('fullLevelNumber', init.get('bp_code', 'N/A'))

                if days_diff > 0:  # 过期
                    if days_diff >= 60:
                        severity = 'P0'
                    elif days_diff >= 30:
                        severity = 'P1'
                    else:
                        severity = 'P1'
                else:
                    severity = 'PASS'

                results.append({
                    'code': code,
                    'name': name,
                    'owners': ', '.join(owners) if owners else '未指定',
                    'kr_name': kr_name,
                    'plan_start': plan_start,
                    'plan_end': plan_end,
                    'status': status,
                    'days_overdue': days_diff if days_diff > 0 else 0,
                    'severity': severity
                })
            except Exception:
                continue

        return results

    # ── v2.3: 单个BP完整审计 ────────────────────────────────────────────────

    def check_goal_alignment(self, bp_data: dict, upstream_kr: str) -> dict:
        """检查BP目标与上游KR的对齐性"""
        bp_name = self.strip_html(bp_data.get("name", ""))
        bp_measure = self.strip_html(bp_data.get("measureStandard", ""))
        upstream_measure = upstream_kr  # upstream_kr是KR的fullLevelNumber，此处简化处理
        upward = bp_data.get("upwardTaskList", [])
        if not upward:
            return {"aligned": False, "conclusion": "WARN-无上游承接",
                    "reason": "该BP无upwardTaskList，无法确认上游KR承接关系"}
        # 简单判断：BP名称/度量词是否与上游KR存在语义关联（关键词匹配）
        shared_kw = []
        for kw in DIRECT_REVENUE_KW + REVENUE_MEASURE_KW:
            if kw in bp_measure or kw in bp_name:
                shared_kw.append(kw)
        if shared_kw:
            return {"aligned": True, "conclusion": "PASS",
                    "reason": f"度量词包含{shared_kw[0]}，与上游对齐"}
        if bp_measure:
            return {"aligned": True, "conclusion": "PASS",
                    "reason": "有度量标准，上游承接明确"}
        return {"aligned": False, "conclusion": "WARN-无度量标准",
                "reason": "该BP无度量标准"}

    def check_owner_for_cost_management(self, bp_data: dict) -> str:
        """检查成本管理类BP的owner是否匹配"""
        task_users = bp_data.get("taskUsers", [])
        owners = [u["name"] for emp in task_users for u in emp.get("empList", [])]
        if not owners:
            return "WARN-未分配owner"
        for owner_name in owners:
            emp_info = call_cwork_search_emp(owner_name, verbose=True)
            title = emp_info.get("title", "") if emp_info else ""
            dept = emp_info.get("department", "") if emp_info else ""
            if any(kw in title or kw in dept for kw in ["财务", "成本", "经营", "管理", "总监", "总经理"]):
                return f"PASS-owner={owner_name}（{title}）"
        return f"WARN-owner={owners[0]}，title/部门中未发现成本管理相关关键词"

    def collect_problems(self, audit: BPAuditResult) -> list:
        """从审计结果中收集问题"""
        problems = []
        for kr in audit.kr_assessments:
            for p in kr.get("problems", []):
                problems.append(p)
        for init in audit.initiative_assessments:
            if init.get("severity", "PASS") != "PASS":
                problems.append({
                    "code": init.get("code", ""),
                    "severity": init.get("severity", "P1"),
                    "description": f"举措已过期{init.get('days_overdue', 0)}天",
                    "suggestion": f"截止日期={init.get('plan_end', 'N/A')}，责任人={init.get('owners', '')}"
                })
        if audit.goal_assessment.get("conclusion", "").startswith("WARN"):
            problems.append({
                "code": audit.bp_code,
                "severity": "P1",
                "description": f"目标对齐性：{audit.goal_assessment.get('conclusion', '')}",
                "suggestion": audit.goal_assessment.get("reason", "")
            })
        return problems

    def assess_krs(self, key_results: list) -> list:
        """对KR列表做维度评估"""
        assessments = []
        for kr in key_results:
            kr_code = kr.get("fullLevelNumber", "N/A")
            kr_name = self.strip_html(kr.get("name", ""))
            measure = self.strip_html(kr.get("measureStandard", ""))
            status = kr.get("statusDesc", "unknown")
            task_users = kr.get("taskUsers", [])
            owners = [u["name"] for emp in task_users for u in emp.get("empList", [])]
            downstream = kr.get("downTaskList", []) or []

            # 5维度评估
            dims = []
            # 维度1：SMART
            if measure and len(measure) >= 10:
                dims.append({"dimension": "SMART", "verdict": "PASS", "actual": measure[:30]})
            elif measure:
                dims.append({"dimension": "SMART", "verdict": "P1", "actual": f"度量过短:{measure[:20]}"})
            else:
                dims.append({"dimension": "SMART", "verdict": "P0", "actual": "无度量标准"})

            # 维度2：Owner
            if owners:
                dims.append({"dimension": "Owner", "verdict": "PASS", "actual": ",".join(owners[:2])})
            else:
                dims.append({"dimension": "Owner", "verdict": "P0", "actual": "无责任人"})

            # 维度3：支撑（举措/下游BP）
            if downstream or kr.get("actionCount", 0) > 0:
                dims.append({"dimension": "支撑", "verdict": "PASS",
                             "actual": f"{len(downstream)}下游BP"})
            else:
                dims.append({"dimension": "支撑", "verdict": "P0", "actual": "无下游BP/举措"})

            # 维度4：目标有效性
            if self.enable_deep and measure:
                validity = target_design_validity(kr)
                dims.append({"dimension": "目标有效性",
                             "verdict": validity.get("severity", "PASS"),
                             "actual": validity.get("detail", "")[:40]})
            else:
                dims.append({"dimension": "目标有效性", "verdict": "N/A", "actual": "深度分析未开启"})

            # 维度5：状态
            dims.append({"dimension": "状态", "verdict": "P1" if status == "未启动" else "PASS",
                         "actual": status})

            assessments.append({
                "code": kr_code,
                "name": kr_name,
                "dimensions": dims,
            })
        return assessments

    def audit_single_bp(self, bp_id: str, upstream_kr: str) -> BPAuditResult:
        """对单个BP做完整审计（v2.3核心新增方法）"""
        result = BPAuditResult()
        result.bp_id = bp_id
        result.upstream_kr = upstream_kr

        # 获取BP详情
        bp_detail = self.client.get_goal_detail(bp_id)
        if bp_detail.get("resultCode") != 1:
            result.problems.append({
                "code": bp_id, "severity": "P0",
                "description": f"无法获取BP详情: {bp_detail.get('resultMsg', 'unknown')}",
                "suggestion": "检查BP ID是否正确"
            })
            return result

        bp_data = bp_detail.get("data", {})
        result.bp_code = bp_data.get("fullLevelNumber", "N/A")
        result.bp_name = self.strip_html(bp_data.get("name", ""))

        # Owner
        task_users = bp_data.get("taskUsers", [])
        result.owner = ", ".join(
            u["name"] for emp in task_users for u in emp.get("empList", [])
        ) or "未分配"

        # 目标对齐性
        result.goal_assessment = self.check_goal_alignment(bp_data, upstream_kr)

        # KR层评估
        result.kr_assessments = self.assess_krs(bp_data.get("keyResults", []))

        # 举措评估（过期分析）
        initiatives = self.collect_initiatives_from_bp(bp_data)
        result.initiative_assessments = self.analyze_initiative_expiry(initiatives)

        # 口径一致性（如果上游KR有度量标准）
        kr_measure_text = upstream_kr  # upstream_kr为fullLevelNumber，此处传入度量文本供检查
        if kr_measure_text:
            result.caliber_check = self._check_caliber_for_bp(bp_data, kr_measure_text)

        # owner匹配（成本管理/开发类BP）
        if "成本效益" in result.bp_name or "开发" in result.bp_name:
            result.owner_match = self.check_owner_for_cost_management(bp_data)

        # 收集问题
        result.problems = self.collect_problems(result)

        return result

    def _check_caliber_for_bp(self, bp_data: dict, upstream_measure_text: str) -> str:
        """检查BP与上游KR的口径一致性（返回文字结论）"""
        p_ext = regex_extract_measure(upstream_measure_text)
        c_ext = regex_extract_measure(self.strip_html(bp_data.get("measureStandard", "")))
        check = check_caliber_consistency(p_ext, c_ext)
        if check.get("consistent", True):
            return "PASS-口径一致"
        return f"{check.get('severity','P1')}-{check.get('reason','')}"

    def collect_initiatives_from_bp(self, bp_data: dict) -> list:
        """从BP数据中收集直接关联的举措（不递归下游）"""
        initiatives = []
        for kr in bp_data.get("keyResults", []):
            kr_id = kr.get("id")
            if not kr_id:
                continue
            kr_detail = self.client.get_key_result_detail(kr_id)
            kr_data = kr_detail.get("data", {})
            for action in kr_data.get("actions", []):
                action_copy = dict(action)
                action_copy["kr_id"] = kr_id
                action_copy["kr_name"] = self.strip_html(kr_data.get("name", ""))
                action_copy["bp_code"] = bp_data.get("fullLevelNumber", "")
                initiatives.append(action_copy)
        return initiatives

    def evaluate_recursive(self, bp_id: str, depth: str = "layer1",
                           visited: set = None) -> Tuple[List[dict], dict, List[dict], List[BPAuditResult]]:
        if visited is None:
            visited = set()
        if bp_id in visited:
            return [], {}, []
        visited.add(bp_id)
        all_problems, child_map, all_actions = [], {}, []
        bp_result = self.client.get_goal_detail(bp_id)
        if bp_result.get("resultCode") != 1:
            all_problems.append({"level": "P0", "dimension": "system", "item": bp_id,
                                  "problem": f"Cannot fetch BP: {bp_result.get('resultMsg', 'unknown')}",
                                  "suggestion": "Verify BP ID is correct"})
            return all_problems, child_map, all_actions, []
        bp_data = bp_result.get("data", {})
        bp_code = bp_data.get("fullLevelNumber", "N/A")
        all_problems.extend(self.evaluate_objective(bp_data))
        all_actions.extend(collect_upward_tasks(bp_data))
        key_results = bp_data.get("keyResults", [])

        # v2.2: 收集所有下游举措用于过期分析
        all_initiatives = []

        for kr in key_results:
            kr_code = kr.get("fullLevelNumber", "N/A")
            all_problems.extend(self.evaluate_kr(kr, bp_code))
            downstream = kr.get("downTaskList") or []
            if downstream:
                child_map[kr_code] = [
                    {"id": d.get("id"), "name": d.get("name", ""),
                     "group": d.get("groupInfo", {}).get("name", "")}
                    for d in downstream
                ]
                # §3.3 Caliber consistency
                if self.enable_deep:
                    kr_measure = strip_html(kr.get("measureStandard", ""))
                    if kr_measure:
                        for child_bp_entry in downstream:
                            child_id = child_bp_entry.get("id")
                            if child_id:
                                child_result = self.client.get_goal_detail(child_id)
                                if child_result.get("resultCode") == 1:
                                    child_bp_data = child_result.get("data", {})
                                    for cf in caliber_consistency_analysis(
                                            {"measureStandard": kr.get("measureStandard", "")},
                                            [child_bp_data]):
                                        if cf["severity"] != "PASS":
                                            self.deep_findings.append({
                                                "type": "caliber-consistency",
                                                "code": cf["code"], "severity": cf["severity"],
                                                "title": "口径不一致", "detail": cf["reason"],
                                                "parent_measure": cf["parent_measure"],
                                                "child_measure": cf["child_measure"],
                                                "confidence": cf["confidence"],
                                            })
            if depth == "full":
                for child_bp_entry in downstream:
                    child_id = child_bp_entry.get("id")
                    if child_id:
                        cp, cm, ca = self.evaluate_recursive(child_id, depth, visited)
                        all_problems.extend(cp)
                        child_map.update(cm)
                        all_actions.extend(ca)

        # v2.2: 递归收集下游所有举措详情
        if self.enable_deep:
            downstream_initiatives = self.get_all_initiatives_downstream(bp_id, set())
            all_initiatives.extend(downstream_initiatives)
            # 分析举措过期情况
            if all_initiatives:
                expiry_results = self.analyze_initiative_expiry(all_initiatives)
                for er in expiry_results:
                    if er['severity'] != 'PASS':
                        self.deep_findings.append({
                            'type': 'initiative-expiry-v2',
                            'code': er['code'],
                            'name': er['name'],
                            'severity': er['severity'],
                            'title': f"举措已过期{er['days_overdue']}天" if er['days_overdue'] > 0 else f"举措正常",
                            'detail': f"截止={er['plan_end']}，责任人={er['owners']}，KR={er['kr_name']}，状态={er['status']}",
                            'days_overdue': er['days_overdue'],
                            'plan_end': er['plan_end'],
                            'owners': er['owners'],
                            'kr_name': er['kr_name'],
                            'status': er['status'],
                            'confidence': 'HIGH',
                        })

        # v2.3: 为每个下游BP生成完整审计结果
        bp_audit_results = []
        for kr in key_results:
            kr_full_number = kr.get("fullLevelNumber", "")
            downstream = kr.get("downTaskList") or []
            for child in downstream:
                child_id = child.get("id")
                if child_id:
                    audit = self.audit_single_bp(child_id, kr_full_number)
                    bp_audit_results.append(audit)

        return all_problems, child_map, all_actions, bp_audit_results

    def run_deep_analysis(self, all_actions: List[dict], bp_data: dict) -> List[dict]:
        """Run all deep analysis modules (§3.1–3.6)."""
        if not self.enable_deep:
            return []
        current_date = date.today()
        all_findings = list(self.deep_findings)

        # §3.1 举措过期时间线
        for f in initiative_expiry_analysis(all_actions, current_date):
            if f["severity"] != "PASS":
                title = (f"举措已过期{abs(f['overdue_days'])}天" if f["overdue_days"] > 0
                         else f"举措即将到期（剩余{-f['overdue_days']}天）")
                detail = (f"截止日期={f['deadline']}，已过期{f['overdue_days']}天"
                          if f["overdue_days"] > 0 else f"截止日期={f['deadline']}，剩余{-f['overdue_days']}天")
                all_findings.append({"type": "initiative-expiry", "code": f["code"],
                                     "name": f["name"], "severity": f["severity"],
                                     "title": title, "detail": detail,
                                     "overdue_days": f["overdue_days"], "deadline": f["deadline"],
                                     "confidence": "HIGH"})

        # §3.2 责任人能力匹配
        for f in owner_match_analysis(all_actions, use_llm=self.use_llm):
            if f["severity"] != "PASS":
                all_findings.append({"type": "owner-capability", "code": f["code"],
                                     "severity": f["severity"],
                                     "title": f"责任人能力{'不匹配' if f['severity'] == 'P0' else '弱关联'}",
                                     "detail": f"责任人={f['owner']}，职位={f['title']}，部门={f['department']}；{f['reason']}",
                                     "owner": f["owner"], "title": f["title"],
                                     "department": f["department"], "reason": f["reason"],
                                     "confidence": f["confidence"]})

        # §3.4 因果链追溯
        for kr in bp_data.get("keyResults", []):
            kr_measure = strip_html(kr.get("measureStandard", ""))
            if not kr_measure:
                continue
            for f in initiative_income_chain_analysis(all_actions, kr_measure, use_llm=self.use_llm):
                if f["severity"] != "PASS":
                    all_findings.append({"type": "causal-chain", "code": f["code"],
                                         "name": f["name"], "severity": f["severity"],
                                         "title": f"因果链{'断裂' if f['severity'] == 'P0' else '间接'}",
                                         "detail": f["reason"], "surface_type": f["surface_type"],
                                         "causal_chain": f["causal_chain"],
                                         "confidence": f["confidence"],
                                         "disclaimer": f.get("disclaimer", "")})

        # §3.5 TBD placeholder — log to findings
        for action in all_actions:
            owners = []
            for tu in action.get("taskUsers", []):
                for emp in tu.get("empList", []):
                    owners.append(emp.get("name", ""))
            for owner_name in owners:
                tbd = personal_bp_verification(owner_name, strip_html(action.get("name", "")))
                # Don't add TBD as findings (not yet implemented)
                _ = tbd  # reserved for future version

        return all_findings

    # ── Report generation ───────────────────────────────────────────────────

    def generate_report_v2(self, bp_id: str, goal_code: str,
                           problems: List[dict], deep_findings: List[dict],
                           child_map: dict, bp_data: dict = None) -> str:
        """Generate v2.2 format report."""
        p0 = [p for p in problems if p.get("level") == "P0"]
        p1 = [p for p in problems if p.get("level") == "P1"]
        p2 = [p for p in problems if p.get("level") == "P2"]

        filtered = self._filter_sev(deep_findings)
        df_p0 = [f for f in filtered if f.get("severity") == "P0"]
        df_p1 = [f for f in filtered if f.get("severity") == "P1"]
        df_p2 = [f for f in filtered if f.get("severity") == "P2"]

        # Top 3 most urgent problems
        urgent = sorted(filtered, key=lambda x: self._sev_score(x.get("severity", "PASS")))
        top3 = urgent[:3]

        lines = [
            "# BP 诊断报告 v2.2",
            "",
            f"**审计对象：** {goal_code or bp_id}",
            f"**审计时间：** {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"**深度分析：** {'开启' if self.enable_deep else '关闭'}",
            "",
            "---",
            "",
            "## 执行摘要",
            "",
            f"- **审计范围：** {goal_code or bp_id}",
            f"- **P0（立即执行）：** {len(p0) + len(df_p0)} 个",
            f"- **P1（本周完成）：** {len(p1) + len(df_p1)} 个",
            f"- **P2（本月完成）：** {len(p2) + len(df_p2)} 个",
            "",
            "### 最紧急3个问题",
            "",
        ]
        for i, f in enumerate(top3, 1):
            lines.append(f"{i}. **[{f.get('severity')}]** {f.get('title', f.get('problem',''))}")
            lines.append(f"   - 编码：{f.get('code', 'N/A')} | {f.get('detail', f.get('problem',''))[:60]}")

        lines.extend(["", "---", "", "## 深度发现", ""])

        # §3.1 举措过期时间线 (v2.2 downstream initiatives)
        expiry_v2 = [f for f in filtered if f.get("type") == "initiative-expiry-v2"]
        if expiry_v2:
            lines.extend(["", "### 1. 举措过期时间线（下游BP）", ""])
            lines.append(f"| 编码 | 举措名称 | KR | 责任人 | 截止日期 | 过期天数 | 严重度 |")
            lines.append("|------|----------|----|--------|----------|---------|--------|")
            for f in expiry_v2:
                lines.append(f"| {f.get('code','N/A')} | {f.get('name','')[:18]} | "
                             f"{f.get('kr_name','')[:12]} | {f.get('owners','')[:10]} | "
                             f"{f.get('plan_end','')} | {f.get('days_overdue','')}天 | {f.get('severity')} |")

        # §3.2 责任人能力匹配
        owner = [f for f in filtered if f.get("type") == "owner-capability"]
        if owner:
            lines.extend(["", "### 2. 责任人能力匹配", ""])
            lines.append(f"| 编码 | 责任人 | 职位 | 部门 | 严重度 | 判断依据 |")
            lines.append("|------|--------|------|------|--------|----------|")
            for f in owner:
                lines.append(f"| {f.get('code','N/A')} | {f.get('owner','')} | "
                             f"{f.get('title','')[:15]} | {f.get('department','')[:15]} | "
                             f"{f.get('severity')} | {f.get('reason','')[:30]} |")

        # §3.3 口径一致性
        caliber = [f for f in filtered if f.get("type") == "caliber-consistency"]
        if caliber:
            lines.extend(["", "### 3. 口径一致性", ""])
            lines.append(f"| 编码 | 子BP名称 | G层口径 | A层口径 | 严重度 | 原因 |")
            lines.append("|------|----------|---------|---------|--------|----|")
            for f in caliber:
                lines.append(f"| {f.get('code','N/A')} | {f.get('child_measure','')[:15]} | "
                             f"{f.get('parent_measure','')[:20]} | "
                             f"{f.get('child_measure','')[:20]} | {f.get('severity')} | "
                             f"{f.get('detail','')[:25]} |")

        # §3.4 因果链追溯
        causal = [f for f in filtered if f.get("type") == "causal-chain"]
        if causal:
            lines.extend(["", "### 4. 因果链追溯", ""])
            lines.append(f"| 编码 | 举措名称 | 表面类型 | 因果链 | 严重度 | 判断依据 |")
            lines.append("|------|----------|---------|--------|--------|----------|")
            for f in causal:
                lines.append(f"| {f.get('code','N/A')} | {f.get('name','')[:15]} | "
                             f"{f.get('surface_type','')} | {f.get('causal_chain','')} | "
                             f"{f.get('severity')} | {f.get('detail','')[:25]} |")

        # §3.6 目标设计有效性
        target_validity = [f for f in filtered if f.get("type") == "target-design-validity"]
        if target_validity:
            lines.extend(["", "### 5. 目标设计有效性", ""])
            lines.append(f"| 编码 | 严重度 | 结论 | 详情 |")
            lines.append("|------|--------|------|------|")
            for f in target_validity:
                lines.append(f"| {f.get('code','N/A')} | {f.get('severity')} | "
                             f"{f.get('title','')} | {f.get('detail','')[:40]} |")

        # §3.5 TBD
        lines.extend(["", "### 6. 个人BP核对", "",
                      "**状态：TBD** — 个人BP核对功能在 v2.2 中标注为 TBD，待 BP 系统 API 就绪后实现。", ""])

        # Problem summary table
        lines.extend(["---", "", "## 问题汇总表", ""])
        lines.append("| 编码 | 问题 | 严重度 | 整改建议 | 责任人 |")
        lines.append("|------|------|--------|----------|--------|")
        for f in filtered:
            code = f.get("code", "N/A")
            problem = f.get("title", f.get("detail", ""))[:40]
            severity = f.get("severity", "")
            owner = f.get("owner", f.get("department", ""))
            suggestion = f.get("reason", f.get("detail", ""))[:30]
            lines.append(f"| {code} | {problem} | {severity} | {suggestion} | {owner} |")

        for p in problems:
            lines.append(f"| {p.get('item','N/A')} | {p.get('problem','')[:40]} | "
                         f"{p.get('level','')} | {p.get('suggestion','')[:30]} | |")

        # Remediation roadmap
        lines.extend(["---", "", "## 整改路线图", ""])
        lines.append("### P0（立即执行）")
        for f in df_p0:
            lines.append(f"- [{f.get('code','N/A')}] {f.get('title','')} — 责任人：{f.get('owner','')}")
        for p in p0:
            lines.append(f"- [{p.get('item','N/A')}] {p.get('problem','')[:50]}")
        lines.append("")
        lines.append("### P1（本周完成）")
        for f in df_p1:
            lines.append(f"- [{f.get('code','N/A')}] {f.get('title','')}")
        for p in p1:
            lines.append(f"- [{p.get('item','N/A')}] {p.get('problem','')[:50]}")
        lines.append("")
        lines.append("### P2（本月完成）")
        for f in df_p2:
            lines.append(f"- [{f.get('code','N/A')}] {f.get('title','')}")
        for p in p2:
            lines.append(f"- [{p.get('item','N/A')}] {p.get('problem','')[:50]}")

        lines.extend(["", "---",
                      f"*Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | v2.2 deep analysis={self.enable_deep}*"])

        return "\n".join(lines)

    def generate_report_legacy(self, bp_id: str, goal_code: str,
                               problems: List[dict], child_map: dict, depth: str) -> str:
        """Generate legacy v1.0 format report."""
        p0 = [p for p in problems if p["level"] == "P0"]
        p1 = [p for p in problems if p["level"] == "P1"]
        p2 = [p for p in problems if p["level"] == "P2"]
        lines = [
            "# BP Evaluation Report", "",
            f"**BP ID:** {bp_id}",
            f"**Goal Code:** {goal_code}",
            f"**Evaluation Time:** {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"**Depth:** {'Full' if depth == 'full' else 'Layer1 Only'}",
            "", "---", "",
            "## Problem Summary", "",
            f"- **P0 (Immediate):** {len(p0)}",
            f"- **P1 (Optimize):** {len(p1)}",
            f"- **P2 (Iterate):** {len(p2)}", "",
        ]
        if p0:
            lines.extend(["", "### P0 Issues", ""])
            for p in p0:
                lines.extend([f"- **{p['dimension']}** | {p['item']}",
                              f"  - Problem: {p['problem']}",
                              f"  - Suggestion: {p['suggestion']}", ""])
        if p1:
            lines.extend(["", "### P1 Issues", ""])
            for p in p1:
                lines.extend([f"- **{p['dimension']}** | {p['item']}",
                              f"  - Problem: {p['problem']}",
                              f"  - Suggestion: {p['suggestion']}", ""])
        if p2:
            lines.extend(["", "### P2 Issues", ""])
            for p in p2:
                lines.extend([f"- **{p['dimension']}** | {p['item']}",
                              f"  - Problem: {p['problem']}",
                              f"  - Suggestion: {p['suggestion']}", ""])
        if child_map:
            lines.extend(["---", "", "## Downstream Mapping", ""])
            for kr_code, children in child_map.items():
                lines.append(f"**{kr_code}** downstream:")
                for child in children:
                    lines.append(f"- {child['name']} ({child['group']})")
                lines.append("")
        lines.extend(["---", "",
                      f"*Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*"])
        return "\n".join(lines)

    # ── v2.3: 按BP组织报告 ─────────────────────────────────────────────────

    def generate_bp_centric_report(self, bp_id: str, goal_code: str,
                                   problems: List[dict],
                                   bp_audit_results: List[BPAuditResult],
                                   bp_data: dict = None) -> str:
        """生成v2.3格式报告：按BP组织，两层结构清晰"""
        # 收集统计数据
        p0_basic = [p for p in problems if p.get("level") == "P0"]
        p1_basic = [p for p in problems if p.get("level") == "P1"]
        p2_basic = [p for p in problems if p.get("level") == "P2"]

        all_problems_flat = list(problems)
        for audit in bp_audit_results:
            all_problems_flat.extend(audit.problems)

        p0_all = [p for p in all_problems_flat if p.get("severity") == "P0" or p.get("level") == "P0"]
        p1_all = [p for p in all_problems_flat if p.get("severity") == "P1" or p.get("level") == "P1"]
        p2_all = [p for p in all_problems_flat if p.get("severity") == "P2" or p.get("level") == "P2"]

        # Top3最紧急
        top3 = sorted(all_problems_flat,
                      key=lambda x: self._sev_score(x.get("severity", x.get("level", "PASS"))))[:3]

        lines = ["# BP 评估报告", "",
                 f"**审计对象：** {goal_code or bp_id}",
                 f"**审计时间：** {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
                 f"**报告版本：** v2.3（按BP组织）",
                 f"**深度分析：** {'开启' if self.enable_deep else '关闭'}",
                 "", "---", "",
                 "## 一、执行摘要", "",
                 f"- **审计范围：** {goal_code or bp_id}",
                 f"- **第一层问题（P0/P1/P2）：** {len(p0_basic)} / {len(p1_basic)} / {len(p2_basic)}",
                 f"- **第二层问题（下游BP汇总）：** {len(p0_all)-len(p0_basic)} P0 / "
                 f"{len(p1_all)-len(p1_basic)} P1 / {len(p2_all)-len(p2_basic)} P2",
                 f"- **下游BP数量：** {len(bp_audit_results)}",
                 "",
                 "### 最紧急3个问题", ""]
        for i, p in enumerate(top3, 1):
            sev = p.get("severity", p.get("level", ""))
            desc = p.get("description", p.get("problem", p.get("title", "")))
            lines.append(f"{i}. **[{sev}]** {desc[:60]}")
            suggestion = p.get("suggestion", p.get("reason", ""))
            if suggestion:
                lines.append(f"   - 整改：{suggestion[:50]}")
        lines.append("")

        # ── 第二层评估（下游BP各一节）────────────────────────────────────
        lines.extend(["---", "", "## 二、第二层评估（承接BP）", ""])

        if not bp_audit_results:
            lines.extend(["*（无下游BP或暂未获取到）*", ""])
        else:
            for i, audit in enumerate(bp_audit_results, 1):
                lines.extend([
                    f"### 2.{i} {audit.bp_code}（{audit.bp_name}）",
                    f"**承接上游：{audit.upstream_kr}**",
                    f"**Owner：{audit.owner}**", ""
                ])

                # 目标对齐性
                ga = audit.goal_assessment
                ga_verdict = ga.get("conclusion", "PASS")
                lines.extend([
                    "**目标对齐性：**",
                    f"| 检查项 | 判定 |",
                    f"|---------|------|",
                    f"| 上游承接 | {ga_verdict} |",
                    f"| 对齐依据 | {ga.get('reason', 'N/A')} |",
                    ""
                ])

                # KR评估
                if audit.kr_assessments:
                    lines.extend(["**KR评估：**",
                                  "| KR | SMART | Owner | 支撑 | 目标有效性 | 状态 |",
                                  "|---|-------|-------|------|------------|------|"])
                    for kr in audit.kr_assessments:
                        code = kr.get("code", "")
                        dims = {d["dimension"]: d for d in kr.get("dimensions", [])}
                        smart = dims.get("SMART", {}).get("verdict", "N/A")
                        owner_v = dims.get("Owner", {}).get("verdict", "N/A")
                        support_v = dims.get("支撑", {}).get("verdict", "N/A")
                        target_v = dims.get("目标有效性", {}).get("verdict", "N/A")
                        status_v = dims.get("状态", {}).get("verdict", "N/A")
                        lines.append(f"| {code} | {smart} | {owner_v} | {support_v} | {target_v} | {status_v} |")
                    lines.append("")

                # 举措评估
                if audit.initiative_assessments:
                    lines.extend(["**举措评估（过期分析）：**", "",
                                 "| 举措编码 | 责任人 | 截止日期 | 过期天数 | 判定 |", "|---|---|---|---|---|"])
                    for init in audit.initiative_assessments:
                        lines.append(f"| {init.get('code','N/A')} | {init.get('owners','未指定')} | "
                                     f"{init.get('plan_end','N/A')} | {init.get('days_overdue',0)}天 | "
                                     f"{init.get('severity','N/A')} |")
                    lines.append("")

                # 口径一致性
                if audit.caliber_check:
                    lines.extend([f"**口径一致性：** {audit.caliber_check}", ""])

                # owner匹配
                if audit.owner_match:
                    lines.extend([f"**Owner匹配：** {audit.owner_match}", ""])

                # 问题汇总
                if audit.problems:
                    lines.extend(["**问题汇总：**", "",
                                 "| 编码 | 问题 | 严重度 | 整改建议 |",
                                 "|------|------|--------|----------|"])
                    for p in audit.problems:
                        desc = p.get("description", p.get("problem", ""))[:40]
                        sev = p.get("severity", "N/A")
                        sug = p.get("suggestion", "")[:30]
                        code = p.get("code", audit.bp_code)
                        lines.append(f"| {code} | {desc} | {sev} | {sug} |")
                    lines.append("")

        # ── 问题汇总表（全局）────────────────────────────────────────────
        lines.extend(["---", "", "## 三、问题汇总表", ""])
        lines.extend(["| 编码 | 层级 | 问题 | 严重度 | 整改建议 |", "|------|------|------|--------|----------|"])
        for p in all_problems_flat:
            sev = p.get("severity", p.get("level", ""))
            if self._sev_score(sev) > self._sev_score(self.severity_thresh):
                continue
            desc = (p.get("description") or p.get("problem") or p.get("title", ""))[:40]
            sug = (p.get("suggestion") or p.get("reason") or "")[:30]
            code = p.get("code", p.get("item", "N/A"))
            # 判断层级
            layer = "第一层"
            if p.get("description") or p.get("suggestion"):
                layer = "第二层"
            lines.append(f"| {code} | {layer} | {desc} | {sev} | {sug} |")
        lines.append("")

        # ── 总体结论 ──────────────────────────────────────────────────────
        lines.extend(["---", "", "## 四、总体结论", ""])
        p0_total = len(p0_all)
        p1_total = len(p1_all)
        p2_total = len(p2_all)
        if p0_total == 0:
            lines.append("✅ **P0全部清零**，BP质量达标。")
        else:
            lines.append(f"⚠️ **存在{p0_total}个P0问题，需立即处理。**")
        if p1_total > 0:
            lines.append(f"🔸 存在{p1_total}个P1问题，建议本周内完成整改。")
        if p2_total > 0:
            lines.append(f"🔹 存在{p2_total}个P2问题，建议本月内完成整改。")
        lines.extend(["",
                      f"*Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | v2.3 BP-centric report*"])
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BP Evaluator v2.3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bp-id", help="BP unique identifier")
    group.add_argument("--goal-code", help="Goal code, e.g. G-1")
    parser.add_argument("--depth", choices=["layer1", "full"], default="layer1")
    parser.add_argument("--output", default="markdown", choices=["markdown", "json"])
    parser.add_argument("--enable-deep-analysis", dest="deep", action="store_true",
                        default=True, help="Enable deep analysis (default: enabled)")
    parser.add_argument("--disable-deep-analysis", dest="deep", action="store_false",
                        help="Disable deep analysis")
    parser.add_argument("--no-llm", action="store_true",
                        help="Disable LLM, force keyword fallback (for debugging)")
    parser.add_argument("--severity-threshold", default="P2",
                        choices=["P0", "P1", "P2"],
                        help="Output only problems at or above this severity")
    parser.add_argument("--legacy-format", action="store_true",
                        help="Output v1.0 legacy format")
    parser.add_argument("--v2-format", action="store_true", default=True,
                        help="Output v2.x BP-centric format (default)")
    args = parser.parse_args()

    evaluator = BPEvaluatorV2(
        enable_deep_analysis=args.deep,
        use_llm=not args.no_llm,
        severity_threshold=args.severity_threshold,
    )

    bp_id = args.bp_id
    if args.goal_code:
        bp_id = GOAL_CODE_MAP.get(args.goal_code)
        if not bp_id:
            known = ", ".join(GOAL_CODE_MAP.keys())
            print(f"Error: goal code '{args.goal_code}' not in mapping. Known: {known}",
                  file=sys.stderr)
            sys.exit(1)

    problems, child_map, all_actions, bp_audit_results = evaluator.evaluate_recursive(bp_id, args.depth)

    # Fetch BP data for deep analysis
    bp_result = evaluator.client.get_goal_detail(bp_id)
    bp_data = bp_result.get("data", {}) if bp_result.get("resultCode") == 1 else {}

    deep_findings = evaluator.run_deep_analysis(all_actions, bp_data)

    # JSON output
    if args.output == "json":
        p0p = [p for p in problems if p.get("level") == "P0"]
        p1p = [p for p in problems if p.get("level") == "P1"]
        p2p = [p for p in problems if p.get("level") == "P2"]
        df_p0 = [f for f in evaluator._filter_sev(deep_findings) if f.get("severity") == "P0"]
        df_p1 = [f for f in evaluator._filter_sev(deep_findings) if f.get("severity") == "P1"]
        df_p2 = [f for f in evaluator._filter_sev(deep_findings) if f.get("severity") == "P2"]
        output = {
            "bp_id": bp_id, "goal_code": args.goal_code or "",
            "problems": problems, "deep_findings": evaluator._filter_sev(deep_findings),
            "downstream_map": child_map,
            "summary": {
                "p0_basic": len(p0p), "p1_basic": len(p1p), "p2_basic": len(p2p),
                "p0_deep": len(df_p0), "p1_deep": len(df_p1), "p2_deep": len(df_p2),
                "p0_total": len(p0p) + len(df_p0),
                "p1_total": len(p1p) + len(df_p1),
                "p2_total": len(p2p) + len(df_p2),
            }
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Markdown output
    if args.legacy_format:
        report = evaluator.generate_report_legacy(bp_id, args.goal_code or bp_id,
                                                  problems, child_map, args.depth)
    else:
        report = evaluator.generate_bp_centric_report(bp_id, args.goal_code or bp_id,
                                                       problems, bp_audit_results, bp_data)

    print(report)

    # Save to memory
    out_dir = Path(__file__).parent.parent.parent / "memory" / "BP-evaluator-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = evaluator.timestamp.strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"{bp_id}-{ts}.md"
    out_file.write_text(report, encoding="utf-8")
    print(f"\n[Report saved: {out_file}]", file=sys.stderr)


if __name__ == "__main__":
    main()
