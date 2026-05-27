# KB Graph v0.1 测试说明

## 环境准备

```bash
pip3 install networkx python-louvain

# 设置 API Key（任选其一）
export MINIMAX_API_KEY="your-key"
export ZHIPU_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

---

## 测试 1：小规模验证（2个文件）

```bash
SKILL_ROOT=~/.../projects/2605261/kb-graph/scripts

mkdir -p /tmp/kb-test/2026/05

echo '# AI 是什么
人工智能（AI）是让机器具有人类智能的技术。' > /tmp/kb-test/2026/05/test-ai.md

echo '# Python 编程
Python 是一种广泛使用的高级编程语言。' > /tmp/kb-test/2026/05/test-python.md

# 全量构建
python3 $SKILL_ROOT/kb_graph.py build /tmp/kb-test
# 预期：built:2

# 查询
python3 $SKILL_ROOT/kb_graph.py query "AI" --dir /tmp/kb-test
# 预期：找到 test-ai.md

# 图谱
python3 $SKILL_ROOT/build_graph.py --dir /tmp/kb-test
# 预期：nodes:2
```

---

## 测试 2：增量跳过验证

```bash
# 再次构建（应跳过）
python3 $SKILL_ROOT/kb_graph.py build /tmp/kb-test
# 预期：built:0, skipped:2

# 修改文件后增量
echo '涉及机器学习。' >> /tmp/kb-test/2026/05/test-ai.md
python3 $SKILL_ROOT/kb_graph.py build /tmp/kb-test
# 预期：built:1, skipped:1
```

---

## 测试 3：Link Archivist 归档验证（需 PR #66 合并后）

```bash
ARCHIVE_SCRIPT=~/.../projects/2604131/link-archivist/scripts/archive_report.py

echo '# Test Report
这是测试报告正文。' > /tmp/test-report.md

python3 $ARCHIVE_SCRIPT /tmp/test-report.md /tmp \
  --entities '["AI","Python"]' \
  --summary "测试报告摘要" \
  --confidence high

# 检查 YAML frontmatter
head -15 /tmp/2026/05/K-*.md
# 预期含：entities / summary / confidence 字段
```

---

## 测试 4：真实 Vault（可选，耗时约 20-30 分钟）

```bash
VAULT="/Users/evan/Library/Mobile Documents/iCloud~md~obsidian/Documents/日常学习"
SKILL_ROOT=~/.../projects/2605261/kb-graph/scripts

nohup python3 $SKILL_ROOT/kb_graph.py build "$VAULT" \
  > /tmp/kb-vault.log 2>&1 &

# 每分钟检查
sleep 60 && python3 -c "
import json
d=json.load(open('$VAULT/.kb-workdir/entries.json'))
c=json.load(open('$VAULT/.kb-workdir/kb_cache.json'))
failed=sum(1 for v in c.values() if v.get(\"status\")==\"failed\")
print(failed)
"

# 最终验证
python3 -c "
import json
with open('$VAULT/.kb-workdir/kb_cache.json') as f:
    cache = json.load(f)
failed = sum(1 for v in cache.values() if v.get('status') == 'failed')
print(failed)
"
# 预期：0

# 验证图谱构建
python3 $SKILL_ROOT/build_graph.py --dir "$VAULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['stats']['node_count'])
"
# 预期：351

---

## PR 信息

- Link Archivist PR: https://github.com/evan-zhang/agent-factory/pull/66
- KB Graph 项目: `projects/2605261/kb-graph/`
