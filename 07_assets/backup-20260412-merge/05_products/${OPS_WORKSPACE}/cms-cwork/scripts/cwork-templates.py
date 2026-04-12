#!/usr/bin/env python3
"""
cwork-templates.py — 模板管理

功能：
1. 查询汇报模板列表

用法：
    python3 cwork-templates.py list --limit 50
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import make_client


def list_templates(args):
    """查询模板列表"""
    client = make_client()
    
    result = client.list_templates()
    
    if args.output_raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 结构化输出
    templates = result if isinstance(result, list) else result.get("rows", [])
    
    output = {
        "success": True,
        "action": "list",
        "total": len(templates),
        "items": [
            {
                "id": t.get("id"),
                "name": t.get("name") or t.get("templateName"),
                "type": t.get("type"),
                "typeName": t.get("typeName"),
                "grade": t.get("grade"),
            }
            for t in templates
        ]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="CWork 模板管理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="action", help="操作类型")
    
    # list 子命令
    list_parser = subparsers.add_parser("list", help="查询模板列表")
    list_parser.add_argument("--limit", type=int, default=50, help="返回数量限制")
    list_parser.add_argument("--begin-time", type=int, help="开始时间戳")
    list_parser.add_argument("--end-time", type=int, help="结束时间戳")
    list_parser.add_argument("--output-raw", action="store_true", help="输出原始响应")
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    if args.action == "list":
        list_templates(args)


if __name__ == "__main__":
    main()
