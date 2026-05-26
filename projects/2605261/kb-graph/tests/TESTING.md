# KB Graph v0.1 测试说明

## 项目概述

KB Graph v0.1 是一个为 Markdown 文件构建知识库图谱的独立 OpenClaw Skill，支持增量索引、LLM 语义编译、Leiden 社区发现和双引擎查询。

## 测试环境

- Python 3.8+
- Linux/macOS
- （可选）LLM API 配置（MiniMax/DeepSeek/GLM）

## 测试准备

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/evan-zhang/agent-factory.git
cd agent-factory

# Sparse checkout KB Graph
git sparse-checkout set projects/2605261/kb-graph
```

### 2. 创建测试数据

```bash
# 创建测试目录
mkdir -p /tmp/kb-graph-test

# 创建测试 Markdown 文件
cat > /tmp/kb-graph-test/doc1.md << 'EOF'
# AI Agent 开发指南

## 概述
AI Agent 是能够自主执行任务的智能系统。

## 核心组件
- 感知模块
- 规划模块
- 执行模块
- 记忆模块
EOF

cat > /tmp/kb-graph-test/doc2.md << 'EOF'
# Python 并发编程

## 多线程
Python 的 threading 模块提供多线程支持。

## 异步编程
asyncio 是 Python 3.4+ 内置的异步编程库。
EOF

cat > /tmp/kb-graph-test/doc3.md << 'EOF'
# 微服务架构设计

## 原则
- 单一职责
- 独立部署
- 接口标准化
EOF
```

## 功能测试

### 测试 1：全量构建（测试模式）

**目标**：验证扫描、索引、缓存功能，不依赖 LLM API

```bash
cd projects/2605261/kb-graph

# 执行全量构建（测试模式）
python3 scripts/kb_graph.py build /tmp/kb-graph-test --test-mode
```

**预期结果**：
```json
{
  "ok": true,
  "built": 3,
  "skipped": 0,
  "errors": [],
  "failed_files": []
}
```

**验证点**：
- ✓ `.kb-workdir/kb_cache.json` 缓存文件已生成
- ✓ `.kb-workdir/entries.json` 索引数据已生成
- ✓ `.kb-index.md` YAML 索引文件已生成
- ✓ 每个文件都有 sha256 和状态标记为 "success"

### 测试 2：索引验证

**目标**：验证索引文件格式正确

```bash
# 验证索引文件
python3 scripts/validate_index.py --index /tmp/kb-graph-test/.kb-index.md
```

**预期结果**：
```json
{
  "ok": true,
  "errors": [],
  "warnings": ["Graph data not found in HTML comments"]
}
```

**说明**：warning 是正常的，因为还没有生成图谱数据。

### 测试 3：状态检查

**目标**：验证缓存统计功能

```bash
# 查看状态
python3 scripts/identity scripts/kb_graph.py status /tmp/kb-graph-test
```

**预期结果**：
```json
{
  "ok": true,
  "total_cached": 3,
  "success": 3,
  "failed": 0,
  "cache_path": "/tmp/kb-graph-test/.kb-workdir/kb_cache.json"
}
```

### 测试 4：增量更新（测试模式）

**目标**：验证增量更新只处理变更的文件

```bash
# 修改一个文件
echo "" >> /tmp/kb-graph-test/doc1.md

# 执行增量更新
python3 scripts/kb_graph.py update /tmp/kb-graph-test --test-mode
```

**预期结果**：
```json
{
  "ok": true,
  "updated": 1,
  "skipped": 2,
  "errors": [],
  "failed_files": []
}
```

### 测试 5：单文件更新

**目标**：验证单文件更新功能

```bash
# 创建新文件
cat > /tmp/kb-graph-test/doc4.md << 'EOF'
# 数据库优化
索引设计和查询优化是关键。
EOF

# 更新单文件
python3 scripts/kb_graph.py update-single /tmp/kb-graph-test/doc4.md --test-mode
```

**预期结果**：
```json
{
  "ok": true,
  "entry": {
    "title": "数据库优化",
    "summary": "测试模式：...",
    "entities": ["实体1", "实体2"],
    "tags": ["AI", "架构"],
    "confidence": "medium",
    ...
  }
}
```

### 测试 6：Lint 质量检查

**目标**：验证 Lint 功能

```bash
# 执行 lint
python3 scripts/kb_graph.py lint /tmp/kb-graph-test
```

**预期结果**：
```json
{
  "ok": true,
  "issues": []
}
```

### 测试 7：文件删除处理

**目标**：验证删除文件后索引正确更新

```bash
# 删除一个文件
rm /tmp/kb-graph-test/doc3.md

# 执行更新
python3 scripts/kb_graph.py update /tmp/kb-graph-test --test-mode

# 验证缓存
python3 scripts/kb_graph.py status /tmp/kb-graph-test
```

**预期结果**：
- 缓存中的文件数应该减少
- `.kb-index.md` 中不再包含删除的文件

### 测试 8：全量构建（生产模式，需要 LLM API）

**目标**：验证完整的 LLM 语义编译流程

**前提条件**：
- 配置 LLM API Key（MiniMax/DeepSeek/GLM 之一）
- 创建配置文件 `~/.openclaw/kb-graph-config.json`

```json
{
  "watch_dirs": ["/tmp/kb-graph-test"],
  "llm_provider": "minimax",
  "model": "MiniMax-M2.7-highspeed",
  "fallback_models": ["GLM-Z1-0528", "deepseek-v4-flash"]
}
```

```bash
# 清理缓存
rm -rf /tmp/kb-graph-test/.kb-workdir

