#!/usr/bin/env python3
"""
BP Manager 命令实现

提供各种 BP 知理命令的实现，包括查看、管理、检查、提醒等功能。
"""

import json
import argparse
from typing import Dict, List, Optional
from bp_client import BPClient, get_current_period, find_my_group

# ==================== 查看 BP 命令 ====================

def cmd_view_my_bp(client: BPClient, employee_id: str = None) -> Dict:
    """
    查看我的 BP
    
    Args:
        employee_id: 员工ID（可选，不提供则使用环境变量）
    """
    # 获取当前周期
    period = get_current_period(client)
    if not period:
        return {"success": False, "error": "未找到启用的周期"}
    
    period_id = period["id"]
    print(f"当前周期: {period['name']} (ID: {period_id})")
    
    # 获取个人分组
    group_id = find_my_group(client, period_id, employee_id)
    if not group_id:
        return {"success": False, "error": "未找到您的个人分组"}
    
    print(f"您的分组ID: {group_id}")
    
    # 获取 BP Markdown
    result = client.get_group_markdown(group_id)
    if result.get("resultCode") == 1:
        return {"success": True, "markdown": result["data"]}
    else:
        return {"success": False, "error": result.get("resultMsg", "获取 BP 失败")}


def cmd_view_group_bp(client: BPClient, group_id: str) -> Dict:
    """
    查看指定分组的 BP
    
    Args:
        group_id: 分组ID
    """
    result = client.get_group_markdown(group_id)
    if result.get("resultCode") == 1:
        return {"success": True, "markdown": result["data"]}
    else:
        return {"success": False, "error": result.get("resultMsg", "获取 BP 失败")}


def cmd_view_subordinate_bp(client: BPClient, subordinate_name: str, period_id: str = None) -> Dict:
    """
    查看下属的 BP
    
    Args:
        subordinate_name: 下属姓名
        period_id: 周期ID（可选）
    """
    # 如果没有提供周期，获取当前周期
    if not period_id:
        period = get_current_period(client)
        if not period:
            return {"success": False, "error": "未找到启用的周期"}
        period_id = period["id"]
    
    # 搜索分组
    result = client.search_groups(period_id, subordinate_name)
    if result.get("resultCode") != 1 or not result.get("data"):
        return {"success": False, "error": f"未找到名为 '{subordinate_name}' 的分组"}
    
    groups = result["data"]
    if len(groups) == 0:
        return {"success": False, "error": f"未找到名为 '{subordinate_name}' 的分组"}
    
    # 如果找到多个，选择第一个（个人类型优先）
    target_group = None
    for g in groups:
        if g.get("type") == "personal":
            target_group = g
            break
    if not target_group:
        target_group = groups[0]
    
    group_id = target_group["id"]
    print(f"找到分组: {target_group['name']} (类型: {target_group['type']})")
    
    # 获取 BP Markdown
    return cmd_view_group_bp(client, group_id)


# ==================== 管理 BP 命令 ====================

def cmd_add_key_result(client: BPClient, goal_id: str, name: str, 
                       plan_start_date: str = None, plan_end_date: str = None,
                       owner_ids: List[str] = None, measure_standard: str = None,
                       **kwargs) -> Dict:
    """
    为目标新增关键成果
    
    Args:
        goal_id: 目标ID
        name: 关键成果名称
        plan_start_date: 计划开始日期 (yyyy-MM-dd)
        plan_end_date: 计划结束日期 (yyyy-MM-dd)
        owner_ids: 承接人ID列表
        measure_standard: 衡量标准
    """
    data = {"name": name}
    if plan_start_date:
        data["planStartDate"] = plan_start_date
    if plan_end_date:
        data["planEndDate"] = plan_end_date
    if owner_ids:
        data["ownerIds"] = owner_ids
    if measure_standard:
        data["measureStandard"] = measure_standard
    data.update(kwargs)
    
    result = client.add_key_result(goal_id, **data)
    if result.get("resultCode") == 1:
        return {
            "success": True, 
            "key_result_id": result["data"],
            "message": f"已成功创建关键成果【{name}】"
        }
    else:
        return {"success": False, "error": result.get("resultMsg", "创建关键成果失败")}


