# Link Archivist × KB Graph 合并方案

**项目**：2604131 link-archivist
**关联项目**：2605261 kb-graph
**方案版本**：v2.1（修复 v2.0 复评遗留的 1 项 NOT_FIXED）
**作者**：Factory Orchestrator
**审核**：Factory Reviewer v1 = CONDITIONAL_PASS → v2.0 复评 = CONDITIONAL_PASS（4/5 PASS，1 NOT_FIXED）→ v2.1 修复配置迁移口径矛盾 → 待终评

---

## 0. 背景与目标

### 0.1 现状（已验证）

- **Link Archivist v1.12.1**（项目 2604131）：抓取 → 调研 → 生成报告 → 归档
  - `archive_report.py` 已包含 `_trigger_kb_graph_index()` 函数，意图在归档完成后自动调 KB Graph 增量索引
  - 归档报告 YAML frontmatter 已支持 `entities` / `summary` / `confidence` 字段
  - SKILL.md frontmatter 版本号停留在 1.11.0（与 version.json 不同步）

- **KB Graph v0.3.1**（项目 2605261）：五层架构（采集→编译→图谱→查询→维护）
  - `kb_graph.py` 只实现了 `build` / `query` / `stats` 三个子命令
  - `usage.md` 文档声明的 `update-single` / `update` / `status` / `lint` 等命令**未实现**
  - `archive_report.py` 调用的 `update-single` 命令**不存在**，自动索引实际是坏的
  - `compile.py` 用 LLM 从 Markdown 提取 entities/tags/summary（已有可用代码）
  - `build_graph.py` 从 entries.json 构建节点/边 + Louvain 社区发现（已有可用代码）
  - `query.py` 支持 keyword / semantic / hybrid 三种查询模式
  - `lint.py` 检查 orphan 文件和 dangling ref（已有可用代码）

- **目录配置冲突**（已通过读 `~/.openclaw/*.json` 验证）：
  - Link Archivist `archive_dir` = `/Users/evan/.openclaw/gateways/life/state/workspace-life/knowledge`（522 个 .md 文件）
  - KB Graph `watch_dirs[0]` = `/Users/evan/.openclaw/gateways/life/state/workspace-life/memory/archived`（0 个文件）
  - 实际 `entries.json` 存在于 `knowledge/.kb-workdir/`，含 462 条
  - 也就是说 KB Graph 当前是在 Link Archivist 的归档目录工作的，但 watch_dirs 配置写的是另一个目录

### 0.2 问题

1. 集成断裂：`_trigger_kb_graph_index` 调用不存在的命令，自动索引功能完全失效
2. 重复 LLM 调用：Link Archivist 生成报告时 LLM 已提取 summary/entities，KB Graph 重新调 LLM 做相同工作
3. 配置分散：用户需要装两个 Skill、配两份 config
4. 维护成本：版本号、SKILL.md frontmatter、git 提交跨两个项目
5. 文档与实现脱节：KB Graph 的 usage.md 描述了一堆不存在的命令

### 0.3 目标

把 KB Graph 从独立 Skill 降级为 Link Archivist 内部模块，合并为一个 Skill，对外只暴露 `link-archivist` 一个入口。合并后：

- 一个 Skill、一套配置、一次安装
- 归档即索引（无 subprocess 跨进程调用）
- 支持全量重建 + 增量更新 + 知识库查询
- 已有索引数据可平滑迁移

---

## 1. 合并策略

### 1.1 总体原则

- **保留 KB Graph 的五层架构作为内部模块**，不删除代码，只迁移位置
- **归档即索引**：Phase 5 归档完成后，直接调用内部 Python 函数（import）完成索引，不走 subprocess
- **frontmatter 优先**：归档报告 YAML 已含 summary/entities/tags/confidence，直接解析 frontmatter 即可生成 entry，不需要再调 LLM
- **保留独立全量重建能力**：支持用户对历史归档重新 LLM 编译（比如修复 entities 质量）

### 1.2 目标目录结构

