## 审查结论

**总体评级**：CONDITIONAL_PASS
**置信度**：0.86
**审查对象**：A 类业务评审 — DESIGN-01.md 与 design/DESIGN.md 合并方案
**审查时间**：2026-06-23 07:56 CST
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 合理性 | 4 | 合并方向合理，可消除命名混淆并让设计档案前置；但必须区分“评审基线”和“后续变更记录”，否则会丢失一次性方案的冻结语义。 |
| B 类评审影响 | 3 | B 类仍可审 `design/DESIGN.md`，但评审对象应限定为 S3 baseline 版本/章节；需要补充评审口径，否则持续维护内容会让评审结论漂移。 |
| 执行影响 | 3 | S3-S8 反复修改会带来版本混乱风险；需要引入状态字段、变更日志、评审记录引用和冻结/解冻规则。 |
| 一致性 | 2 | 当前 SOP 仍多处硬编码 `DESIGN-01.md`/`DESIGN-01`，合并后若不同步改写会直接矛盾。 |
| 遗漏识别 | 3 | 方案未明确目录创建时机、必备章节模板、历史决策与当前设计的边界、评审结论如何绑定到具体版本。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 一致性 | SOP S3/S4/S8 | 合并方案与现有 SOP 硬编码引用冲突。S3 仍要求输出 `DESIGN-01.md`，B 类评审仍写 `DESIGN-01 完成后`，S4 仍要求“按 DESIGN-01 创建目录和文件”。如果只宣布合并但不改这些引用，执行者会继续生成旧文件或不知道该按哪个文件实现。 | `SKILL.md:93-102` 要求输出/评审 `DESIGN-01.md`；`SKILL.md:110` 要求按 DESIGN-01 创建目录和文件；`SKILL.md:248-260` 又要求 S8 更新 `DESIGN.md`。 | 全量替换 SOP 引用：S3 输出改为 `design/DESIGN.md`；B 类评审改为“审查 `design/DESIGN.md` 的 S3 baseline”；S4 改为“按已通过 B 类评审的 `design/DESIGN.md` baseline 创建目录和文件”；S8 改为“复核并补齐同一文件”。 |
| F002 | major | 版本/基线漂移 | 合并方案 S3-S8 | 合并后同一个文件既是 B 类评审对象，又是持续维护档案。如果 S4-S7 修改设计但评审结论仍指向旧内容，会出现“评审通过的不是当前文件”的漂移问题。 | 待评审方案说明 S3 创建、B 类评审、S4-S7 关键决策变更更新、S8 确保最新；现有 SOP B 关卡发生在 S3 后（`SKILL.md:281-282`），而 S8 档案要求持续维护（`SKILL.md:248-260`）。 | 在 `design/DESIGN.md` 增加头部元数据：`status: draft/baseline-approved/changed-after-review/archived`、`baseline_review: reviews/...`、`baseline_time`、`last_design_change`。S3 评审通过后标记 baseline；S4-S7 任何重大变更追加决策记录，并把状态改为 `changed-after-review`；重大变更触发局部 B 类复审或在 S7/D 类验收中显式复核。 |
| F003 | major | 评审口径 | B 类评审影响 | B 类原来审一次性方案文档，合并后审持续档案。若不限定评审范围，reviewer 可能把历史决策记录、S8 复盘内容也纳入 S3 方案可行性审查，造成标准混乱。 | 现有 B 类评审只在 `DESIGN-01 完成后` 触发（`SKILL.md:100-106`）；设计档案规范定义 `DESIGN.md` 包含产品目标、边界、核心流程、关键决策（`SKILL.md:256-260`），内容范围比原 S3 技术方案更宽。 | 将 B 类任务说明改成：“审查 `design/DESIGN.md` 中 S3 Baseline 章节：目标/边界/技术方案/数据流/接口规范/文件结构/UX 兜底/粒度判断/风险与验收；决策日志仅作为上下文，不作为完整性扣分项，除非与 baseline 矛盾。” |
| F004 | minor | 信息完整性 | 合并方案内容 | 合并不会天然导致信息丢失，但当前方案没有给出模板映射，容易遗漏 DESIGN-01 中“外部 API 官方文档唯一真相源”“文件结构（最小结构）”“粒度判断”等工程性内容。 | 原 S3b 明确列出 DESIGN-01 必含项：技术方案、数据流、接口规范、文件结构、用户体验、粒度判断、外部 API 官方文档（`SKILL.md:93-98`）；S8 DESIGN.md 描述较概括：产品目标、边界、核心流程、关键决策（`SKILL.md:258-260`）。 | 规定 `design/DESIGN.md` 必备章节至少包含：1. 产品目标；2. 非目标/边界；3. S3 Baseline 技术方案；4. 数据流；5. 接口/API 规范与官方来源；6. 文件结构；7. UX/错误兜底；8. 粒度决策；9. 风险与验收；10. Decision Log；11. Post-review Changes；12. S8 归档补充。 |
| F005 | minor | 流程清晰度 | 目录创建与归档 | 合并后 S3 就要创建 `design/` 目录，但现有设计档案规范仍像 S8 才建立档案集。若不说明 S3 创建目录，执行者可能在根目录创建 DESIGN.md 或等到 S8 再补。 | 待评审方案要求 S3 创建 `design/DESIGN.md`；现有 SOP 只在 S8 提到更新设计档案并列出 design/ 档案集（`SKILL.md:246-260`）。 | 在 S3b 增加：“先创建 `design/`，并初始化 `design/DESIGN.md`；`DISCUSSION-LOG.md`/`LEARNING-LOOP.md` 可在 S8 补齐或有讨论时提前创建。” |

