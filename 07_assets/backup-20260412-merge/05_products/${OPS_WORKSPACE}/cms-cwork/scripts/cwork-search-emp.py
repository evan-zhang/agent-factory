#!/usr/bin/env python3
"""
CWork 员工搜索工具

用途：根据姓名搜索员工 ID 和详细信息
场景：发送汇报前确认接收人、处理待办时确认发件人、创建任务时确认责任人

用法：
  python3 cwork-search-emp.py --name "张"
  python3 cwork-search-emp.py --name "成伟" --verbose
  python3 cwork-search-emp.py --name "刘" --max-results 10
"""

import argparse
import json
import sys
import os

# Add parent directory to path to import cwork_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import CWorkClient, CWorkError


def search_employees(client: CWorkClient, search_key: str, max_results: int = 5, verbose: bool = False) -> dict:
    """
    Search employees by name keyword.
    
    Args:
        client: CWork API client
        search_key: Search keyword (supports fuzzy matching)
        max_results: Maximum results to return per category (inside/outside)
        verbose: Include additional details
    
    Returns:
        {
          "success": true,
          "searchKey": "张",
          "inside": [...],
          "outside": [...],
          "totalInside": 10,
          "totalOutside": 2
        }
    """
    try:
        result = client.search_emp_by_name(search_key)
        
        # Parse inside employees
        inside_list = []
        inside_data = result.get("inside", {})
        if inside_data:
            company = inside_data.get("companyVO", {})
            emp_list = inside_data.get("empList", [])
            
            for emp in emp_list[:max_results]:
                emp_info = {
                    "empId": emp.get("id"),
                    "name": emp.get("name"),
                    "title": emp.get("title", ""),
                    "mainDept": emp.get("mainDept", ""),
                    "status": "在职" if emp.get("status") == 1 else "离职"
                }
                
                if verbose:
                    emp_info.update({
                        "personId": emp.get("personId"),
                        "dingUserId": emp.get("dingUserId"),
                        "corpId": emp.get("corpId"),
                        "company": company.get("name", "")
                    })
                
                inside_list.append(emp_info)
        
        # Parse outside contacts
        outside_list = []
        outside_data = result.get("outside", [])
        if outside_data:
            for item in outside_data:
                company = item.get("companyVO", {})
                emp_list = item.get("empList", [])
                
                for emp in emp_list[:max_results]:
                    emp_info = {
                        "empId": emp.get("id"),
                        "name": emp.get("name"),
                        "title": emp.get("title", ""),
                        "mainDept": emp.get("mainDept", ""),
                        "status": "在职" if emp.get("status") == 1 else "离职",
                        "company": company.get("name", "")
                    }
                    outside_list.append(emp_info)
        
        return {
            "success": True,
            "searchKey": search_key,
            "inside": inside_list,
            "outside": outside_list,
            "totalInside": len(result.get("inside", {}).get("empList", [])) if result.get("inside") else 0,
            "totalOutside": sum(len(item.get("empList", [])) for item in result.get("outside", [])) if result.get("outside") else 0
        }
        
    except CWorkError as e:
        return {
            "success": False,
            "error": str(e),
            "searchKey": search_key
        }


def main():
    parser = argparse.ArgumentParser(
        description="Search CWork employees by name",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python3 cwork-search-emp.py --name "张"
  
  # Verbose mode (includes personId, dingUserId, etc.)
  python3 cwork-search-emp.py --name "成伟" --verbose
  
  # More results
  python3 cwork-search-emp.py --name "刘" --max-results 10
        """
    )
    
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Employee name or keyword to search (supports fuzzy matching)"
    )
    
    parser.add_argument(
        "--max-results", "-m",
        type=int,
        default=5,
        help="Maximum results to return per category (default: 5)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include additional details (personId, dingUserId, etc.)"
    )
    
    parser.add_argument(
        "--output-raw",
        action="store_true",
        help="Output raw API response"
    )
    
    args = parser.parse_args()
    
    try:
        client = CWorkClient()
        
        # Output raw response if requested
        if args.output_raw:
            result = client.search_emp_by_name(args.name)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        
        # Normal search
        result = search_employees(
            client,
            args.name,
            max_results=args.max_results,
            verbose=args.verbose
        )
        
        # Output JSON to stdout
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # Exit with error code if failed
        if not result.get("success"):
            sys.exit(1)
            
    except CWorkError as e:
        error_output = {
            "success": False,
            "error": str(e),
            "searchKey": args.name
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_output = {
            "success": False,
            "error": f"Unexpected error: {e}",
            "searchKey": args.name
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
