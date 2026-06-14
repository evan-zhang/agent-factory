# REQ-v0.9.2 — 单一入口（Opportunity-Driven Entry）

**版本**: v0.9.2 (DRAFT)
**日期**: 2026-06-13
**对应 Skill**: bd-eval-cms
**前置版本**: v0.9.1 质量护栏版
**状态**: 需求固化（待用户确认后进入 S3b 方案设计）

---

## 1. 背景

v0.9.1 已完成质量护栏（Phase 5.5 preflight / TTL 文案 / 渲染同步硬隔离 / batch-upload.sh 清理 / health-check 修复 / changelog 补全）。

但全链路执行入口仍不"单一"。当前如果要由外部程序触发一次新评估，需要：

1. `mkdir -p {品种名}/` （业务侧程序不知道怎么选目录名）
2. 手写 `state.json` 12 个 gateStatus + opportunity 元数据
3. 调用 `scripts/run.sh {caseCode}` 启动 Phase 1

这违背了"程序只给品种名 + 公司名，剩余全自动"的真实生产形态目标。

## 2. 用户原始诉求

> "你再确认一下我们这个 skill 执行的入口啊，就是必须相对单一啊。所以我给你的项目只能是一些项目内容，包括这个品种的名称啊，公司啊，这些不可能包含对应的品种类型，所以它更多的是一个泛泛的商机，最多可能包含品种的名称和这个公司的名称，确保这个商机的唯一性，然后你要做的就是帮我跑完整的全链路，然后输出最后的这个报告。而且这个报告应该按照 skill 的要求，帮我把它传到产品中心的知识库里面去。这就是我们全链路的验证，因为后续我们将会自动化的运行这个 skill，由程序控制给出对应的品种名称和公司名称，甚至可以多给一点商品的信息，但剩下的就是系统全自动运行"

## 3. 核心约束

| 约束 | 说明 |
|------|------|
| 入口必须单一 | 一次调用即可启动全链路，不能要业务程序理解 Skill 内部状态文件结构 |
| 输入不需含品种类型 | A-1/A-5/A-7 类型由 Skill 内部 Phase 2 路由自动判定 |
| 必须有唯一性保证 | 同品种 + 同公司 → 同一 caseCode，避免重复 |
| 可选额外信息 | 业务方可多给适应症 / 地区 / 背景资料 |
| 全自动跑完 | 程序只需一次调用，Skill 必须自驱 Phase 1→5.5 |
| 输出报告 + 上传知识库 | 最终输出可访问的 HTML 报告链接 |

## 4. 验收标准

1. **入口脚本**: `scripts/run-opportunity.sh`，支持 flag 形式与 JSON 形式两种输入
2. **输入校验**: 至少校验 product + company 必填，可选字段透传
3. **唯一性**: 同一对 (product, company) 在同一日期下生成同一 caseCode，重复调用幂等
4. **状态机**: 首次调用 → 创建 case + 初始化 state.json + 启动 Phase 1；后续调用 → 续跑
5. **可观测**: 输出三段：case 路径、caseCode、当前 phase 状态
6. **dry-run**: 提供 `--dry-run` 仅打印将要执行的动作，不写文件、不调 orchestrator
7. **可被 cron / 流水线 / 程序控制** 调用：非交互式（无 read、无 tty 要求）
8. **可补资料**: 支持 `--ext path/...` 或 `--notes` 在初始化时挂到 case
9. **文档**: EXECUTION.md 增加"单一入口"章节；SKILL.md frontmatter description 增加触发词

## 5. 不做什么

- 不修改 Phase 1~5.5 内部逻辑（保持 v0.9.1 质量护栏版不变）
- 不改变 run.sh / orchestrator-resume.sh / start-phase.sh 的对外行为
- 不破坏既有 22 个 skill 文件
- 不重命名历史 case 目录
- 不引入新的依赖

## 6. 验收方式

| 验证 | 方式 |
|------|------|
| 入口脚本语法 | `bash -n scripts/run-opportunity.sh` 通过 |
| dry-run | 任意输入下退出码 0、零文件副作用 |
| 真跑一条 | 创建一个测试 case，验证 caseCode、state.json、目录结构、状态机正常 |
| 与 v0.9.1 兼容 | preflight / health-check / 已有 fixture 测试均通过 |
| 文档同步 | SKILL.md frontmatter description 增加触发词；EXECUTION.md 新增章节 |
| 与 orchestrator 衔接 | 脚本调通后必须保证 orchestrator-resume.sh 能正常接管 |

## 7. 风险与对策

| 风险 | 对策 |
|------|------|
| 重复调用生成多个 case | 同日同 product+company → 同 caseCode，目录已存在则视为续跑 |
| 中文字段 4 字母缩写冲突 | pypinyin + 冲突时追加 -01 / -02 后缀 |
| 程序调用时 stdout 解析困难 | 关键输出用结构化 prefix：`CASE_PATH=` / `CASE_CODE=` / `PHASE_STATUS=` |
| 程序无 TTY | 脚本无 read / 颜色强制开 / 无 tput |
| preflight 误拦 | 新 case 无产物时不应触发 preflight（preflight 只在 Phase 5.5 触发，初始化时无产物是正常） |
