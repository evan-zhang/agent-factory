## 评审结论

**总体评级**：CONDITIONAL_PASS

**评审对象**：D 类（上线前最终验收）+ C 类（代码改动）— bd-eval-cms v0.9.1+v0.9.2+v0.9.3 合并发布（5 个 commit，基准 b1e2ff1）
**评审时间**：2026-06-14

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---|---|
| 1. Commit 结构与 Git 历史 | 3 | 5 个 commit 拆分粒度合理，但 acf4cf3 合并发布导致 v0.9.1/v0.9.2/v0.9.3 代码混包，不可回滚；版本号管理发现漏洞（SKILL.md frontmatter 停在 0.9.2） |
| 2. 代码质量（render.py / test_render.py / smoke） | 4 | 测试套件 4/4 全过，向后兼容设计到位（省略 profile 自动检测）；仅残留 render.py 第 751 行一处 "A-5" 用法示例注释，属无害文档残留 |
| 3. Profile 收敛完整性（v0.9.3 核心） | 3 | profiles/A-5.json + A-7.json 已删，registry.json 单一 A-1 active 正确；但 `templates/style-a1/contracts/markdown-contract.md`（未提交 untracked）仍含 A-5/A-7 章节，形成文档层面残留；SKILL.md 路由表/技能组合表中 A-5/A-7 引用属于业务路由逻辑（技能本身未删除），不视为错误 |
| 4. 治理升级完整性 | 4 | Rule-W26-01/W26-02 正本入 git，SOUL.md 红线与 CLAUDE-CODE-USAGE-GUIDE v5.0 一致；但 `_runtime/state/projects/` 未创建任何实体文件，Rule-W26-01 强制读取的 state.json 实际不存在，规则可能在重启时 fail-fast |
| 5. doc-viewer 删除安全性 | 3 | bd-eval-cms 自 v0.7.0 已自包含（hardiso 已实施）；但 `projects/2605281/METADATA.json` 和 `README.md` 中 doc-viewer 仍被列为 `required: true` 的依赖，与已删除的物理路径不一致，会导致安装者困惑 |
| 6. SKILL.md 规范符合度 | 2 | frontmatter `version: 0.9.2` 未随 1f02489 版本号同步 commit 更新，与 VERSION 文件 / version.json 均为 0.9.3 不一致；UPGRADE-LOG.md 仅记录到 v0.5.0，v0.5→v0.9.3 共 6 个版本变更无台账 |
| 7. 遗留风险 | 3 | contracts/ 目录（设计层关键文档，含 A-5/A-7 旧契约）、smoke/README.md、profiles/schema.json 均为 untracked；260612-TEST / 260613-SMQT 测试目录未 gitignore；.refactor-backup/.serena 等噪音目录无明确处置策略 |

---

**关键问题**（最多 5 个）

1. **[严重度：高] SKILL.md frontmatter `version: 0.9.2` 未更新**
   → 修复建议：在 SKILL.md 第 24 行将 `version: 0.9.2` 改为 `version: 0.9.3`，追加 commit 或 amend 1f02489。此为唯一明确的版本号不同步漏洞。

2. **[严重度：中] contracts/markdown-contract.md 是 untracked 文件，且内容含 A-5/A-7 章节（与 v0.9.3 收敛方向矛盾）**
   → 修复建议：若 contracts/ 是生产依赖（smoke/README.md 明确引用），必须 `git add` 提交；同时将 markdown-contract.md 中 §4 A-5 特定要求、§5 A-7 特定要求 修改为历史兼容说明（"已收敛为 A-1，以下为历史参考"），或整体删除 A-5/A-7 专用节。

3. **[严重度：中] `_runtime/state/projects/` 空目录未创建 factory.json，Rule-W26-01 强制读取动作将因文件不存在而降级为无效**
   → 修复建议：创建 `_runtime/state/factory.json`（哪怕只是 `{"status": "running"}`）并 git add，确保重启校验路径真实可用；或在 AGENTS.md 中补充"文件不存在时 graceful fallback"的说明。

4. **[严重度：中] METADATA.json / README.md 仍将 doc-viewer 标记为 `required: true`，而对应物理目录已被 a7d1297 删除**
   → 修复建议：更新 `projects/2605281/METADATA.json` 的 `skills.doc-viewer` 条目（移除或改为 `required: false` 并注明已内联），同步更新 `projects/2605281/README.md` 中的 skill 组成表。

5. **[严重度：低] UPGRADE-LOG.md 仅记录到 v0.5.0，v0.5→v0.9.3 跨 6 个版本的变更台账缺失**
   → 修复建议：补填 0.5.0→0.9.3 的台账条目（可从 version.json changelog 提取摘要），确保升级记录与版本历史一致。

---

**最重要的一条建议**

**立即修复 SKILL.md frontmatter 版本号**（第 24 行 `version: 0.9.2` → `0.9.3`）：这是发布后对外暴露的元数据，任何工具读取此字段都会得到错误的版本信息，其他问题可以分批跟进。

---

*存档路径：projects/2606131/_review/2026-06-14-D-bd-eval-cms-v0.9.3-CONDITIONAL_PASS.md*
