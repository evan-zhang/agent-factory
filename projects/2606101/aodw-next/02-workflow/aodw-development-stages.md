# AODW 开发阶段分析

## 阶段总览

AODW 将开发过程分为 7 个主要阶段，对应 RT 状态机：created → intaking → decided → in-progress → reviewing → done

---

## 阶段 1: Intake（立项）

**状态转换**: created → intaking → decided

**主要任务**:
- 生成 RT-ID（RT-{seq}）
- 创建 RT 目录结构（RT/RT-XXX/）
- 通过交互式提问收集需求信息
- 记录原始描述、问题与答案
- 初步判断需求类型（Feature/Bug/Enhancement/Refactor/Research）

**阶段目标**: 明确需求范围、风险等级、影响模块估计，为 Profile 决策做准备

**输出物**:
- `RT/RT-XXX/meta.yaml`（RT 元数据）
- `RT/RT-XXX/intake.md`（立项记录）
- `RT/index.yaml`（全局索引更新）

**协作方式**:
- AI: 主动提出澄清问题，每个问题提供 2-5 个选项，给出推荐选项和理由
- 用户: 选择推荐项或提供简短自定义答案（≤5 词），回答业务相关问题

---

## 阶段 2: Decision（决策）

**状态转换**: intaking → decided

**主要任务**:
- 根据 Intake 信息判断复杂度
- 选择 Spec-Full 或 Spec-Lite profile
- 创建 feature 分支（feature/RT-XXX-{short-name}）
- 切换到 feature 分支并验证

**阶段目标**: 确定开发模式，创建并切换到正确的 feature 分支

**输出物**:
- `RT/RT-XXX/decision.md`（决策记录，包含选择理由）
- feature 分支（已创建并切换）

**协作方式**:
- AI: 分析复杂度，推荐 Profile（Full/Lite），解释推荐理由，创建分支
- 用户: 确认推荐方案或显式切换 Profile，确认分支名

**关键检查点**: 必须验证当前在 feature 分支上，严禁在 main/master 分支修改代码

**CSF 审查（推荐）**: Decision 阶段完成后，建议执行 CSF 审查，验证 Profile 选择是否合理，目标与复杂度是否匹配。详见 `.aodw-next/01-core/csf-thinking-framework.md`

---

## 阶段 3: Analysis（分析）

**状态转换**: decided → in-progress

**主要任务**:
- 影响分析：识别直接/间接影响的模块、文件、功能
- 不变量检查：列出必须保持不变的行为、接口、约束
- 风险评估：数据损坏、安全、性能、用户体验风险

**阶段目标**: 明确变更边界和约束条件，避免破坏现有功能

**输出物**:
- `RT/RT-XXX/impact.md`（影响分析）
- `RT/RT-XXX/invariants.md`（不变量清单）

**协作方式**:
- AI: 主导分析，自动识别影响范围，列出不变量
- 用户: 确认关键约束，补充业务层面的不变量

**触发条件**: 在修改代码前必须完成此阶段

---

## 阶段 4: Spec/Plan（规格/计划）

**状态**: in-progress

**主要任务**:

**Spec-Full**:
- 编写完整需求说明（spec.md）：背景、目标、用户故事、功能/非功能需求、成功标准
- 编写技术实现方案（plan.md）：技术背景、方案概览、组件变更、代码结构与分层设计、数据流、风险缓解、分阶段计划
- 编写数据模型文档（data-model.md，如涉及）
- 编写契约文档（contracts/，如涉及）
- 编写任务清单（tasks.md，按 User Story 和 Phase 拆分）
- 编写质量检查清单（checklists/）

**Spec-Lite**:
- 编写精简需求说明（rt-lite.md §1）：背景、目标、当前/期望行为、影响范围
- 编写精简技术方案（rt-lite.md §2）：修改点、方案描述、代码结构与分层设计、风险注意事项

**阶段目标**: 明确"做什么"和"怎么做"，确保方案符合编码规范

**输出物**:
- Spec-Full: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `tasks.md`, `checklists/`
- Spec-Lite: `rt-lite.md`（单文件模式）

**协作方式**:
- AI: 基于 Intake 信息自动生成文档，确保符合编码规范（前端/后端）
- 用户: 审阅 spec/plan，从业务视角确认方案合理性，批准执行计划

**关键检查点**: Plan 完成后必须暂停，展示摘要，询问"计划已就绪，是否批准执行？"，严禁未获批准前开始修改代码

**CSF 审查（必须）**: Plan 完成后，在进入"计划批准"节点前，**必须**执行 CSF 审查。审查重点：验证方案是否直接贡献于目标、分解是否 MECE、识别 CSF、检查端到端关键路径、评估技术方案合理性。详见 `.aodw-next/01-core/csf-thinking-framework.md`

