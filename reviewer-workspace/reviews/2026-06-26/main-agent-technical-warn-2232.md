## 审查结论

**总体评级**：WARN  
**置信度**：0.83  
**审查对象**：技术方案 — `CP202601120013_执行失败复盘_v0.1.md`（OpenClaw sub-agent 编排架构，重点复核 B2）  
**审查时间**：2026-06-26  
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 架构选择 | 4 | B2 方向合理，但“最优”依赖 30 分钟内完成的估算，需加超时余量或改分段。 |
| 并发控制 | 4 | reviewer batch=3 保守且匹配 provider 风险；需注意写作阶段“spawn 5 个写作 sub-agent”不可一次性并发，需串行/分批。 |
| 依赖处理 | 4 | 否决 B3 的核心理由成立；搜索章并行收益被继承章/收口章依赖削弱。 |
| OpenClaw 机制符合性 | 3 | sessions_yield 理解基本正确，但 runTimeout 是按整个子会话累计运行计时，不是每个 yield 后重置；文档中 1800s 够用的结论偏乐观。 |
| 风险与可恢复性 | 3 | 有 fallback/batch 设计，但缺少硬性的阶段检查点、超时降级策略和失败重启边界。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 超时估算 | 目标文档 L403-L409, L451-L455 | B2 声称“1800s runTimeout 够用”，但编排者 1/2 都被设计为约 30 分钟，几乎无余量；且源码显示 yield 后重新激活会累计 runtime，不是重置 1800s。 | `subagents.md` L144：runTimeout 来自全局配置；源码 `replaceSubagentRunAfterSteer` 保留 `sessionStartedAt` 并设置 `accumulatedRuntimeMs = getSubagentSessionRuntimeMs(...)`；`resolveSubagentRunDurationMs` 将 1800s 转为硬 deadline。目标文档 L333 还记录过写作 sub-agent 592s-3056s 的实测跨度。 | 不建议以 1800s 直接落地。将 B2 拆为 3 个 orchestrator（搜索、写作+预聚合、复核+终审），或把全局 runTimeout 提到 3600s；若必须 1800s，则每个 orchestrator 目标控制在 ≤20-24 分钟，并设置阶段检查点。 |
| F002 | major | 方案表述不一致 | 任务描述 vs 目标文档 L345-L368 | 用户复核点说“编排者 1 要 spawn 5 个写作 sub-agent，每个写 4 章”；文档执行计划更像 5 个写作 batch 串行，每批 spawn 1 个并 yield。若一次 spawn 5 个会触发并发/依赖/资源风险。 | 目标文档 L263-L265、L345-L368：每批 spawn 1 个写作 sub-agent，每批之间 sessions_yield；配置中 `maxConcurrent=8`，默认 `maxChildrenPerAgent` 源码为 5。 | 明确禁止编排者 1 一次性 spawn 5 个写作 worker；应串行 W1→yield→预聚合→W2...，或最多 2 个无依赖搜索章并发。 |
| F003 | major | 并发上限事实 | 目标文档 L224-L225 | 文档把 `maxChildrenPerAgent=5` 写成默认值是正确的，但当前 openclaw.json 未显式配置该项；若未来默认变化或配置覆盖，方案会失去约束依据。 | 当前配置 `agents.defaults.subagents` 仅有 `maxConcurrent=8`, `runTimeoutSeconds=1800`, `maxSpawnDepth=2`, `allowAgents`；源码在未配置时 `cfg...maxChildrenPerAgent ?? 5`。 | 在方案中注明“当前未显式配置，源码默认 5”；若要作为生产约束，建议显式写入配置或在执行前检查。 |
| F004 | minor | B3 ROI 判断 | 目标文档 L421-L456 | 否决 B3 基本合理，但“为省 25 分钟不值得”需要补充失败恢复成本：B3 的 state.json 并发写、跨组依赖栅栏、继承章输入完整性都会引入额外验证点。 | 文档已识别搜索章可并行、继承章/收口章依赖全部结果（L423-L428），并列出 state.json 冲突与依赖协调风险（L444-L445）。 | 保持否决 B3；补充“除非搜索阶段成为瓶颈且具备原子 state 更新/依赖栅栏脚本，否则不采用”。 |
| F005 | minor | reviewer batch | 目标文档 L313-L320, L370-L376 | batch=3 是合适的保守选择，但“1-2 分钟完成”只是推断，历史 reviewer 平均 tool call 高、成本高；预聚合与 tool 限制能改善但未实测。 | usage log L64/L108-L111：单 reviewer 平均 35 次 tool call、输入未预聚合是核心问题；目标文档 L319 称预聚合+≤5 tool call 应该 1-2 分钟。 | 首个 case 先用 batch=2 或 3 进行 smoke test，记录真实 p50/p95；若 GLM 高峰报负载，降到 2；若 p95 > 6-8 分钟，复核编排者 1800s 不够。 |
| F006 | info | sessions_yield 机制 | 目标文档 L187-L205 | 对 sessions_yield 的基本理解符合文档：spawn 后 yield，completion event 作为下一条 model-visible 消息唤醒 requester/sub-agent。 | `subagents.md` L65-L74、L80-L84、L252-L266 明确非阻塞、push-based completion、需要 child 结果时调用 sessions_yield，且不要轮询。源码 `markSubagentRunPausedAfterYield` 标记 `pauseReason="sessions_yield"`，`reactivateCompletedSubagentSession`/`replaceSubagentRunAfterSteer` 支持完成后重新激活。 | 保留该机制；prompt 中必须硬性要求：spawn 必要 children 后不要总结结束，必须 `sessions_yield`；恢复后核对所有 expected child 再继续。 |

---

**最重要的一条建议**

B2 可以落地，但不要按“两个各 30 分钟 orchestrator + 1800s runTimeout 刚好够”落地；请把每个 orchestrator 的预算压到 20-24 分钟或把 runTimeout 提高到 3600s，并明确写作 batch 串行、reviewer batch=3/可降到2、每次 yield 后做检查点。

## 对 5 个核心问题的明确结论

1. **B2 是否最优？** 结论：⚠️ 部分可行但需修正。相对 B1/B3，B2 是当前工程上最稳的选择；但不是在 1800s 下“无条件最优”。若不提高 timeout，建议拆成更小阶段或强制阶段预算。
2. **runTimeout=1800s 是否够？** 结论：⚠️ 不稳。源码和文档支持全局 runTimeout；yield 不等于清零。两个 orchestrator 都贴近 30 分钟，任何 provider 慢、fallback、reviewer 超时都会越界。
3. **B3 被否决是否合理？** 结论：✅ 合理。搜索章能并行，但继承章/收口章依赖形成栅栏；为了约 25 分钟引入更多编排者、state 冲突和依赖协调，ROI 不高。
4. **reviewer batch=3 是否合适？** 结论：✅ 合适但需动态降级。3 小于默认 maxChildrenPerAgent=5，也低于全局 maxConcurrent=8，对 GLM provider 更友好；高峰期降到 2。
5. **sessions_yield 行为是否符合预期？** 结论：✅ 基本符合。文档和源码均支持 sub-agent/orchestrator spawn children 后 yield，completion 以内部事件唤醒继续下一 turn；但必须保证 agentId/工具策略允许 depth=1 spawn，且 maxSpawnDepth=2 已配置。

## 最终 verdict

**⚠️ 部分可行但有增量修正。** 不是重大架构错误；主要风险是 1800s 超时余量不足和执行计划表述需从“一次 spawn 5 个写作”修正为“写作 batch 串行/有限并发”。
