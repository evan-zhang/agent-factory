# Link Archivist v1.12.1 集成测试说明

## 项目概述

Link Archivist v1.12.1 增强了与 KB Graph 的集成能力，支持在归档时自动提取 entities 和 summary，并写入 YAML frontmatter，为后续知识库图谱构建提供结构化数据。

## 改造内容

### 1. 新增归档参数

**archive_report.py** 新增三个可选参数：

- `--entities`: 关键实体列表（JSON 数组或逗号分隔）
- `--summary`: 报告摘要（一句话描述）
- `--confidence`: 提取置信度（high/medium/low）

### 2. 增强的 YAML Frontmatter

归档报告现在包含更丰富的元数据：

```yaml
---
archive: K-260526-001
source: unknown
created_at: 2026-05-26T21:30:00.123456
entities:
  - AI Agent
  - 知识库
  - OpenClaw
summary: KB Graph 是一个为 Markdown 文件构建知识库图谱的独立 Skill
confidence: medium
tags: []
---
```

### 3. Wiki 链接注入支持

支持在报告正文中使用 Wiki 链接语法引用其他报告，KB Graph 可识别为边关系：

```markdown
## 个人洞察

本项目与 [[K-260410-002-MCP协议调研]] 在架构思路上有一定关联...
```

## 测试准备

### 1. 确保环境已安装 Link Archivist

```bash
# 检查是否已安装
test -f ~/.openclaw/skills/link-archivist/scripts/archive_report.py || echo "未安装"

# 如未安装，执行安装
cp -r projects/2604131/link-archivist ~/.openclaw/skills/
```

### 2. 准备测试报告

```bash
# 创建测试报告
cat > /tmp/test-report.md << 'EOF'
# KB Graph 技术调研

## 概述
KB Graph 是一个为 Markdown 文件构建知识库图谱的独立 OpenClaw Skill。

## 核心功能
- 增量索引
- LLM 语义编译
- Leiden 社区发现
- 双引擎查询

## 技术栈
- Python 3.8+
- OpenAI API (MiniMax/DeepSeek/GLM)
- NetworkX (图谱构建)

## 相关项目
- OpenClaw Agent Framework
- Link Archivist v1.12.1
EOF
```

## 功能测试

### 测试 1：基本归档（不使用新参数）

**目标**：验证向后兼容性

```bash
cd ~/.openclaw/skills/link-archivist

# 基本归档（不使用新参数）
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "KB Graph 技术调研"
```

**预期结果**：
```json
{
  "ok": true,
  "archive_id": "K-260526-001",
  "path": "/tmp/link-archive/2026/05/K-260526-001-KB-Graph-技术调研.md"
}
```

**验证点**：
- ✓ 归档成功生成
- ✓ 生成正确的归档 ID
- ✓ YAML frontmatter 存在但 entities 和 summary 为空

### 测试 2：使用 Entities 参数

**目标**：验证 entities 字段正确写入

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "KB Graph 技术调研 v2" \
  --entities '["KB Graph","知识库图谱","OpenClaw","Python","NetworkX"]' \
  --summary "KB Graph 是一个为 Markdown 文件构建知识库图谱的独立 Skill" \
  --confidence high
```

**验证点**：
- ✓ 归档文件包含 entities 列表
- ✓ entities 限制在 10 个以内
- ✓ summary 字段存在
- ✓ confidence 字段为 "high"

```bash
# 检查生成的文件
cat /tmp/link-archive/2026/05/K-260526-002-KB-Graph-技术调研-v2.md
```

**预期 YAML**：
```yaml
---
archive: K-260526-002
source: unknown
created_at: 2026-05-26T...
entities:
  - KB Graph
  - 知识库图谱
  - OpenClaw
  - Python
  - NetworkX
summary: KB Graph 是一个为 Markdown 文件构建知识库图谱的独立 Skill
confidence: high
tags: []
---
```

### 测试 3：使用 JSON 格式 Entities

**目标**：验证 JSON 格式解析

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "KB Graph 技术调研 v3" \
  --entities '[{"name":"KB Graph"},{"name":"知识库图谱"}]' \
  --summary "测试 JSON 格式 entities" \
  --confidence medium
```

**预期结果**：
- JSON 格式正确解析
- 正确提取 name 字段

### 测试 4：测试 Entities 超过限制

**目标**：验证 entities 自动截断到 10 个

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "KB Graph 技术调研 v4" \
  --entities '["实体1","实体2","实体3","实体4","实体5","实体6","实体7","实体8","实体9","实体10","实体11","实体12"]' \
  --summary "测试 entities 限制" \
  --confidence low
```

**验证点**：
- ✓ 只有前 10 个 entities 被保留
- ✓ 第 11、12 个 entities 被忽略

### 测试 5：Wiki 链接注入测试

**目标**：验证报告正文包含 Wiki 链接

```bash
# 创建包含 Wiki 链接的测试报告
cat > /tmp/test-report-wiki.md << 'EOF'
# KB Graph 技术调研

