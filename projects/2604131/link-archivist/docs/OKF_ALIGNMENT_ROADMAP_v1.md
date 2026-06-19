# Link Archivist × OKF / LLM-Wiki 对齐路线图

**项目**：2604131 link-archivist
**当前版本基线**：Link Archivist v2.0.0（commit b646ead）
**方案版本**：v1.0 草案
**作者**：Factory Orchestrator
**待审**：Factory Reviewer 深度评审

---

## 0. 结论先行

Link Archivist 应该**参考并引用 OKF / LLM-Wiki**，但不应在 v2.x 立即宣称“完全兼容 OKF”或把主数据模型硬迁移为 OKF。

推荐定位：

> Link Archivist 继续保持“来源归档 + 索引 + 查询”的知识生命周期 Skill；
> OKF 作为“对外兼容的知识包格式”和“未来 wiki synthesis layer 的参考规范”。

执行策略：

1. **v2.0.x**：只做文档引用和字段映射，不改变主流程
2. **v2.1.x**：新增 OKF-style frontmatter 可选字段 + 只读导出脚本
3. **v2.2.x**：生成 `index.md` / `log.md`，形成人类可读 bundle
4. **v3.0**：先复核 OpenClaw 是否已有 synthesis/wiki 能力，再评估是否增加 living wiki synthesis layer（可演化主题页/实体页），且保留归档层不可变

---

## 1. 背景与来源核验

### 1.1 本地归档来源

本方案基于两篇已归档文章：

1. `knowledge/2026/06/K-260619-053-Google-OKF规范标准化LLM-Wiki.md`
   - 来源：今日头条 · AI观察室
   - 核心观点：Google 发布 OKF v0.1，把 Karpathy 的 LLM-Wiki 模式标准化

2. `knowledge/2026/06/K-260619-054-Google-OKF-VibeCoder深度解读.md`
   - 来源：今日头条 · VibeCoder
   - 核心观点：OKF 是 Knowledge Bundle + YAML frontmatter + index.md/log.md + 宽容解析器
   - 第二篇内容更完整，包含分工、风险和落地建议

### 1.2 官方源核验

优先引用官方源，而不是二手转述：

- Google Cloud 官方博客：《Introducing the Open Knowledge Format》（2026-06-13）
  - URL: <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing>
- Karpathy LLM-Wiki 原始 gist：
  - URL: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>

Google Cloud 官方博客确认：

- OKF 是 open specification，用于把 LLM-wiki pattern 形式化为 portable / interoperable format
- OKF v0.1 表示为一个 Markdown 文件目录 + YAML frontmatter
- 结构字段包括：`type`、`title`、`description`、`resource`、`tags`、`timestamp`
- 目标是 vendor-neutral、agent-friendly、human-readable
- 官方明确强调：不是新 runtime，不需要 SDK，不是复杂压缩格式；就是 Markdown + files + YAML frontmatter

Karpathy 的 `llm-wiki.md` gist 核心思想：

- 不要每次 query 都重新 RAG 原始文档
- LLM 应该持续维护一个结构化、交叉链接的 persistent wiki
- Raw sources 不改；Wiki 层由 LLM 维护；Schema/AGENTS/CLAUDE 文件约束 LLM 如何维护
- 人负责选择来源和提问，LLM 负责摘要、交叉引用、归档和 bookkeeping

### 1.3 核验结论

OKF 是 Google Cloud 公开提出的 open specification，值得引用和参考。

但当前它是 v0.1，尚不是成熟标准化组织（如 W3C/RFC）批准的稳定标准。因此 Link Archivist 应采取“alignment / export / compatible style”的保守策略，而不是立刻承诺“full OKF compliance”。

---

## 2. Link Archivist v2.0.0 与 OKF 的相同点

### 2.1 Markdown-first

OKF：一个 Knowledge Bundle 是一组 Markdown 文件。

Link Archivist：每次归档生成一个 Markdown 报告，按日期目录组织：

```text
knowledge/
└── 2026/
    └── 06/
        ├── K-260619-053-...
        └── K-260619-054-...
```

### 2.2 YAML frontmatter

OKF：frontmatter 用于可查询字段，例如：

```yaml
type: BigQuery Table
title: Orders
description: One row per completed customer order.
resource: https://...
tags: [sales, revenue]
timestamp: 2026-05-28T14:30:00Z
```