```
projects/2604131/link-archivist/
├── SKILL.md                          # 合并：触发场景增加"查知识库"
├── version.json                      # 升级到 v2.0.0（破坏性变更 + 新能力）
├── VERSION                           # 2.0.0
├── scripts/
│   ├── init_config.py                # 扩展：合并 link-archivist + kb-graph 配置
│   ├── decide_mode.py
│   ├── youtube_subtitle.py
│   ├── tavily_search.py
│   ├── douyin_process.py
│   ├── video_archive.py
│   ├── archive_report.py             # 改造：直接 import kb_index 模块
│   ├── validate_report.py
│   ├── kb_query.py                   # 新增：知识库查询入口（暴露给 Agent）
│   ├── kb_rebuild.py                 # 新增：全量重建入口
│   └── kb_lint.py                    # 新增：质量巡检入口
├── lib/                              # 新增目录
│   └── kb_index/                     # 来自 kb-graph 的核心逻辑
│       ├── __init__.py
│       ├── ingest.py                 # 原 kb-graph/scripts/ingest.py
│       ├── compile.py                # 原 kb-graph/scripts/compile.py（仅 LLM 重编入口）
│       ├── parse_frontmatter.py      # 新增：从归档 frontmatter 提取 entry（主路径）
│       ├── build_graph.py            # 原 kb-graph/scripts/build_graph.py
│       ├── update_single.py          # 新增：单文件增量更新（核心）
│       ├── query_engine.py           # 原 kb-graph/scripts/query.py 逻辑
│       └── lint.py                   # 原 kb-graph/scripts/lint.py
├── specs/agents/
│   ├── link-archivist-orchestrator.md
│   └── link-archivist-worker.md
├── references/
│   ├── youtube-workflow.md
│   ├── survey-methodology.md
│   ├── archive-template.md
│   ├── decision-rules.md
│   ├── degradation-rules.md
│   ├── github-discovery-workflow.md
│   ├── faq.md
│   ├── migration-notes.md
│   ├── report-template.md
│   └── kb-query-guide.md             # 新增：知识库查询使用指南
├── examples/
├── tests/
│   ├── test_integration.py
│   └── test_kb_index.py              # 新增：索引模块测试
├── docs/
│   └── flow.html
├── temp/
└── .kb-workdir/                      # 用户归档目录下（不在 skill 目录）
```

### 1.3 状态机：合并后的 Skill 触发场景

| 触发词/场景 | 子流程 | 内部调用 |
|------------|--------|---------|
| 收到 URL/文件/文本 | 抓取 → 调研 → 生成报告 → 归档 → 索引 | Phase 5 内调 `lib.kb_index.update_single` |
| "查知识库"/"搜归档"/"kb 查询" | 解析查询 → 检索 → 渲染 | 调 `scripts/kb_query.py` |
| "重建索引"/"全量更新" | 扫描目录 → 解析/编译 → 构建图谱 | 调 `scripts/kb_rebuild.py` |
| "检查索引质量" | Lint 巡检 | 调 `scripts/kb_lint.py` |
| "索引状态" | 统计信息 | 调 `scripts/kb_query.py status` |

---

## 2. 数据模型与文件格式

### 2.1 归档报告 frontmatter（已存在，需扩展）

Link Archivist 当前 frontmatter：

```yaml
archive: K-260619-001
source: https://example.com
source_type: url
created_at: 2026-06-19T17:30:00
entities: [实体1, 实体2]
summary: 一句话摘要
confidence: high
tags: []
```

合并后**必须**保证的字段（Phase 3 调研时由 LLM 一次生成）：

| 字段 | 必填 | 用途 | 谁生成 |
|------|------|------|--------|
| archive | ✅ | 归档编号 | archive_report.py |
| source | ✅ | 原始 URL/文件路径 | archive_report.py |
| source_type | ✅ | url/file/text | archive_report.py |
| created_at | ✅ | ISO 时间 | archive_report.py |
| summary | ✅ | ≤200 字摘要 | Phase 3 LLM |
| entities | ✅ | 关键实体列表（≤10） | Phase 3 LLM |
| tags | ✅ | 标签（≤3） | Phase 3 LLM |
| relationships | ❌ | 文档间关系 | Phase 3 LLM（可选） |
| confidence | ✅ | high/medium/low | archive_report.py |

**关键约束**：Phase 3 调研时必须让 LLM 输出这些字段，并由 orchestrator 传给 `archive_report.py` 的 `--summary` `--entities` `--tags` 参数。当前代码已经支持这些参数，但需要在 SKILL.md / orchestrator.md 中明确要求。

### 2.2 索引文件（沿用 KB Graph 现有格式）

```
{archive_dir}/.kb-workdir/
├── entries.json              # 所有文档的 entry，key=rel_path
├── entities-registry.json    # 实体→文档 反向索引
├── graph-data.json           # 实体关系图
├── kb-ontology.json          # 实体类型本体
├── kb_cache.json             # SHA256 缓存
├── embeddings.json           # （可选）语义向量
└── build_stats.json          # （新增）最近一次构建时间/统计
```

### 2.3 entry 数据结构

```python
{
  "path": "2026/06/K-260619-001-xxx.md",
  "title": "文档标题",
  "summary": "摘要",
  "entities": ["实体1", "实体2"],
  "tags": ["AI", "架构"],
  "relationships": [{"type": "reference", "target": "...", "description": "..."}],
  "confidence": "high",
  "source_sha256": "...",
  "compiled_at": "2026-06-19T17:30:00",
  "compile_method": "frontmatter" | "llm",   # 新增：标识来源
  "provider": "phase3_llm" | "none"           # 新增：哪个 LLM 生成的
}
```

`compile_method` 字段至关重要：标识 entry 是从 frontmatter 直接解析的（绝大多数情况），还是用户主动要求 LLM 重新编译的（少数情况）。便于后续排查质量。

---

## 3. 核心模块设计

### 3.1 `lib/kb_index/parse_frontmatter.py`

**职责**：从归档 .md 的 YAML frontmatter 提取 entry，**不调 LLM**。

