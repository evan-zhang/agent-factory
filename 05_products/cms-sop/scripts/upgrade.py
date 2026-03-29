#!/usr/bin/env python3
"""
cms-sop: Lite→Full 升级脚本
功能：将 Lite 实例升级为 Full 实例，继承已有文件，创建新的 Full 专有文件
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='cms-sop Lite→Full 升级')
    parser.add_argument('--instance-path', required=True, help='Lite 实例目录路径')
    parser.add_argument('--reason', required=True, help='升级原因')
    return parser.parse_args()


def load_state(instance_path: Path) -> dict:
    state_file = instance_path / 'state.json'
    if not state_file.exists():
        raise FileNotFoundError(f"state.json 不存在: {state_file}")
    return json.loads(state_file.read_text(encoding='utf-8'))


def validate_lite_instance(state: dict):
    """验证：必须是 Lite 模式，且 status 非 DONE/ARCHIVED"""
    if state.get('mode') != 'lite':
        raise ValueError(
            f"实例 {state.get('id')} 的 mode={state.get('mode')}，不是 lite，无法升级。\n"
            "upgrade.py 只允许对 Lite 实例使用。\n"
            "请确认：1) 已读取 references/lite-guide.md；2) 使用了正确的 Lite 实例路径。"
        )
    if state.get('status') in ('DONE', 'ARCHIVED'):
        raise ValueError(
            f"实例 {state.get('id')} 的 status={state.get('status')}，已完成或已归档，无法升级。\n"
            "只能对进行中的 Lite 实例执行升级。"
        )


def inject_inheritance_declaration(task_file: Path, instance_id: str, reason: str):
    """在 TASK.md 元数据块之后、第一个 ## 标题之前插入继承声明区"""
    content = task_file.read_text(encoding='utf-8')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    declaration = f"""## 继承声明

- **升级自**：{instance_id}
- **升级时间**：{now}
- **升级原因**：{reason}
- **继承文件**：TASK.md、LOG.md

> 原 Lite 实例：[{instance_id}]()

"""

    # 找到元数据块结束位置（在 "---" 之后的内容中找第二个 "---"）
    meta_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if meta_match:
        # 在元数据块之后、第一个 ## 标题之前插入
        insert_pos = meta_match.end()
        new_content = content[:insert_pos] + '\n' + declaration + content[insert_pos:]
    else:
        # 没有找到标准元数据块，直接在顶部插入
        new_content = declaration + content

    task_file.write_text(new_content, encoding='utf-8')


def tag_log_as_inherited(log_file: Path, instance_id: str):
    """LOG.md 所有内容行前加 [继承自Lite] 标记"""
    content = log_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    marked_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过空行、标题、水平线和元数据
        if stripped and not stripped.startswith('---') and not stripped.startswith('#') and not stripped.startswith('*'):
            # 检查是否是表格内容行（以 | 开头，且不是纯分隔线）
            if stripped.startswith('|'):
                # 纯分隔线行（如 |------|------|）不标记，只标记真实数据行
                cell_content = stripped.strip('|')
                # 分隔线内容只含 -、:、空格（没有实际文字内容）
                is_separator = not any(c.isalnum() for c in cell_content)
                if is_separator:
                    marked_lines.append(line)  # 分隔线不标记
                else:
                    marked_lines.append(line.replace('|', '| [继承自Lite]', 1))  # 数据行标记
            else:
                marked_lines.append(line)
        else:
            marked_lines.append(line)

    # 追加升级分隔线
    separator = f"\n\n---\n*升级为 Full 模式 | {now} | 原实例: {instance_id}*\n\n"
    new_content = '\n'.join(marked_lines) + separator
    log_file.write_text(new_content, encoding='utf-8')


def create_full_documents(instance_path: Path, templates_dir: Path,
                           instance_id: str, title: str, owner: str):
    """创建 PLAN.md / DECISIONS.md / ARTIFACTS.md"""
    now = datetime.now().isoformat()

    full_templates = {
        'PLAN-template.md': 'PLAN.md',
        'DECISIONS-template.md': 'DECISIONS.md',
        'ARTIFACTS-template.md': 'ARTIFACTS.md'
    }

    for tpl_name, target_name in full_templates.items():
        tpl_path = templates_dir / 'full' / tpl_name
        if tpl_path.exists():
            content = tpl_path.read_text(encoding='utf-8')
            content = (content.replace('{{id}}', instance_id)
                       .replace('{{title}}', title)
                       .replace('{{owner}}', owner)
                       .replace('{{createdAt}}', now))
            (instance_path / target_name).write_text(content, encoding='utf-8')


