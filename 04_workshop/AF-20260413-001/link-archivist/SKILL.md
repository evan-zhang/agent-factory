---
name: link-archivist
description: Link Archivist v11. 收到链接或文件后，判断 short/full，抓取调研，生成报告，归档本地。
---

# Link Archivist v11

## 触发判断

```
收到消息
 ├─ URL/链接         → 抓取内容 → 决定模式
 ├─ 文件             → 调用外部解析工具提取文本 → 决定模式
 ├─ 粘贴文本         → 直接判断模式
 └─ 未初始化         → 引导配置 archive_dir
```

## 首次使用

1. 检测 `~/.openclaw/link-archivist-config.json` 是否存在
2. 不存在 → 引导用户设置 `archive_dir`（知识库主目录）
3. 设置后写入配置文件

**配置文件**：
```json
{
  "archive_dir": "/Users/evan/知识库"
}
```

## 工作流

1. **检测配置** → `scripts/init_config.py`
2. **抓取内容** → r.jina.ai（通用）/ yt-dlp+whisper（YouTube）/ 外部文件解析
3. **决定模式** → `scripts/decide_mode.py`（来源优先 + 关键词判断）
   - **full**：GitHub/YouTube 来源，或关键词命中（开源、框架、论文等）→ 完整调研报告
   - **short**：新闻资讯类 → 2-3 句话摘要
   - **ask**：不确定 → 问用户
4. **执行调研**（full 模式含 web_search 交叉验证）
5. **生成洞察**（读本地索引 + 搜 Agent 记忆，动态生成）
6. **归档本地** → `{archive_dir}/{YYYY-MM-DD}/K-{YYMMDD}-{NNN}-{标题简称}.md`
   - 编号规则：K-YYMMDD-NNN，当日最大编号 +1
   - 详见 `references/archive-template.md`

## 职责边界

**本 Skill 负责**：抓取 → 判断 → 调研 → 生成报告 → 归档本地

**不负责**：
- 发送到哪个渠道（由 Agent 自己决定）
- 文件解析（PDF/Word/PPT/图片等，由外部工具处理）
- 知识索引管理（见 AF-20260413-003 LLM Wiki）
- 云端同步（见 AF-20260413-002 知识库同步服务）

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/init_config.py` | 检测/创建配置文件 |
| `scripts/decide_mode.py` | 判断 short/full/ask |
| `scripts/archive_report.py` | 归档报告到本地目录 |

## 参考

| 文件 | 内容 |
|------|------|
| `references/report-template.md` | 报告模板（full + short） |
| `references/archive-template.md` | 归档目录结构、编号规则 |
| `references/decision-rules.md` | 模式判断规则说明 |
| `references/SOP-诸葛工作流.md` | 详细 SOP（抓取→判断→搜索→写报告） |
| `references/migration-notes.md` | 版本迁移说明 |
| `examples/` | 4 个完整示例 |

## 关联项目

| 项目编号 | 名称 | 关系 |
|----------|------|------|
| AF-20260413-002 | 知识库同步服务 | 本地→云端同步 |
| AF-20260413-003 | LLM Wiki | 知识索引与管理 |