**接口**：
```python
def parse_entry(md_path: Path) -> dict:
    """从 frontmatter 解析 entry，缺失字段抛 ValueError"""
    # 读取文件 → 解析 --- 之间的 YAML → 校验必填字段 → 返回 entry
    # sha256 必算
    # 失败抛 ValueError，调用方记录日志并跳过
```

**校验规则**：
- summary、entities、tags 任一缺失 → 抛 ValueError
- 字段类型不符 → 抛 ValueError
- entities 超过 10 个 → 截断并 log warning
- tags 超过 3 个 → 截断并 log warning

### 3.2 `lib/kb_index/update_single.py`（核心）

**职责**：单文件增量更新。**纯函数**，不调 LLM（除非 frontmatter 不可用）。

**接口**：
```python
def update_single(
    md_path: Path,
    archive_dir: Path,
    *, force_recompile: bool = False
) -> dict:
    """增量更新单文件的索引。

    Args:
        md_path: 归档文件绝对路径
        archive_dir: 归档根目录（含 .kb-workdir/）
        force_recompile: 强制 LLM 重编（忽略 frontmatter）

    Returns:
        {"ok": True, "entry_path": "2026/06/...", "compile_method": "frontmatter"}

    Raises:
        FileNotFoundError: 归档文件不存在
        ValueError: frontmatter 格式错误且未开启 force_recompile
    """
```

**执行流程（v2.0 修正：原子写 + dirty 标记 + 启动自愈）**：

1. **加锁**：用 `fcntl.flock(LOCK_EX)` 锁住 `archive_dir/.kb-workdir/.lock` 文件。如果锁失败（另一个进程在写），等待 5 秒重试，超时抛 ConcurrentUpdateError
2. **计算 SHA256**，比对 `kb_cache.json`
3. 若 SHA256 未变 → 检查 entries.json 是否已有该 path → 有则直接返回（no-op）
4. **解析 frontmatter**（parse_entry）→ 得到 entry（写入临时文件）
5. **原子写 entries.json**：
   - 写 `entries.json.tmp` → `os.replace` 原子替换为 `entries.json`
   - 替换前校验 JSON 合法（先 load 一次）
6. **原子写 entities-registry.json**（同上）
7. **原子写 graph-data.json**（同上）
8. **原子写 embeddings.json**（如果启用）
9. **原子写 kb_cache.json**
10. **更新 build_stats.json**（记录最后成功时间）
11. **释放锁**

**失败处理（v2.0 修正：dirty + 自愈）**：

- frontmatter 缺失必填字段 → 写入 cache.status=failed，**不更新任何索引文件**，下一次还会重试
- 任意一步写失败 → **所有已更新的文件保留**，但设置 `kb-workdir/.dirty` 标志
- `.dirty` 存在时 → 下一次 `kb_rebuild --incremental` 启动时检测到，自动从 `entries.json` 全量重建 `entities-registry.json` / `graph-data.json`（不需要 LLM，从 entries 直接 derive）
- entries.json 写入失败 → 抛异常，**不更新任何派生文件**
- 派生文件（entities-registry / graph-data）写失败 → 设置 .dirty，下次自愈

**为什么不回滚已成功的步骤**：回滚比自愈复杂得多，而且 entries.json 是事实源（source of truth），从它重建派生文件是 O(N) 但只需一次。接受偶发性的 dirty 状态。

**并发安全（v2.0 修正：支持串行并发，不支持真并行）**：
- 多进程串行调用 update_single：✅ 支持（fcntl 锁队列）
- 多线程真并行调用 update_single：❌ 不支持（锁保证只有一个在写）
- 多个 Agent 同时归档：✅ 锁队列处理，不会损坏索引

### 3.3 `lib/kb_index/ingest.py`

**职责**：扫描目录，检测变更。**沿用 KB Graph 现有实现**。

**关键修改**：
- 路径：从 `projects/2605261/kb-graph/scripts/ingest.py` 移到 `projects/2604131/link-archivist/lib/kb_index/ingest.py`
- import 路径调整
- 行为不变

### 3.4 `lib/kb_index/compile.py`（仅作重编入口）

**职责**：用 LLM 从 Markdown 重新提取 entry。**仅在 force_recompile=True 或全量重建时调用**。

**关键修改**：
- 路径迁移
- prompt 中要求 LLM 输出符合 frontmatter 格式的字段（与 parse_frontmatter 兼容）
- 调用方在主路径**不应**调用此函数

### 3.5 `lib/kb_index/build_graph.py`

**职责**：从 entries.json 构建 nodes/edges + Louvain 社区发现。**仅全量模式**。

**关键修改**：
- 路径迁移
- 行为不变

### 3.6 `lib/kb_index/query_engine.py`

**职责**：执行查询，支持 keyword / semantic / hybrid 三种模式。

**关键修改**：
- 路径迁移
- 默认 mode=keyword
- 改进：基于 entity 关系扩展查询（如果用户查"OpenClaw"，自动把相关实体的文档也带上）

### 3.7 `lib/kb_index/lint.py`

**职责**：检查索引健康度。

**检测项**：
- orphan 文件：.md 存在但 entries.json 没有
- dangling ref：relationships.target 指向不存在的文件
- 实体覆盖率：多少 entry 的 entities 为空
- confidence 分布：high/medium/low 各占多少