---

**最重要的一条建议**

可以合并，但不要把“一个文件”误当成“一个版本”：必须在 `design/DESIGN.md` 内建立 S3 baseline + 后续变更日志 + 评审记录绑定机制，并同步清除 SOP 中所有 `DESIGN-01` 引用。

---

## 结论与建议

### 1. 是否合理

合并是合理的，建议采用。原因：

- 它解决了 `DESIGN-01.md` 与 `design/DESIGN.md` 命名相似、职责割裂的问题。
- 它让设计档案从 S3 开始存在，符合“设计史记”应贯穿项目生命周期的定位。
- DESIGN-01 的主要内容可以作为 `design/DESIGN.md` 的 “S3 Baseline” 章节保留，不必丢失。

但条件是：文件合并不等于语义合并。`DESIGN-01.md` 原本承担“评审前方案快照”的角色；`DESIGN.md` 承担“持续维护档案”的角色。合并后必须用章节和元数据保留这两个语义。

### 2. B 类评审如何调整

B 类评审仍应发生在 S3 后，但评审任务应绑定到 `design/DESIGN.md` 的 S3 baseline，而不是泛泛审整个持续档案。建议 SOP 明确：

```md
### B 类评审（强制）

`design/DESIGN.md` 的 S3 Baseline 完成后，spawn `factory-reviewer` 做 B 类方案评审。
评审范围：目标/边界/技术方案/数据流/接口规范/文件结构/UX 兜底/粒度判断/风险与验收。
Decision Log 仅作为上下文；若与 baseline 冲突，按一致性问题处理。
```

### 3. 如何防止版本混乱

建议在 `design/DESIGN.md` 顶部加入最小元数据：

```yaml
status: draft | baseline-approved | changed-after-review | archived
baseline_review: reviews/YYYY-MM-DD/xxx.md
baseline_time: YYYY-MM-DD HH:mm
last_design_change: YYYY-MM-DD HH:mm
```

并规定：

- S3 生成时为 `draft`。
- B 类 PASS/CONDITIONAL_PASS 修复后，改为 `baseline-approved` 并记录评审文件路径。
- S4-S7 如果发生关键设计变更，必须追加到 Decision Log / Post-review Changes，并把状态改为 `changed-after-review`。
- 影响目标、边界、接口、数据流、文件结构或安全模型的重大变更，触发 B 类局部复审；一般实现细节变更可留到 S7/D 类验收复核。
- S8 归档时改为 `archived`，补齐决策记录和迭代方向。

### 4. SOP 需要同步修改的关键点

至少改这些位置：

- `SKILL.md:93`：`输出 DESIGN-01.md` → `创建/更新 design/DESIGN.md`。
- `SKILL.md:102`：`DESIGN-01 完成后` → ``design/DESIGN.md` 的 S3 Baseline 完成后`。
- `SKILL.md:110`：`按 DESIGN-01 创建目录和文件` → `按已通过 B 类评审的 design/DESIGN.md baseline 创建目录和文件`。
- `SKILL.md:248-260`：S8 归档表述改为“复核并补齐 S3 已创建的设计档案”，避免暗示 DESIGN.md 到 S8 才出现。

### 5. 推荐落地模板

```md
# DESIGN

---
status: draft
baseline_review:
baseline_time:
last_design_change:
---

## 1. 产品目标
## 2. 非目标与边界
## 3. S3 Baseline 技术方案
### 3.1 数据流
### 3.2 接口/API 规范（含官方来源）
### 3.3 文件结构（最小结构）
### 3.4 用户体验与错误兜底
### 3.5 粒度判断
## 4. 风险、约束与验收标准
## 5. Decision Log
| 日期 | 阶段 | 决策 | 原因 | 影响 | 是否需复审 |
## 6. Post-review Changes
## 7. S8 归档补充与迭代方向
```

## 最终评级

**CONDITIONAL_PASS**：合并方向正确，建议执行；但通过条件是同步修改 SOP 引用、补充 `design/DESIGN.md` 模板、建立 baseline/变更/评审绑定机制。若不做这些配套，合并会从“减少重复”变成“评审对象漂移和执行引用混乱”。
