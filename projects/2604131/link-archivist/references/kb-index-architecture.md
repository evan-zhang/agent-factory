# KB Index Architecture

Link Archivist v2.0.0 内置的知识库索引架构设计文档。

## 设计目标

1. **轻量级**：纯 Python 实现，最小化外部依赖
2. **原子性**：使用 fcntl 锁和临时文件保证并发安全
3. **自愈性**：派生文件损坏时从 entries.json 重建
4. **兼容性**：支持 KB Graph v0.3.x 索引文件格式

## 五层架构

```
┌─────────────────────────────────────────────┐
│          1. Ingest Layer (采集)              │
│  scan_markdown_files() + detect_changes()   │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│      2. Parse Layer (解析)                  │
│  parse_frontmatter (主路径)                 │
│  compile.py LLM (仅 force-llm 时)           │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│    3. Storage Layer (存储)                  │
│  entries.json (source of truth)              │
│  kb_cache.json (SHA256 缓存)                 │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│   4. Derivative Layer (派生)                │
│  entities-registry.json (实体反向索引)        │
│  graph-data.json (关系图)                    │
│  embeddings.json (语义向量)                  │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│     5. Query Layer (查询)                   │
│  keyword / semantic / hybrid                │
└─────────────────────────────────────────────┘
```

## 核心模块

### 1. parse_frontmatter.py

**职责**：从 YAML frontmatter 提取 entry，不调 LLM

**校验规则：**
- summary、entities、tags 任一缺失 → ValueError
- summary > 200 字 → 截断并 warning
- entities > 10 个 → 截断
- tags > 3 个 → 截断
- confidence 不在 {high, medium, low} → ValueError

**关键函数：**
```python
def parse_entry(md_path: Path) -> dict:
    """从 frontmatter 解析 entry，缺失字段抛 ValueError"""
```

### 2. update_single.py

**职责**：单文件增量更新，纯函数，fcntl 锁

**执行流程：**
1. 加锁（fcntl.flock LOCK_EX）
2. 计算 SHA256，比对 kb_cache.json
3. 解析 frontmatter
4. 原子写 entries.json（临时文件 + os.replace）
5. 原子写派生文件
6. 更新 build_stats.json
7. 释放锁

**失败处理：**
- frontmatter 缺失 → 写入 cache.status=failed
- 写入失败 → 设置 .dirty 标志
- 派生文件损坏 → 下次启动自愈

**关键函数：**
```python
def update_single(md_path: Path, archive_dir: Path, *, force_recompile: bool = False) -> dict:
    """增量更新单文件的索引"""

def self_heal(workdir: Path) -> bool:
    """从 entries.json 重建派生索引"""
```

### 3. query_engine.py

**职责**：三种查询模式实现

**查询模式：**
- **keyword**（默认）：title + summary + tags + entities 全字段搜索
- **semantic**：向量相似度搜索（需要 OPENAI_API_KEY）
- **hybrid**：keyword 60% + semantic 40% 融合

**关键函数：**
```python
def query(query_str: str, root: Path, mode: str = "keyword") -> dict:
    """主查询入口"""

def search_by_keyword(root: Path, query_str: str) -> List[dict]:
    """关键词搜索：title +10, summary +5, tags +3, entities +3"""

def search_by_semantic(root: Path, query_str: str) -> List[dict]:
    """语义搜索：cosine 相似度"""

def search_by_hybrid(root: Path, query_str: str) -> List[dict]:
    """混合搜索：加权融合"""
```

### 4. lint.py

**职责**：索引健康检查

**检测项：**
- orphan 文件：.md 存在但 entries.json 没有
- dangling ref：relationships.target 指向不存在的文件
- 实体覆盖率：多少 entry 的 entities 为空
- confidence 分布：high/medium/low 各占多少

**关键函数：**
```python
def lint_index(archive_dir: Path) -> dict:
    """运行完整检查"""
```

## 并发安全

### 文件锁机制

使用 `fcntl.flock(LOCK_EX)` 实现进程间排他锁：

```python
def acquire_lock(lock_file: Path, timeout: float = 5.0) -> bool:
    """获取独占锁，超时抛 ConcurrentUpdateError"""
    fd = open(lock_file, "w")
    fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return True
```

**并发行为：**
- ✅ 多进程串行调用：锁队列处理
- ❌ 多线程真并行：不支持
- ✅ 多个 Agent 同时归档：锁队列处理

### 原子写机制

使用临时文件 + os.replace 保证原子性：

```python
def save_json_atomic(path: Path, data: Any) -> bool:
    """原子写 JSON"""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json_str, encoding="utf-8")
    temp_path.replace(path)  # 原子操作
    return True
```

## 自愈机制

### Dirty 标记

当派生文件写入失败时，设置 `.dirty` 标志：