## 概述
KB Graph 是一个为 Markdown 文件构建知识库图谱的独立 OpenClaw Skill。

## 相关项目
本项目与 [[K-260410-002-MCP协议调研]] 在架构思路上有一定关联。

与 [[K-260520-003-Link-Archivist-v1-12-1]] 有直接集成关系。

## 个人洞察
通过分析 [[K-260420-005-AI-Agent开发指南]]，我们发现...
EOF

python3 scripts/archive_report.py \
  --file /tmp/test-report-wiki.md \
  --dir /tmp/link-archive \
  --title "KB Graph Wiki 链接测试" \
  --entities '["KB Graph","Wiki 链接"]' \
  --summary "测试 Wiki 链接注入功能"
```

**验证点**：
- ✓ Wiki 链接语法被保留在正文中
- ✓ KB Graph 可以识别为边关系

## 集成测试

### 测试 6：Link Archivist + KB Graph 完整流程

**目标**：验证从抓取到归档再到图谱构建的完整流程

#### 步骤 1：使用 Link Archivist 归档报告

```bash
# 模拟 Link Archivist 生成的报告
cat > /tmp/ai-agent-report.md << 'EOF'
# AI Agent 开发调研

## 概述
AI Agent 是能够自主执行任务的智能系统。

## 核心组件
- 感知模块
- 规划模块
- 执行模块
- 记忆模块

## 技术选型
- LangChain
- OpenAI GPT-4
- AutoGPT

## 参考资料
参考了 [[K-260410-002-MCP协议调研]] 的架构设计。

## 关键发现
与 [[K-260420-001-LLM应用开发模式]] 相比，AI Agent 更强调自主性。
EOF

# 使用 Link Archivist 归档
cd ~/.openclaw/skills/link-archivist
python3 scripts/archive_report.py \
  --file /tmp/ai-agent-report.md \
  --dir /tmp/knowledge-base \
  --entities '["AI Agent","LangChain","OpenAI","AutoGPT"]' \
  --summary "AI Agent 是能够自主执行任务的智能系统，核心包括感知、规划、执行、记忆模块" \
  --confidence high
```

#### 步骤 2：使用 KB Graph 构建图谱

```bash
cd projects/2605261/kb-graph

# 使用 KB Graph 扫描知识库
python3 scripts/kb_graph.py build /tmp/knowledge-base --test-mode
```

#### 步骤 3：验证集成

```bash
# 检查 KB Graph 索引
cat /tmp/knowledge-base/.kb-index.md

# 验证 entities 和 summary 被正确提取
python3 scripts/validate_index.py --index /tmp/knowledge-base/.kb-index.md
```

**验证点**：
- ✓ Link Archivist 归档的报告包含 entities 和 summary
- ✓ KB Graph 正确识别并索引这些元数据
- ✓ Wiki 链接被识别为潜在的关系边

### 测试 7：多报告关联性测试

**目标**：验证多个报告之间的关联性被正确识别

```bash
# 创建多个相关报告
for i in {1..5}; do
  cat > /tmp/report$i.md << EOF
# 报告 $i：AI 相关技术

## 内容
这是关于 AI 技术的第 $i 份报告。

## 相关报告
- [[K-260526-00$((i-1))-前序报告]]
- [[K-260526-00$((i%5+1))-循环引用]]

## 关键概念
- 机器学习
- 深度学习
- 自然语言处理
EOF

  cd ~/.openclaw/skills/link-archivist
  python3 scripts/archive_report.py \
    --file /tmp/report$i.md \
    --dir /tmp/knowledge-base \
    --entities '["机器学习","深度学习","NLP"]' \
    --summary "AI 技术报告 $i" \
    --confidence high
done

# 使用 KB Graph 构建图谱
cd projects/2605261/kb-graph
python3 scripts/kb_graph.py build /tmp/knowledge-base --test-mode
```

**验证点**：
- ✓ 所有报告被正确索引
- ✓ Entities 被正确提取
- ✓ KB Graph 可以识别 Wiki 链接关系

## 边界测试

### 测试 8：空 Entities 和 Summary

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "空元数据测试" \
  --entities '[]' \
  --summary ""
```

**预期结果**：
- entities 和 summary 字段存在但为空
- 归档仍然成功

### 测试 9：超长 Summary

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "超长摘要测试" \
  --entities '["测试"]' \
  --summary "$(printf '%.0s这是超长摘要测试 ' {1..100})"
```

**预期结果**：
- 超长 summary 被保留（不做长度限制）
- 归档成功

### 测试 10：特殊字符处理

```bash
python3 scripts/archive_report.py \
  --file /tmp/test-report.md \
  --dir /tmp/link-archive \
  --title "特殊字符测试" \
  --entities '["特殊字符：引号\"单引号\'括号()方括号[]花括号{}"]' \
  --summary "包含特殊字符的摘要：\"引号\" 和 '单引号'"
