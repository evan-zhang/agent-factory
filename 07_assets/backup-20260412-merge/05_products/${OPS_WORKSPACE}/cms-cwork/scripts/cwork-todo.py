#!/usr/bin/env python3
"""
cwork-todo.py — 待办管理

功能：
1. 查询待办列表
2. 完成待办

用法：
    python3 cwork-todo.py list --page-size 20 --status pending
    python3 cwork-todo.py complete --todo-id <id> --content "已完成"
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import make_client


def list_todos(args):
    """查询待办列表"""
    client = make_client()
    
    result = client.get_todo_list(
        page_index=args.page_index,
        page_size=args.page_size
    )
    
    if args.output_raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 结构化输出
    rows = result.get("rows", [])
    total = result.get("total", len(rows))
    
    output = {
        "success": True,
        "action": "list",
        "total": total,
        "items": [
            {
                "id": item.get("id"),
                "title": item.get("title") or item.get("main"),
                "type": item.get("type"),
                "status": item.get("status"),
                "createTime": item.get("createTime"),
                "creator": item.get("creatorName"),
            }
            for item in rows
        ]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def complete_todo(args):
    """完成待办"""
    client = make_client()
    
    if not args.todo_id:
        print(json.dumps({
            "success": False,
            "error": "缺少必填参数: --todo-id"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    if not args.content:
        print(json.dumps({
            "success": False,
            "error": "缺少必填参数: --content"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    if args.dry_run:
        print(json.dumps({
            "success": True,
            "action": "complete",
            "dryRun": True,
            "todoId": args.todo_id,
            "content": args.content
        }, ensure_ascii=False, indent=2))
        return
    
    result = client.complete_todo(
        todo_id=args.todo_id,
        content=args.content,
        operate=args.operate
    )
    
    output = {
        "success": True,
        "action": "complete",
        "todoId": args.todo_id,
        "result": result
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="CWork 待办管理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="action", help="操作类型")
    
    # list 子命令
    list_parser = subparsers.add_parser("list", help="查询待办列表")
    list_parser.add_argument("--page-index", type=int, default=1, help="页码")
    list_parser.add_argument("--page-size", type=int, default=20, help="每页数量")
    list_parser.add_argument("--status", type=str, help="状态筛选")
    list_parser.add_argument("--output-raw", action="store_true", help="输出原始响应")
    
    # complete 子命令
    complete_parser = subparsers.add_parser("complete", help="完成待办")
    complete_parser.add_argument("--todo-id", type=str, required=True, help="待办 ID")
    complete_parser.add_argument("--content", type=str, required=True, help="完成说明")
    complete_parser.add_argument("--operate", type=str, default="complete", help="操作类型")
    complete_parser.add_argument("--dry-run", action="store_true", help="仅预览")
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    if args.action == "list":
        list_todos(args)
    elif args.action == "complete":
        complete_todo(args)


if __name__ == "__main__":
    main()
