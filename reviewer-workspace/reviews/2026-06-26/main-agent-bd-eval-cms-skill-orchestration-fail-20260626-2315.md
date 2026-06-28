## 审查结论

**总体评级**：FAIL
**置信度**：0.86
**审查对象**：bd-eval-cms Skill 改造方案 — N2 orchestrator directive 三项架构决策
**审查时间**：2026-06-26 23:15 GMT+8
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 决策1：独立编排指令位置 | 4 | 新建轻量执行指令文件优于塞入 1400+ 行设计文档，但 SKILL.md 不能只加弱引用，必须设为运行 N2 的必读入口。 |
| 决策2：checklist+pseudocode 格式 | 4 | 是 LLM agent 最容易稳定执行的格式之一；还应补状态机、DoD、失败处理表、恢复点。 |
| 决策3：流水线/分阶段调度 | 2 | 搜索章逐章复核思路合理，但收口章并发违反 manifest 依赖；16 次 yield + 3600s timeout 估算缺少子任务实际耗时，风险高。 |
| 可迁移性/复用性 | 3 | 方向正确，但需把路径、agent 名、模型、并发、timeout、恢复检查显式参数化，否则迁移到其他 agent 仍依赖隐性经验。 |
| 证据一致性 | 3 | 方案与失败复盘和 OpenClaw sessions_yield 文档总体一致，但与 chapter-manifest 的 Ch0/Ch1/Ch17/Ch18 依赖不一致。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 调度依赖错误 | 决策3：收口章 4 章一起 spawn 写作 | Ch17 依赖 Ch1 和 Ch2-Ch16；Ch0 又依赖 Ch17；Ch18 依赖 Ch17。因此 Ch0/Ch1/Ch17/Ch18 不能一起写。 | `chapter-manifest.json`: Ch17 depends_on = Ch1+Ch2..Ch16；Ch0 depends_on = Ch1,Ch3,Ch10,Ch17；Ch18 depends_on = Ch1..Ch17。 | 改为 `Ch1 → Ch17 → (Ch0, Ch18 并行)`；终审在 Ch0/Ch18 完成后再跑。 |
| F002 | major | timeout 估算不足 | 决策3：总 16 次 yield，~60 分钟，runTimeout=3600s | 估算只把每次 yield 恢复/处理按 2-3 分钟计入，没有把搜索、写作、复核 child 的 wall-clock 时间充分计入。复盘中写作 sub-agent 曾 592s-3056s；sub-agent run timeout 若覆盖等待期，3600s 几乎无余量。 | 复盘文档：上次写作 sub-agent 运行时间 592s-3056s；OpenClaw docs: `sessions_yield` ends current turn and lets completion events arrive; run timeout由配置控制，`sessions_spawn` 不接受 per-call timeout。 | 不建议单个 depth-1 orchestrator 在 3600s 内包完整 19 章。采用阶段拆分：搜索/搜索章写审/继承章/收口章/终审，或主 agent 编排。每个 orchestrator 控制在 20-30 分钟预算。 |
| F003 | major | 章节依赖/批处理边界 | 决策3：搜索章 11 章逐章流水线 vs 批量 | 逐章“搜索→写作→复核”能最早发现质量问题，但 11 次 yield 开销偏高；同时搜索章内部也有依赖链，不能简单改成 3-4 章全写完再复核。 | `chapter-manifest.json`: Ch3 depends Ch2；Ch4 depends Ch2/Ch3；Ch5/6/7 depends Ch3；Ch11 depends Ch2；Ch12 depends Ch11；Ch14 depends Ch10。 | 保留 topo-order，但优化为“依赖层级小批”：Ch2 → Ch3 → 并行/批量 Ch4/5/6/7/8/11/10（按实际硬依赖校正）→ Ch12/14。每批写完立即预聚合+复核，不必固定 11 次 yield。 |
| F004 | minor | 并发写 state 风险 | 决策3：继承章 4 章一起 spawn 写作 | 继承章在搜索章完成后互不依赖，内容层面可并发；但如果多个 worker 同时 `jq` 改同一个 `state.json`，存在覆盖/竞态。 | 协议标准流程第4步要求每章写后更新 `state.json`；继承章 Ch9/13/15/16 depends_on 分别为 Ch8/none/Ch11+Ch12/Ch14，无互相依赖。 | worker 只写章节文件和局部产物；由父 orchestrator 在 yield 后统一更新 state.json，或使用带锁脚本更新。 |
| F005 | minor | Skill 入口弱引用 | 决策1：SKILL.md 加一行指向 | 只加“N2 执行流程见...”可能不够强，agent 可能只读 SKILL 前部路由，不主动读取 references 文件。 | 当前 SKILL.md 已有长篇路由/规则；n2-runner-protocol.md 是 1400+ 行流程规范，复盘明确“当前 Skill 缺编排指令”。 | 在 SKILL.md 增加明确触发规则：当用户要求“跑完整评估/N2/两书/全链路”时，必须先读 `references/n2-orchestrator-directive.md`，并声明该文件优先于人读协议的执行顺序。 |
| F006 | minor | 指令可迁移性不足 | 决策1/2 整体 | 独立 directive 有利迁移，但若写死 absolute path、固定 agentId/model/provider、固定 runTimeout，就不能“任何 agent 拿到都能跑”。 | OpenClaw docs: sub-agent model/timeout来自配置；`sessions_spawn` 支持 agentId/model/context/cwd，run timeout不支持 per-call；复盘中 provider 负载曾失败。 | directive 顶部放“环境变量/可配置项”：skill root、case dir、writer agent、reviewer agent、max concurrent、timeout budget、fallback model、resume command。 |

