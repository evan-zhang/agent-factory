# bp-reporting-templates Discussion Log

## 2026-04-01 — 质检驱动修复

**问题**：xgjk-skill-auditor 审计发现 D2 无中文触发词、D4 缺 setup.md（External Endpoints 未声明）、D5 design/ 缺失、根目录有 4 个 output-* 测试目录（D1 卫生问题）、ClawHub 版本停在 v0.4.3 未同步 v0.5.0 改动。

**操作**：
- output-* 目录移入 tests/output-archives/
- 新建 setup.md（env 声明 + External Endpoints）
- description 补中文触发词 + metadata.requires.env
- 补 design/ 档案
- 发布 v0.5.1