# 执行全量构建（生产模式）
python3 scripts/kb_graph.py build /tmp/kb-graph-test
```

**预期结果**：
- 每个文件都有真实的摘要、实体和标签
- confidence 字段为 "high" 或 "medium"
- entities 包含从内容中提取的真实实体
- tags 从预定义标签表中选择

## 边界测试

### 测试 9：空目录处理

```bash
# 测试空目录
mkdir -p /tmp/kb-graph-empty
python3 scripts/kb_graph.py build /tmp/kb-graph-empty --test-mode
```

**预期结果**：
```json
{
  "ok": true,
  "built": 0,
  "skipped": 0,
  "errors": [],
  "failed_files": []
}
```

### 测试 10：不支持文件类型

```bash
# 测试不支持文件
cat > /tmp/kb-graph-test/doc5.txt << 'EOF'
这是纯文本文件
EOF
python3 scripts/kb_graph.py build /tmp/kb-graph-test --test-mode
```

**预期结果**：
- doc5.txt 应该被忽略（只处理 .md 文件）

### 测试 11：权限错误处理

```bash
# 创建无权限目录
mkdir -p /tmp/kb-graph-readonly/no-permission
chmod 000 /tmp/kb-graph-readonly/no-permission

python3 scripts/kb_graph.py build /tmp/kb-graph-readonly --test-mode
```

**预期结果**：
- 错误被正确捕获
- 其他文件继续处理

## 性能测试

### 测试 12：大规模文件处理

```bash
# 创建 100 个测试文件
for i in {1..100}; do
  cat > /tmp/kb-graph-large/doc$i.md << EOF
# 测试文档 $i
内容：这是一个大规模测试文档。
EOF
done

# 测量执行时间
time python3 scripts/kb_graph.py build /tmp/kb-graph-large --test-mode
```

**性能指标**：
- 100 个文件处理时间 < 10 秒（测试模式）
- 内存占用 < 100MB

## 已知限制

1. **LLM 依赖**：生产模式需要配置 LLM API
2. **文件类型**：仅支持 Markdown (.md) 文件
3. **语言支持**：主要为中文内容优化
4. **图谱构建**：当前版本图谱功能为基础实现

## 回归测试清单

- [ ] 全量构建（测试模式）
- [ ] 增量更新（目录）
- [ ] 单文件更新
- [ ] 索引验证
- [ ] 状态检查
- [ ] Lint 质量检查
- [ ] 文件删除处理
- [ ] 空目录处理
- [ ] 权限错误处理
- [ ] 大规模文件处理

## 测试报告模板

```markdown
# KB Graph v0.1 测试报告

**测试日期**：2026-05-26
**测试环境**：macOS Python 3.9
**测试人员**：Evan

## 测试结果汇总

| 测试项 | 通过 | 失败 | 备注 |
|--------|------|------|------|
| 全量构建 | ✓ | | |
| 增量更新 | ✓ | | |
| 单文件更新 | ✓ | | |
| 索引验证 | ✓ | | |
| ... | | | |

## 发现的问题

1. 问题描述
   - 严重程度：高/中/低
   - 重现步骤
   - 预期行为
   - 实际行为

## 建议

1. 功能建议
2. 性能优化建议
3. 文档改进建议
```

## 自动化测试脚本

```bash
#!/bin/bash
# KB Graph 自动化测试脚本

set -e

TEST_DIR="/tmp/kb-graph-auto-test"
SCRIPT_DIR="projects/2605261/kb-graph/scripts"

echo "🧪 开始 KB Graph 自动化测试"

# 清理和准备
rm -rf $TEST_DIR
mkdir -p $TEST_DIR

# 创建测试数据
echo "📝 创建测试数据..."
cat > $TEST_DIR/doc1.md << 'EOF'
# AI Agent
人工智能代理系统。
EOF

# 测试 1：全量构建
echo "🔨 测试 1：全量构建..."
RESULT=$(python3 $SCRIPT_DIR/kb_graph.py build $TEST_DIR --test-mode)
echo $RESULT | grep -q '"ok": true' && echo "✅ 通过" || echo "❌ 失败"

# 测试 2：索引验证
echo "🔍 测试 2：索引验证..."
RESULT=$(python3 $SCRIPT_DIR/validate_index.py --index $TEST_DIR/.kb-index.md)
echo $RESULT | grep -q '"ok": true' && echo "✅ 通过" || echo "❌ 失败"

# 测试 3：状态检查
echo "📊 测试 3：状态检查..."
RESULT=$(python3 $SCRIPT_DIR/kb_graph.py status $TEST_DIR)
echo $RESULT | grep -q '"success": 1' && echo "✅ 通过" || echo "❌ 失败"

# 清理
rm -rf $TEST_DIR

echo "✨ 测试完成"
```

## 问题反馈

发现问题请提交 Issue：
https://github.com/evan-zhang/agent-factory/issues

标题格式：`[BUG] kb-graph: 问题描述` 或 `[FEATURE] kb-graph: 功能建议`