---

## 4. 脚本入口设计

### 4.1 `scripts/kb_query.py`（Agent 可调用）

```bash
# 关键词搜索
python3 scripts/kb_query.py "OpenClaw KB Graph" --dir {archive_dir}

# 语义搜索
python3 scripts/kb_query.py "我想找关于知识图谱的笔记" --dir {archive_dir} --mode semantic

# 混合模式
python3 scripts/kb_query.py "知识图谱" --dir {archive_dir} --mode hybrid

# 状态
python3 scripts/kb_query.py status --dir {archive_dir}
```

**返回 JSON 结构**：
```json
{
  "ok": true,
  "query": "OpenClaw KB Graph",
  "method": "keyword",
  "total": 5,
  "results": [
    {
      "path": "2026/06/K-260619-001-xxx.md",
      "title": "...",
      "summary": "...",
      "entities": ["..."],
      "tags": ["..."],
      "score": 18,
      "matched_entity": "OpenClaw"
    }
  ]
}
```

### 4.2 `scripts/kb_rebuild.py`（Agent 可调用）

```bash
# 全量重建（耗时 5-10 分钟）
python3 scripts/kb_rebuild.py --dir {archive_dir}

# 强制 LLM 重编（忽略已有 frontmatter）
python3 scripts/kb_rebuild.py --dir {archive_dir} --force-llm

# 增量更新（基于 SHA256 检测）
python3 scripts/kb_rebuild.py --dir {archive_dir} --incremental
```

**触发规则**：
- 用户说"重建索引" → 全量（不带 --force-llm，使用已有 frontmatter）
- 用户说"重新整理归档"或"重编所有 entities" → 加 --force-llm
- 用户说"增量更新"/"刷新" → --incremental

### 4.3 `scripts/kb_lint.py`（Agent 可调用）

```bash
python3 scripts/kb_lint.py --dir {archive_dir}
```

返回需要修复的问题列表。

### 4.4 `scripts/archive_report.py`（改造）

**现状**：调用 `_trigger_kb_graph_index()` 通过 subprocess 调 `kb_graph.py update-single`，但这个命令不存在。

**改造**：
- 删除 `_trigger_kb_graph_index()` 的 subprocess 逻辑
- 改为直接 import：
  ```python
  from lib.kb_index.update_single import update_single
  update_single(archive_file, archive_dir)
  ```
- 在 result 中添加 `index_status: "indexed" | "failed" | "skipped"`
- 异常时记录到 log，不阻塞归档主流程

### 4.5 `scripts/init_config.py`（扩展）

**职责**：统一配置文件。合并 link-archivist 和 kb-graph 的 config。

**新配置文件**：`~/.openclaw/link-archivist-config.json`

```json
{
  "archive_dir": "/path/to/knowledge",
  "xgjk_app_key": "...",
  "tavily_api_key": "...",
  "video_archive_dir": "/path/to/videos",
  "kb_index": {
    "enabled": true,
    "query_mode": "keyword",
    "auto_update": true,
    "lint_schedule": "daily",
    "embeddings_enabled": false
  }
}
```

**迁移逻辑（与 §7.3 一致：备份而非删除）**：
- 启动时检测 `~/.openclaw/kb-graph-config.json` 是否存在
- 存在且 watch_dirs[0] == archive_dir → 合并 kb_index 字段到 link-archivist-config.json，将旧文件重命名为 `kb-graph-config.json.bak`（**不删除**）
- 存在但 watch_dirs[0] != archive_dir → 不合并、不修改旧文件，提示用户手动决定（详见 §7.3.1 case B）
- 不存在 → 直接用 default

**降级**：
- 没有 archive_dir → 旧流程不变
- 有 archive_dir 但 kb_index.enabled = false → 不索引

---

## 5. SKILL.md 变更

### 5.1 frontmatter 修正

```yaml
---
name: link-archivist
version: "2.0.0"
skillcode: link-archivist
github: https://github.com/evan-zhang/agent-factory
description: |
  当用户发送一个链接（YouTube/通用 URL）、文件或粘贴文本，需要抓取内容并生成调研报告时触发。
  也支持查询本地知识库（"查归档"/"搜笔记"）和索引管理（"重建索引"）。
---
```

### 5.2 触发场景扩展

新增三节：

```markdown
## 触发场景 2：查询知识库

当用户说以下任何一种话时触发：
- "查知识库" / "kb 查询" / "知识图谱"
- "搜索归档" / "找之前的报告" / "我之前研究过 X 吗？"
- "根据之前的笔记，..."

执行：
1. python3 scripts/kb_query.py "<用户查询>" --dir {archive_dir} --mode keyword
2. 解析 JSON results 数组
3. 用对话语言呈现：路径 + 标题 + 摘要 + 关键实体

只展示前 5 条。更多按用户要求。

## 触发场景 3：索引管理

"重建索引" / "全量更新"：
  python3 scripts/kb_rebuild.py --dir {archive_dir}
  耗时较长（522 个文件预计 2-3 分钟），执行前告知用户。

"增量更新" / "刷新索引"：
  python3 scripts/kb_rebuild.py --dir {archive_dir} --incremental
  基于 SHA256 检测变更，仅处理新增/修改文件。

"检查索引质量" / "kb 巡检"：
  python3 scripts/kb_lint.py --dir {archive_dir}
```