def update_full_state(state: dict, reason: str) -> dict:
    """生成 Full 模式的新 state"""
    now = datetime.now().isoformat()
    original_id = state['id']

    state['mode'] = 'full'
    state['status'] = 'DISCUSSING'
    state['upgradedFrom'] = original_id
    state['confirmCount'] = 0
    state['blockedReason'] = state.get('blockedReason', '')
    state['updatedAt'] = now
    state['resume'] = {
        'lastCompleted': '',
        'currentBlocked': '',
        'waitingFor': '',
        'nextAction': '补充 PLAN.md 执行计划'
    }
    state['reason'] = reason
    return state


def update_original_state(instance_path: Path, state: dict):
    """将原 Lite 实例状态设为 UPGRADED"""
    state['status'] = 'UPGRADED'
    state['updatedAt'] = datetime.now().isoformat()
    state_file = instance_path / 'state.json'
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')


def append_upgrade_log(instance_path: Path, instance_id: str, reason: str):
    """追加升级记录到 LOG.md"""
    log_file = instance_path / 'LOG.md'
    if not log_file.exists():
        log_file.write_text(
            f"# LOG.md - {instance_id}\n\n"
            "| 时间 | 阶段 | 操作 | 详情 |\n"
            "|------|------|------|------|\n",
            encoding='utf-8'
        )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n| {timestamp} | UPGRADE | 升级为 Full 模式 | OK | reason: {reason} |\n"
    log_file.write_text(log_file.read_text(encoding='utf-8') + entry, encoding='utf-8')


def main():
    args = parse_args()
    instance_path = Path(args.instance_path).resolve()

    if not instance_path.exists():
        print(f"ERROR: 实例目录不存在: {instance_path}", file=sys.stderr)
        sys.exit(1)

    try:
        state = load_state(instance_path)
        instance_id = state['id']
        title = state.get('title', '')
        owner = state.get('owner', '')

        print(f"验证 Lite 实例: {instance_id} ...")
        validate_lite_instance(state)
        print("✓ 验证通过")

        # 1. TASK.md 插入继承声明
        task_file = instance_path / 'TASK.md'
        if task_file.exists():
            inject_inheritance_declaration(task_file, instance_id, args.reason)
            # 更新元数据中的 mode 字段
            content = task_file.read_text(encoding='utf-8')
            content = content.replace('mode**：lite', 'mode**：full')
            task_file.write_text(content, encoding='utf-8')
            print(f"✓ 已更新 TASK.md（插入继承声明，mode→full）")

        # 2. LOG.md 标记继承
        log_file = instance_path / 'LOG.md'
        if log_file.exists():
            tag_log_as_inherited(log_file, instance_id)
            # 更新元数据中的 mode 字段
            content = log_file.read_text(encoding='utf-8')
            content = content.replace('mode**：lite', 'mode**：full')
            log_file.write_text(content, encoding='utf-8')
            print(f"✓ 已更新 LOG.md（标记为继承，mode→full）")

        # 3. 创建 Full 专有文档
        script_dir = Path(__file__).parent
        templates_dir = script_dir.parent / 'references' / 'templates'
        create_full_documents(instance_path, templates_dir, instance_id, title, owner)
        print("✓ 已创建 PLAN.md / DECISIONS.md / ARTIFACTS.md")

        # 4. 更新 state.json 为 Full
        new_state = update_full_state(state, args.reason)
        state_file = instance_path / 'state.json'
        state_file.write_text(json.dumps(new_state, indent=2, ensure_ascii=False), encoding='utf-8')
        print("✓ 已更新 state.json（mode=full, status=DISCUSSING, upgradedFrom set）")

        # 5. 追加升级日志
        append_upgrade_log(instance_path, instance_id, args.reason)

        print(f"\n✓ 升级完成: {instance_id} (lite → full)")
        print(f"  状态已重置为 DISCUSSING，请补充 PLAN.md 执行计划")

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