def cmd_add_action(client: BPClient, key_result_id: str, name: str,
                  plan_start_date: str = None, plan_end_date: str = None,
                  owner_ids: List[str] = None, measure_standard: str = None,
                  **kwargs) -> Dict:
    """
    为关键成果新增关键举措
    
    Args:
        key_result_id: 关键成果ID
        name: 关键举措名称
        plan_start_date: 计划开始日期 (yyyy-MM-dd)
        plan_end_date: 计划结束日期 (yyyy-MM-dd)
        owner_ids: 承接人ID列表
        measure_standard: 衡量标准
    """
    data = {"name": name}
    if plan_start_date:
        data["planStartDate"] = plan_start_date
    if plan_end_date:
        data["planEndDate"] = plan_end_date
    if owner_ids:
        data["ownerIds"] = owner_ids
    if measure_standard:
        data["measureStandard"] = measure_standard
    data.update(kwargs)
    
    result = client.add_action(key_result_id, **data)
    if result.get("resultCode") == 1:
        return {
            "success": True, 
            "action_id": result["data"],
            "message": f"已成功创建关键举措【{name}】"
        }
    else:
        return {"success": False, "error": result.get("resultMsg", "创建关键举措失败")}


# ==================== 查看汇报历史命令 ====================

def cmd_view_reports(client: BPClient, task_id: str, page_size: int = 10) -> Dict:
    """
    查看任务的汇报历史
    
    Args:
        task_id: 任务ID
        page_size: 每页数量
    """
    result = client.list_task_reports(task_id, page_size=page_size)
    if result.get("resultCode") == 1:
        data = result["data"]
        return {
            "success": True,
            "total": data.get("total", 0),
            "reports": data.get("list", [])
        }
    else:
        return {"success": False, "error": result.get("resultMsg", "获取汇报历史失败")}


# ==================== 延期提醒命令 ====================

def cmd_send_delay_reminder(client: BPClient, receiver_emp_id: str, 
                           task_name: str, plan_end_date: str,
                           custom_content: str = None) -> Dict:
    """
    发送延期提醒汇报
    
    Args:
        receiver_emp_id: 接收人员工ID
        task_name: 延期的任务名称
        plan_end_date: 计划结束日期
        custom_content: 自定义提醒内容（可选）
    """
    report_name = f"BP延期提醒 - {task_name}"
    
    if custom_content:
        content = custom_content
    else:
        content = f"您负责的任务【{task_name}】已延期，计划结束日期为{plan_end_date}，请尽快跟进处理。"
    
    result = client.send_delay_report(receiver_emp_id, report_name, content)
    if result.get("resultCode") == 1:
        return {
            "success": True,
            "report_id": result["data"],
            "message": f"已成功发送延期提醒给员工 {receiver_emp_id}"
        }
    else:
        return {"success": False, "error": result.get("resultMsg", "发送延期提醒失败")}


# ==================== 搜索命令 ====================

def cmd_search_tasks(client: BPClient, group_id: str, keyword: str) -> Dict:
    """
    搜索任务
    
    Args:
        group_id: 分组ID
        keyword: 搜索关键词
    """
    result = client.search_tasks(group_id, keyword)
    if result.get("resultCode") == 1:
        return {"success": True, "tasks": result.get("data", [])}
    else:
        return {"success": False, "error": result.get("resultMsg", "搜索任务失败")}


def cmd_search_groups(client: BPClient, period_id: str, keyword: str) -> Dict:
    """
    搜索分组
    
    Args:
        period_id: 周期ID
        keyword: 搜索关键词
    """
    result = client.search_groups(period_id, keyword)
    if result.get("resultCode") == 1:
        return {"success": True, "groups": result.get("data", [])}
    else:
        return {"success": False, "error": result.get("resultMsg", "搜索分组失败")}


# ==================== AI 检查命令 ====================

