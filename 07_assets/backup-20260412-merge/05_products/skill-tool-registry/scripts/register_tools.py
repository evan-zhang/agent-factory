#!/usr/bin/env python3
"""
register_tools.py -- Tool registration and discovery for OpenClaw agents

Multi-layer discovery:
  ~/.openclaw/skills/         -> Gateway shared skills
  ~/.openclaw/workspace/skills/ -> Agent private skills

Commands:
  python3 register_tools.py discover          # Show full deployment topology
  python3 register_tools.py list              # List all skills at all levels
  python3 register_tools.py register <skill>  # Register skill's tools (auto-detect scope)
  python3 register_tools.py register-all      # Register all skills at all levels
  python3 register_tools.py register --scope gateway <skill>   # Force gateway scope
  python3 register_tools.py register --scope agent <skill>    # Force agent scope
  python3 register_tools.py --help            # Show this help

All output is ASCII-safe.
"""
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Layer paths
OPENCLAW_HOME = Path.home() / ".openclaw"
GATEWAY_SKILLS = OPENCLAW_HOME / "skills"
AGENT_SKILLS = OPENCLAW_HOME / "workspace" / "skills"
GATEWAY_TOOLS = OPENCLAW_HOME / "skills" / "TOOLS.md"
AGENT_TOOLS = OPENCLAW_HOME / "workspace" / "TOOLS.md"


def parse_frontmatter(content):
    """Parse tools_provided from SKILL.md frontmatter."""
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return []
    block = fm_match.group(1)
    tools = []
    in_tools = False
    current = {}
    for line in block.split('\n'):
        if line.startswith('tools_provided:'):
            in_tools = True
            continue
        if in_tools:
            if line.startswith('  - name:'):
                if current:
                    tools.append(current)
                current = {'name': line.split('name:')[1].strip()}
            elif ':' in line:
                key = line.split(':')[0].strip()
                val = ':'.join(line.split(':')[1:]).strip().strip('"').strip("'")
                if key in ('category', 'risk_level', 'permission', 'description', 'channels', 'status'):
                    current[key] = val
    if current:
        tools.append(current)
    return tools


def read_tools_md(path):
    """Read TOOLS.md and return list of (category, tool_name, status)."""
    if not path.exists():
        return {}
    content = path.read_text(encoding='utf-8')
    tools = {}
    current_cat = None
    for line in content.split('\n'):
        if line.startswith('## '):
            parts = line.lstrip('## ').split('--')[0].strip().split('  ')
            current_cat = parts[0].strip()
            tools[current_cat] = []
        elif line.startswith('### '):
            name = line.lstrip('### ').strip()
            if current_cat:
                tools[current_cat].append({'name': name})
    return tools


def write_tools_md(path, tools):
    """Write tools dict to TOOLS.md at given path."""
    cat_names = {
        'search': 'search -- Search Tools',
        'file': 'file -- File Operations',
        'exec': 'exec -- Execution Tools',
        'memory': 'memory -- Memory Tools',
        'system': 'system -- System Tools',
        'network': 'network -- Network Tools',
    }
    lines = [
        "# TOOLS.md -- Tool Registry",
        "---",
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        "---",
        "",
        "## Tool Metadata Schema",
        "",
        "| Field | Description |",
        "|-------|-------------|",
        "| name | Tool name |",
        "| category | Category |",
        "| risk_level | Risk (low/medium/high/critical) |",
        "| permission | Permission (read/write/exec/admin) |",
        "| status | active/deprecated/disabled |",
        "",
    ]
    for cat, cat_tools in tools.items():
        if not cat_tools:
            continue
        lines.append(f"## {cat_names.get(cat, cat)}")
        lines.append("")
        for t in cat_tools:
            lines.append(f"### {t['name']}")
            for key in ['category', 'risk_level', 'permission', 'description', 'channels', 'status']:
                val = t.get(key, '')
                if val:
                    lines.append(f"- **{key}**: {val}")
            lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8')


def merge_tool(tools, tool_meta, category):
    name = tool_meta.get('name', '')
    if not name:
        return
    tools[category] = [t for t in tools.get(category, []) if t.get('name') != name]
    tools[category].append(tool_meta)