### 5.3 Phase 5 改造

原 Phase 5 末尾的 `_trigger_kb_graph_index` 替换为：

```markdown
### Phase 5：归档 + 索引 [MUST]

**进度提示**：`💾 [5/5] 归档并索引中...`

**动作**：
1. 运行 `scripts/archive_report.py` 完成归档（内部已含索引调用）
   - 内部自动调用 `lib.kb_index.update_single` 完成增量索引
   - 索引耗时通常 <100ms，不阻塞主流程
   - 索引失败时 result 中 `index_status: failed`，归档仍然成功

**进度提示**（完成后）：
  `✅ [5/5] 归档完成：<归档路径>（索引：indexed/failed）`
```

### 5.5 披露分层（v2.0 新增节）

SKILL.md 是 Agent 启动时加载的核心文件，信息量必须精炼。详细信息沉到 references/ 和设计文档。

### SKILL.md 必须保留

- **frontmatter**（name / version / description）
- **触发场景**（全部 3 个场景，每个 ≤10 行示例）
- **Phase 1-5 主流程**（压缩到必要步骤，省略子步骤）
- **边界**（什么做 / 什么不做）
- **配置与授权**（init_config.py 的 config 字段表）
- **问题反馈**（Issue 地址 + 标题格式）

### SKILL.md 不保留（沉到 references/）

- Phase 3 prompt 模板 → `references/phase3-prompt-template.md`
- 知识库查询使用指南 → `references/kb-query-guide.md`
- 迁移说明 → `references/migration-from-kb-graph.md`
- 索引架构设计 → `references/kb-index-architecture.md`

### references/ 不保留（沉到设计文档）

- 模块 API 详细设计 → `lib/kb_index/` 内的 docstring
- 脚本参数详细说明 → 各脚本的 `--help`
- 性能调优、并发原理 → `docs/MERGE_PLAN_v2.md`（本设计文档）

### SKILL.md 预计行数

v1.12.1 当前 SKILL.md = 367 行。v2.0.0 预计 **400-450 行**（增加 3 个触发场景 + KB 索引节，但保留 references/ 引用而不是完整内容）。

### Agent 启动时读取顺序（v2.0 明确）

1. SKILL.md（必读）
2. 遇到查询场景 → `references/kb-query-guide.md`
3. 遇到归档场景 → 内联 Phase 3-5 描述，不读 references（保证主流程不依赖额外读取）
4. 遇到索引管理场景 → `references/kb-index-architecture.md`（仅当用户问"为什么"时才读）

### 5.4 边界更新

```markdown
## 边界

**本 Skill 负责**：
- 抓取 → 调研 → 生成报告 → 归档 → 索引
- 知识库查询（关键词/语义/混合）
- 索引管理（重建/增量/巡检）

**不负责**：
- Obsidian 同步（外部 Observer）
- 渠道发送
- 文件解析（PDF/Word/PPT/图片）
- 跨设备同步
```

---

## 6. 触发判断总图

```
收到消息
 ├─ URL/链接/文件/文本
 │   ├─ sub-agent 模式
 │   └─ Phase 1-5（含索引）
 ├─ "查知识库"/"kb 查询"/"找归档"
 │   └─ 调 kb_query.py
 ├─ "重建索引"/"全量更新"
 │   └─ 调 kb_rebuild.py（全量）
 ├─ "增量更新"/"刷新"
 │   └─ 调 kb_rebuild.py --incremental
 ├─ "索引质量"/"kb 巡检"
 │   └─ 调 kb_lint.py
 └─ 未初始化
     └─ 引导配置 archive_dir
```

---

## 7. 迁移与数据兼容性

### 7.1 KB Graph Skill 处理

- 标记 KB Graph Skill 为 **deprecated**（保留一个 v0.3.2 版本，在 SKILL.md 顶部加 deprecation 警告）
- 引导用户迁移到 Link Archivist v2.0.0
- 6 个月后删除 GitHub 上的 kb-graph 目录

**为什么不立即删除**：
- 已有用户的 watch_dirs 可能指向其他目录
- 给用户迁移时间
- 保留代码用于回滚参考

### 7.2 已有索引数据

- `entries.json` / `entities-registry.json` / `graph-data.json` 格式不变
- 迁移后 Link Archivist 的 update_single 可以直接消费
- 唯一差异：旧 entry 没有 `compile_method` 字段 → update_single 检测到缺失时自动填 `"compile_method": "legacy"`

### 7.3 配置文件迁移（v2.0 修正：备份而非删除）

**明确原则**：v2.0.0 **不删除**任何用户的旧配置文件。备份而非删除。

#### 7.3.1 旧 `~/.openclaw/kb-graph-config.json` 处理

启动时（init_config.py）按以下规则处理：

