# DISCUSSION LOG - bd-eval-cms

## 2026-06-13 14:34 CST

- 触发背景：bd-eval-cms v0.9.0 已发布到 GitHub master，需要决定下一阶段工作方法。
- 用户反馈/诉求：Evan 认可“v0.9.1 先做质量固化，而不是直接扩 20 个 profile”的思路，并要求选择一套行之有效的工作方法，确认是否按当前 Agent Factory 的流程和 SOP 执行。
- 关键决策：下一阶段按 Agent Factory AF-SOP 管理 Skill 产品迭代；bd-eval-cms 自身 SOP 只用于具体品种报告生产；v0.9.1 先走 S8 复盘归档 + S2 需求固化，不直接进入代码开发。
- 需要修改的内容：新增 v0.9 复盘归档文档与 v0.9.1 需求固化草案。
- 执行结果：已新增 `design/v0.9-retrospective.md` 与 `design/REQ-v0.9.1.md`。
- 待办：Evan 确认 REQ-v0.9.1 后，进入 S3，产出 `design/DESIGN-v0.9.1.md`，随后按 AF-REVIEW-SOP 做独立设计评审。

## 2026-06-13 14:38 CST

- 触发背景：Evan 确认继续 v0.9.1 S3 方案设计。
- 用户反馈/诉求：在已确认 REQ-v0.9.1 的基础上，进入方案设计，但仍不直接写代码。
- 关键决策：S3 设计围绕质量固化展开，核心为 profile schema、profile registry、Markdown contract、renderer 失败策略、测试矩阵与发布白名单。
- 需要修改的内容：新增 `design/DESIGN-v0.9.1.md`。
- 执行结果：已完成 DESIGN-v0.9.1 草案。
- 待办：按 AF-REVIEW-SOP 对 DESIGN-v0.9.1 做独立评审，评审通过后再进入 S4 开发。

## 2026-06-13 14:46 CST

- 触发背景：DESIGN-v0.9.1 完成后进入独立只读评审。
- 用户反馈/诉求：按 AF-REVIEW-SOP 做设计门控，不直接进入 S4。
- 关键决策：评审结论为 CONDITIONAL_PASS；需闭环字段命名、profile version 迁移、default_profile fallback、strict 路径、负向测试对齐五项问题。
- 需要修改的内容：新增 `design/REVIEW-DESIGN-v0.9.1.md`，并修订 `design/DESIGN-v0.9.1.md`。
- 执行结果：已将五项条件写入 DESIGN-v0.9.1 的 §3.5 与相关章节，设计门控条件已闭环。
- 待办：Evan 确认后进入 S4 小步开发。

## 2026-06-13 15:30 CST

- 触发背景：Evan 确认进入 S4 小步开发，要求严格依据设计文档实现 v0.9.1 质量固化版本。
- 用户反馈/诉求：执行 S4 小步开发，范围限定为质量固化，不发布、不 commit、不 push。
- 关键决策：按 §11 实施顺序执行，重点实现 profile schema、registry、contract、strict 校验、测试增强与 smoke 入口。
- 执行结果：已完成所有 8 项 S4 任务：
  1. ✅ 新增 `templates/style-a1/profiles/schema.json`：定义 profile 最小结构，支持 common/skill 两种类型校验
  2. ✅ 新增 `templates/style-a1/profiles/registry.json`：管理 3 个 active profiles 与 17 个 planned profiles
  3. ✅ 升级 4 个 profile 文件版本：`common.json`、`A-1.json`、`A-5.json`、`A-7.json` 的 version 字段从 0.9.0 升级到 0.9.1
  4. ✅ 新增 `templates/style-a1/contracts/markdown-contract.md`：定义上游 Markdown 输出契约，包含通用必选结构与 A-1/A-5/A-7 特定要求
  5. ✅ 修改 `templates/style-a1/render.py`：实现严格校验逻辑，包括 registry 加载、schema 校验、7 类 fail-fast 条件、禁止 default_profile 自动 fallback
  6. ✅ 修改 `templates/style-a1/test_render.py`：增加 schema/registry 正向测试与 7 类负向测试（profile-not-registered、profile-file-missing、profile-schema-invalid、required-component-missing、critical-component-missing、template-token-unreplaced、output-html-missing）
  7. ✅ 新增 `templates/style-a1/smoke/` 目录：包含 README.md 与 run_smoke_test.sh，提供真实案例验收入口
  8. ✅ 更新 `design/DISCUSSION-LOG.md`：记录本条 S4 执行结果

