## 评审结论

**总体评级**：CONDITIONAL_PASS

**评审对象**：A/B/C/D — AODW 0.6 Skill 编排升级方案 + `~/.openclaw/skills/aodw-next/manifest.yaml` v0.5.1
**评审时间**：2026-06-17

---

## A 类：需求方案 / 业务设计评审

**总体评级**：CONDITIONAL_PASS

**评审对象**：A 类 — AODW 0.6 Skill 编排方案
**评审时间**：2026-06-17

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 需求完整性 | 4 | 准确抓住“skill 装了但不会主动用”的痛点，但缺少误触发、冲突、降级、撤销机制。 |
| 可行性 | 3 | 文档层面可做，自动 Hook 调度层面证据不足，不能按“改 manifest 就实现自动编排”理解。 |
| 价值合理性 | 4 | 值得做，但必须从“强制调用矩阵”改成“路由建议 + 最小必要调用 + 可跳过理由”。 |
| 风险识别 | 3 | 识别了核心 skill，但未充分评估流程僵化、token 成本、外部 skill 质量不均和 AODW 既有规则重叠。 |
| 边界明确性 | 2 | 没写清“不装哪些 skill、不自动调用哪些重型 skill、什么时候跳过、失败后怎么退回 AODW 原生流程”。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] 方案把“AI 想不起来用”直接改成“阶段强制用”，有从遗忘问题变成僵化问题的风险 → 修复建议：把矩阵改成三级策略：`must`（极少数硬门控）、`should`（默认建议，可记录跳过原因）、`may`（按需工具箱）。
2. [严重度：高] 统一入口 Hook 的实现路径没有被事实证明，AODW manifest 当前只是规则索引，不是可执行 hook 注册表 → 修复建议：0.6 先在 `SKILL.md`/constitution/profile 中做“入口路由协议”，不要承诺 OpenClaw hook 自动调度；若要 Hook，另立插件级实现 Spike。
3. [严重度：中] 4 个核心 skill 质量差异明显，不能无差别纳入核心链路 → 修复建议：只把 `superpowers-systematic-debugging` 和 `code-review` 作为首批高价值补充；`spec-workflow-guide` 与 AODW Spec-Full 高重叠，`git-workflow` 弱于 AODW git-discipline，不宜强制。
4. [严重度：中] multi-model-consensus 与 multi-model-orchestrator 都是重型编排，会与 AODW 自身多 Agent / Ralph Loop 重叠 → 修复建议：consensus 只用于高代价架构/产品决策；orchestrator 只用于任务拆分后存在独立并行子任务的实现阶段。
5. [严重度：中] Spec-Autonomous Phase 0.5 合理但不应成为新人工 Gate，也不能破坏“启动一次确认后自主执行”的定位 → 修复建议：作为 AI 内部“Skill Routing Snapshot”写入 `rt-lite.md`，允许执行中追加/放弃 skill 并记录原因。

---

**最重要的一条建议**

不要做“强制编排矩阵”，要做“轻量 Skill Router：默认建议、可跳过、可追踪、失败可退回 AODW 原生流程”。

---

## B 类：事实核查

**总体评级**：CONDITIONAL_PASS