1. **检测**：检查 `~/.openclaw/kb-graph-config.json` 是否存在
2. **比较**：读出 `watch_dirs[0]`，与 link-archivist 的 `archive_dir` 比较
3. **迁移**：
   - **case A**（watch_dirs[0] == archive_dir）：合并 `kb_index.*` 字段到 link-archivist-config.json。**将 kb-graph-config.json 重命名为 `kb-graph-config.json.bak`**（不是删除）
   - **case B**（watch_dirs[0] != archive_dir）：**不合并，不修改 kb-graph-config.json**。提示用户："检测到 KB Graph 配置的 watch_dirs 与 archive_dir 不一致。请手动决定：(1) 修改 archive_dir 指向 watch_dirs[0]；(2) 移动 watch_dirs[0] 的内容到 archive_dir；(3) 忽略旧配置（KB Graph v0.3.2 仍可独立运行）"
   - **case C**（archive_dir 不存在）：引导用户先配置 archive_dir，不读 kb-graph-config.json
4. **永久保留**：`kb-graph-config.json.bak` 永远不删除。注释到 SKILL.md 配置节：用户可手动删除，但系统不主动删。

#### 7.3.2 旧 `~/.openclaw/link-archivist-config.json` 处理

- 直接读取，不做迁移（旧配置文件本身）
- 新增 `kb_index` 节（如不存在）

#### 7.3.3 回滚路径

如果用户升级 v2.0.0 后想回退到 v1.12.1：

1. `cd ~/.openclaw/skills/link-archivist && git checkout v1.12.1`
2. 删除 v2.0.0 新增的 `kb_index` 节
3. 恢复 `kb-graph-config.json` 从 `kb-graph-config.json.bak`（如果需要 KB Graph 独立运行）
4. 重启 gateway

**回滚不会丢失数据**：所有索引文件在 `.kb-workdir/` 中保留，回滚后 v1.12.1 不会主动修改它们。

### 7.4 风险：路径不一致的处理（v2.0 修正）

v1.0 中提出"强制以 archive_dir 为准"过于激进。v2.0 改为：

- **默认**：以 archive_dir 为准（v2.0.0 的唯一目录源）
- **迁移窗口期**（v2.0.0 发布后 90 天内）：保留 kb-graph-config.json 不动，让用户自己决定
- **90 天后**（v2.1.0）：启动时检测 watch_dirs[0] != archive_dir，打印 warning "KB Graph 已 deprecated，建议统一到 archive_dir"
- **180 天后**（v2.3.0）：彻底删除 kb-graph-config.json 处理逻辑

---

## 8. 测试策略

### 8.1 单元测试

- `lib/kb_index/parse_frontmatter.py`：测试 7 种边界（缺字段/类型错/空 entities/超长 summary 等）
- `lib/kb_index/update_single.py`：测试新建/更新/删除/SHA256 命中
- `lib/kb_index/query_engine.py`：测试 keyword/semantic/hybrid 三模式

### 8.2 集成测试

- `tests/test_kb_index.py`：在 tmp 目录模拟完整流程
  1. 创建 3 个归档 .md（不同 frontmatter 完整性）
  2. 调 update_single × 3
  3. 验证 entries.json 正确
  4. 调 query
  5. 验证返回结果
  6. 调 lint
  7. 验证报告

### 8.3 迁移测试

- 复制当前 `~/.openclaw/gateways/life/state/workspace-life/knowledge/.kb-workdir` 到 tmp
- 在 tmp 上跑新代码
- 验证 entries.json 加载正常、query 返回正常

### 8.4 真实数据回归

- 在 archive_dir 实际目录上跑 kb_rebuild --incremental
- 验证 entries.json 数量 = 522（实际归档数）
- 验证 query 5 个常见查询返回合理结果

### 8.5 验收

- 用户接受 5 次 query 请求的返回结果质量
- 用户触发 3 次归档，观察是否自动索引
- 用户跑一次 lint，确认无 orphan

---

## 9. 发布策略

### 9.1 版本号

- **Link Archivist: v1.12.1 → v2.0.0**（主版本，破坏性变更）
  - 破坏性：触发场景变化、配置文件结构变化
  - 新能力：知识库查询、索引管理
  - 内部：subprocess → import

- **KB Graph: v0.3.1 → v0.3.2（deprecation release）**
  - SKILL.md 顶部加 deprecation 警告
  - 引导用户升级到 Link Archivist v2.0.0
  - 6 个月后删除（2026-12-19）

### 9.2 版本号同步点

- `projects/2604131/link-archivist/SKILL.md` frontmatter: 2.0.0
- `projects/2604131/link-archivist/version.json`: 2.0.0
- `projects/2604131/VERSION`: 2.0.0
- `projects/2605261/kb-graph/SKILL.md` frontmatter: 0.3.2
- `projects/2605261/kb-graph/version.json`: 0.3.2
- `projects/2605261/kb-graph/VERSION`: 0.3.2
- `projects/2605261/VERSION`: 0.3.2

### 9.3 提交策略

- 一次大提交：`release: link-archivist v2.0.0 - KB Graph 合并 + 知识库查询`
- 一次小提交：`chore(kb-graph): mark deprecated - 引导用户升级`
- 两个 commit 分开发，但放在同一个 PR