- 关键技术实现：
  - **字段命名统一**：common 与 skill profile 统一使用 `required_components`，不引入 `expected_components` 作为 profile 主字段
  - **版本迁移完成**：4 个既有 profile 版本统一升级到 0.9.1
  - **Fail-fast 策略**：未知 profile 不允许自动 fallback，registry.default_profile 仅用于元数据
  - **Strict 默认开启**：render.py 默认执行严格校验，不新增 CLI `--strict` flag
  - **负向测试完整**：7 类 fail-fast 条件一一对应负向测试用例

- 待验证：运行 `python3 templates/style-a1/test_render.py` 验证正向测试仍为 100%，负向测试能证明 fail-fast 生效。
- 待办：验证测试通过后，进行小范围评审与质量门控，确认无问题后再考虑发布 v0.9.1。

## 2026-06-13 15:16 CST

- 触发背景：S4 coding agent 完成后，主调度员做独立复验。
- 用户反馈/诉求：进入 S4 开发，完成后必须验证，不直接进入发布。
- 关键发现：初次复验发现正向测试失败，原因是 strict 校验把 CSS selector 当正则检查，且 A-5/A-7 高级组件被误设为 v0.9.1 必选项。
- 修复决策：renderer/test_render 改为按 CSS selector 校验；A-5/A-7 高级业务组件保持 optional，符合 v0.9.1 质量固化、不扩业务组件的边界；未知 profile 继续 fail-fast，不 fallback。
- 验证结果：`python3 templates/style-a1/test_render.py` 返回 0；A-1/A-5/A-7 正向 100%；7 类负向测试 100%；`bash templates/style-a1/smoke/run_smoke_test.sh` 通过；`scripts/render_report.sh` 对 A-1/A-5/A-7 自动检测渲染均通过。
- 待办：进入 S5 质量门控，检查版本三处一致、白名单 staging、style-12/13 不回归。

## 2026-06-13 15:24 CST

- 触发背景：S5 质量门控。
- 用户反馈/诉求：S4 完成后继续验证，不等待人工确认。
- 关键决策：v0.9.1 质量门控前同步版本号到 `VERSION`、`version.json`、`SKILL.md` metadata 与 style-a1 expected fixture 版本。
- 验证结果：`python3 templates/style-a1/test_render.py` 返回 0；`bash templates/style-a1/smoke/run_smoke_test.sh` 返回 0；style-12/style-13 回归渲染返回 0；profile versions 与 skill 版本均为 0.9.1。
- 待办：整理白名单变更，进入发布前审查；确认后 commit + push 发布 v0.9.1。

## 2026-06-13 15:38 CST

- 触发背景：发布 v0.9.1 前，Evan 要求检查 GitHub Issue #72。
- Issue 内容：清除 v0.6.0 前旧 `doc.20100706.xyz` 上传流程引用，避免 Agent 混用旧 30 天临时上传路径。
- 处理范围：仅清理活跃代码/文档与 issue 指定文件；不改历史案例目录中的既有报告链接。
- 关键变更：删除 `scripts/batch-upload.sh`；`cms-report-to-html.py` 移除 `--upload/--doc-id` 旧上传逻辑；`start-phase.sh`、health-check、archive-links、QUICKREF、PLAN、ARCHITECTURE-REVIEW、SKILL、version 说明统一改为产品引进知识库 / doc.aishuo.co。
- 验证结果：活跃文件 grep `doc.20100706.xyz|20100706` 为 0；bash -n / py_compile 通过；style-a1 完整测试与 smoke 通过；style-12/style-13 回归通过。
- 待办：将 Issue #72 修复纳入 v0.9.1 发布白名单，再 commit/push。

## 2026-06-13 16:10 CST