```python
def mark_dirty(workdir: Path) -> None:
    """标记需要自愈"""
    (workdir / ".dirty").write_text(f"dirty_since: {datetime.now().isoformat()}\n")
```

### 自愈逻辑

下次 `kb_rebuild --incremental` 启动时检测到 .dirty，自动重建：

```python
def self_heal(workdir: Path) -> bool:
    """从 entries.json 重建派生索引"""
    entries = load_json(workdir / "entries.json")

    # 重建 entities-registry.json
    entities_registry = update_entities_registry(entries)
    save_json_atomic(workdir / "entities-registry.json", entities_registry)

    # 重建 graph-data.json
    graph_data = derive_graph_data(entries)
    save_json_atomic(workdir / "graph-data.json", graph_data)

    clear_dirty(workdir)
    return True
```

## 数据流

### 归档即索引（主路径）

```
Phase 3 LLM (生成 frontmatter)
    ↓
archive_report.py (写入 .md 文件)
    ↓
update_single() (解析 frontmatter)
    ↓
entries.json (原子写)
    ↓
entities-registry.json (派生)
    ↓
graph-data.json (派生)
```

### 查询流程

```
Agent 调用 kb_query.py
    ↓
query() (根据 mode 选择)
    ↓
load_entries() (读取 entries.json)
    ↓
search_by_*() (匹配算法)
    ↓
返回 results[] (按 score 排序)
```

### 增量更新流程

```
kb_rebuild.py --incremental
    ↓
detect_changes() (SHA256 比对)
    ↓
filter new/modified files
    ↓
for each file:
    update_single() (加锁 + 解析 + 原子写)
    ↓
remove deleted files from entries.json
    ↓
rebuild derivatives (if dirty)
```

## 性能考虑

### 时间复杂度

- `parse_entry`: O(1) - 单文件解析
- `update_single`: O(E) - E = entities 数量
- `query` (keyword): O(N) - N = entries 总数
- `query` (semantic): O(N) - 余弦相似度计算
- `lint`: O(N + R) - R = relationships 数量

### 空间复杂度

- entries.json: O(N × E) - N 个 entry，每个平均 E 个 entities
- entities-registry.json: O(E × F) - E 个实体，每个平均 F 个文件
- graph-data.json: O(N + E^2) - N 节点 + E^2 边（最坏情况）

### 优化策略

1. **SHA256 缓存**：避免重复解析未修改文件
2. **原子写**：减少锁持有时间
3. **自愈机制**：接受偶发性 dirty，避免复杂回滚
4. **查询限制**：只返回 top 10 结果

## 错误处理

### 非阻塞原则

索引失败不阻塞归档主流程：

```python
try:
    result = update_single(archive_file, archive_dir)
    if result.get("ok"):
        index_status = "indexed"
    else:
        index_status = "failed"
except Exception as e:
    index_status = f"error: {e[:100]}"

# 归档仍然成功
return {"ok": True, "archive_file": "...", "index_status": index_status}
```

### 重试机制

frontmatter 解析失败时，写入 cache.status=failed：

```python
cache[rel_path] = {
    "status": "failed",
    "error": str(e),
    "sha256": current_sha256,
    "last_attempt": datetime.now().isoformat(),
}
```

用户可手动补充 frontmatter 后重试：

```bash
python3 scripts/kb_rebuild.py --dir <archive_dir> --incremental
```

## 测试策略

### 单元测试

- `parse_frontmatter.py`: 7 种边界测试（缺字段/类型错/空 entities）
- `update_single.py`: 并发/原子写/dirty 标记测试
- `query_engine.py`: 三种模式正确性测试

### 集成测试

- 完整流程：3 个归档 → update_single → query → lint
- 迁移测试：加载 v0.3.1 entries.json → 验证兼容性

### 真实数据回归

- 在实际 archive_dir 上运行 `kb_rebuild --incremental`
- 验证 entries 数量 = 522
- 验证 5 个常见查询返回合理结果

## 扩展点

### 新增查询模式

在 `query_engine.py` 中添加新函数：

```python
def search_by_xyz(root: Path, query_str: str) -> List[dict]:
    """自定义查询逻辑"""
    pass
```

然后在 `query()` 中注册：

```python
if mode == "xyz":
    results = search_by_xyz(root, query_str)
```

### 新增派生索引

在 `update_single.py` 中添加新的派生文件生成：

```python
# 在原子写 entries.json 成功后
try:
    custom_data = derive_custom_data(entries)
    custom_path = workdir / "custom-data.json"
    if not save_json_atomic(custom_path, custom_data):
        mark_dirty(workdir)
except Exception:
    mark_dirty(workdir)
```

## 参考文档

- MERGE_PLAN_v2.md: 完整合并方案设计
- phase3-prompt-template.md: Phase 3 LLM prompt 模板
- kb-query-guide.md: 查询使用指南
- migration-from-kb-graph.md: 迁移指南