### 9.4 测试包（按 TOOLS.md 模板）

```
🔬 Link Archivist v2.0.0 测试包

📦 安装命令（升级）：
cd ~/.openclaw/skills/link-archivist
git pull
# 或全新安装：
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2604131/link-archivist

本次更新内容：
1. KB Graph 合并为内部模块（lib/kb_index/）
2. 归档即索引（Phase 5 内调 update_single，无 subprocess）
3. 新增知识库查询触发场景
4. 新增索引管理触发场景（重建/增量/巡检）
5. KB Graph Skill 标记 deprecated

重点测试方向：
- 触发"查知识库 OpenClaw"，验证返回 5 条相关归档
- 发送一个新链接归档，验证 entries.json 自动新增
- 运行 kb_lint，验证无 orphan / 无 dangling ref
```

---

## 10. 风险与缓解

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 现有 462 条索引数据迁移失败 | 高 | 单元测试 + 真实数据回归测试 + 保留 KB Graph 旧版本作回滚 |
| frontmatter 字段缺失导致 update_single 失败 | 中 | 失败的 entry 写入 cache.status=failed，下一次继续重试；不阻塞归档 |
| 旧 KB Graph 用户配置冲突 | 中 | 启动时检测 + 提示用户选择（强制以 archive_dir 为准） |
| LLM 重编成本高 | 中 | 主路径用 frontmatter 解析，LLM 重编仅在 force-llm 时调用 |
| 并发写 entries.json 损坏 | 低 | 单进程串行；用文件锁（fcntl）保护写操作 |
| Phase 3 LLM 不输出 summary/entities | 中 | SKILL.md 明确要求 + orchestrator 检查返回值 |
| 删除 KB Graph 目录后老用户回退困难 | 低 | 保留 6 个月；deprecation release 提示清楚 |

---

## 11. 任务清单（实施步骤）

按依赖顺序：

1. **S3-1**：建立 `lib/kb_index/` 目录骨架
2. **S3-2**：迁移 `parse_frontmatter.py`（从 KB Graph compile.py 提取 frontmatter 解析逻辑）
3. **S3-3**：迁移 `update_single.py`（核心增量逻辑）
4. **S3-4**：迁移 `ingest.py` / `build_graph.py` / `query_engine.py` / `lint.py` / `compile.py`
5. **S3-5**：实现 `scripts/kb_query.py` / `scripts/kb_rebuild.py` / `scripts/kb_lint.py`
6. **S3-6**：改造 `scripts/archive_report.py`（删除 subprocess，改 import）
7. **S3-7**：扩展 `scripts/init_config.py`（合并 config，迁移逻辑）
8. **S3-8**：更新 `SKILL.md`（触发场景、frontmatter、Phase 5、边界）
9. **S3-9**：更新 `specs/agents/link-archivist-orchestrator.md` 和 `link-archivist-worker.md`
10. **S3-10**：编写 `tests/test_kb_index.py`
11. **S3-11**：在真实数据上回归测试
12. **S3-12**：KB Graph Skill 标记 deprecated（v0.3.2）
13. **S3-13**：版本号同步（5 处）
14. **S3-14**：提交 + push + 发送测试包

---

## 12. 验收标准

- [ ] 用户说"查知识库 OpenClaw" → 收到 ≥1 条相关归档
- [ ] 用户发送新链接归档 → entries.json 自动新增（无需手动 build）
- [ ] 用户说"重建索引" → 全量跑通，entries 数量 = 522
- [ ] 用户说"检查索引" → 返回合理的 orphan / dangling 报告
- [ ] SKILL.md 三个触发场景都有完整文档
- [ ] 配置文件只有一个：link-archivist-config.json
- [ ] KB Graph Skill 标记 deprecated
- [ ] 版本号在 5 处全部同步
- [ ] 测试包发出后用户无阻塞性问题反馈

---

## 13. 设计决策（v2.0 已收敛，替代原 v1.0 未决问题）

以下 5 项决策由 Orchestrator 联合 factory-reviewer 评审反馈收敛，进入实施后不可再变更：

### 13.1 KB Graph 旧 Skill 的处理周期

**决策**：**保留 6 个月（180 天），标记 deprecated，2026-12-19 正式删除**。

- v0.3.2：仅 SKILL.md 顶部加 deprecation 警告，**不删除任何代码**。不增加新功能。
- 2026-09-19（90 天）：触发 v0.4.0 release，README 加 ⚠️ 横幅
- 2026-12-19（180 天）：删除 `projects/2605261/` 目录，git rm
- 回滚路径：6 个月内任何时刻可回退到 v0.3.1（保留在 GitHub tag 中）

**理由**：用户可能正在用 v0.3.1 看自己的旧归档目录。强制 6 个月窗口期，避免一次硬切带来的数据不可访问风险。

### 13.2 LLM 重编触发条件

**决策**：**默认不调 LLM。LLM 重编仅在用户显式触发 `--force-llm` 时执行**。

