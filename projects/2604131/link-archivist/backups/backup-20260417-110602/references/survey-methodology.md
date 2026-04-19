# 调研方法论：执行调研（full 模式）

> 当 full 模式需要执行调研时，AI 读取此文件。

## 调研步骤

### 第一步：内容分析
分析已抓取的标题、正文，判断内容类型：
- 开源项目介绍 → 重点分析架构、技术栈、团队背景
- 新闻/资讯 → 提取关键信息，不写长报告
- 教程/讲解 → 提取步骤，可操作执行
- 对比分析 → 重点做对比表格
- 观点/评论 → 记录观点，不做深度分析

### 第二步：信息补充与交叉验证（full 模式必须执行）

#### 2.1 开源项目：GitHub API 优先（推荐）

对于 GitHub 开源项目，优先使用 GitHub API 获取实时数据，比 web_search 更准确：

```bash
# 搜索仓库
curl -sL "https://api.github.com/search/repositories?q=<项目名>&sort=stars" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for repo in data.get('items', [])[:3]:
    print(f\"Name: {repo['full_name']}\")
    print(f\"Stars: {repo['stargazers_count']}\")
    print(f\"Desc: {repo.get('description', 'N/A')[:200]}\")
    print(f\"URL: {repo['html_url']}\")
    print(f\"Updated: {repo['updated_at']}\")
    print('---')
"

# 读取 README
curl -sL "https://api.github.com/repos/<owner>/<repo>/readme" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
print(base64.b64decode(data['content']).decode('utf-8')[:2000])
"
```

**优势**：无需认证、Star 数实时、可直接读 README。

#### 2.2 通用 Web Search 交叉验证

**搜索策略：**
- 开源项目：`项目名 GitHub 功能关键词 2026`
- 新闻事件：`项目名 最新 2026`
- 融资/公司：`公司名 融资 投资 2026`

**必须验证的数据：**
- Star 数 / 用户数 / 融资额
- 投资方、金额、轮次
- 创始人背景、公司历史

### 第三步：生成报告

按 `references/report-template.md` 的格式输出。

## 洞察生成步骤

当 SKILL.md 第 5 步"生成洞察"触发时：

1. 使用 `session_search` 搜相关历史会话记录
2. 使用 `read_index` 搜本地知识库文件
3. 结合两者动态生成个性化洞察

## 报告质量检查

生成报告后，检查以下各项：
- [ ] 项目名称正确
- [ ] Star 数/融资已验证
- [ ] GitHub 链接正确
- [ ] 核心功能描述准确
- [ ] 技术栈列出
- [ ] 与已有项目对比完成
- [ ] 应用场景说明
- [ ] 局限性讨论