- 触发背景：用户批准执行 v0.9.1 质量护栏版，但明确要求不 commit、不 push、不发布。
- 用户反馈/诉求：在现有 v0.9.1 未提交改动基础上，完成发布前必须修复的质量护栏：#73 Phase 前置检查、#70 TTL 文案修正、#71 bd-eval-cms 侧硬隔离、保持 #72 清理、不做 #68 Mermaid 修复。
- 关键决策：实现 Phase 5.5 readiness preflight 机制，防止缺少关键阶段产物时仍生成看起来完整的 REPORT.html；修正 TTL 文案为更严谨的"长期预览/配置记录为 5y"；明确硬隔离路径。
- 需要修改的内容：
  1. ✅ 新增 `scripts/preflight-phase.sh`：Phase 5.5 前置检查脚本，检查 state.json、04-final-report.md、关键上游产物、gateStatus 状态
  2. ✅ 修改 `scripts/render_report.sh`：在渲染前默认执行 preflight 检查，支持 BD_EVAL_CMS_SKIP_PREFLIGHT=1 跳过
  3. ✅ 修改 `scripts/start-phase.sh`：在 phase-5-5-html 执行前调用 preflight，失败则标记 failed 退出
  4. ✅ 修正 #70 TTL 文案：`sync-to-knowledge-base.sh`、`config.yaml`、`version.json` 中"5年有效期"改为"长期预览/配置记录为 5y/接口未返回 expire 字段"
  5. ✅ 明确 #71 硬隔离：`render_report.sh` 和 `sync-to-knowledge-base.sh` 头部添加硬隔离职责说明
  6. ✅ 更新 `SKILL.md`：新增 Phase 5.5 质量护栏与硬隔离路径章节，说明 preflight 检查项和硬隔离路径
- 执行结果：已完成所有 5 项质量护栏任务，新增 preflight 机制，修正 TTL 文案，明确硬隔离路径，更新文档。
- 发布前复核修正：preflight 从宽松检查升级为生产护栏——`state.json.gateStatus` 必须存在，Phase 5.5 前置 gate 必须全部为 `completed`，Gate 0~5 物理产物必须齐全；旧案例仅允许通过 `BD_EVAL_CMS_SKIP_PREFLIGHT=1` 做测试/历史回放。
- 待验证：运行验证命令（bash -n/py_compile/测试/负向案例）+ grep 检查旧上传流程清理。
- 待办：验证通过后输出改动文件清单、issue 处理状态、验证命令和结果，明确说明未 commit/未 push。

## 2026-06-13 19:55 CST

- 触发背景：用户指出"我们是不是可以先拿一个项目测试一下"，并明确 Skill 入口必须相对单一：程序只给品种名 + 公司名（最多再多给点商品信息），剩下的全链路自动跑完，最终按 Skill 要求上传产品中心知识库。后续真实生产形态是"由程序控制给出对应的品种名称和公司名称"的全自动化。
- 关键洞察：当前 `run.sh` 仍要求业务程序先创建 case 目录、写 state.json，再传入 caseCode；这违背"单一入口"诉求。需要在 v0.9.1 质量护栏之上补一个"商机驱动"的最外层入口。
- 决策：v0.9.2 = 单一入口版，定位为"业务程序可调用的最小必要接口"，不修改 Phase 1~5.5 内部逻辑、22 个 skill 文件、v0.9.1 质量护栏。
- 实现：
  1. ✅ `scripts/run-opportunity.sh` —— 单一入口，支持 `--product/--company` 必填 + 可选 `--indication/--region/--notes/--ext/--scheme/--mode/--json/--dry-run`
  2. ✅ `caseCode` 自动生成 = `YYMMDD + 4字母缩写`（英文取前4大写 / 中文用 pypinyin FIRST_LETTER / 混合 + 不足 4 位 X 补齐）
  3. ✅ `opportunity_id = caseCode::product::company` 实现幂等续跑；同日同 product+company 重复调用不覆盖
  4. ✅ 冲突处理：同日同 4字母缩写但不同 product/company → 自动加 `-1 / -2` 后缀
  5. ✅ 新 case 初始化 state.json（12 gateStatus=pending + 完整 opportunity 元数据 + lastHeartbeat + currentVersion=1）
  6. ✅ 写 `00-opportunity.md` 留底原始输入（产品/公司/适应症/地区/备注/ext 列表/submittedAt）
  7. ✅ `--ext` 文件自动复制到 `EXT/EXT-001-<filename>` 并生成 `EXT-001.md` 元数据
  8. ✅ `auto` 模式调 `orchestrator-resume.sh` 自驱 Phase 1→5.5；`semi` 模式只初始化等人工确认；`--dry-run` 零副作用
  9. ✅ stdout 输出 4 个结构化 prefix：`CASE_PATH=` / `CASE_CODE=` / `PHASE_STATUS=` / `OPPORTUNITY_ID=`
  10. ✅ `scripts/test-run-opportunity.sh` 17 用例全过（缺参 / 无效参数 / 帮助 / 英文 / 中文 / 真实创建 / 子目录 / state.json / 00-opportunity.md / 幂等 / 4 prefix / JSON 文件 / JSON stdin / 冲突后缀 / dry-run 零副作用）
  11. ✅ `references/opportunity.example.json` JSON 模板
  12. ✅ `design/REQ-v0.9.2.md` + `design/DESIGN-v0.9.2.md` 方案设计
  13. ✅ `SKILL.md` frontmatter description 增加单一入口触发词 + 新增 Step 1.5 调用小节
  14. ✅ `EXECUTION.md` 替换"快速开始"为程序调用示例 + 新增"单一入口脚本"章节
  15. ✅ `VERSION` 0.9.1→0.9.2；`version.json` 同 + 补 `0.9.1->0.9.2` changelog 条目（含 description 同步追加）
