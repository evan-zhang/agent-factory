# 调研方法论：执行调研（full 模式）

> 当 full 模式需要执行调研时，AI 读取此文件。
> 版本：v1.4.0 | 更新：2026-04-19（新增隐含项目发现 + Claim 验证）

## 调研步骤

### 第一步：内容分析

分析已抓取的标题、正文，判断内容类型：
- 开源项目介绍 → 重点分析架构、技术栈、团队背景
- 新闻/资讯 → 提取关键信息，不写长报告
- 教程/讲解 → 提取步骤，可操作执行
- 对比分析 → 重点做对比表格
- 观点/评论 → 记录观点，不做深度分析

**同时检测**：内容中是否提到 GitHub 项目（显式 URL 或疑似项目名）。

---

### 第二步：信息补充与交叉验证

#### 2.0：隐含 GitHub 项目发现

> 读取：`references/github-discovery-workflow.md`

**触发条件**：内容中提到项目名 + "GitHub"/"开源"等关键词，但没有完整链接。

```
Step 1：用 github_discovery.py 提取显式 GitHub URL
Step 2：提取疑似项目名（CamelCase、引号包裹等）
Step 3：对每个疑似项目名，GitHub API 搜索 Top 3
Step 4：核验 description 是否与原描述相关
Step 5：匹配则触发 GitHub 深度调研
```

运行示例：
```bash
python3 scripts/github_discovery.py "<文本内容>"
```

#### 2.1：GitHub 项目深度调研

对发现的每个 GitHub 项目，用 GitHub API 获取完整信息：

```bash
# 搜索仓库（按 Star 排序）
curl -sL "https://api.github.com/search/repositories?q=<项目名>&sort=stars" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for repo in data.get('items', [])[:3]:
    print(f\"Name: {repo['full_name']}\")
    print(f\"Stars: {repo['stargazers_count']}\")
    print(f\"Desc: {repo.get('description', 'N/A')[:200]}\")
    print(f\"URL: {repo['html_url']}\")
    print(f\"Updated: {repo['updated_at'][:10]}\")
    print(f\"License: {repo.get('license', {}).get('spdx_id', 'N/A')}\")
    print('---')
"

# 读取 README
curl -sL "https://api.github.com/repos/<owner>/<repo>/readme" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
print(base64.b64decode(data['content']).decode('utf-8')[:3000])
"
```

#### 2.2：通用 Web Search 交叉验证

**搜索策略：**
- 开源项目：`项目名 GitHub 功能关键词 2026`
- 新闻事件：`项目名 最新 2026`
- 融资/公司：`公司名 融资 投资 2026`

**必须验证的数据：**
- Star 数 / 用户数 / 融资额
- 投资方、金额、轮次
- 创始人背景、公司历史

#### 2.3：Claim 验证（批判性论证）

> **重要**：所有关键 claim 必须联网验证，不接受"作者说什么就是什么"。

**Claim 分类处理：**

| Claim 类型 | 验证方式 | 处理 |
|-----------|---------|------|
| 精确数字（Star 数、用户数、融资额）| GitHub API / 官网核实 | 对比原描述，一致 ✅，不一致 ❌ |
| 时间性描述（"最新更新"、"2025年发布"）| GitHub API / PR 历史核实 | 核实实际时间，过时 ⚠️ |
| 功能/特性描述 | README / 官方文档对比 | 一致 ✅，夸大 ⚠️ |
| 第三方背书（"被 XX 公司使用"）| Web Search 核实 | 找到 ✅，找不到 ❌ |
| 性能指标 | Web Search + 官方 benchmark | 可信度评估 |

**Claim 验证输出格式**（供报告使用）：
```
| 序号 | 作者原话 | 声称数据 | 实际核查 | 结论 |
|------|---------|---------|---------|------|
| 1 | "Star 10k" | 10,000 | 实际 3,200 | ❌ 夸大 3x |
| 2 | "最新更新 2025" | 2025年 | 实际 2024-06 | ⚠️ 数据过时 9个月 |
| 3 | "支持多模态" | 有 | README 核实存在 | ✅ 已验证 |
```

---

### 第三步：生成报告

按 `references/report-template.md` 的格式输出，包含：
- 概述、核心功能/架构
- 技术栈、关键数据
- **隐含项目发现**（如有）
- **Claim 验证**
- 对比分析、应用场景
- 局限性、个人洞察

---

## 洞察生成步骤

当 SKILL.md 第 5 步"生成洞察"触发时：

1. 使用 `session_search` 搜相关历史会话记录
2. 使用 `read_index` 搜本地知识库文件
3. 结合两者动态生成个性化洞察

---

## 报告质量检查

生成报告后，检查以下各项：
- [ ] 项目名称正确
- [ ] Star 数 / 融资已验证（Claim 验证通过）
- [ ] GitHub 链接正确
- [ ] 核心功能描述准确
- [ ] 技术栈列出
- [ ] Claim 验证已执行（关键 claim 全部有核查结论）
- [ ] 隐含项目已发现（如有）
- [ ] 与已有项目对比完成
- [ ] 应用场景说明
- [ ] 局限性讨论
