#!/usr/bin/env python3
"""
cms-sop: 交接脚本
功能：创建/更新 HANDOVER.md，更新状态为 HANDOVER_PENDING，记录到 LOG.md
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='cms-sop 任务交接')
    parser.add_argument('--instance-path', required=True)
    parser.add_argument('--from-owner', required=True)
    parser.add_argument('--to-owner', required=True)
    parser.add_argument('--reason', required=True)
    parser.add_argument('--next-steps', required=True)
    return parser.parse_args()


def load_state(instance_path: Path) -> dict:
    state_file = instance_path / 'state.json'
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    return json.loads(state_file.read_text(encoding='utf-8'))


def validate_from_owner(instance_path: Path, from_owner: str):
    state = load_state(instance_path)
    current_owner = state.get('owner')
    if from_owner != current_owner:
        print(f"交接失败：from-owner={from_owner} 与当前 owner={current_owner} 不一致",
              file=sys.stderr)
        sys.exit(1)


def create_handover_file(instance_path: Path, from_owner: str, to_owner: str,
                         reason: str, next_steps: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    instance_id = instance_path.name
    state = load_state(instance_path)
    title = state.get('title', '')

    existing = ''
    handover_file = instance_path / 'HANDOVER.md'
    if handover_file.exists():
        existing = handover_file.read_text(encoding='utf-8')

    header = f"""# HANDOVER.md - {instance_id}

---
- **实例 ID**：{instance_id}
- **任务标题**：{title}
- **文档状态**：DRAFT
- **版本**：v1.0
- **创建时间**：{timestamp}
- **mode**：{state.get('mode', 'lite')}
---

## 交接信息

- **交出方**：{from_owner}
- **接入方**：{to_owner}
- **交接时间**：{timestamp}
- **交接原因**：{reason}

## 后续步骤

{next_steps}

## 交接检查清单

- [ ] 已完成当前阶段的所有任务
- [ ] 已更新 state.json 状态
- [ ] 已在 LOG.md 记录关键操作
- [ ] 已向新负责人说明背景和上下文

---

*交接时间: {timestamp}*
"""
    handover_file.write_text(header, encoding='utf-8')
    return handover_file


def append_handover_to_log(instance_path: Path, from_owner: str, to_owner: str, reason: str):
    log_file = instance_path / 'LOG.md'
    if not log_file.exists():
        log_file.write_text(
            f"# LOG.md - {instance_path.name}\n\n"
            "| 时间 | 阶段 | 操作 | 详情 |\n"
            "|------|------|------|------|\n",
            encoding='utf-8'
        )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n| {timestamp} | HANDOVER | {from_owner} → {to_owner} | {reason} |\n"
    log_file.write_text(log_file.read_text(encoding='utf-8') + entry, encoding='utf-8')


def call_update_state(instance_path: Path, to_owner: str, reason: str):
    script_dir = Path(__file__).parent
    update_script = script_dir / 'update_state.py'
    if not update_script.exists():
        raise FileNotFoundError(f"update_state.py 不存在: {update_script}")

    state = load_state(instance_path)
    current_stage = state.get('stage', 'TARGET')

    cmd = [
        'python3', str(update_script),
        '--instance-path', str(instance_path),
        '--status', 'HANDOVER_PENDING',
        '--stage', current_stage,
        '--owner', to_owner,
        '--reason', f'交接: {reason}',
        '--confirm',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"update_state.py 执行失败: {result.stderr.strip()}")


def main():
    args = parse_args()
    instance_path = Path(args.instance_path).resolve()

    if not instance_path.exists():
        print(f"ERROR: 实例目录不存在: {instance_path}", file=sys.stderr)
        sys.exit(1)

    try:
        validate_from_owner(instance_path, args.from_owner)

        handover_file = create_handover_file(
            instance_path, args.from_owner, args.to_owner,
            args.reason, args.next_steps
        )
        print(f"✓ 已创建: {handover_file}")

        append_handover_to_log(instance_path, args.from_owner, args.to_owner, args.reason)
        print("✓ 已追加交接记录到 LOG.md")

        call_update_state(instance_path, args.to_owner, args.reason)
        print("✓ 已更新状态为 HANDOVER_PENDING")

        print(f"\n交接完成: {args.from_owner} → {args.to_owner}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
