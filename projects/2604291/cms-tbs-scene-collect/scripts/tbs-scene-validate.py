#!/usr/bin/env python3
"""
tbs-scene-validate.py

Validate the draft payload before calling POST /scene/createScene.
"""

import argparse
import json
import sys
from typing import Any, Dict, List


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def require_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _first_non_empty(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in d and require_non_empty(d.get(k)):
            return d.get(k)
    return None


def _validate_step3(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step3 只收集并确认：
      - 时间地点
      - 医生担忧点
      - 代表目标
      - 医生画像（人设配置/简介描述/姓氏/职称）
      - 最佳实践要点（开场话术/回应问题话术/推荐建议）

    因为 draftJson 的中间形态可能不同，这里做“结构优先、兜底次之”的校验：
    1) 优先从 scene.scenarioBase / scene.doctorPersona / scene.bestPracticePoints 校验结构化字段
    2) 若结构化字段不存在，则从 createScene 里“可能承载这些信息”的字符串字段/数组做兜底校验
    """
    # 结构化容器（优先）
    scenario_base = scene.get("scenarioBase") if isinstance(scene.get("scenarioBase"), dict) else scene
    doctor_persona = scene.get("doctorPersona") if isinstance(scene.get("doctorPersona"), dict) else {}
    best_practice_points = scene.get("bestPracticePoints") if isinstance(scene.get("bestPracticePoints"), dict) else {}

    # 兼容：doctorPersona/bestPracticePoints 可能也在 scenarioBase 内
    if not doctor_persona and isinstance(scenario_base.get("doctorPersona"), dict):
        doctor_persona = scenario_base["doctorPersona"]
    if not best_practice_points and isinstance(scenario_base.get("bestPracticePoints"), dict):
        best_practice_points = scenario_base["bestPracticePoints"]
    # 兼容：doctorPersona/bestPracticePoints 的四要素/三项也可能直接挂在 scenarioBase 上
    if not doctor_persona:
        if any(k in scenario_base for k in ["personaConfig", "humanSetting", "profileConfig", "人设配置", "introDescription", "intro", "简介描述", "surname", "姓氏", "title", "职称"]):
            doctor_persona = scenario_base
    if not best_practice_points:
        if any(k in scenario_base for k in ["openingScript", "openingTalk", "开场话术", "questionResponseScript", "responseTalk", "回应问题话术", "recommendation", "recommendationAdvice", "推荐建议"]):
            best_practice_points = scenario_base

    missing: List[str] = []

    # 时间地点
    time_place = _first_non_empty(
        scenario_base,
        [
            "timePlace",
            "timeLocation",
            "location",
            "时间地点",
        ],
    )
    if not require_non_empty(time_place):
        missing.append("时间地点")

    # 医生担忧点
    doctor_concerns = _first_non_empty(
        scenario_base,
        [
            "doctorConcerns",
            "doctorConcernPoints",
            "doctorConcernsText",
            "医生担忧点",
        ],
    )
    if not require_non_empty(doctor_concerns):
        missing.append("医生担忧点")

    # 代表目标
    rep_goal = _first_non_empty(
        scenario_base,
        [
            "repGoal",
            "representativeGoal",
            "repBriefing",
            "代表目标",
        ],
    )
    if not require_non_empty(rep_goal):
        missing.append("代表目标")

    # 医生画像（四要素）
    persona_config = _first_non_empty(
        doctor_persona,
        ["personaConfig", "humanSetting", "profileConfig", "人设配置"],
    )
    persona_intro = _first_non_empty(
        doctor_persona,
        ["introDescription", "intro", "简介描述"],
    )
    persona_surname = _first_non_empty(
        doctor_persona,
        ["surname", "姓氏"],
    )
    persona_title = _first_non_empty(
        doctor_persona,
        ["title", "职称"],
    )

    if not (
        require_non_empty(persona_config)
        and require_non_empty(persona_intro)
        and require_non_empty(persona_surname)
        and require_non_empty(persona_title)
    ):
        # 兜底：若上游已完成 personaId 映射，则 personaIds 非空也视为医生画像已齐全
        persona_ids = scene.get("personaIds", [])
        if not (isinstance(persona_ids, list) and len(persona_ids) > 0):
            missing.append("医生画像")

    # 最佳实践要点（三项）
    opening_script = _first_non_empty(
        best_practice_points,
        ["openingScript", "openingTalk", "开场话术"],
    )
    question_response_script = _first_non_empty(
        best_practice_points,
        ["questionResponseScript", "responseTalk", "回应问题话术"],
    )
    recommendation = _first_non_empty(
        best_practice_points,
        ["recommendation", "recommendationAdvice", "推荐建议"],
    )

    best_practice_ok = (
        require_non_empty(opening_script)
        and require_non_empty(question_response_script)
        and require_non_empty(recommendation)
    )
    if not best_practice_ok:
        missing.append("最佳实践要点")

    passed = len(missing) == 0
    out = {
        "success": True,
        "passed": passed,
        "missingFields": missing,
        "mode": "step3",
        "snapshot": {
            "location": time_place,
            "hasDoctorOnlyContext": require_non_empty(scene.get("doctorOnlyContext")),
            "hasCoachOnlyContext": require_non_empty(scene.get("coachOnlyContext")),
            "hasRepBriefing": require_non_empty(scene.get("repBriefing")),
        },
    }
    return out


def _validate_create_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    # createScene 门禁校验：确保 POST /scene/createScene 所需字段齐全
    required_fields = [
        "title",
        "departmentId",
        "drugId",
        "businessDomainId",
        "location",
        "doctorOnlyContext",
        "coachOnlyContext",
        "repBriefing",
        "personaIds",
        "knowledgeIds",
    ]

    missing: List[str] = []
    for k in required_fields:
        if not require_non_empty(scene.get(k)):
            missing.append(k)

    # Blocking check: personaIds must be non-empty array
    persona_ids = scene.get("personaIds", [])
    if "personaIds" not in missing:
        if not isinstance(persona_ids, list) or len(persona_ids) == 0:
            missing.append("personaIds")

    passed = len(missing) == 0
    out = {
        "success": True,
        "passed": passed,
        "missingFields": missing,
        "mode": "createScene",
        "sceneSnapshot": {
            "title": scene.get("title"),
            "departmentId": scene.get("departmentId"),
            "drugId": scene.get("drugId"),
            "businessDomainId": scene.get("businessDomainId"),
            "location": scene.get("location"),
        },
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params-file", required=False, help="Path to draft.json")
    ap.add_argument("--params-json", required=False, help="Draft JSON string (optional)")
    ap.add_argument(
        "--mode",
        required=False,
        choices=["step3", "createScene"],
        default="step3",
        help="校验模式：step3=只校验 Step3 收集字段；createScene=校验 createScene 必填字段",
    )
    args = ap.parse_args()

    try:
        if args.params_json:
            payload = json.loads(args.params_json)
        else:
            if not args.params_file:
                raise ValueError("either --params-file or --params-json is required")
            payload = load_json(args.params_file)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"load_json failed: {e}"}), file=sys.stderr)
        return 2

    scene = payload.get("scene") or payload.get("draft") or payload
    if not isinstance(scene, dict):
        print(json.dumps({"success": False, "error": "scene must be an object"}), file=sys.stderr)
        return 2

    if args.mode == "createScene":
        out = _validate_create_scene(scene)
    else:
        out = _validate_step3(scene)

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