def cmd_check_bp(client: BPClient, group_id: str) -> Dict:
    """
    AI 检查 BP 质量（基于康哲规则）
    
    检查项包括：
    1. 结构完整性：是否按 G-R-A 三层拆解
    2. 衡量标准：所有关键成果是否有合格的衡量标准
    3. 承接关系：是否正确承接上级任务
    4. 举措可执行性：关键举措是否具体可执行
    5. 时间合理性：时间范围是否合理
    
    Args:
        group_id: 分组ID
    """
    # 获取 BP Markdown
    result = client.get_group_markdown(group_id)
    if result.get("resultCode") != 1:
        return {"success": False, "error": "获取 BP 失败"}
    
    markdown = result["data"]
    
    # 基于康哲规则的检查逻辑（简化版）
    issues = []
    
    # 这里应该调用 AI 进行深度检查
    # 目前先返回基本信息
    return {
        "success": True,
        "markdown": markdown,
        "message": "BP 数据已获取，建议结合康哲规则进行人工检查或调用 AI 进行深度分析"
    }


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="BP Manager 命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 查看我的 BP
    parser_view_my = subparsers.add_parser("view-my", help="查看我的 BP")
    parser_view_my.add_argument("--employee-id", help="员工ID（可选）")
    
    # 查看分组 BP
    parser_view_group = subparsers.add_parser("view-group", help="查看指定分组的 BP")
    parser_view_group.add_argument("group-id", required=True, help="分组ID")
    
    # 查看下属 BP
    parser_view_subordinate = subparsers.add_parser("view-subordinate", help="查看下属的 BP")
    parser_view_subordinate.add_argument("name", help="下属姓名")
    parser_view_subordinate.add_argument("--period-id", help="周期ID")
    
    # 新增关键成果
    parser_add_kr = subparsers.add_parser("add-kr", help="新增关键成果")
    parser_add_kr.add_argument("goal-id", required=True, help="目标ID")
    parser_add_kr.add_argument("name", help="关键成果名称")
    parser_add_kr.add_argument("--plan-start", help="计划开始日期")
    parser_add_kr.add_argument("--plan-end", help="计划结束日期")
    parser_add_kr.add_argument("--measure", help="衡量标准")
    
    # 新增关键举措
    parser_add_action = subparsers.add_parser("add-action", help="新增关键举措")
    parser_add_action.add_argument("key-result-id", required=True, help="关键成果ID")
    parser_add_action.add_argument("name", help="关键举措名称")
    parser_add_action.add_argument("--plan-start", help="计划开始日期")
    parser_add_action.add_argument("--plan-end", help="计划结束日期")
    parser_add_action.add_argument("--measure", help="衡量标准")
    
    # 查看汇报历史
    parser_reports = subparsers.add_parser("reports", help="查看汇报历史")
    parser_reports.add_argument("task-id", required=True, help="任务ID")
    parser_reports.add_argument("--page-size", type=int, default=10, help="每页数量")
    
    # 发送延期提醒
    parser_delay = subparsers.add_parser("delay-reminder", help="发送延期提醒")
    parser_delay.add_argument("emp-id", required=True, help="接收人员工ID")
    parser_delay.add_argument("task-name", help="任务名称")
    parser_delay.add_argument("plan-end", help="计划结束日期")
    parser_delay.add_argument("--content", help="自定义提醒内容")
    
    # 搜索任务
    parser_search_tasks = subparsers.add_parser("search-tasks", help="搜索任务")
    parser_search_tasks.add_argument("group-id", required=True, help="分组ID")
    parser_search_tasks.add_argument("keyword", help="搜索关键词")
    
    # 搜索分组
    parser_search_groups = subparsers.add_parser("search-groups", help="搜索分组")
    parser_search_groups.add_argument("period-id", required=True, help="周期ID")
    parser_search_groups.add_argument("keyword", help="搜索关键词")
    
    args = parser.parse_args()
    
    # 创建客户端
    client = BPClient()
    
    # 执行命令
    if args.command == "view-my":
        result = cmd_view_my_bp(client, args.employee_id)
    elif args.command == "view-group":
        result = cmd_view_group_bp(client, args.group_id)
    elif args.command == "view-subordinate":
        result = cmd_view_subordinate_bp(client, args.name, args.period_id)
    elif args.command == "add-kr":
        result = cmd_add_key_result(
            client, args.goal_id, args.name,
            args.plan_start, args.plan_end,
            measure_standard=args.measure
        )
    elif args.command == "add-action":
        result = cmd_add_action(
            client, args.key_result_id, args.name,
            args.plan_start, args.plan_end,
            measure_standard=args.measure
        )
    elif args.command == "reports":
        result = cmd_view_reports(client, args.task_id, args.page_size)
    elif args.command == "delay-reminder":
        result = cmd_send_delay_reminder(
            client, args.emp_id, args.task_name, 
            args.plan_end, args.content
        )
    elif args.command == "search-tasks":
        result = cmd_search_tasks(client, args.group_id, args.keyword)
    elif args.command == "search-groups":
        result = cmd_search_groups(client, args.period_id, args.keyword)
    else:
        result = {"success": False, "error": f"未知命令: {args.command}"}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
