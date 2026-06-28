# v3.0 Living Wiki 评估结论

**评估日期**：2026-06-19
**评估人**：Factory Orchestrator
**基线**：Link Archivist v2.2.0 / OKF_ALIGNMENT_ROADMAP_v1.md §7.4

---

## 结论：v3.0 不做独立 living wiki

### 原因

OpenClaw 已内置 `memory-wiki` 插件（`docs/plugins/memory-wiki.md`），提供了路线图 v3.0 设想的全部能力：

| v3.0 设想 | OpenClaw memory-wiki 已有 |
|---|---|
| 实体页 | `entities/` 目录，确定性页面布局 |
| 主题页 | `concepts/` 目录 |
| 综合页 | `syntheses/` 目录 |
| provenance | 页面级溯源、confidence、contradictions |
| 变更追踪 | `index.md` / `AGENTS.md` / `WIKI.md` |
| 搜索 | `wiki_search` / `wiki_get` |
| 与 memory 集成 | bridge 模式，从 memory-core 导入 artifacts |
| Obsidian 兼容 | 可选 Obsidian-friendly render mode |

按工厂红线"不造 OpenClaw 将来一定会做的事"，v3.0 不应另建独立 living wiki。

### 正确定位

Link Archivist 的 archive 层（归档报告 + KB 索引）是 **source of truth for raw knowledge**。

OpenClaw memory-wiki 是 **synthesis layer**。

两者关系：

```
Link Archivist archive → (raw knowledge source)
        ↓ bridge mode or export
OpenClaw memory-wiki → (compiled synthesis layer)
```

未来如果需要 living wiki，正确做法是：
1. 让 memory-wiki bridge 模式消费 Link Archivist 的归档作为 input artifacts
2. 或者用 `kb_export_okf.py` 导出的 OKF bundle 作为 memory-wiki 的导入源

而不是在 Link Archivist 内部重建一套 wiki 系统。

---

## 修订后的路线图

| 版本 | 状态 | 内容 |
|---|---|---|
| v2.0.0 | ✅ 已发布 | KB Graph 合并 |
| v2.0.1 | ✅ 已发布 | OKF 文档对齐 |
| v2.1.0 | ✅ 已发布 | OKF-style 只读导出 |
| v2.2.0 | ✅ 已发布 | 根目录 index/log + ingest 跳过 |
| v3.0 | ❌ 不做 | 原因：OpenClaw memory-wiki 已覆盖此能力 |

**后续方向**（不等同于 v3.0）：

如果未来 Evan 希望让 Link Archivist 归档接入 memory-wiki：
1. 调研 memory-wiki bridge 模式的 artifact 格式要求
2. 写一个 `scripts/kb_export_wiki_bridge.py`，把归档导出为 memory-wiki 可消费的格式
3. 在 memory-wiki 侧配置 bridge 模式消费 Link Archivist 目录

但这属于跨 Skill 集成，不是 Link Archivist 自身的功能扩展，需另立项目评估。

---

## Factory Review 红线自检

✅ **不造轮子**：v3.0 living wiki 已确认 OpenClaw memory-wiki 覆盖，不做重复实现。
✅ **保守对齐**：OKF alignment 保持 OKF-style，不承诺 full compliance。
✅ **归档不可变**：v2.x 全程未改变归档报告的不可变性。
✅ **输入宽容，事实源严格**：parse 阶段做类型清洗，entries.json 不写坏结构。
