"""
bp_fetcher.py
=============
BP树拉取与递归遍历模块。

负责与 cwork open-api 交互，提供：
- 按名称搜索组织（精确 / 模糊）
- 获取BP周期列表
- 获取组织BP简单树
- 获取单个BP的目标+KR+举措完整详情
- 从举措的 taskDepts 中提取承接方
- 批量获取个人BP入口 groupId
- 获取完整BP任务树
"""

import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("BP_BASE_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
APP_KEY = os.environ.get("BP_APP_KEY", "")


def _headers() -> dict:
    """构造请求头，包含 AppKey 认证。"""
    return {
        "Content-Type": "application/json",
        "AppKey": APP_KEY,
    }


def _get(path: str, params: dict = None) -> dict:
    """
    封装 HTTP GET 请求。

    :param path: 接口路径（相对 BASE_URL）
    :param params: URL 查询参数
    :return: 响应 JSON（已解析）
    :raises: requests.HTTPError / ValueError
    """
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data


def _post(path: str, body: dict = None) -> dict:
    """
    封装 HTTP POST 请求。

    :param path: 接口路径（相对 BASE_URL）
    :param body: 请求体（JSON）
    :return: 响应 JSON（已解析）
    :raises: requests.HTTPError / ValueError
    """
    url = f"{BASE_URL}{path}"
    resp = requests.post(url, headers=_headers(), json=body or {}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def search_by_name(name: str) -> list[dict]:
    """
    按组织名称精确搜索，返回匹配的组织列表。

    每个元素结构：{"groupId": str, "name": str, "type": str}
    若返回多条，调用方须提示用户选择，不可自动取第一条。

    :param name: 组织名称（完整）
    :return: 匹配的组织列表
    """
    resp = _get("/searchByName", params={"name": name})
    return resp.get("data", [])


def search_by_name_fuzzy(name: str, group_type: str = "dept") -> list[dict]:
    """
    按名称模糊搜索分组，用于 deptId → groupId 跳转。

    :param name: 部门名称（可部分匹配）
    :param group_type: 分组类型，默认 "dept"
    :return: 匹配的分组列表
    """
    resp = _post("/bp/group/searchByNameFuzzy", body={"name": name, "type": group_type})
    return resp.get("data", [])


def resolve_dept_to_group_id(dept_name: str) -> Optional[str]:
    """
    将 taskDepts 中的部门名称解析为 groupId。

    优先按完整名称精确匹配；若结果仍有歧义，返回 None（由调用方标注[承接方定位模糊]）。

    :param dept_name: 部门名称
    :return: 解析得到的 groupId，或 None（模糊/无结果）
    """
    results = search_by_name_fuzzy(dept_name)
    if not results:
        logger.warning("模糊搜索无结果: %s", dept_name)
        return None

    # 精确匹配优先
    exact = [r for r in results if r.get("name") == dept_name]
    if len(exact) == 1:
        return exact[0]["groupId"]
    if len(exact) > 1:
        # 精确匹配仍有多条 → 歧义
        logger.warning("部门名称歧义（精确匹配多条）: %s", dept_name)
        return None

    # 无精确匹配但有模糊匹配，仅1条时接受
    if len(results) == 1:
        return results[0]["groupId"]

    logger.warning("部门名称歧义（模糊匹配多条）: %s", dept_name)
    return None


def get_all_periods(group_id: str) -> list[dict]:
    """
    获取指定组织的 BP 周期列表。

    :param group_id: 组织的 groupId
    :return: 周期列表，每项含 {periodId, name, ...}
    """
    resp = _get("/getAllPeriod", params={"groupId": group_id})
    return resp.get("data", [])


def get_simple_tree(group_id: str, period_id: str) -> list[dict]:
    """
    获取组织的一级 BP 列表（轻量版，不含 KR 详情）。

    :param group_id: 组织的 groupId
    :param period_id: BP 周期 ID
    :return: BP 节点列表
    """
    resp = _get("/getSimpleTree", params={"groupId": group_id, "periodId": period_id})
    return resp.get("data", [])


def get_goal_and_key_result(bp_id: str, period_id: str) -> dict:
    """
    获取单个 BP 的完整详情：目标 + KR + 举措（含 taskDepts）。

    :param bp_id: BP ID
    :param period_id: BP 周期 ID
    :return: BP 详情字典
    """
    resp = _get("/getGoalAndKeyResult", params={"bpId": bp_id, "periodId": period_id})
    return resp.get("data", {})


def get_undertakers_from_bp(bp_detail: dict) -> list[dict]:
    """
    从 BP 详情中提取所有承接方（role == "undertaker"）。

    按举措粒度独立处理：返回结构为
      [{"measureId": str, "measure_desc": str, "undertakers": [{"deptId", "name", ...}]}]

    :param bp_detail: get_goal_and_key_result 返回的 BP 详情
    :return: 按举措分组的承接方列表
    """
    result = []
    measures = bp_detail.get("measures", [])
    for measure in measures:
        undertakers = [
            dept for dept in measure.get("taskDepts", [])
            if dept.get("role") == "undertaker"
        ]
        if undertakers:
            result.append({
                "measureId": measure.get("measureId", ""),
                "measure_desc": measure.get("description", ""),
                "undertakers": undertakers,
            })
    return result


def get_personal_group_ids(user_ids: list[str]) -> dict[str, Optional[str]]:
    """
    批量从员工 ID 获取个人 BP 入口 groupId。

    :param user_ids: 员工 ID 列表
    :return: {userId: groupId | None}，None 表示未建 BP
    """
    resp = _post("/bp/group/getPersonalGroupIds", body={"userIds": user_ids})
    return resp.get("data", {})


def get_tree(group_id: str, period_id: str) -> dict:
    """
    获取个人或部门的完整 BP 任务树。

    :param group_id: 个人/部门 groupId
    :param period_id: BP 周期 ID
    :return: BP 任务树根节点
    """
    resp = _get("/bp/group/getTree", params={"groupId": group_id, "periodId": period_id})
    return resp.get("data", {})


def batch_get_key_position_markdown(group_ids: list[str]) -> dict:
    """
    批量获取关键岗位状态、奖金系数建议、目标权重（API 4.17）。

    :param group_ids: 个人 BP groupId 列表
    :return: {groupId: markdown_text}
    """
    resp = _post("/bp/group/batchGetKeyPositionMarkdown", body={"groupIds": group_ids})
    return resp.get("data", {})
