# OKF Alignment

Link Archivist 的知识管理设计参考 [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) 和 [Karpathy LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。

## 定位

Link Archivist 是**归档生命周期 Skill**（抓取→调研→归档→索引→查询），不是 OKF 实现。

OKF 是**知识资产格式**（Markdown + YAML frontmatter + Git-friendly），是 Link Archivist 可以对齐和导出的格式层。

两者方向一致但层级不同。

## 当前对齐状态（v2.0.1）

Link Archivist v2.0.x 的 frontmatter 已与 OKF v0.1 高度兼容：

| OKF 字段 | Link Archivist 字段 | 对齐方式 |
|----------|-------------------|---------|
| `title` | 报告正文第一个 `#` 标题 | 自动提取 |
| `description` | `summary` | 语义等价 |
| `resource` | `source` | 语义等价 |
| `tags` | `tags` | 直接映射 |
| `timestamp` | `created_at` | 语义等价 |
| `type` | `source_type`（近似） | v2.1 可选扩展 |

Link Archivist 独有字段（OKF 未定义）：

- `archive`：稳定归档编号（如 `K-260619-054`）
- `entities`：关键实体列表
- `relationships`：结构化文档关系
- `confidence`：LLM 抽取质量

这些字段不冲突，作为 OKF 的扩展保留。

## 设计原则

1. **保守对齐**：只称 OKF-style / OKF-aligned，不承诺 full compliance
2. **归档不可变**：frontmatter 由 Phase 3 LLM 生成，不因 OKF 对齐而重写历史归档
3. **输入宽容，事实源严格**：frontmatter 可以缺字段，但 entries.json 不能写坏结构
4. **不造轮子**：v3 living wiki 立项前必须先核查 OpenClaw 平台是否已具备 synthesis/wiki 能力

## 字段写入策略

- v2.0.x：不改变归档 frontmatter，只写文档说明
- v2.1.x：新增 OKF-style 可选字段（`type` / `title` / `description` / `resource` / `timestamp`），**opt-in 默认关闭**
- 历史归档不主动重写；导出时做映射

## 导出能力（v2.1 规划）

未来 `scripts/kb_export_okf.py` 将支持：

```bash
python3 scripts/kb_export_okf.py --dir <archive_dir>
```

输出到 `.kb-workdir/okf-export/`（不是知识库根目录，避免被 ingest 重复索引）：

```text
.kb-workdir/okf-export/
├── index.md          # 知识库导航
├── log.md            # 变更日志
└── archive/          # OKF-style concept documents
```

## 后续路线

- **v2.0.1**（本版）：文档对齐
- **v2.1.0**：只读 OKF-style 导出 + opt-in 字段
- **v2.2.0**：根目录 `index.md` / `log.md`（需 ingest 跳过 system docs）
- **v3.0**：Living wiki synthesis layer（立项前核查 OpenClaw 平台能力）

详见 `docs/OKF_ALIGNMENT_ROADMAP_v1.md`。