def create_lifecycle(tool_meta, scope):
    """Create per-tool lifecycle JSON."""
    tools_dir = OPENCLAW_HOME / "memory" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    tool_file = tools_dir / f"{tool_meta['name']}.json"
    data = {
        'name': tool_meta['name'],
        'scope': scope,
        'category': tool_meta.get('category', ''),
        'risk_level': tool_meta.get('risk_level', ''),
        'permission': tool_meta.get('permission', ''),
        'description': tool_meta.get('description', ''),
        'status': tool_meta.get('status', 'active'),
        'registered_at': datetime.now().isoformat(),
        'skill': tool_meta.get('skill', ''),
        'log': []
    }
    tool_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def log_event(tool_name, event, detail=''):
    tool_file = OPENCLAW_HOME / "memory" / "tools" / f"{tool_name}.json"
    if tool_file.exists():
        data = json.loads(tool_file.read_text(encoding='utf-8'))
        data['log'].append({'time': datetime.now().isoformat(), 'event': event, 'detail': detail})
        tool_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def find_skill_in_dir(skill_name, base_dir):
    """Find a skill directory within base_dir. Handles 'skill-' prefix variants."""
    if not base_dir.exists():
        return None
    name_variants = [skill_name, f"skill-{skill_name}", skill_name.replace("skill-", "")]
    for item in base_dir.iterdir():
        if item.is_dir():
            if item.name in name_variants or skill_name in item.name:
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    return item
    return None


def discover_topology():
    """Discover the full deployment topology."""
    print("\n=== OpenClaw Deployment Topology ===\n")
    print(f"OPENCLAW_HOME: {OPENCLAW_HOME}")
    print(f"Gateway skills: {GATEWAY_SKILLS}")
    print(f"Agent skills:   {AGENT_SKILLS}")
    print()

    # Gateway layer
    print("[Gateway Layer] -- ~/.openclaw/skills/")
    if GATEWAY_SKILLS.exists():
        gateway_tools = read_tools_md(GATEWAY_TOOLS)
        gw_total = sum(len(v) for v in gateway_tools.values())
        print(f"  TOOLS.md: {gw_total} tools registered")
        skills = [d.name for d in GATEWAY_SKILLS.iterdir() if d.is_dir()]
        for s in sorted(skills):
            skill_md = GATEWAY_SKILLS / s / "SKILL.md"
            tools = parse_frontmatter(skill_md.read_text(encoding='utf-8')) if skill_md.exists() else []
            print(f"  - {s}/  [{len(tools)} tools declared]")
    else:
        print("  (directory does not exist)")
    print()

    # Agent layer
    print("[Agent Layer] -- ~/.openclaw/workspace/skills/")
    if AGENT_SKILLS.exists():
        agent_tools = read_tools_md(AGENT_TOOLS)
        ag_total = sum(len(v) for v in agent_tools.values())
        print(f"  TOOLS.md: {ag_total} tools registered")
        skills = [d.name for d in AGENT_SKILLS.iterdir() if d.is_dir()]
        for s in sorted(skills):
            skill_md = AGENT_SKILLS / s / "SKILL.md"
            tools = parse_frontmatter(skill_md.read_text(encoding='utf-8')) if skill_md.exists() else []
            print(f"  - {s}/  [{len(tools)} tools declared]")
    else:
        print("  (directory does not exist)")
    print()

    # Unified TOOLS.md
    print("[Unified View] -- All registered tools")
    all_tools = {}
    for path, scope in [(GATEWAY_TOOLS, 'gateway'), (AGENT_TOOLS, 'agent')]:
        if path.exists():
            content = path.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('### '):
                    name = line.lstrip('### ').strip()
                    if name not in all_tools:
                        all_tools[name] = scope
    for name, scope in sorted(all_tools.items()):
        print(f"  {name}  [{scope}]")


def list_all_skills():
    """List all skills at all levels."""
    print("\n=== All Skills ===\n")
    all_skills = []
    for label, base_dir in [("gateway", GATEWAY_SKILLS), ("agent", AGENT_SKILLS)]:
        if base_dir.exists():
            for item in sorted(base_dir.iterdir()):
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    tools = parse_frontmatter(skill_md.read_text(encoding='utf-8')) if skill_md.exists() else []
                    all_skills.append({
                        'name': item.name,
                        'scope': label,
                        'path': str(item),
                        'tools': [t['name'] for t in tools],
                        'count': len(tools)
                    })
    for s in all_skills:
        print(f"  [{s['scope']:7s}] {s['name']}")
        print(f"            path: {s['path']}")
        print(f"            tools: {s['count']} -- {s['tools']}")
        print()


