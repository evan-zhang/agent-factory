#!/usr/bin/env python3
"""
cas_setup.py — CAS 成长体系一键初始化脚本

功能：
1. 检查 .cas_initialized 标志文件
2. 检查三个复盘 cron 是否已存在
3. 不存在则通过 openclaw cron add 创建
4. 写入 .cas_initialized 标志
5. 输出初始化结果

使用：
  python3 cas_setup.py [--archive-root ~/.openclaw/chat-archive] [--agent factory-orchestrator] [--auto]
  --auto: 静默模式，不打印交互提示，供 handler.ts 自动调用
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


CRON_SPECS = [
    {
        "name": "CAS 每日成长日报",
        "cron": "0 19 * * *",
        "tz": "Asia/Shanghai",
        "message": (
            "请生成今日 CAS Daily Growth Log。"
            "步骤：1) 调用 cas_review.py daily 获取统计数字；"
            "2) 读取今日归档日志 ~/.openclaw/chat-archive/life/logs/$(date +%Y-%m-%d).md 分析真实对话内容；"
            "3) 按模板写出完整日报（含今日经验沉淀/主人洞察/数字分身逼近度/明日待跟进），不要留空占位符；"
            "4) 保存到 ~/.openclaw/chat-archive/life/daily/$(date +%Y-%m-%d).md；"
            "5) 发摘要给主人（📊 Daily Growth Log + 最大收获 + 需改进 + 关于主人新发现 + 文件路径）。"
        ),
    },
    {
        "name": "CAS 周复盘 Weekly Joint Review",
        "cron": "0 10 * * 6",
        "tz": "Asia/Shanghai",
        "message": (
            "请生成本周 CAS Weekly Joint Review。"
            "步骤：1) 读取本周7天日报；"
            "2) 提炼成功经验、失败教训、主人洞察；"
            "3) 写「致同伴」（第一人称，真诚，100-200字，有温度）；"
            "4) 识别跨 Agent 共识新规则并写入 memory/RULES.md；"
            "5) 按模板生成完整周复盘报告，保存到 ~/.openclaw/chat-archive/life/weekly/本周编号.md；"
            "6) 发摘要给主人，邀请深聊。"
        ),
    },
    {
        "name": "CAS 月复盘 Monthly Org Review",
        "cron": "0 18 * * 5",
        "tz": "Asia/Shanghai",
        "message": (
            "请先判断今天是否为本月最后一个周五。"
            "如果不是，回复「本周不是月末周五，跳过月复盘」即可。"
            "如果是，请生成本月 CAS Monthly Org Review："
            "1) 读取本月所有周复盘报告；"
            "2) 审查职能边界、协作链路、组织能力缺口；"
            "3) 深化主人画像，更新数字分身逼近度评分；"
            "4) 写各 Agent 月度寄语（真诚，有温度，100-300字）；"
            "5) 输出组织决议；"
            "6) 保存报告并归档决议；"
            "7) 发摘要给主人，等待 CEO 审批。"
        ),
    },
]


def get_existing_cron_names() -> list[str]:
    """通过 openclaw cron list --json 获取已有 cron 名称列表"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        jobs = data if isinstance(data, list) else data.get("jobs", [])
        return [j.get("name", "") for j in jobs]
    except Exception:
        return []


def create_cron(spec: dict, agent: str, auto: bool) -> bool:
    """调用 openclaw cron add 创建单个 cron，返回是否成功"""
    cmd = [
        "openclaw", "cron", "add",
        "--name", spec["name"],
        "--cron", spec["cron"],
        "--tz", spec["tz"],
        "--session", "session:agent:factory-orchestrator:main",
        "--agent", agent,
        "--message", spec["message"],
        "--announce",
        "--channel", "telegram",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception:
        return False


def run_setup(archive_root: str, agent: str, auto: bool) -> None:
    root = Path(archive_root).expanduser()
    flag = root / ".cas_initialized"

    if flag.exists():
        if not auto:
            print("✅ CAS 成长体系已初始化，无需重复操作。")
        return

    if not auto:
        print("🚀 开始初始化 CAS 成长体系...")

    existing_names = get_existing_cron_names()
    results = []

    for spec in CRON_SPECS:
        if spec["name"] in existing_names:
            results.append(f"  ⏭️  {spec['name']}（已存在，跳过）")
            continue
        ok = create_cron(spec, agent, auto)
        if ok:
            results.append(f"  ✅ {spec['name']} 创建成功")
        else:
            results.append(f"  ❌ {spec['name']} 创建失败（请手动执行 openclaw cron add）")

    # 写标志文件
    root.mkdir(parents=True, exist_ok=True)
    flag.write_text("initialized\n", encoding="utf-8")

    if not auto:
        print("\n初始化结果：")
        for r in results:
            print(r)
        print("\n🎉 CAS 成长体系初始化完成！")
        print("   - 每日 19:00 自动生成日报")
        print("   - 每周六 10:00 自动生成周复盘")
        print("   - 每月最后周五 18:00 自动生成月复盘")
    else:
        # auto 模式只输出一行供 handler.ts 判断
        print("CAS_SETUP_OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="CAS 成长体系一键初始化")
    parser.add_argument("--archive-root", default="~/.openclaw/chat-archive")
    parser.add_argument("--agent", default="factory-orchestrator")
    parser.add_argument("--auto", action="store_true", help="静默模式，供 handler.ts 自动调用")
    args = parser.parse_args()
    run_setup(args.archive_root, args.agent, args.auto)


if __name__ == "__main__":
    main()
