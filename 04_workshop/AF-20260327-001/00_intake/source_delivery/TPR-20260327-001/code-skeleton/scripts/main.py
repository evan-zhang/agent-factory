#!/usr/bin/env python3
"""
bp-reporting-templates 主程序入口

功能：
1. 解析用户指令（组织名/个人名 + 生成类型）
2. 获取 BP 数据（API 或文件）
3. 并行生成填写规范
4. 审查并输出
"""

import asyncio
import argparse
from pathlib import Path
from typing import List, Optional

from input_handler import parse_user_input
from api_client import BPAPIClient
from parser import parse_bp_from_api, parse_bp_from_file
from template_manager import TemplateManager
from filler import fill_template
from reviewer import review_template
from utils import save_output, setup_logging

# 配置
CONFIG = {
    "base_url": "https://sg-al-cwork-web.mediportal.com.cn/open-api",
    "app_key": "TsFhRR7OywNULeHPqudePf85STc4EpHI",
    "period_id": "1994002024299085826",
    "output_dir": "./output"
}


async def generate_single_template(
    bp_data: dict,
    template_type: str,
    template_manager: TemplateManager
) -> dict:
    """生成单套填写规范"""
    
    # 1. 加载模板
    template = template_manager.load_template(template_type)
    
    # 2. 填充模板
    filled_content = fill_template(template, bp_data, template_type)
    
    # 3. 审查
    review_result = review_template(filled_content, bp_data)
    
    return {
        "template_type": template_type,
        "content": filled_content,
        "review": review_result
    }


async def generate_templates(
    user_input: str,
    bp_file: Optional[str] = None
) -> List[dict]:
    """主流程：并行生成多套填写规范"""
    
    # 1. 解析用户输入
    parsed = parse_user_input(user_input)
    org_name = parsed["org_name"]
    person_name = parsed.get("person_name")
    template_types = parsed["template_types"]
    
    print(f"📋 解析结果:")
    print(f"   组织: {org_name}")
    print(f"   个人: {person_name or '未指定'}")
    print(f"   生成: {', '.join(template_types)}")
    
    # 2. 获取 BP 数据
    if bp_file:
        print(f"\n📄 从文件读取 BP: {bp_file}")
        bp_data = parse_bp_from_file(bp_file)
    else:
        print(f"\n🔗 从 API 获取 BP...")
        api_client = BPAPIClient(CONFIG["base_url"], CONFIG["app_key"])
        bp_data = api_client.fetch_bp_data(org_name, person_name, CONFIG["period_id"])
    
    print(f"   获取到 {len(bp_data.get('goals', []))} 个目标")
    
    # 3. 加载模板管理器
    template_manager = TemplateManager()
    
    # 4. 并行生成多套
    print(f"\n⚙️ 并行生成 {len(template_types)} 套填写规范...")
    tasks = [
        generate_single_template(bp_data, t_type, template_manager)
        for t_type in template_types
    ]
    results = await asyncio.gather(*tasks)
    
    # 5. 输出结果
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result["review"]["passed"]:
            filename = f"{org_name}_{person_name or '组织'}_{result['template_type']}填写规范.md"
            filepath = output_dir / filename
            save_output(filepath, result["content"])
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️ {result['template_type']} 审查未通过:")
            for issue in result["review"]["issues"]:
                print(f"      - {issue['type']}: {issue['detail']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="BP 填写规范生成器")
    parser.add_argument("input", help="用户输入，如 '为产品中心生成四套'")
    parser.add_argument("--bp-file", help="BP 文件路径（可选，不指定则从 API 获取）")
    parser.add_argument("--output", default="./output", help="输出目录")
    
    args = parser.parse_args()
    CONFIG["output_dir"] = args.output
    
    setup_logging()
    
    asyncio.run(generate_templates(args.input, args.bp_file))


if __name__ == "__main__":
    main()