**评审对象**：B 类 — AODW v0.5.1 状态与 ClawHub 推荐 skill 质量核查
**评审时间**：2026-06-17

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 设计与需求的一致性 | 3 | 外部 skill 编排方向回应了需求，但部分 skill 与 AODW 已有能力重复。 |
| 唯一真相源 | 3 | 已读取本地 AODW 与 ClawHub 安装 skill；但 Hook 能力未在 AODW skill 层发现可执行依据。 |
| 三层披露合理性 | 2 | 现有 AODW 已有 summary/full 结构；再塞大矩阵和外部 skill 容易增加 token 与认知负担。 |
| 触发词设计 | 3 | 触发条件方向合理，但“任何 PR / merge 前”“commit / push / merge 前”过宽，会造成重复门控。 |
| 失败兜底与错误处理 | 2 | 缺少 skill 不存在、版本不兼容、误分类、外部 skill 自身规则冲突时的兜底。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] AODW v0.5.1 的 manifest 实际只有 21 条 rule，不是题述“22 条 rule” → 修复建议：升级文档先校正事实，避免基于错误计数做迁移。
2. [严重度：高] `aodw-constitution.md` 正文疑似损坏/占位，仅包含 `$(cat /tmp/constitution_main.md)`，真正可读的是 `01-core/aodw-constitution-summary.md` → 修复建议：0.6 前先修复 constitution 完整正文，否则“写入 aodw-constitution.md”的落地点不可靠。
3. [严重度：中] “AODW 没有集成外部 skill”基本准确：manifest 与本地 AODW 文档未发现 `multi-model-*` 或 external skill references；但 AODW 已内建 Claude Code 审查、Ralph Loop、多 Agent 协同，不是没有编排能力。 |
4. [严重度：中] `spec-workflow-guide` 与 AODW Spec-Full 高重叠：都要求 requirements/design/tasks、阶段确认、验收标准；作为外部强制 skill 会重复造文档 → 修复建议：只借鉴 EARS acceptance criteria，不作为 AODW 核心必调。
5. [严重度：中] `git-workflow` 质量弱于 AODW `git-discipline`：它建议 `git add .`、commit/push 自动化，而 AODW 已有 RT 引用、worktree、confirm-gated execution、pre-merge checklist → 修复建议：不要安装为核心，最多作为非 AODW 项目的通用参考。

---

**事实核查摘要**

- AODW v0.5.1 真实边界：`SKILL.md` 声明 RT 生命周期、Spec-Full / Spec-Lite、确认门控、git/worktree、审计；`spec-autonomous-profile.md` 声明启动一次确认、Ralph Loop、Claude Code 审查、测试失败 3 轮修复、交付通知；`manifest.yaml` 是 21 条规则索引。
- 外部 skill 集成：未在 `manifest.yaml`、yaml 配置、AODW markdown 中查到外部 skill references。
- 4 个 ClawHub skill 质量：
  - `spec-workflow-guide` v2.21.1：质量中上，但与 Spec-Full 重叠严重，适合吸收 EARS 与“是否需要 full spec”的判断规则。
  - `code-review` v1.0：质量较好，结构化覆盖 security/performance/correctness/testing；可作为 AODW Gate 4 审查维度补强。
  - `superpowers-systematic-debugging`：质量高，流程清晰，正好补 AODW “测试失败/bug 修复”阶段的调试纪律。
  - `git-workflow` v1.0.0：过于通用，且部分建议与 AODW confirm-gated、RT 引用、worktree 隔离不一致；不应进入核心。
- multi-model-consensus vs multi-model-orchestrator：两者定位不同但重叠在“多模型参与决策/协作”。在 AODW 同时装可行，但必须限制触发：consensus=重大决策评审，orchestrator=并行实现/调试/前端等工作流，不得在同一普通 RT 同时默认触发。

---

**最重要的一条建议**

先修 AODW 自身 constitution 正文和 manifest 事实，再谈 0.6 外部编排；不要把质量参差的 ClawHub skill 直接全部升为核心依赖。

---

## C 类：风险评估

**总体评级**：CONDITIONAL_PASS

