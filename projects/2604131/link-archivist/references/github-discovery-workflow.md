# GitHub 项目发现工作流

> 当内容中提到 GitHub 项目但没有明确链接时，触发此流程。

## 触发条件

阶段 4（执行调研）的内容分析完成后：

1. 检测到文本中包含 `github.com/<owner>/<repo>` 模式 → 直接提取
2. 未检测到 GitHub URL，但有以下关键词 → 触发项目发现：
   - "GitHub"、"开源项目"、"在 GitHub 上"
   - CamelCase 项目名（带大写的项目名）
   - 引号/括号包裹的专有名词

## 流程

### Step 1：显式 URL 提取
用 `github_discovery.py` 提取文本中所有 `github.com/<owner>/<repo>` URL。

### Step 2：疑似项目名提取
对没有显式链接的内容，提取引号/括号中的 CamelCase 项目名。

### Step 3：GitHub API 搜索
对每个疑似项目名，调用 GitHub API 搜索，取 Top 3 结果。

### Step 4：匹配验证
逐一核验搜索结果的 description 是否与原描述相关：
- 匹配 → 标记为"候选项目"
- 不匹配 → 跳过

### Step 5：深度调研
对每个候选项目，调用 GitHub API 获取完整信息：
- Star 数（验证与描述是否一致）
- README 全文（与内容描述对比）
- 最近更新时间
- LICENSE
- issues/PR 活跃度

### Step 6：报告输出
在调研报告中新增"隐含项目"一节，记录发现的每个项目及验证结论。

## 输出格式

```markdown
### 隐含项目发现

| 项目名 | Star 数 | 更新时间 | 与原内容关联 |
|--------|---------|---------|------------|
| xxx | 3.2k | 2025-06 | ✅ 描述一致 |
| yyy | 500 | 2024-01 | ⚠️ 数据已过时 |

注：项目 A 在原内容中声称 Star 10k，实际仅 3.2k，已在 Claim 验证中标记。
```

## 调用示例

```bash
python3 scripts/github_discovery.py "最近有个叫 AutoGPT 的项目很火，在 GitHub 上有 50k star..."
```

```json
{
  "ok": true,
  "explicit_urls": [],
  "suspected_names": ["AutoGPT"],
  "search_results": [
    {
      "query": "AutoGPT",
      "matches": [
        {"name": "Sigourney/AutoGPT", "stars": 8900, ...},
        {"name": "Terrauto/AutoGPT", "stars": 3200, ...}
      ]
    }
  ]
}
```