Link Archivist v2.0.0：frontmatter 用于归档和索引字段：

```yaml
archive: K-260619-054
source: https://...
source_type: url
created_at: 2026-06-19T19:53:00
summary: ...
entities:
  - OKF
  - LLM-Wiki
tags:
  - AI
  - 架构
confidence: high
relationships:
  - type: reference
    target: OKF
    description: ...
```

两者都把“给 Agent/搜索器使用的结构化元数据”放在 Markdown 文件头部。

### 2.3 文件系统即知识包

OKF：bundle 可以托管在 Git、zip、tarball、文件系统。

Link Archivist：`archive_dir` 就是本地知识包事实源，`.kb-workdir/` 是派生索引。

### 2.4 AI 可维护

OKF / LLM-Wiki：AI 维护 index、cross-link、log。

Link Archivist：LLM 生成报告和 frontmatter；脚本维护 entries、entity registry、graph、lint。

### 2.5 反对重复 RAG

OKF / LLM-Wiki 的精神是“编译一次，持续复用”。

Link Archivist v2.0.0 的归档即索引也是同一方向：归档时提取 `summary / entities / tags / relationships`，后续 query 直接消费已编译结构，不每次重新读原文。

---

## 3. 关键差异

### 3.1 层级不同：格式 vs 生命周期 Skill

OKF 是知识资产格式。

它回答：

> 一个知识包应该如何组织，才方便人和 Agent 共同消费？

Link Archivist 是知识生命周期 Skill。

它回答：

> 一个链接/视频/文档进入本地知识库后，如何抓取、调研、归档、索引、查询？

所以 OKF 不替代 Link Archivist。OKF 更像 Link Archivist 可以输出/对齐的格式层。

### 3.2 编辑模式不同：Living Wiki vs Append-only Archive

OKF / LLM-Wiki 倾向 living wiki：

- index.md 持续更新
- entity/topic 页面持续演化
- log.md 记录变化
- AI 会更新已有页面

Link Archivist 当前是 append-only archive：

- 每次归档生成一篇报告
- 归档报告原则上不可变
- `.kb-workdir` 作为派生索引可重建
- 暂无 synthesis wiki 层

这不是缺陷，而是领域定位不同。Link Archivist 保留归档审计价值，不能随意让 AI 改写历史报告。

### 3.3 ID 体系不同

OKF：文件路径就是 concept identity。

Link Archivist：`archive_id` 是稳定编号，路径是时间分区。

例如：

```yaml
archive: K-260619-054
path: 2026/06/K-260619-054-Google-OKF-VibeCoder深度解读.md
```

Link Archivist 的 archive_id 对审计、引用、群聊追踪更友好；OKF 的 path-as-id 对可移植 bundle 更友好。

### 3.4 字段目的不同

OKF 字段偏资产描述：

- type
- title
- description
- resource
- tags
- timestamp

Link Archivist 字段偏归档处理和索引：

- archive
- source
- source_type
- created_at
- summary
- entities
- relationships
- confidence

两者应做字段映射，而不是强行二选一。

---

## 4. 设计原则

### 4.1 不把 v0.1 当强标准绑定

OKF v0.1 值得参考，但还不应成为 Link Archivist 的硬依赖。

禁止措辞：

- “Link Archivist 完全兼容 OKF”
- “Link Archivist 是 OKF 实现”
- “所有归档必须迁移成 OKF”

推荐措辞：

- “OKF-style”
- “OKF-aligned”
- “可导出为 OKF-style knowledge bundle”
- “参考 OKF / LLM-Wiki 设计思想”

### 4.2 归档层不可变，派生层可重建

归档报告是事实源，原则上不可改写。

可重建内容包括：

- `.kb-workdir/entries.json`
- `.kb-workdir/entities-registry.json`
- `.kb-workdir/graph-data.json`
- 未来的 `index.md`
- 未来的 `log.md`
- 未来的 `okf_bundle/`

### 4.3 输入宽容，事实源严格，派生层自愈

OKF 倡导宽容解析，但 Link Archivist 不能让坏结构污染 entries。

原则：

- frontmatter 输入可以不完整
- parse 阶段必须类型清洗
- entries.json 不能写坏结构
- graph/lint 遇到坏历史数据不能崩
- 派生文件出错可由 entries.json 自愈

