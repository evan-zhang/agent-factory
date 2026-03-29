#!/usr/bin/env python3
"""
cms-sop: 更新实例状态脚本
支持状态管理、语义化操作、高风险门禁、多轮确认计数
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

STATUS_CHOICES = [
    'DISCUSSING', 'READY', 'RUNNING', 'REVIEWING', 'WAITING_USER',
    'BLOCKED', 'PAUSED', 'ON_HOLD', 'CANCELLED', 'DONE', 'ARCHIVED',
    'HANDOVER_PENDING', 'UPGRADED',
]

STAGE_CHOICES = ['TARGET', 'PLAN', 'CHECKLIST', 'EXECUTE', 'ARCHIVE', 'DONE']

HIGH_RISK_STATUSES = {'DONE', 'ARCHIVED', 'UPGRADED'}


def parse_args():
    parser = argparse.ArgumentParser(description='更新 cms-sop 实例状态')
    parser.add_argument('--instance-path', required=True)
    parser.add_argument('--status', choices=STATUS_CHOICES)
    parser.add_argument('--stage', choices=STAGE_CHOICES)
    parser.add_argument('--owner')
    parser.add_argument('--reason')
    parser.add_argument('--waiting-for', help='等待用户的事项（配合 wait-user 使用）')
    parser.add_argument(
        '--action',
        choices=['pause', 'resume', 'shelve', 'restart',
                 'wait-user', 'reviewed', 'increment-confirm'],
        help='语义化操作'
    )
    parser.add_argument('--confirm', action='store_true', help='显式确认高风险操作')
    return parser.parse_args()


def load_state(instance_path: Path) -> dict:
    state_file = instance_path / 'state.json'
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    return json.loads(state_file.read_text(encoding='utf-8'))


def save_state(instance_path: Path, state: dict):
    state_file = instance_path / 'state.json'
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')


def append_log_entry(instance_path: Path, stage: str, operation: str,
                     reason: Optional[str], detail: str):
    log_file = instance_path / 'LOG.md'
    if not log_file.exists():
        # LOG.md 缺失时自动创建基础结构，确保审计链路不丢失
        log_file.write_text(
            f"# LOG.md - {instance_path.name}\n\n"
            "| 时间 | 阶段 | 操作 | 详情 |\n"
            "|------|------|------|------|\n",
            encoding='utf-8'
        )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    note = reason or 'N/A'
    entry = f"\n| {timestamp} | {stage} | {operation} | {detail}; 原因: {note} |\n"
    log_file.write_text(log_file.read_text(encoding='utf-8') + entry, encoding='utf-8')


def apply_action(action: str, current_reason: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
    mapping = {
        'pause': ('PAUSED', current_reason or '暂停', None),
        'resume': ('RUNNING', current_reason or '恢复执行', None),
        'shelve': ('ON_HOLD', current_reason or '搁置', None),
        'restart': ('RUNNING', current_reason or '重启执行', ''),
        'wait-user': ('WAITING_USER', current_reason or '等待用户', None),
        'reviewed': ('RUNNING', current_reason or '复核通过', None),
    }
    if action in mapping:
        return mapping[action]
    raise ValueError(f'不支持的 action: {action}')


def ensure_checklist_completed(state: dict):
    if state.get('checklistConfirmed') is False:
        raise PermissionError('执行前确认单未完成，禁止进入 RUNNING')


def main():
    args = parse_args()
    instance_path = Path(args.instance_path).resolve()

    if not instance_path.exists():
        print(f"ERROR: 实例目录不存在: {instance_path}", file=sys.stderr)
        sys.exit(1)

    try:
        state = load_state(instance_path)
        old_status = state.get('status', 'DISCUSSING')
        old_stage = state.get('stage', 'TARGET')
        old_owner = state.get('owner')

        # 语义化操作
        if args.action == 'increment-confirm':
            state['confirmCount'] = state.get('confirmCount', 0) + 1
            count = state['confirmCount']
            state['updatedAt'] = datetime.now().isoformat()
            save_state(instance_path, state)
            append_log_entry(instance_path, old_stage, 'INCREMENT_CONFIRM',
                             args.reason, f'confirmCount: {count}')
            print(f"✓ confirmCount: {count}")
            if count >= 3:
                import json as _json
                print(_json.dumps({
                    "type": "INTERVENTION_REQUIRED",
                    "reason": "多轮未达成一致",
                    "instanceId": state['id'],
                    "confirmCount": count
                }, ensure_ascii=False))
            return

        new_status = args.status if args.status else old_status
        new_stage = args.stage if args.stage else old_stage
        reason = args.reason

        # 语义化操作映射
        if args.action in ('pause', 'resume', 'shelve', 'restart', 'wait-user', 'reviewed'):
            new_status, reason_override, blocked_clear = apply_action(args.action, reason)
            if reason_override is not None and reason is None:
                reason = reason_override
            if blocked_clear == '':
                state['blockedReason'] = state.get('blockedReason', '')
        elif args.action:
            raise ValueError(f'不支持的 action: {args.action}')

        # wait-user 时更新 waitingFor
        if args.action == 'wait-user' and args.waiting_for:
            # 使用 or {} 而非 .get(key, {})，确保 None 值也被替换为 {}
            resume = state.get('resume') or {}
            resume['waitingFor'] = args.waiting_for
            resume['nextAction'] = f"等待用户: {args.waiting_for}"
            state['resume'] = resume

        # 进入 RUNNING 前门禁
        if new_status == 'RUNNING':
            ensure_checklist_completed(state)

        # 高风险门禁
        owner_changed = bool(args.owner and args.owner != old_owner)
        high_risk = owner_changed or (new_status in HIGH_RISK_STATUSES)
        if high_risk and not args.confirm:
            print('高风险操作需要显式确认，请加 --confirm 参数', file=sys.stderr)
            sys.exit(1)

        # 更新 state.json
        state['status'] = new_status
        state['stage'] = new_stage
        state['updatedAt'] = datetime.now().isoformat()
        if args.owner:
            state['owner'] = args.owner
        if reason is not None:
            state['reason'] = reason

        save_state(instance_path, state)

        owner_detail = ''
        if args.owner and args.owner != old_owner:
            owner_detail = f'; owner: {old_owner} → {args.owner}'
        detail = f'status: {old_status} → {new_status}; stage: {old_stage} → {new_stage}{owner_detail}'
        append_log_entry(instance_path, new_stage, args.action.upper() if args.action else 'UPDATE_STATE',
                         reason, detail)

        print(f"✓ 状态已更新: {new_status} / {new_stage}")
        if owner_changed:
            print(f"✓ Owner 已切换: {old_owner} → {args.owner}")

    except PermissionError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
