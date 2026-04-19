# Decision Rules

## 判断优先级（两阶段机制）

### 阶段 1：快速判断（无需抓取内容）
1. **来源判断**（最高优先级）
   - YouTube / GitHub 链接 → 直接 full
2. **用户输入关键词**
   - 命中 full 关键词 → full
   - 命中 short 关键词 → short
3. **默认** → 进入阶段 2

### 阶段 2：内容判断（需要抓取后分析）
- 检查标题和正文中的关键词密度
- full 关键词 ≥ 2 个 → full
- short 关键词 ≥ 1 个 → short
- full 关键词 ≥ 1 个 → full
- 都不满足 → ask

## Full 关键词
github, star, open source, repo, tutorial, 对比, 教程, 开源, 发布, 突破, 重磅, 深度, 分析, 评测, 框架, 工具, 模型, 论文, architecture, benchmark, comparison, deep dive, release, agent, llm, 大模型, 智能体, 超级智能体, 字节跳动, 火山引擎

## Short 关键词
news, 新闻, 热点, 观点, commentary, 快讯, 简讯, 公告, 通知, 更新, 涨价, 降价

## 使用示例

```bash
# 今日头条链接（快速判断 → ask，需要抓取内容）
python3 decide_mode.py "https://m.toutiao.com/is/xxxxx"

# 抓取后深度判断（发现"开源"、"框架" → full）
python3 decide_mode.py "https://m.toutiao.com/is/xxxxx" --content "字节跳动开源DeerFlow框架..."
```

## 特殊场景
- 文件输入 → 提取文本后走同一套判断
- 用户明确说"详细看看" → 强制 full
- 用户明确说"简单说" → 强制 short
