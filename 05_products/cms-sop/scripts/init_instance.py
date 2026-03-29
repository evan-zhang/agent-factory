#!/usr/bin/env python3
"""
cms-sop: 初始化实例脚本
功能：原子性创建 SOP 实例目录，分配序号，初始化文件
支持 Lite（4件套）和 Full（7件套）两种模式
"""

import argparse
import fcntl
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='初始化 cms-sop 实例')
    parser.add_argument('--mode', choices=['lite', 'full'], default='lite',
                        help='实例模式：lite（四件套）或 full（七件套）')
    parser.add_argument('--title', required=True, help='任务标题')
    parser.add_argument('--owner', default='factory-orchestrator', help='负责人')
    parser.add_argument('--root', default='~/.openclaw/sop-instances/', help='实例根目录')
    return parser.parse_args()


def get_next_instance_number(root_dir: Path, date_str: str) -> int:
    pattern = re.compile(rf'^SOP-{date_str}-(\d{{3}})$')
    max_num = 0
    if root_dir.exists():
        for item in root_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def create_instance(root_dir: Path, instance_id: str, title: str, owner: str,
                    mode: str, templates_dir: Path) -> Path:
    instance_path = root_dir / instance_id
    instance_path.mkdir(parents=True, exist_ok=False)
    now = datetime.now().isoformat()

    state = {
        "id": instance_id,
        "title": title,
        "mode": mode,
        "owner": owner,
        "status": "DISCUSSING",
        "stage": "TARGET",
        "createdAt": now,
        "updatedAt": now,
        "deadline": "",
        "reason": "",
        "blockedReason": "",
        "checklistConfirmed": False,
        "confirmCount": 0,
        "upgradedFrom": "",
        "resume": {
            "lastCompleted": "",
            "currentBlocked": "",
            "waitingFor": "",
            "nextAction": "完成 TASK.md 目标定义"
        }
    }

    with open(instance_path / "state.json", 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # 四件套（Lite + Full 共有）
    lite_templates = {
        'TASK-template.md': 'TASK.md',
        'LOG-template.md': 'LOG.md',
        'RESULT-template.md': 'RESULT.md',
        'HANDOVER-template.md': 'HANDOVER.md'
    }

    lite_templates_dir = templates_dir / 'lite'
    for tpl_name, target_name in lite_templates.items():
        tpl_path = lite_templates_dir / tpl_name
        if not tpl_path.exists():
            raise FileNotFoundError(
                f"必需模板缺失: {tpl_path}\n"
                f"无法创建 {target_name}，实例初始化中止。"
            )
        content = tpl_path.read_text(encoding='utf-8')
        content = (content.replace('{{id}}', instance_id)
                   .replace('{{title}}', title)
                   .replace('{{owner}}', owner)
                   .replace('{{createdAt}}', now)
                   .replace('mode**：lite', f'mode**：{mode}'))
        (instance_path / target_name).write_text(content, encoding='utf-8')

    # Full 额外三件套
    if mode == 'full':
        full_templates = {
            'PLAN-template.md': 'PLAN.md',
            'DECISIONS-template.md': 'DECISIONS.md',
            'ARTIFACTS-template.md': 'ARTIFACTS.md'
        }
        full_templates_dir = templates_dir / 'full'
        for tpl_name, target_name in full_templates.items():
            tpl_path = full_templates_dir / tpl_name
            if not tpl_path.exists():
                raise FileNotFoundError(
                    f"必需模板缺失: {tpl_path}\n"
                    f"无法创建 {target_name}，实例初始化中止。"
                )
            content = tpl_path.read_text(encoding='utf-8')
            content = (content.replace('{{id}}', instance_id)
                       .replace('{{title}}', title)
                       .replace('{{owner}}', owner)
                       .replace('{{createdAt}}', now))
            (instance_path / target_name).write_text(content, encoding='utf-8')

    return instance_path


def main():
    args = parse_args()
    root_dir = Path(os.path.expanduser(args.root)).resolve()
    script_dir = Path(__file__).parent
    templates_dir = script_dir.parent / 'references' / 'templates'

    root_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d')
    lock_file = root_dir / '.create.lock'

    try:
        with open(lock_file, 'w') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                next_num = get_next_instance_number(root_dir, date_str)
                instance_id = f"SOP-{date_str}-{next_num:03d}"
                instance_path = create_instance(
                    root_dir, instance_id, args.title, args.owner, args.mode, templates_dir
                )
                print(str(instance_path))
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
