# GRV Battle Round 2 — stock-picking Review

## 审查结论

**总体评级**：WARN
**置信度**：0.88
**审查对象**：方案类文档（GRV / B 类） — `REQ-01.md` v(讨论基线 2026-06-23) + `design/GRV.md` (Draft for Battle v2, 2026-06-24)
**审查时间**：2026-06-24
**使用模型**：newapi-openai/MiniMax-M3
**本轮范围**：Battle 二轮，复查 B001 / M001-M005 吸收情况，并对 S3 / Ralph Loop 准入给出判断

---

**摘要**：B001 / M001-M005 全部被结构性吸收，无残留 blocker。本轮发现 1 项 minor 与 2 项 info/观察，不阻塞 S3 启动，但 M3.5 闸门必须覆盖到这 1 项 minor。建议：可进入 S3 设计，但需在 S3 设计稿 `DESIGN.md` 中显式落地的内容比 M4a 多一项——`registry_snapshot` 的"先读后选"原子性保证的具体实现方式。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| B001 吸收（评审吸收矩阵） | 5 | 24 条 Node 0/1/2/4 finding 全部 marked `absorbed`，落点可追踪至 R/V，`open=0` |
| M001 吸收（优先级 + 里程碑拆分） | 5 | R1-R6 全部带 P0/P1；M4 拆为 M4a 安全/验证底座 / M4b 业务模块，里程碑与 V/M 链路自洽 |
| M002 吸收（execution guard 最小骨架 + 拒绝用例） | 5 | 5 条拒绝用例明确写入 R5 验收标准；V7 把 `futu_tool.py buy` 列为首个安全修复 |
| M003 吸收（custom_ref 白名单 / 双冻结 / Chokepoint exit） | 5 | R3 全部命中；Chokepoint exit criteria 6 个月 + 10 次 manual + 无 thesis break 三条件齐备 |
| M004 吸收（风险→真正缓解） | 5 | 6 条风险全部用"真正缓解："重写，而非把已定设计伪装成缓解 |
| M005 吸收（M3.5 reviewer 闸门） | 5 | M3.5 / M4a / M4b 在 V/M/R 三处一致出现，Ralph Loop 准入条件显式列出 M3.5 |
| 文档内一致性 | 4 | REQ-01 与 GRV 在关键约束（dry_run 默认 true、approval artifact、schema 双冻结）上一致；存在 1 处 R5 / R6 引用细节需注意 |
| S3 / Ralph Loop 准备度 | 4 | GRV 已收敛；M3.5 闸门机制到位；下一步 DESIGN.md 应直接产出模块目录、调用顺序、失败行为 |

---

## 吸收矩阵核对（逐条）

| ID | 吸收？ | 证据 | 备注 |
|----|--------|------|------|
| B001 | ✅ | `design/GRV.md` L15-51，24 条全部 `absorbed`，`open` finding 为空 | 完全吸收 |
| M001 | ✅ | R1-R6 全部带 P0/P1（P0×5，P1×1=Evidence Store）；M4a/M4b 在 L218-219 + L239-240 | 完全吸收；R6 列为 P1 与"evidence store 是 SOP 共享底座"定位一致 |
| M002 | ✅ | L142-143 execution guard 8 项骨架 + 5 条拒绝用例；V7 列为首个安全修复 | 完全吸收 |
| M003 | ✅ | L95 custom_ref 白名单 / L98 Chokepoint exit criteria / L111 Node 7 状态机单向 / L126 schema 双冻结 | 完全吸收 |
| M004 | ✅ | L200-210 全部 6 条风险以"真正缓解："重写 | 完全吸收；缓解措施具体到"先做只读兼容投影""R5 先交付 guard 骨架再碰 broker buy"等 |
| M005 | ✅ | L174 V9c + L210 风险 + L217 M3.5 闸门 + L230 准入条件 + L238 开发顺序 | 完全吸收；5 处冗余提及反而强化闸门不被绕过 |

---

## 本轮新发现

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | minor | 边界模糊 | `design/GRV.md` L98 + R3 验收标准 | Chokepoint exit criteria 的"6 个月 + 10 次 manual"是 AND 还是 OR 未明确；REQ-01 Node 4 段落用"运行满 6 个月、manual 调用不少于 10 次、无重大 thesis break 后"，语序上看是 AND，但评审是否可只满足部分（例：6 个月未满但 thesis 强）未声明 | GRV L98 "至少 6 个月、manual 调用不少于 10 次、无重大 thesis break 后，才评审是否开放 HK/CN、tracking 或 sop" | S3 在 `DESIGN.md` 中明确 Chokepoint exit criteria 的逻辑连接（建议保持 AND），并定义"重大 thesis break"的判定口径（来源：risk_event.thesis_broken 累计次数？还是人工评审？） |
| F002 | minor | 隐式漂移风险 | `design/GRV.md` L95 + REQ-01 Node 2 验收 | `custom_ref` 白名单在 GRV 与 REQ-01 都明确要求，但"白名单来源"（registry 内置 vs 独立 yaml vs 运行时注册）未定；该决策直接影响 R4b 验证底座的实现 | GRV L95 + REQ-01 Node 2 | S3 在 registry 设计中明确 `custom_ref` 白名单的存放位置、加载时机、变更审计路径 |
| I001 | info | 强化建议 | `design/GRV.md` L137-146 R5 验收 | R5 验收标准覆盖 5 条 execution-guard 拒绝用例，但 `bin/futu_tool.py buy` 修复属于 S4 代码改造，验收标准未给"已修复"的可观测信号（如 broker API 调用统计为 0） | R5 L142-143 | S5 验收可加一条：`dry_run=false` 真实 buy 路径下，broker API 调用次数必须经过 execution-guard 中转，可被 audit log 反查 |
| I002 | info | 强化建议 | `design/GRV.md` L100-114 R4a | R4a 要求"validation 幂等"，但幂等键 `(draft_id, validation_run_id, signal_date)` 中的 `signal_date` 来自 Node 1 输出；如果 Node 1 重跑（同 calendar）产生新 `signal_date`，幂等会失效 | R4a + REQ-01 Node 6 | S3 在 data-schema 中补充：幂等键应包含 `calendar_checked_at` 或 `run_id` 而非依赖 `signal_date`，或显式声明 signal_date 不变则幂等 |