- 兼容性验证（同步跑 v0.9.1 既有验证门）:
  - preflight 测试 8/8 通过
  - style-a1 test_render.py 通过
  - smoke 通过
  - health-check 9/9 通过
  - 新 test-run-opportunity.sh 17/17 通过
  - 22 个 skill 文件未触动
  - 4 个 profile 未触动
  - run.sh / orchestrator-resume.sh / start-phase.sh / preflight-phase.sh / render_report.sh / sync-to-knowledge-base.sh 未触动
- 已知/未做：
  - **不修改 Phase 1~5.5 内部逻辑**：v0.9.1 start-phase.sh 仍是占位输出，真实业务子 Agent 仍由 Orchestrator (OpenClaw chat session) 接管调度；新入口只是把"创建 case + 启动 orchestrator-resume"这两步从手工/两次调用合成一次调用。
  - **后续真实生产测试**：等用户提供一个真实品种走 run-opportunity.sh 全链路验证，作为发布前最后一道验收。
- 待办：等用户提供真实品种后跑全链路；通过后与 v0.9.1 一起打包成"v0.9.2 单一入口 + v0.9.1 质量护栏"联合发布。

---

## [2026-06-14] v0.9.3 内部清理：profile 集合收敛为单一 A-1 骨架

**决策**：将 A-1 / A-5 / A-7 三个 profile 收敛为单一 A-1（通用投前评估骨架）。

**前车之鉴**：
- 18 个历史 case 中 11 个 routedSkill=A-1，5 个 A-5，2 个 A-2，0 个 A-7
- 三份 profile 契约（`profiles/A-1.json` / `A-5.json` / `A-7.json`）的 critical_components 高度重叠（A-1 多了 exclusion-box + gate-card + battle-* + one-pager + stage-a），A-5 / A-7 实际从未要求过差异化
- 三份 profile 渲染出来的 HTML 字节级几乎完全相同（仅 profile_code 字符串不同），业务侧无法感知差异
- "按 profile 差异化" 是给空气做衣服，无真实业务驱动

**清理范围**：
- 删除：`profiles/A-5.json` + `profiles/A-7.json` + `fixtures/sample-a-5.md` + `fixtures/sample-a-7.md` + `fixtures/expected/by-skill/A-5.json` + `fixtures/expected/by-skill/A-7.json`
- 收敛：`profiles/registry.json` 中 active_profiles 从 3 减为 1
- 注释收敛：`render.py` / `test_render.py` / `smoke/run_smoke_test.sh` / `scripts/render_report.sh` 中 A-5/A-7 引用全部移除
- 逻辑保留：render.py 仍接受 `--profile` 参数（默认 A-1，向后兼容）

**业务影响**：
- 18 个历史 case 不受影响（`routedSkill` 字段保留，REPORT.html 渲染逻辑未变）
- 未来真有 A-5 / A-7 独立"长相"需求时，重新建 profile 不晚（成本低）

**不升版本号**：本次为内部清理，不影响 v0.9.1 / v0.9.2 已 commit 的功能；待后续发布时合并到 v0.9.3 主版本号。