这条原则来自 v2.0.0 S5 审查经验：relationships 解析错误曾导致 entries 污染和 build_graph 崩溃。

### 4.4 增量演进，不重构主流程

v2.0.0 刚完成 KB Graph 合并，不应立即做大规模目录重构。

OKF alignment 应以“可选字段 + 只读导出 + 人类可读索引”为主，避免破坏已稳定的归档链路。

---

## 5. 字段映射方案

### 5.1 Link Archivist → OKF 映射

| Link Archivist | OKF-style | 说明 |
|---|---|---|
| `archive` | `id` 或保留 `archive` | OKF 官方示例未强制 id；建议保留 archive，导出时可用作 id |
| `source` | `resource` | 原始链接/文件路径 |
| `source_type` | `type` 的补充 | 不建议直接映射为 type；type 应为知识单元类型 |
| `created_at` | `timestamp` | 归档时间 |
| `summary` | `description` | OKF description 可用 summary 填充 |
| `entities` | 保留扩展字段 | OKF 官方示例未列 entities，但可作为扩展 |
| `tags` | `tags` | 直接映射 |
| `relationships` | Markdown links / 扩展字段 | OKF 更偏用 Markdown link，Link Archivist 可保留结构化 relationships |
| `confidence` | 保留扩展字段 | 用于 LLM 抽取质量，不属于 OKF 核心字段 |

### 5.2 推荐 frontmatter 扩展（v2.1 可选）

不删除现有字段，只新增 OKF-style 字段：

```yaml
# Link Archivist native fields
archive: K-260619-054
source: https://m.toutiao.com/is/TJTBuPzwuus/
source_type: url
created_at: 2026-06-19T19:53:00
summary: Google OKF 深度解读，说明其 Knowledge Bundle、frontmatter、index/log 设计。
entities:
  - OKF
  - LLM-Wiki
  - Google Cloud
tags:
  - AI
  - 架构
confidence: high
relationships:
  - type: topic
    target: 知识管理
    description: 属于知识管理规范方向

# OKF-style optional fields
type: archive
title: Google Open Knowledge Format 深度解读
description: Google OKF 深度解读，说明其 Knowledge Bundle、frontmatter、index/log 设计。
resource: https://m.toutiao.com/is/TJTBuPzwuus/
timestamp: 2026-06-19T19:53:00
okf_alignment: v0.1-style
```

### 5.3 字段写入策略

- v2.0.x：不改变归档 frontmatter，只写文档说明
- v2.1.x：新增 OKF-style 字段，**opt-in 默认关闭**，必须用户显式启用
- 历史归档不主动重写；仅导出时做映射
- 若用户主动运行 `kb_rebuild --force-llm`，也不重写原归档，只更新 `.kb-workdir/entries.json`

---

## 6. 目录结构演进

### 6.1 当前 v2.0.0

```text
knowledge/
├── 2026/06/K-*.md
└── .kb-workdir/
    ├── entries.json
    ├── entities-registry.json
    ├── graph-data.json
    ├── kb_cache.json
    └── build_stats.json
```

### 6.2 v2.1 建议：OKF-style 导出，不改主目录

```text
knowledge/
├── 2026/06/K-*.md
└── .kb-workdir/
    ├── entries.json
    └── okf-export/               # 可选导出目录，位于已被 ingest 排除的 .kb-workdir 内
        ├── index.md
        ├── log.md
        └── archive/
            └── 2026/06/K-*.md
```

**关键修正**：导出目录必须放在 `.kb-workdir/okf-export/`，不能放在 `knowledge/.okf-export/`。当前 v2.0.0 的 `scan_markdown_files()` 只跳过路径包含 `.kb-workdir` 的文件；若放在根目录 `.okf-export/`，`index.md`、`log.md` 和归档副本会被重新 ingest，制造重复 entries。

优点：

- 不污染现有归档目录
- 可以安全重建
- 可以删除重新导出
- 便于外部工具消费

### 6.3 v2.2 建议：根目录 index/log

在确认 OKF-style 导出有价值后，再考虑生成：

```text
knowledge/
├── index.md
├── log.md
├── 2026/06/K-*.md
└── .kb-workdir/
```

注意：`index.md` / `log.md` 若放在根目录，会进入知识库扫描范围，必须让 ingest 跳过或标记为 system document，避免把派生文档误当普通归档。

