## 评审结论

**总体评级**：FAIL

**评审对象**：D 类上线前最终验收 — bd-eval-cms v0.9.3 / HEAD 2aebfee（基准 b1e2ff1）
**评审时间**：2026-06-14

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 产出物存在性校验 | 2 | 四个补提交关键文件已入 git，但仍有被 SKILL.md / EXECUTION.md / version.json / smoke README 引用的 design 文档未提交。 |
| 版本号一致性 | 5 | projects/2605281/VERSION、bd-eval-cms/VERSION、version.json、SKILL.md frontmatter、projects/2605281/METADATA.json 均为 0.9.3。 |
| 代码完整性 | 5 | render.py 可正常 import；schema.json / registry.json 可读且已跟踪；test_render、preflight、run-opportunity、smoke 四套检查均通过。 |
| 治理升级完整性 | 3 | _runtime/experience/RULES.md、_runtime/state/factory.json、_runtime/state/projects/2605281.json 已入 git；但任务要求的 projects/2605281.json 不存在，且 AGENTS.md / SOUL.md 有少量引用路径不可访问。 |
| doc-viewer 删除安全性 | 4 | METADATA.json / README.md 不再引用 doc-viewer，bd-eval-cms 运行路径无 dependencies/doc-viewer 依赖；仅历史设计草案和 changelog 保留删除背景描述。 |
| 遗留风险 / untracked | 2 | 排除 .refactor-backup / .serena / 2606* / Epioxa / JMKX003948 后，仍有 8 个 bd-eval-cms 文档未跟踪，其中至少 4 个被当前文档直接引用，应提交。 |

---

**关键核验结果**

1. **已确认补提交成功的关键文件（均 TRACKED）**
   - `projects/2605281/bd-eval-cms/templates/style-a1/profiles/schema.json`
   - `projects/2605281/bd-eval-cms/scripts/run-opportunity.sh`
   - `projects/2605281/bd-eval-cms/scripts/test-run-opportunity.sh`
   - `projects/2605281/bd-eval-cms/scripts/preflight-phase.sh`
   - 同时确认 `scripts/test-preflight-phase.sh`、`references/opportunity.example.json`、`templates/style-a1/profiles/registry.json`、`templates/style-a1/smoke/run_smoke_test.sh` 也已入 git。

2. **回归检查结果**
   - `python3 templates/style-a1/test_render.py`：PASS
   - `bash scripts/test-preflight-phase.sh`：PASS（8/8）
   - `bash scripts/test-run-opportunity.sh`：PASS（17/17）
   - `bash templates/style-a1/smoke/run_smoke_test.sh`：PASS

3. **仍遗漏 / 未提交文件完整清单（排除指定目录后）**

   应提交但遗漏：
   - `projects/2605281/bd-eval-cms/design/REQ-v0.9.1.md`
   - `projects/2605281/bd-eval-cms/design/DESIGN-v0.9.1.md`
   - `projects/2605281/bd-eval-cms/design/REVIEW-DESIGN-v0.9.1.md`
   - `projects/2605281/bd-eval-cms/design/v0.9-retrospective.md`
   - `projects/2605281/bd-eval-cms/design/REQ-v0.9.2.md`
   - `projects/2605281/bd-eval-cms/design/DESIGN-v0.9.2.md`
   - `projects/2605281/bd-eval-cms/design/REVIEW-DESIGN-v0.9.2.md`

   可选归档 / 需决策是否提交：
   - `projects/2605281/bd-eval-cms/docs/MIGRATION-V0.5.0-PLAN.md`

4. **遗漏文件的引用证据**
   - `SKILL.md:103` 引用 `design/REQ-v0.9.2.md` + `design/DESIGN-v0.9.2.md`
   - `EXECUTION.md:115` 引用 `design/DESIGN-v0.9.2.md`
   - `version.json` 的 `0.9.1->0.9.2` changelog 明确称新增 `design/REQ-v0.9.2.md` + `design/DESIGN-v0.9.2.md`
   - `templates/style-a1/smoke/README.md:211` 引用 `design/DESIGN-v0.9.1.md`
   - `design/DISCUSSION-LOG.md` 多处记录 v0.9.1/v0.9.2 设计与评审文档已产出，但这些文档未入 git。

5. **治理路径问题**
   - 实际已跟踪的是 `_runtime/state/projects/2605281.json`，不是任务清单写的 `projects/2605281.json`。
   - `.gitignore` 例外规则覆盖 `_runtime/experience/RULES.md`、`_runtime/state/README.md`、`_runtime/state/factory.json`、`_runtime/state/projects/*.json`，这一点是正确的。
   - `AGENTS.md` / `SOUL.md` 引用但当前不可访问：`specs/agents/link-archivist-orchestrator.md`、`specs/agents/link-archivist-worker.md`、`config/factory.yaml`。

---

**关键问题**（最多 5 个）

1. [严重度：高] v0.9.1 / v0.9.2 的设计与评审文档仍是 untracked，且被当前 SKILL.md、EXECUTION.md、version.json、smoke README 直接引用 → 修复建议：将上述 7 个 `design/*.md` 文件纳入 git；若不想发布评审草案，则同步删除/改写所有引用与 changelog 表述。
2. [严重度：中] `docs/MIGRATION-V0.5.0-PLAN.md` 处于 untracked，当前未发现主路径强引用，但会造成工作区长期脏状态 → 修复建议：明确它是发布资料还是本地草稿；发布则提交，不发布则加入 `.gitignore` 或移至归档目录。
3. [严重度：中] 治理任务要求的 `projects/2605281.json` 不存在，实际文件在 `_runtime/state/projects/2605281.json` → 修复建议：统一任务清单/文档中的治理状态路径，避免 reviewer 与实现口径不一致。
4. [严重度：低] AGENTS.md / SOUL.md 存在少量不可访问引用路径 → 修复建议：补齐 `specs/agents/link-archivist-*.md` 与 `config/factory.yaml`，或从文档中移除/更新这些路径。
5. [严重度：低] 测试 case / 运行产物目录（如 `2606*`、Epioxa、JMKX003948）目前依赖人工排除 → 修复建议：若这些均为本地运行产物，应在 `.gitignore` 增加明确规则，防止后续 `git add` 再次误选或漏选。

---

**最重要的一条建议**

先把 v0.9.1 / v0.9.2 相关 `design/*.md` 引用文件全部提交；当前核心脚本已可跑，但发布包仍不是“文档引用闭环”的完整包。