```

**预期结果**：
- 特殊字符被正确转义
- YAML 格式有效

## 性能测试

### 测试 11：批量归档性能

```bash
# 创建 100 个测试报告
for i in {1..100}; do
  cat > /tmp/report-batch-$i.md << EOF
# 批量测试报告 $i

## 内容
这是批量测试报告 $i。

## 关键概念
- 概念 A
- 概念 B
- 概念 C
EOF

  cd ~/.openclaw/skills/link-archivist
  python3 scripts/archive_report.py \
    --file /tmp/report-batch-$i.md \
    --dir /tmp/knowledge-base-batch \
    --entities '["概念 A","概念 B","概念 C"]' \
    --summary "批量测试报告 $i" \
    --confidence high > /dev/null
done

# 测量 KB Graph 处理时间
time python3 projects/2605261/kb-graph/scripts/kb_graph.py build /tmp/knowledge-base-batch --test-mode
```

**性能指标**：
- 100 个报告归档时间 < 30 秒
- KB Graph 构建索引时间 < 10 秒

## 回归测试清单

### Link Archivist 功能
- [ ] 基本归档（不使用新参数）
- [ ] 使用 Entities 参数（数组格式）
- [ ] 使用 Entities 参数（JSON 格式）
- [ ] 使用 Summary 参数
- [ ] 使用 Confidence 参数
- [ ] Entities 超过 10 个自动截断
- [ ] 空 Entities 和 Summary 处理
- [ ] 超长 Summary 处理
- [ ] 特殊字符转义

### 集成功能
- [ ] Link Archivist 归档报告包含 entities
- [ ] Link Archivist 归档报告包含 summary
- [ ] KB Graph 正确识别 entities
- [ ] KB Graph 正确识别 summary
- [ ] Wiki 链接被保留在正文中
- [ ] 多报告关联性被正确识别

### 性能和稳定性
- [ ] 单个报告归档 < 0.5 秒
- [ ] 100 个报告批量归档 < 30 秒
- [ ] KB Graph 处理 100 个报告 < 10 秒
- [ ] 内存占用 < 100MB

## 自动化测试脚本

```bash
#!/bin/bash
# Link Archivist 集成测试脚本

set -e

LA_DIR="~/.openclaw/skills/link-archivist"
KB_DIR="projects/2605261/kb-graph"
ARCHIVE_DIR="/tmp/link-archivist-test"
KB_TARGET="/tmp/kb-graph-test"

echo "🧪 开始 Link Archivist 集成测试"

# 清理
rm -rf $ARCHIVE_DIR $KB_TARGET
mkdir -p $ARCHIVE_DIR $KB_TARGET

# 测试报告
cat > /tmp/test-la-report.md << 'EOF'
# Link Archivist 测试报告

## 概述
这是用于测试 Link Archivist 集成功能的报告。

## 关键概念
- Link Archivist
- KB Graph
- 知识库
EOF

# 测试 1：基本归档
echo "📝 测试 1：基本归档..."
cd $LA_DIR
RESULT=$(python3 scripts/archive_report.py \
  --file /tmp/test-la-report.md \
  --dir $ARCHIVE_DIR \
  --entities '["Link Archivist","KB Graph","知识库"]' \
  --summary "Link Archivist 测试报告" \
  --confidence high)
echo $RESULT | grep -q '"ok": true' && echo "✅ 通过" || echo "❌ 失败"

# 测试 2：KB Graph 集成
echo "🔗 测试 2：KB Graph 集成..."
cp -r $ARCHIVE_DIR/* $KB_TARGET/
cd $KB_DIR
RESULT=$(python3 scripts/kb_graph.py build $KB_TARGET --test-mode)
echo $RESULT | grep -q '"built": 1' && echo "✅ 通过" || echo "❌ 失败"

# 测试 3：Entities 提取验证
echo "🔍 测试 3：Entities 提取验证..."
cat $KB_TARGET/.kb-index.md | grep -q "Link Archivist" && echo "✅ 通过" || echo "❌ 失败"

# 清理
rm -rf $ARCHIVE_DIR $KB_TARGET /tmp/test-la-report.md

echo "✨ 测试完成"
```

## 问题反馈

发现问题请提交 Issue：
https://github.com/evan-zhang/agent-factory/issues

标题格式：`[BUG] link-archivist: 问题描述` 或 `[FEATURE] link-archivist: 功能建议`

## 已知限制

1. **Entities 提取**：当前需要手动指定，未来可集成 LLM 自动提取
2. **Wiki 链接解析**：当前仅保留在正文中，KB Graph 可识别但未完全实现边关系构建
3. **置信度计算**：当前为手动指定，未来可基于 LLM 提取质量自动计算