### 6.4 v3.0 候选：living wiki synthesis layer

```text
knowledge/
├── archive/       # 归档事实源，不改写
├── wiki/          # LLM 可维护的主题页、实体页、综合页
├── index.md
├── log.md
└── .kb-workdir/
```

这一步属于大版本级设计，需另走完整 S3 → S5 评审，不在 v2.1 实施。

---

## 7. 功能路线图

### 7.1 v2.0.1：文档对齐（低风险）

目标：只补文档，不改运行路径。

任务：

1. 新增 `references/okf-alignment.md`
2. 在 `references/phase3-prompt-template.md` 增加 OKF 字段映射说明
3. 在 `references/kb-index-architecture.md` 增加 OKF / LLM-Wiki 背景引用
4. 在 SKILL.md 的知识库查询/索引说明里增加一句“OKF-style alignment”说明

验收：

- 文档清晰，无运行时改动
- Factory Review B 类 PASS

### 7.2 v2.1.0：OKF-style 导出（中风险）

目标：新增只读导出能力，不改变主归档。

新增脚本：

```bash
python3 scripts/kb_export_okf.py --dir <archive_dir> --out <okf_bundle_dir>
```

输出：

```text
.kb-workdir/okf-export/
├── index.md
├── log.md
└── archive/...
```

设计要求：

- 只读读取 `entries.json` 和归档 Markdown
- 不修改原始归档
- 可重复运行，输出目录可删除重建
- `index.md` 包括主题、标签、实体、最近归档
- `log.md` 从 build_stats/cache 派生，无法还原历史时标注“generated from current index”
- v2.1 硬验收：导出目录必须位于 `.kb-workdir/okf-export/`，或同批实现 ingest/system-doc 显式跳过；不得把 `.okf-export/` 放在 knowledge 根目录

验收：

- 临时 KB 导出成功
- 真实 archive 只读导出到 temp 目录成功
- 输出 Markdown 可被普通编辑器阅读
- 不产生真实 archive 写入

### 7.3 v2.2.0：Root index/log（中风险）

目标：在 knowledge 根目录生成人类可读导航。

风险：

- `index.md` / `log.md` 可能被扫描为普通归档
- 根目录文件会影响用户已有 Obsidian/同步工具

前置条件：

- v2.1 OKF export 被实际使用
- 用户确认希望根目录存在 `index.md` / `log.md`
- ingest 明确跳过 system docs

### 7.4 v3.0：Living Wiki（高风险）

目标：引入 AI 可维护的 synthesis layer。

范围：

- `wiki/entities/*.md`
- `wiki/topics/*.md`
- `wiki/syntheses/*.md`
- AI 维护 cross-links 和 contradictions

红线：

- 不允许自动改写 archive 层
- 每次 wiki 更新必须有 diff/review
- 必须能从 archive + entries 重建 wiki

---

## 8. 与 OKF 相邻标准的边界

### 8.1 llms.txt

定位：站点/仓库给 LLM 的入口导航。

Link Archivist 不需要把主知识库改成 llms.txt，但未来 OKF export 可附带生成：

```text
llms.txt
```

用于指向 `index.md` 和关键知识包入口。

### 8.2 MCP

定位：Agent ↔ 工具协议。

Link Archivist 当前是 Skill，不是 MCP server。未来若做 MCP，应暴露 query / export / lint 等工具，不改变知识格式本身。

### 8.3 OpenLineage

定位：运行时数据血缘。

Link Archivist 可借鉴 lineage 概念，但不应引入 OpenLineage 作为依赖。归档来源用 `source/resource` 足够。

---

## 9. 风险与缓解

### 9.1 OKF 规范不稳定

风险：OKF v0.1 字段可能变化。

缓解：只称 OKF-style，不承诺 full compliance；通过导出层隔离。

### 9.2 字段膨胀

风险：frontmatter 过长、重复字段太多。

缓解：OKF-style 字段可选且 **opt-in 默认关闭**；用户显式启用后才在新归档写入，历史归档通过 export 映射。

### 9.3 派生文档污染索引

风险：index.md/log.md 被当作普通知识单元。

缓解：短期放到 `.kb-workdir/okf-export/`，复用当前 ingest 已排除 `.kb-workdir` 的事实；若未来放根目录，ingest 必须先实现 system docs / export dir 显式跳过。

