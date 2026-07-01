# 配置与授权

## 安装

```bash
# 方式一：手动安装（推荐）
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2604131/link-archivist
cp -r projects/2604131/link-archivist ~/.openclaw/skills/
cd ~/.openclaw/skills/link-archivist
python3 scripts/init_config.py --set archive_dir=/你的知识库目录
openclaw gateway restart

# 方式二：ClawHub（发布后）
openclaw skills install link-archivist
```

## 前置条件

- `agents.defaults.subagents.maxSpawnDepth: 2`

## 配置文件

路径（按优先级）：
1. `~/.openclaw/link-archivist-config.json`
2. `~/.hermes/link-archivist-config.json`
3. `~/.config/link-archivist-config.json`

## 必填

| 配置项 | 说明 |
|--------|------|
| `archive_dir` | **本地知识库**归档目录 |

> 与云端知识库、玄关知识库、公司知识库相互独立。所有数据存本地。

## 可选

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `tavily_api_key` | Web Search 交叉验证（提升报告质量） | https://tavily.com |
| `firecrawl_api_key` | **默认页面抓取引擎**（2026-07 改为首选） | https://firecrawl.dev |
| `video_archive_dir` | 视频归档目录（仅 full 模式） | 自行指定 |
| `xgjk_app_key` | 玄关 appKey（AI 慧记转写） | 联系玄关管理员 |

> **Firecrawl 配额**：免费版 1000 页/月，Hobby plan $16/月 5000 页。建议每月 25-28 号检查用量，避免月底归档失败。

## 抓取引擎选择

**2026-07 起，Firecrawl 取代 Jina Reader 作为默认抓取引擎**：

| 引擎 | 优势 | 劣势 |
|------|------|------|
| **Firecrawl**（默认） | 输出最干净、附 metadata、反爬能力最强 | 付费、有月配额 |
| **Crawl4AI**（降级 1st） | 零成本、本地跑、出错少 | 噪音大、需 LLM 二次提炼 |
| **Jina Reader**（降级 2nd） | 零安装、速度最快 | 容易被反爬封、不稳定 |

降级链完整规则见 `references/degradation-rules.md`。

## K/M 编号

| 类型 | 前缀 | source_type | 触发条件 |
|------|------|------------|----------|
| 外部抓取 | `K` | `url`（默认） | 发链接/文件 |
| 手工录入 | `M` | `manual` | `--source-type manual --project-id <ID>` |

## KB 索引配置

```json
{
  "kb_index": {
    "enabled": true,
    "query_mode": "keyword",
    "auto_update": true,
    "embeddings_enabled": false
  }
}
```

## XGKB 玄关同步（可选）

在知识库目录放 `.xgkb.json` 即可启用：
```json
{ "enabled": true, "remoteRoot": "Obsidian/日常学习" }
```

需先安装 xgkb-sync-helper：
```bash
git clone https://github.com/evan-zhang/xgkb-sync-helper.git ~/.openclaw/skills/xgkb-sync-helper
```

## 无需配置即可用

r.jina.ai 网页抓取（降级链备用）、Crawl4AI（如果已安装）、YouTube 字幕提取、抖音视频 ASR、GitHub 项目发现。
