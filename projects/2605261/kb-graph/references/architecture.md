# KB Graph 五层架构

详见设计文档：K-260526-087 企业知识库图谱方案 v2.0
路径：/Users/evan/.openclaw/gateways/life/state/workspace-life/memory/archived/2026/05/K-260526-087-企业知识库图谱方案-全自动AI驱动.md

## 五层说明

| 层次 | 职责 |
|------|------|
| 采集层（Ingestion） | 文件监听、变更检测（SHA256 缓存）、增量更新 |
| 编译层（Compilation） | Markdown 解析、LLM 语义编译（摘要/实体/标签/关系） |
| 图谱层（Graph） | 节点/边构建、Leiden 社区发现、SQLite 持久化 |
| 查询层（Query） | 图谱引擎 + Wiki 引擎双引擎查询 |
| 维护层（Maintenance） | Lint 巡检、矛盾检测、自动修复 |