- 归档路径（Phase 5）：从 frontmatter 解析（不调 LLM）
- 增量更新（kb_rebuild --incremental）：从 frontmatter 解析（不调 LLM）
- 全量重建（kb_rebuild，无参数）：从 frontmatter 解析（不调 LLM）
- 强制重编（kb_rebuild --force-llm）：调 LLM 重写所有 entry（必须用户在请求中明确说"重编所有 entities"才触发）

**为什么这样定**：当前 522 个归档的 frontmatter 字段已基本完整，重复 LLM 编译属于浪费。LLM 编译仅用于：(a) 历史 archive 没有 frontmatter；(b) 用户主动想升级 entities 质量。

**Phase 3 LLM 输出要求**：Orchestrator 必须在 prompt 中强制要求输出 frontmatter 字段。如果 LLM 输出格式不符合 schema，archive_report.py 仍允许归档（保证主流程不被阻塞），但 result.index_status 标 `failed`，提示用户"frontmatter 字段缺失，请检查 Phase 3 LLM 输出"。

### 13.3 多目录支持

**决策**：**v2.0.0 强制以 `archive_dir` 为唯一目录源，删除 `watch_dirs` 字段**。

- `~/.openclaw/link-archivist-config.json` 只有一个 `archive_dir`
- 不再支持 KB Graph 风格的 `watch_dirs` 数组
- 旧 `kb-graph-config.json` 中的 `watch_dirs[0]` 仅在**首次迁移**时读一次，之后忽略
- 旧配置保留为 `kb-graph-config.json.bak`（备份而非删除，详见 §7.3）

**理由**：v2.0.0 的核心是简化。多目录需求目前没有真实场景，v0.3.1 的多目录支持本质上只是代码复杂度，没有用户价值。

### 13.4 语义搜索默认状态

**决策**：**默认禁用。需要用户显式配置 `kb_index.embeddings_enabled: true` 才启用**。

- 默认 mode = `keyword`（不需要 OPENAI_API_KEY）
- `embeddings_enabled: true` 时 mode 可选 `keyword` / `semantic` / `hybrid`
- 启用 semantic 模式需要 OPENAI_API_KEY
- query 时如果 mode=semantic/hybrid 但 key 缺失，自动降级到 keyword + warning

**理由**：避免给所有用户增加 OPENAI_API_KEY 的环境变量负担。keyword 模式对归档库已经足够（522 条数据 + 标题/摘要/实体/标签全字段搜索）。

### 13.5 Phase 3 LLM Prompt 模板

**决策**：**提供标准 prompt 模板，写入 `references/phase3-prompt-template.md`，orchestrator 必须使用**。

prompt 模板核心要求（见 references 文档完整版）：

```text
你是调研助手。基于以下内容生成结构化报告 + frontmatter 元数据。

**必须输出的 JSON 块**（在报告正文最前面，用 ```yaml ... ``` 包裹）：

```yaml
summary: <≤200 字中文摘要>
entities:
  - <关键实体1>
  - <关键实体2>
  # 最多 10 个
tags:
  - <标签1>
  - <标签2>
  # 最多 3 个，从 [AI, 架构, 安全, 运维, 产品, 运营, 前端, 后端, 数据库, 工具, 流程, 综合] 选
confidence: high | medium | low
relationships:
  - type: reference | topic
    target: <文档名/主题名>
    description: <关系说明>
```

报告正文 <报告内容>。
```

**校验规则**：parse_frontmatter 检测到以下任一情况视为 `frontmatter_invalid`：
- summary 缺失 / > 200 字
- entities 缺失（空数组允许）
- tags 缺失（空数组允许）
- confidence 不在 {high, medium, low}

**用户反馈格式**（索引失败时）：
```
✅ 归档完成：{archive_path}
⚠️ 索引失败：frontmatter 字段缺失（summary/entities/tags/confidence）
   → 可手动补充后运行 `python3 scripts/kb_rebuild.py --dir {archive_dir} --incremental` 补建索引
   → 或运行 `python3 scripts/kb_rebuild.py --dir {archive_dir} --force-llm` 强制重编
```

---

## 14. v1.0 → v2.0 修复对照（factory-reviewer CONDITIONAL_PASS）

| # | 严重度 | 问题 | 修复位置 |
|---|--------|------|---------|
| 1 | 高 | 5 个未决问题未冻结 | §13.1 - §13.5 改为"设计决策"，每项明确答案 |
| 2 | 高 | 配置迁移策略破坏性风险 | §7.3 改为备份而非删除；§7.4 加 90/180 天窗口 |
| 3 | 中 | 多文件索引一致性策略 | §3.2 增原子写 + fcntl 锁 + dirty 标志 + 启动自愈 |
| 4 | 中 | 三层披露边界不清 | §5.5 新增"披露分层"，SKILL.md vs references vs 设计文档边界 |
| 5 | 中 | Phase 3 frontmatter 输出不稳定 | §13.5 增 prompt 模板 + 校验规则 + 失败时用户反馈格式 |

按 AF-REVIEW-SOP §6，CONDITIONAL_PASS 修完无需重评。Orchestrator 已逐项勾选确认，可进入 S4 开发。