---

## 逐项结论

### 决策 1：新建独立 `references/n2-orchestrator-directive.md`

**结论：赞成，但要把它设为 N2 运行的强制入口，而不是弱参考。**

理由：
- 对 Skill 可复用性更好。`n2-runner-protocol.md` 是人读设计/协议，内容长且包含历史、理念、字段合同等；agent 每次完整读取会浪费 context，也会增加执行歧义。
- 独立 directive 更适合作为“agent runbook”：短、可执行、可版本化、可测试、可迁移。
- 迁移到其他 agent 时，只要该文件不写死本机绝对路径和专属 agent 名，而是用相对路径/配置项，就比修改大协议方便得多。

必须补强：
1. SKILL.md 中应写成强制语义：`当执行完整 N2 / 两书 / 全链路评估时，必须先读取 references/n2-orchestrator-directive.md，并按其执行。`
2. directive 顶部列明优先级：执行顺序以 directive 为准；详细质量标准回查 `n2-runner-protocol.md` 和 `chapter-manifest.json`。
3. 所有路径用 `{SKILL_ROOT}`、`{CASE_DIR}`，不要写死 `/Users/evan/...`。

### 决策 2：step-by-step checklist + 内联 pseudocode

**结论：赞成，是比纯 pseudocode 更适合 LLM agent 的格式。**

推荐格式不是“只有 checklist”，而是四层混合：
1. **硬性不变量**：spawn 后必须 `sessions_yield`；yield 后先核验 child 结果；父进程统一更新共享 state；不得并发写同一文件。
2. **阶段 checklist**：每阶段输入、动作、产物、通过条件。
3. **关键 pseudocode**：只用于 spawn/yield/恢复检查这种容易误操作的地方。
4. **失败处理表**：child failed/timed out/provider overloaded/缺文件/blocker review 各自怎么办。

建议 directive 每一步包含固定字段：`Goal / Pre-check / Actions / Yield point / Resume checks / State update / Failure handling / Next step`。

### 决策 3：搜索章流水线、继承章批量、收口章批量

**结论：不能按原方案落地，需要调整。**

1. **搜索章逐章流水线：方向合理，但 11 次 yield 不是最优。**
   - 逐章写+复核能最快发现幻觉/证据不足，适合高风险 BD 报告。
   - 但可按依赖层级小批化，减少 yield。不要简单 3-4 章一批全部写完再复核，否则错误会扩散。

2. **继承章 4 章一起 spawn 写作：内容上基本安全，工程上要防 state 冲突。**
   - Ch9/13/15/16 在搜索章完成后没有互相依赖，可并发写。
   - 但 worker 不应同时写 `state.json`；父 orchestrator yield 后统一更新。

3. **收口章 4 章一起 spawn 写作：不合理。**
   - Ch17 依赖 Ch1 和 Ch2-Ch16；Ch0 依赖 Ch17；Ch18 依赖 Ch17。
   - 正确顺序应是：`Ch1 → Ch17 → Ch0/Ch18 → final review`。

4. **16 次 yield + runTimeout=3600s：风险偏高。**
   - 16 次恢复处理 32-48 分钟只是 orchestration overhead。
   - 加上 child 写作/复核实际耗时，完整流程很可能超过 3600s，尤其写作历史上可达 51 分钟。
   - 若必须使用 sub-agent orchestrator，应拆成多个阶段 orchestrator；如果用主 agent 编排，则 timeout 风险较低但 context 消耗更高。

---

**最重要的一条建议**

保留“独立编排指令 + checklist/pseudocode”的产品化方向，但在落地前必须重写调度图：尤其把收口章改成 `Ch1 → Ch17 → Ch0/Ch18`，并把单个 orchestrator 的 3600s 全流程拆成有超时余量的阶段化执行。