**评审对象**：C 类 — Phase 0.5 / Hook / 落地计划风险
**评审时间**：2026-06-17

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 需求完整性 | 3 | 有三步落地，但没有 Spike、验收指标、失败降级和版本兼容策略。 |
| 可行性 | 3 | 文档路由 1-2 天可行；真正 Hook 自动分类与调度不应按 1-2 天估。 |
| 价值合理性 | 4 | 若控制范围，收益明显；若做成强制大一统编排，收益会被流程成本吞掉。 |
| 风险识别 | 2 | 未充分识别 OpenClaw skill 加载机制和外部 skill 版本漂移风险。 |
| 边界明确性 | 2 | 未定义“判断错了怎么办”“skill 缺失怎么办”“用户不想用怎么办”。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] Phase 0.5 的“任务特征判断”必须由 AI 在 AODW 入口协议中执行，不能假设 Hook 自动完成 → 修复建议：在 RT 创建后输出 `Skill Routing Snapshot`：任务类型、候选 skill、调用级别、跳过理由、缺失处理。
2. [严重度：高] OpenClaw Hook（如 beforePromptBuild / beforeToolCall）属于平台/插件层能力，不是当前 AODW manifest 已能声明的能力 → 修复建议：0.6 Step 1 只改 AODW 文档；若要 Hook，新增 Step 0：验证 hook API、最小插件原型、回归测试。
3. [严重度：中] 三步估时偏乐观：文档升级 0.5-1 天；安装/筛选 skill 0.5 天；真实 RT 验证至少 1-2 天；Hook 自动化另加 2-5 天 Spike → 修复建议：把“1-2 天完成升级”限定为文档版 0.6，不含 Hook 自动化。
4. [严重度：中] 真实 RT 验证失败没有 Plan B → 修复建议：Plan B 应为回退到 v0.5.1 原生流程，只保留 `superpowers-systematic-debugging` 的 bug 阶段建议与 `code-review` 的审查 checklist。
5. [严重度：中] 外部 skill 触发词与 AODW 触发词可能抢占上下文，导致重复加载或流程跳转 → 修复建议：AODW 作为上层 router，不让外部 skill 接管 RT 生命周期；外部 skill 只能提供局部 checklist / procedure。

---

**最重要的一条建议**

把 0.6 拆成“文档路由版”和“平台 Hook 版”两个里程碑；当前只建议 Go 文档路由版，不建议承诺 Hook 自动调度。

---

## D 类：代码/配置评审（manifest.yaml）

**总体评级**：CONDITIONAL_PASS

**评审对象**：D 类 — `~/.openclaw/skills/aodw-next/manifest.yaml` v0.5.1
**评审时间**：2026-06-17

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 正确性 | 4 | manifest 作为规则索引基本清晰，但题述 22 条与实际 21 条不符。 |
| 安全性 | 4 | 当前只是路径索引，无凭证/注入风险；若加入自动安装/调用字段则风险上升。 |
| 健壮性 | 3 | 缺少外部 skill 缺失、版本、可选依赖、冲突策略字段。 |
| 可维护性 | 3 | rule 列表偏平铺，summary/full、core/profile/auditor/tooling 混在一起；可读但扩展 skill 编排会变乱。 |
| 测试覆盖 | 2 | 未见 manifest schema 校验或加载测试；0.6 改动前应加人工/脚本校验。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] 不建议把 Skill 编排矩阵直接塞进现有 `rules` 列表，否则会把“规则文档索引”和“外部能力路由”混为一谈 → 修复建议：新增顶层 `skill_routing` 或 `orchestration` 区块，保留 `rules` 只索引 AODW 内部规则。
2. [严重度：中] 现有 `rules` 中 `project-ai-overview`、`project-modules-index` 指向 templates，却描述为 current project/project-specific，语义上容易混淆 → 修复建议：移动到 `templates` 区块，或明确 `kind: template`。
3. [严重度：中] `ai-coding-rules` 与 `ai-coding-rules-common` 命名边界不清，后续再加外部 `code-review` 会加剧重复 → 修复建议：增加 `kind/category` 字段，区分 `standard/common/stack-specific/review-checklist`。
4. [严重度：中] auditor 三件套（requirement/development/full）与 proposed `code-review` 容易重叠 → 修复建议：manifest 中明确 `code-review` 是 Gate 4 checklist supplement，不替代 `aodw-development-auditor`。
5. [严重度：低] `last_updated_at` 与 version 同步需要在 0.6 一起更新，并同步 `SKILL.md` frontmatter 与 `version.json` → 修复建议：升级清单必须包含三处版本同步。

---

**manifest 最干净改法建议**

不要改现有 21 条 `rules` 的含义；新增独立块，例如：