### 9.4 Living wiki 改写历史

风险：AI 为维护 wiki 改动原始归档。

缓解：archive 层不可变；wiki 层独立；所有 AI 维护必须 diff/review。

### 9.5 权限与敏感信息传播

OKF 官方也提醒权限模型不是格式自身解决的问题。Link Archivist 若导出 bundle，必须继承 archive_dir 的访问边界，不做跨目录导出。

---

## 10. 推荐实施顺序

### 立即做（本方案通过后）

- 不改代码
- 把本方案作为 v2.1 方向文档
- 经过 Factory Review 后作为后续开发基准

### 下一次小版本：v2.0.1

做文档对齐：

- `references/okf-alignment.md`
- phase3 prompt 补字段映射
- SKILL.md 补 OKF-style 说明

### 下一个功能版本：v2.1.0

做只读导出：

- `scripts/kb_export_okf.py`
- `.kb-workdir/okf-export/index.md`
- `.kb-workdir/okf-export/log.md`

### 大版本候选：v3.0

做 living wiki synthesis layer，但必须单独立项、单独评审；立项前必须先复核 OpenClaw 是否已具备平台级 synthesis/wiki 能力，避免重复造轮子。

---

## 11. 验收标准

### 11.1 本方案验收

- [ ] Factory Review B 类 DESIGN 评审 PASS
- [ ] 明确不把 OKF v0.1 作为强依赖
- [ ] 明确 Link Archivist 与 OKF 的定位差异
- [ ] 明确字段映射和版本路线图
- [ ] 明确风险与缓解

### 11.2 后续 v2.0.1 验收

- [ ] references 文档补齐
- [ ] SKILL.md 不膨胀超过必要范围
- [ ] 不改运行时代码
- [ ] 无需真实 archive 写操作

### 11.3 后续 v2.1.0 验收

- [ ] temp KB 导出 OKF-style bundle 成功
- [ ] 真实 archive 只读导出成功
- [ ] 输出 `index.md` / `log.md` 可读
- [ ] 原始归档无改动
- [ ] Factory Review C 类代码审查 PASS

---

## 12. 最终建议

OKF 是值得引用的方向，但不是 Link Archivist 的替代品。

Link Archivist 的优势是“生命周期”：抓取、分析、归档、索引、查询、审计。OKF 的优势是“资产格式”：Markdown-first、YAML frontmatter、Git-friendly、Agent-friendly。

最佳路线是：

> 内部保持 Link Archivist native model；
> 外部提供 OKF-style alignment/export；
> 长期评估 living wiki synthesis layer；v3 立项前先核查 OpenClaw 平台能力，避免重复造轮子。

这样既不牺牲当前 v2.0.0 的稳定性，又能吸收 OKF / LLM-Wiki 的长期价值。

---

## 13. Factory Review CONDITIONAL_PASS 修复记录

Factory Review 结论：`CONDITIONAL_PASS`，存档：`projects/2604131/reviews/2026-06-19-B-DESIGN-OKF-ALIGNMENT-CONDITIONAL_PASS.md`。

已修复：

1. **导出目录污染索引风险**
   - 原方案：导出到 `knowledge/.okf-export/`
   - 问题：v2.0.0 `scan_markdown_files()` 会扫描 `.okf-export/index.md`、`log.md` 和归档副本，制造重复 entries
   - 修复：v2.1 导出目录改为 `.kb-workdir/okf-export/`，复用当前 ingest 已跳过 `.kb-workdir` 的事实
   - 硬验收：若未来改回根目录导出，必须同批实现 ingest/system-doc 显式跳过

2. **OKF-style 字段开关口径冲突**
   - 原方案：v2.1 字段默认开启
   - 问题：与“保守 alignment、不承诺 full compliance”的主策略冲突
   - 修复：OKF-style 字段改为 **opt-in 默认关闭**，用户显式启用后才写入新归档

3. **低严重度问题同步修正**
   - 补官方源链接：Google Cloud blog + Karpathy gist
   - 修正 “Link AIC” 笔误为 “Link Archivist”
   - v3 living wiki 立项前必须先复核 OpenClaw 是否已具备 synthesis/wiki 能力，避免重复造轮子

按评审意见：“两项必修修完无需重评”。本方案可作为后续 OKF alignment 版本迭代基准。
