#!/usr/bin/env python3
"""
发现 Skill — 浏览、搜索、查看详情

用途：查看平台已有 Skill，支持三种模式

使用方式：
  # 浏览全部
  python3 create-xgjk-skill/scripts/skill-management/get_skills.py

  # 按关键词搜索（名称/描述模糊匹配）
  python3 create-xgjk-skill/scripts/skill-management/get_skills.py --search "机器人"

  # 查看某个 Skill 详情（按 code 或 name 匹配）
  python3 create-xgjk-skill/scripts/skill-management/get_skills.py --detail "im-robot"

说明：
  此接口为 nologin 接口，无需 XG_USER_TOKEN。
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
import ssl

API_URL = "https://sg-cwork-api.mediportal.com.cn/im/skill/nologin/list"


def call_api() -> dict:
    """获取 Skill 列表（无需鉴权）"""
    headers = {
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(API_URL, headers=headers, method="GET")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_list(skills: list) -> str:
    """格式化为表格展示"""
    if not skills:
        return "（暂无已发布的 Skill）"

    lines = []
    lines.append(f"{'#':<4} {'名称':<20} {'Code':<20} {'版本':<6} {'状态':<10} {'描述'}")
    lines.append("-" * 100)

    for i, s in enumerate(skills, 1):
        name = (s.get("name") or "")[:18]
        code = (s.get("code") or "")[:18]
        version = str(s.get("version", ""))[:5]
        status = s.get("status") or ""
        desc = (s.get("description") or "")[:40]
        lines.append(f"{i:<4} {name:<20} {code:<20} {version:<6} {status:<10} {desc}")

    lines.append(f"\n共 {len(skills)} 个 Skill")
    return "\n".join(lines)


def format_detail(skill: dict) -> str:
    """格式化单个 Skill 详情"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  名称: {skill.get('name', '-')}")
    lines.append(f"  Code: {skill.get('code', '-')}")
    lines.append(f"    ID: {skill.get('id', '-')}")
    lines.append(f"  版本: {skill.get('version', '-')}")
    lines.append(f"  状态: {skill.get('status', '-')}")
    lines.append(f"  类型: {'内部' if skill.get('isInternal') else '外部'}")
    lines.append(f"  标签: {skill.get('label', '-')}")
    lines.append(f"  描述: {skill.get('description', '-')}")
    lines.append(f"  下载: {skill.get('downloadUrl', '-')}")
    lines.append(f"  创建: {skill.get('createTime', '-')}")
    if skill.get("delistReason"):
        lines.append(f"  下架原因: {skill['delistReason']}")
    lines.append("=" * 60)
    return "\n".join(lines)


def search_skills(skills: list, keyword: str) -> list:
    """按关键词搜索（名称/描述/code 模糊匹配）"""
    keyword_lower = keyword.lower()
    results = []
    for s in skills:
        name = (s.get("name") or "").lower()
        desc = (s.get("description") or "").lower()
        code = (s.get("code") or "").lower()
        if keyword_lower in name or keyword_lower in desc or keyword_lower in code:
            results.append(s)
    return results


def find_detail(skills: list, query: str) -> dict | None:
    """按 code 或 name 精确/模糊匹配单个 Skill"""
    query_lower = query.lower()
    # 精确匹配 code
    for s in skills:
        if (s.get("code") or "").lower() == query_lower:
            return s
    # 精确匹配 name
    for s in skills:
        if (s.get("name") or "").lower() == query_lower:
            return s
    # 模糊匹配
    for s in skills:
        code = (s.get("code") or "").lower()
        name = (s.get("name") or "").lower()
        if query_lower in code or query_lower in name:
            return s
    return None


def main():
    parser = argparse.ArgumentParser(description="发现 Skill — 浏览、搜索、查看详情")
    parser.add_argument("--search", "-s", type=str, help="按关键词搜索 Skill（名称/描述模糊匹配）")
    parser.add_argument("--detail", "-d", type=str, help="查看某个 Skill 的详情（按 code 或 name 匹配）")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON 格式")
    args = parser.parse_args()

    try:
        result = call_api()
    except Exception as e:
        print(f"❌ 请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 提取 skill 列表
    skills = result.get("data") or result.get("resultData") or []
    if isinstance(result, list):
        skills = result

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 详情模式
    if args.detail:
        skill = find_detail(skills, args.detail)
        if skill:
            print(format_detail(skill))
        else:
            print(f"❌ 未找到匹配 \"{args.detail}\" 的 Skill", file=sys.stderr)
            print(f"\n可用的 Skill:", file=sys.stderr)
            for s in skills:
                print(f"  - {s.get('code', '')} ({s.get('name', '')})", file=sys.stderr)
            sys.exit(1)
        return

    # 搜索模式
    if args.search:
        matched = search_skills(skills, args.search)
        if matched:
            print(f"🔍 搜索 \"{args.search}\" 匹配到 {len(matched)} 个结果：\n")
            print(format_list(matched))
        else:
            print(f"🔍 搜索 \"{args.search}\" 无结果", file=sys.stderr)
            print(f"\n平台共有 {len(skills)} 个 Skill，尝试其他关键词", file=sys.stderr)
            sys.exit(1)
        return

    # 列表模式（默认）
    print(f"📋 平台 Skill 列表\n")
    print(format_list(skills))


if __name__ == "__main__":
    main()