```yaml
version: 0.6.0
last_updated_at: 2026-06-17T00:00:00+08:00

skill_routing:
  schema_version: 1
  policy: "advisory-by-default"
  levels:
    must: "必须调用；若缺失则阻断或回退到 AODW 内置等价流程"
    should: "默认调用；可跳过但必须记录理由"
    may: "按需调用；不记录也不阻断"
  routes:
    - id: debugging-discipline
      stage: implementation_or_verification
      skill: superpowers-systematic-debugging
      level: should
      trigger: "测试失败、构建失败、异常、bug 复现失败"
      fallback: "使用 AODW 原生 3 轮调查/修复流程，并记录根因假设"
    - id: code-review-checklist
      stage: pre_commit_or_pre_merge
      skill: code-review
      level: should
      trigger: "Gate 4、PR、merge 前"
      fallback: "使用 aodw-development-auditor-rules.md"
    - id: spec-workflow-reference
      stage: planning
      skill: spec-workflow-guide
      level: may
      trigger: "验收标准不清或需要 EARS 写法"
      fallback: "使用 AODW Spec-Full/Profile 原生模板"
    - id: git-workflow-reference
      stage: git
      skill: git-workflow
      level: may
      trigger: "非 AODW 项目的一般 git 提交"
      fallback: "始终优先使用 git-discipline.md"
```

**现有 21 条 rule 合理性结论**：总体合理，但不是都应保留在同一平面。真正核心规则是 constitution / interaction / knowledge / git-discipline / rt-manager / 三个 profile / auditors / coding rules；project templates 和 tooling 可以分组。没有发现需要直接删除的 rule，但建议重构分组与 `kind` 字段，避免 0.6 加外部路由后变成不可维护清单。

---

**最重要的一条建议**

manifest 只新增“路由元数据”，不要让 manifest 承担实际 Hook 执行；实际执行规则写在 AODW `SKILL.md` 和各 profile 中。

---

## 总体 Go / No-Go 结论

**建议：有条件 Go。**

可 Go 的范围：
1. AODW 0.6 文档层升级：增加 Skill Router / Phase 0.5 Routing Snapshot。
2. 首批只纳入 `superpowers-systematic-debugging` 与 `code-review` 为 `should` 级补强。
3. `spec-workflow-guide` 只作为 EARS / 需求澄清参考，不强制进入 Spec-Full。
4. `git-workflow` 不进入 AODW 核心；AODW Git 继续以 `git-discipline.md` 为唯一真相源。
5. multi-model-consensus 与 multi-model-orchestrator 都不作为默认安装项，只作为高复杂任务可选增强。

暂不 Go 的范围：
1. 不建议直接做“所有入口统一 Hook 自动调度”。
2. 不建议把 9 个 skill 全部写成阶段必调。
3. 不建议把外部 skill 变成 AODW 生命周期的上层控制者。

---

## 单独列出的遗漏风险与更优方案

### 遗漏风险

1. constitution 正文异常：`aodw-constitution.md` 不是可用正文，这会阻断“写入 constitution”的方案。
2. 外部 skill 版本漂移：ClawHub skill 更新后行为可能改变，需 pin version 或记录 tested version。
3. Token 膨胀：AODW 已有 summary/full 渐进披露，引入外部 SKILL.md 会增加上下文负担。
4. 权限和工具边界：部分外部 skill 建议 spawn/write/git 操作，必须受 AODW confirm-gated 和 worktree 约束覆盖。
5. 误分类成本：一旦任务被错误路由到重型 consensus/orchestrator，会显著拖慢普通 RT。

### 更优方案

采用 **Skill Router + Capability Adapter**，而不是 Skill Federation 或能力内化：

- Router：AODW 入口只判断任务特征，生成 Routing Snapshot。
- Adapter：每个外部 skill 只暴露“在 AODW 中怎么用”的最小适配说明。
- Policy：默认 `should/may`，少用 `must`。
- Trace：每次调用或跳过都写入 RT 文档，方便复盘。
- Fallback：外部 skill 缺失时回退到 AODW 原生 profile/auditor/git-discipline。

这比“AI 完全自主判断”更可追踪，比“Skill Federation”更现实，比“能力全部内化”更省维护成本。