---

## 阶段 5: Implementation（实现）

**状态**: in-progress

**主要任务**:
- 开发准备（Dev Ready）：
  - 检查工具已初始化（.aodw-next/tools-status.yaml）
  - 加载编码规范（前端/后端/通用）
- 在 feature 分支上实现代码修改：
  - 遵守项目编码规范
  - 通过工具自动检查（ESLint/Ruff/Black）
  - 符合 plan.md 中设计的代码结构与分层
- 开发结束前自检：
  - 运行 Lint 检查
  - 运行格式化检查
  - 验证文件大小和复杂度符合规范
- 编写/更新测试文档（tests.md）
- 更新变更日志（changelog.md）
- 更新模块文档（如涉及）

**阶段目标**: 实现功能，确保代码质量和规范符合性

**输出物**:
- 代码修改（在 feature 分支上）
- `RT/RT-XXX/tests.md`（测试用例列表）
- `RT/RT-XXX/changelog.md`（变更总结）
- 模块 README 更新（如涉及）

**协作方式**:
- AI: 主导代码实现，自动运行检查工具，更新文档，维护 task.md（如需要）
- 用户: 确认关键实现决策，验证功能是否符合预期

**关键检查点**: 
- 每次写代码前必须验证当前在 feature 分支
- 提交代码前必须展示 git status 和关键 diff，询问"修改已完成，是否提交？"

---

## 阶段 6: Verification（验证）

**状态转换**: in-progress → reviewing

**主要任务**:
- 文档一致性检查：
  - spec/plan 是否完整记录了问题→方案→实现过程
  - impact/invariants/tests/changelog 是否完整
  - 数据模型/接口变更是否已更新相关文档
  - 模块文档是否已更新
- RT 完整性检查：
  - 核心文档是否齐全
  - 过程文档是否在正确位置（RT/RT-XXX/docs/）
  - meta.yaml 与 index.yaml 是否一致

**阶段目标**: 确保 RT 文档完整、一致，符合 AODW 规范

**输出物**:
- 验证结果报告
- 修正后的文档（如发现不一致）

**协作方式**:
- AI: 自动执行一致性检查，发现不一致时主动修正或提示
- 用户: 确认验证结果，必要时补充信息

**CSF 审查（推荐）**: Verification 阶段应执行 CSF 审查，不仅检查文档一致性，还要检查目标达成度、验证端到端关键路径、评估多维决策合理性。详见 `.aodw-next/01-core/csf-thinking-framework.md`

---

## 阶段 7: Completion（完成）

**状态转换**: reviewing → done

**主要任务**:
- 知识蒸馏（Knowledge Distillation）：
  - 读取 modules-index.yaml，找到受影响的模块
  - 更新对应的模块文档（docs/modules/*.md）
  - 确认文档与代码一致
- 提供完成脚本（AI 不得自动执行）：
  - 确认在 feature 分支
  - 确认所有改动已提交
  - 切换到主分支并拉取最新代码
  - 合并 feature 分支（--no-ff）
  - 打标签（done-RT-XXX）
  - 推送代码和标签
  - 删除本地 feature 分支
  - 更新 RT 状态为 done

**阶段目标**: 完成代码合并，更新全局状态，确保知识库同步

**输出物**:
- 合并后的代码（在主分支）
- `done-RT-XXX` 标签
- 更新的模块文档
- `RT/RT-XXX/meta.yaml`（status: done, closed_at）
- `RT/index.yaml`（状态更新）

**协作方式**:
- AI: 执行知识蒸馏，提供完整的手动命令脚本，更新 RT 状态
- 用户: 验证代码质量，验证文档更新，手动执行合并和推送脚本，验证推送结果

**关键规则**: AI 禁止自动执行合并、推送、删除分支操作，必须提供脚本由用户手动执行

---

## 状态机总览

```
created → intaking → decided → in-progress → reviewing → done
  ↓         ↓          ↓           ↓            ↓         ↓
Intake   Intake    Decision   Analysis/    Verification Completion
                        Spec/Plan/
                    Implementation
```

## 关键原则

1. **分支管理**: 所有代码修改必须在 feature 分支上进行，严禁在 main/master 分支直接修改
2. **文档同步**: 文档必须与代码保持同步，文档与代码不一致视为 Bug
3. **选项化提问**: AI 所有关键问题应提供选项和推荐，用户只需选择
4. **主动推进**: AI 应主动推进流程，不等待具体命令
5. **工具无关**: 行为通过仓库文档约束，不依赖特定工具配置
