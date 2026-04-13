# Decision Rules

## 判断优先级

1. **来源判断**（最高优先级）
   - YouTube / GitHub 链接 → 直接 full
2. **关键词判断**
   - 命中 full 关键词 → full
   - 命中 short 关键词 → short
3. **默认** → ask（问用户）

## Full 关键词
github, star, open source, repo, tutorial, 对比, 教程, 开源, 发布, 突破, 重磅, 深度, 分析, 评测, 框架, 工具, 模型, 论文, architecture, benchmark, comparison, deep dive, release

## Short 关键词
news, 新闻, 热点, 观点, commentary, 快讯, 简讯, 公告, 通知, 更新, 涨价, 降价

## 特殊场景
- 文件输入 → 提取文本后走同一套判断
- 用户明确说"详细看看" → 强制 full
- 用户明确说"简单说" → 强制 short