def register_skill(skill_name, scope=None):
    """Register a skill's tools. Auto-detect scope if not specified."""
    # Search both layers
    skill_path = None
    detected_scope = None

    if scope:
        dirs = [("gateway", GATEWAY_SKILLS)] if scope == 'gateway' else [("agent", AGENT_SKILLS)]
    else:
        dirs = [("gateway", GATEWAY_SKILLS), ("agent", AGENT_SKILLS)]

    for s, base_dir in dirs:
        found = find_skill_in_dir(skill_name, base_dir)
        if found:
            skill_path = found
            detected_scope = s
            break

    if not skill_path:
        print(f"Error: Skill '{skill_name}' not found in gateway or agent skills directories.")
        return

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"Error: SKILL.md not found in {skill_path}")
        return

    tools_meta = parse_frontmatter(skill_md.read_text(encoding='utf-8'))
    if not tools_meta:
        print(f"[WARN] No tools_provided found in {skill_md}")
        return

    target_scope = detected_scope
    tools_path = GATEWAY_TOOLS if target_scope == 'gateway' else AGENT_TOOLS
    print(f"\n[REGISTER] {skill_name} -> {target_scope} scope")
    print(f"  path: {skill_path}")
    print(f"  tools: {[t['name'] for t in tools_meta]}")

    # Read existing tools (or start fresh for that scope)
    existing = read_tools_md(tools_path)
    for tm in tools_meta:
        tm['skill'] = skill_name
        cat = tm.get('category', 'system')
        if cat not in existing:
            existing[cat] = []
        merge_tool(existing, tm, cat)
        create_lifecycle(tm, target_scope)
        log_event(tm['name'], 'registered', f'from {skill_name} ({target_scope} scope)')
        print(f"  [OK] {tm['name']} -> {cat}")

    write_tools_md(tools_path, existing)
    total = sum(len(v) for v in existing.values())
    print(f"\n  {tools_path} updated ({total} tools total)")


def register_all():
    """Auto-discover all skills and register them."""
    print("\n[AUTO-REGISTER ALL] Discovering skills across all layers...\n")
    registered = []
    for label, base_dir in [("gateway", GATEWAY_SKILLS), ("agent", AGENT_SKILLS)]:
        if base_dir.exists():
            for item in sorted(base_dir.iterdir()):
                if item.is_dir() and (item / "SKILL.md").exists():
                    skill_name = item.name
                    print(f"  Processing [{label}]: {skill_name}")
                    # Check if already registered by reading tools_meta
                    tools_meta = parse_frontmatter((item / "SKILL.md").read_text(encoding='utf-8'))
                    if not tools_meta:
                        print(f"    (no tools_provided, skipping)")
                        continue
                    tools_path = GATEWAY_TOOLS if label == 'gateway' else AGENT_TOOLS
                    existing = read_tools_md(tools_path)
                    for tm in tools_meta:
                        tm['skill'] = skill_name
                        cat = tm.get('category', 'system')
                        if cat not in existing:
                            existing[cat] = []
                        merge_tool(existing, tm, cat)
                        create_lifecycle(tm, label)
                        log_event(tm['name'], 'auto-registered', f'from {skill_name}')
                    write_tools_md(tools_path, existing)
                    registered.append((skill_name, label, len(tools_meta)))
    print(f"\n[RESULT] {len(registered)} skills processed:")
    for name, scope, count in registered:
        print(f"  {name} [{scope}]: {count} tools")


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'discover':
        discover_topology()
    elif cmd == 'list':
        list_all_skills()
    elif cmd == 'register':
        scope = None
        if '--scope' in args:
            idx = args.index('--scope')
            scope = args[idx + 1] if idx + 1 < len(args) else None
            args = args[:idx] + args[idx+2:]
        skill_name = args[0] if args else None
        if not skill_name:
            print("Error: specify skill name")
            print(__doc__)
            sys.exit(1)
        register_skill(skill_name, scope=scope)
    elif cmd == 'register-all':
        register_all()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