---

## 跨文档一致性

| 主题 | REQ-01 表述 | GRV 表述 | 一致性 |
|------|------------|---------|--------|
| 入口原子性 | Node 0 拒绝 mixed/full/monitor/dry_run=false | R1 验收 + 吸收矩阵 N0-04 | ✅ 一致 |
| 交易日 | Node 1 输出 run_context，统一消费 | R1/R2/R4a + 吸收矩阵 N1-06 | ✅ 一致 |
| 策略边界 | Node 2 registry selector，不执行 | R3 + 吸收矩阵 N2-01/02 | ✅ 一致 |
| Chokepoint 限制 | experimental + manual only + US | R3 验收 + 吸收矩阵 N2-06/N4-01 | ✅ 一致 |
| 审批闸门 | approval artifact machine-checkable | R5 验收 + L140-143 | ✅ 一致 |
| dry_run 默认 | 全部节点 dry_run=true | R1/R5 + Node 0 入口契约 | ✅ 一致 |
| Evidence 两层 | evidence_ref.v1 + claim.v1 | R6 验收 | ✅ 一致 |
| 数据迁移 | 旧 CSV → 新事件模型，迁移需审计回滚 | R4b 验收 + 风险 L199-200 | ✅ 一致 |
| 仓位置信度 | 多策略不虚假综合 | R3/R4a 验收 + 风险 L207-208 | ✅ 一致 |

无矛盾点。REQ-01 是节点的契约基线，GRV 是 R/V/M 与吸收矩阵，二者互为引用、互不重叠。

---

## Ralph Loop / S3 准入判断

按 `design/GRV.md` L223-231 列出的 Ralph Loop 准入条件：

| 条件 | 当前状态 |
|------|---------|
| GRV Battle 二轮没有 blocker | ✅ 本轮结论 WARN，无 blocker |
| `design/DESIGN.md` 已定义模块边界、目录结构、调用顺序、失败行为 | ⏳ 待 S3 产出 |
| `src/references/data-schema.md` 已冻结 P0 schema | ⏳ 待 S3 产出 |
| `src/strategies/registry.yaml` 与 registry validator 设计已冻结 | ⏳ 待 S3 产出 |
| execution guard 最小骨架的拒绝用例已写入 S3 设计 | ⏳ 待 S3 产出 |
| M3.5 factory-reviewer 闸门通过，或仅剩明确可在 S4 第一轮关闭的 WARN | ⏳ 待 S3 完成后触发 |

**结论**：
- Battle 二轮结果：**可进入 S3 设计**。
- **不可直接进入 Ralph Loop / S4**。当前明确阻隔在 M3.5 闸门。
- 启动 S3 时应把本轮 F001 / F002 一并落入 `DESIGN.md` 或 `data-schema.md`，避免 M3.5 闸门再次复发。

---

## 最重要的一条建议

**进入 S3 时，把 `registry_snapshot` 的"先读后选"原子性保证从抽象约束落到具体实现**——REQ-01 Node 2 验收明确要求"读取 registry、解析 default、选择版本、计算 record hash、生成 dispatch 必须来自同一份 registry snapshot"，但当前文档未指明实现方式（事务、copy-on-write、还是仅逻辑约束）。这是 registry 漂移防线的核心，建议在 M3.5 闸门之前就决定。

---

## 所需下一步动作

1. **编排者**：启动 S3 设计任务，把 F001/F002 写进 DESIGN.md 与 data-schema.md 的 Acceptance。
2. **S3 阶段**：完成 design/DESIGN.md、src/references/data-schema.md、src/strategies/registry.yaml、execution-guard 最小骨架 plan。
3. **M3.5 闸门**：在 S3 完成后调用 factory-reviewer 对 DESIGN + schema + registry + execution-guard skeleton plan 做闸门审查。
4. **M4a**：Ralph Loop 第一轮先做安全/验证底座（schema validator / registry validator / execution-guard skeleton / approval-gate skeleton / migration scaffold），不直接进入业务模块。

---

## 归档元数据

- 审查对象类型：B 类（方案类文档）
- 审查模式：battle round 2（聚焦 WARN 吸收核对）
- 上轮结论：WARN（B001 + M001-M005）
- 本轮结论：WARN（B001 + M001-M005 已吸收；新发现 F001/F002 minor + I001/I002 info）
- 进入下阶段：S3 设计（不进入 Ralph Loop）