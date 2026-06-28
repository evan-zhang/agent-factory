## 审查结论

**总体评级**：WARN
**置信度**：0.78
**审查对象**：B 类（方案/GRV）— `stock-picking` REQ-01.md 中的 Node 4（策略选择器，Node 2）+ 涉及的 Chokepoint 策略候选（Node 4 Chokepoint Strategy 章节、registry 设计、`chokepoint-strategy` 模块契约）
**审查时间**：2026-06-23
**使用模型**：newapi-openai/MiniMax-M3（factory-reviewer）
**审查范围**：REQ-01.md 全文 + serenity-skill（SKILL.md / lead-scanner.md / reverse-engine.md / references/thesis-risks.md）— 重点对照 Node 4（策略选择器）与 Node 4 Chokepoint Strategy 章节设计

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 事实准确性 | 4 | 未编造数据；引用 serenity 方法论为方法论来源，不混入战绩数字作运行依据；与 thesis-risks.md 风险侧一致 |
| 完整性（方案类） | 3 | Node 2（策略选择器）契约完整，但 Chokepoint 章节在"策略输出 → draft 契约"的衔接与"如何消费 lead-scanner 的 research 主题"上仍偏粗 |
| 可行性 | 3 | registry 原子化、版本解析、`custom_ref` 白名单这些都很扎实；但 Chokepoint v1 标 `experimental` + `allowed_callers: [manual]` 后，没有给出"退出 experimental 的明确条件" |
| 风险识别 | 4 | 显式区分"战绩资料只作参考，不进运行逻辑"是 REQ-01 的一个亮点；与 thesis-risks.md 的 5 类结构性风险呼应良好 |
| 边界明确性 | 4 | "不做什么"段落清晰；策略选择器不兜底、不融合、不排序、cron 不进 skill 都被反复强调 |
| 一致性 | 3 | Node 2（策略选择器）章节里"Node 2"和 Node 4 Chokepoint 章节里"Node 4"命名不统一（其实是 Node 2 / Node 4 切分口径问题，见 M003）；draft 契约与策略输出契约在"source_evidence 是否必经 evidence store"上有一处轻不一致 |
| 幻觉/方法论混入 | 4 | 没有把 Serenity 战绩数字（+122% / +630% 等）当作运行参数；显式声明"方法论进入策略模块，战绩只作参考" |
| 安全/风控默认 | 4 | experimental 只允许 manual 调用；dry_run 强制；registry snapshot 原子化避免漂移；custom_ref 拒绝自由文本与路径穿越 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| B001 | blocker | 命名/编号不一致 | REQ-01 §"2. 策略选择器" 与 §"4. Chokepoint Strategy" | 用户 task 写"Node 4 Chokepoint Strategy"，但 REQ-01 内部把"策略选择器"叫 **Node 2**，把 Chokepoint 列为 **Node 4**；mermaid 图里 C→D2 是 "Chokepoint Strategy" 而非"Node 4"。如不澄清，SOP 实现方会按 Node 2 还是 Node 4 写？两种编号代表"选择器"和"具体策略"是两层，**但 task 措辞"Node 4"在 REQ-01 里就是 Chokepoint 那个策略模块本身**，并不是选择器 | REQ-01: 流程图 C→D2, §2 标题"策略选择器", §4 标题"Chokepoint Strategy" | 在 REQ-01 顶部加一行"节点编号口径说明"：Node N 的统一是节点而非策略（Node 2 = 策略选择器；Node 4 流程图里其实指的是"Chokepoint 策略模块"作为 D2 那个分支）。或者把 Chokepoint 在流程图里直接画成 `C2[Chokepoint v0.1.0]`，在 §2/§4 之间加一句"§4 是 §2 选出来的 D2 分支策略"，让编号闭环 |
| M001 | major | 契约缺口 | REQ-01 §"2. 策略选择器" v1 输出契约 vs §"4. Chokepoint Strategy" | 策略选择器输出 `output_schema: draft_candidates.v1`；但 Chokepoint 章节说"输出优先进入 `research/_themes`，只有满足证据门槛才转 draft" — **`draft_candidates.v1` 没有覆盖 research → draft 的入口字段**。一个 Chokepoint 产物是 `theme_research.v1`（带 BOM、三高得分、break_conditions、uncertainty_level），另一个是 `draft_candidates.v1`（带 score、reason）；二者没在 §5 统一 Draft 候选里被显式定义转换路径 | REQ-01 §4 末段 + §5"统一 Draft 候选" 改进建议 | 在 §5 顶部加一个"中间产物 schema"层：`theme_research.v1`（Chokepoint 主输出，可选进入 draft）→ `draft_candidates.v1`（统一候选层）。策略选择器 v1 输出契约增加 `output_schema: draft_candidates.v1 \| theme_research.v1`，并在 §4 末尾写明 Chokepoint v0.1.0 的 `output_schema` 应是 `theme_research.v1`，由后续"draft-promoter"通用模块按门槛转换到 draft 候选。这把"什么时候算线索、什么时候算候选"在数据契约上分开 |
| M002 | major | 升级条件缺失 | REQ-01 §"2. 策略选择器" Chokepoint v0.1.0 registry 条目 | Chokepoint 标 `status: experimental` + `allowed_callers: [manual]`，但**没有任何条款定义"什么条件升到 active、允许 cron/sop 调用"**。如果没有退出条件，experimental 会一直 experimental（被长期锁死），或反之被人手动改成 active 而绕过审批 | REQ-01 registry 设计节 | 增加 `experimental_exit_criteria` 字段（自由结构但建议显式）：例如至少 N 次 manual run、无 critical thesis break 命中、source_evidence 覆盖率 ≥ X%、团队评审通过日期。配合 v0.1.0 → v0.2.0 升版的 version bump 规则（semver MAJOR.MINOR.PATCH 含义） |
| M003 | major | 输出契约与 serenity 既有纪律的张力 | REQ-01 §"4. Chokepoint Strategy" + serenity SKILL.md 输出规范 | SKILL.md 强制输出规范："个股分析 → 写入 `data/research/[market]/[code]/industry-chain.md` …文件首次无日期后缀，更新加日期"；`lead-scanner.md` 规定"行业/主题 → `data/research/_themes/[theme-name].md`"。**REQ-01 §4 只说"输出优先进入 `research/_themes`"但没继承日期后缀、索引更新、20 行摘要、T/A/R/O/C 淘汰规则的纪律**。这导致 Chokepoint 接入 stock-picking SOP 时，研究文档的"事实版本"和"主题索引"无法与其他渠道的 research 输出对齐 | SKILL.md 输出规范 §1-4 + REQ-01 §4 | 在 §4 顶部加一节"输出契约（与 serenity SKILL.md 保持一致）"：写明（a）所有 theme 输出进 `data/research/_themes/[name].md` 并同步 `_index.md`；（b）个股输出进 `data/research/{market}/{code}/industry-chain.md`；（c）淘汰规则沿用 T/A 阶段不留目录、R 阶段存 taroc.md、O/C 阶段建目录 + taroc.md；（d）摘要 ≤20 行；（e）写作失败推送告警不发摘要。这些是 serenity 已经定型的纪律，集成时应整段引用而不是重写 |
| M004 | major | 共识信号/伪线索降级规则未进入策略契约 | REQ-01 §"4. Chokepoint Strategy" + lead-scanner.md 阶段三 | lead-scanner.md 阶段三的"黄金/噪音/共识/无效"四象限中，"共识"信号被明确降级（DRAM 暴涨、Ayar 主线投资都是强 B + 大 A → 降级）。**REQ-01 §4 Chokepoint 章节没有把这条降级规则写进 draft 过滤契约**，因此同一个 lead-scanner 跑出来的"共识降级线索"可能在 Chokepoint 策略层被无差别重跑 | lead-scanner.md 阶段三表格 + REQ-01 §4 改进建议 | 在 §4 写明：Chokepoint v0.1.0 必须消费 lead-scanner 输出的 `signal_class` 字段（gold/noise/consensus/invalid），且 `consensus` 与 `noise` 信号**自动降权或直接出 research 而不进 draft**。否则 lead-scanner 的核心价值（不停在共识处）在策略层被消解 |
| M005 | major | "邻居节点"回路未进入 SOP 链 | REQ-01 §"4. Chokepoint Strategy" + reverse-engine.md | reverse-engine.md 第 1 步"定位"→ 第 2 步"逆向验证"→ 第 3 步"横向扩展"明确说："有时一只平庸的股票，最大的用处是当路标"。**但 REQ-01 的 SOP 链里没有"逆向 → 邻居 → 正向"的回流口**：candidate 入池后，如果本体评分是"伪节点/路标"，应该自动触发 `reverse-engine` 在候选池边缘挖邻居节点，但目前 §6-§9 都是围绕"本体"做复选/追踪/建仓 | reverse-engine.md 流程图 + REQ-01 §6-§9 | 在 §6 候选复选模块里加一个分支：`validation_result = "本体伪节点但路标价值高"` 时，自动产生一条 `neighbor_scan_request`，走 `reverse-engine.md` 流程，并把邻居节点作为新的 draft 候选回灌。这样 stock-picking 不只"一只股走到底"，也能复用 Chokepoint 的横向扩展能力 |
| m001 | minor | terminology | REQ-01 全文 | `universe` 这个词在中英文技术文档里同时存在"投资范围/股票池"两个意思；REQ-01 §0 v1 入口契约里 `universe: market \| sector:{name} \| watchlist:{name} \| candidates:{market}` 没有明确 `sector` 是按 GICS 行业代码、自定义标签、还是 universe provider 的标准 | REQ-01 §0 v1 入口契约 | 在 `universe` 字段下加注释：v1 仅接受 `market`（全市场）、`watchlist:{name}`（来自 white-list 配置），`sector` 与 `candidates` 推迟到 S2。S3 再决定 sector 标签体系 |
| m002 | minor | 一致性 | REQ-01 §0 验收标准 vs §2 拒绝码 | §0 验收写"非原子请求必须在入口层失败"，但 §2 拒绝码里没有 `non_atomic_request` 这个码。意味着多策略/多市场请求到 §2 才会被拒，而不是按 §0 验收在 §0 就拒 | REQ-01 §0 验收 + §2 拒绝码 | 在 §2 拒绝码表顶部加 `non_atomic_request` 并在备注里写"应在 Node 0 入口层就拒；出现在 Node 2 说明 Node 0 契约被绕过，需要审计告警" |
| m003 | minor | 命名 | REQ-01 §2 v1 输入契约 | `strategy.id` 和 `strategy_id` 在不同章节里混用：§0 用 `strategy_id`，§2 用 `strategy.id`（带点的 YAML 风格），§4 又回到 `strategy_id` | REQ-01 §0/§2/§4 | 统一为 `strategy_id`（更便于在日志、audit、API 路径里作为单一 key）。如果保留 YAML 嵌套，§2 顶部加一句"本章 `strategy.id` 等价于 §0/§4 的 `strategy_id`" |
| m004 | minor | 数据契约 | REQ-01 §5 改进建议 | §5 写"增加 `candidate_id`、`strategy_id`、`thesis_summary`、`source_evidence`、`negative_evidence`、`expires_at`"，但 `candidate_id` 的生成规则、是否带 `strategy_id` 前缀（`cpt_<strategy>_<code>_<yyyymmdd>`）、去重键都没说 | REQ-01 §5 改进建议 | 在 §5 加 `candidate_id` 命名规则段：建议格式 `<strategy_prefix>_<market>_<code>_<yyyymmdd>`，同一股票同一日多策略允许多 candidate；去重键 = `(market, code, strategy_id, thesis_hash)`，thesis_hash 由 thesis_summary + source_evidence 计算 |
| m005 | minor | 安全/审计 | REQ-01 §2 registry 设计与 §13 Evidence Store | §2 强调"registry snapshot 原子化、record hash 防漂移"，§13 Evidence Store 写"分层 source_url/source_type/claim/observed_at/confidence" — **两者之间没有引用关系**：策略选择器 dispatch 时，是否记录 evidence store 的引用？audit 链是否能从 strategy_dispatch 追到 evidence？ | REQ-01 §2 + §13 | 在 §2 的 `strategy_dispatch` 里增加可选 `evidence_ref: string \| null`，并写明"成功 dispatch 必须把 evidence_ref 写入 audit.evidence_chain；evidence_ref 为 null 时拒绝（v1 强制）"。把"策略选择 → 证据"在审计上连起来 |
| m006 | minor | 边界 | REQ-01 §4 Chokepoint 缺点段 | §4 写"执行成本高，联网搜索和产业链判断更重"，但没有给出"成本上限 / 搜索次数上限 / 单次 run 时长上限"。v1 标 `allowed_callers: [manual]`，但 manual 跑没有护栏时，AI 可能一次调 200 次搜索 | REQ-01 §4 缺点 + §2 registry | 在 Chokepoint registry 条目里加 `resource_budget: { max_searches: 50, max_runtime_minutes: 15, max_evidence_refs: 20 }`，与 §2 通用策略 registry schema 保持一致。experimental 阶段上限更严格 |
| I001 | info | 一致性 | REQ-01 §2 拒绝码表 | 拒绝码 13 个，但 `dry_run_required` 和 `registry_invalid` 实际语义有重叠（registry schema 校验失败 = registry invalid；要求 dry_run = dry_run_required）。可以在 v1 把 `registry_invalid` 拆成 `registry_schema_invalid` 与 `registry_record_missing` 更明确 | REQ-01 §2 拒绝码 | 拆分建议放在 S2 细节时再做，v1 接受 |
| I002 | info | 文档结构 | REQ-01 流程图 | mermaid 图里 `B0[HEARTBEAT_OK 记录跳过原因]` 是个不错的设计，但在 §0-§13 的文字描述里没有专门定义"HEARTBEAT_OK"事件的结构、写入位置、消费者 | REQ-01 mermaid | 增加 §1.5 小节（或并入 §0 末）专门定义 heartbeat event schema：`{ ts, request_id, correlation_id, decision, reason, ... }`，并指明由 Node 1 写、由 Gateway cron 与 audit 消费 |
| I003 | info | 方法论边界 | REQ-01 全文 | REQ-01 没有引用 `case-study.md` 里的"盲扫→Ayar 真实范例"。对一个"已收编 serenity 框架"的 SOP 来说，案例应该被链接，便于后续实现者理解 lead-scanner 与六步框架的衔接 | REQ-01 §4 改进建议 | 在 §4 加一行"参考实现案例：`serenity-skill/case-study.md`"，并说明该案例对应到 REQ-01 的 Node 1→Node 2→Chokepoint→draft 流程是哪一段 |
| I004 | info | 风险/局限 | REQ-01 §4 Chokepoint 缺点 vs thesis-risks.md | thesis-risks.md 列出 5 类结构性风险（单路径依赖 / 微盘流动性 / 不可验证背景 / 存活者偏差 / 集中度与保证金）。REQ-01 §4 缺点段只点出了"执行成本 + 误判技术路径 + 公开战绩只能作参考"3 条，**没有把前 4 条作为框架的"固有结构性风险"列入** | REQ-01 §4 + thesis-risks.md | 在 §4 加一节"框架固有风险"小节，把 thesis-risks.md 的 5 条用 1-2 行引述，并写明"这些是框架层面的，不是 Chokepoint 模块的 bug；stock-picking SOP 应在候选追踪与持仓监控层面对冲" |
| I005 | info | 业绩处理 | REQ-01 全文 | REQ-01 没有显式说明"PhotonCap +122% 1Y 这类第三方校准数据进不进 SOP"。建议在 §4 备注里加一句"v1 不消费任何业绩数据，包括 Serenity 自报 + PhotonCap 第三方 + 关注度信号；业绩只作人读参考" | REQ-01 §4 + thesis-risks.md | v1 明确"零业绩数据进入运行逻辑"作为防幻觉护栏 |

---

**维度专项观察**

### 策略选择器（Node 2）— 评估
- **registry 原子化 + record hash**：防漂移的细节很到位，能挡住"dispatch 过程中 registry 被改"这种隐 bug。
- **`custom_ref` 白名单 + 拒绝路径穿越**：防止 AI 拿到一个自由文本策略名就乱跑，是真的安全护栏。
- **拒绝码表 13 个**：覆盖度足够，能让 Node 0-1-2 之间形成可机器解释的失败传递链。
- **缺口**：`experimental_exit_criteria` 缺失（M002）；策略 ↔ Evidence Store 审计链不闭环（m005）。

### Chokepoint 策略候选（Node 4 Chokepoint Strategy）— 评估
- **核心方法论移植正确**：BOM 拆解 → 三高筛选 → 时机判断 → 龙头定位 → 崩塌条件五步可解耦为算法步骤；lead-scanner.md 解决"线索从哪来"，reverse-engine.md 解决"从个股反推"，与主框架闭环。
- **风险隔离做得好**：显式说"公开战绩类资料只能作参考，不能变成运行逻辑"，这是对 Serenity 类信息源最正确的处理。
- **缺口**：
  - 与 serenity 既有输出规范（日期后缀、索引更新、20 行摘要、淘汰规则）没有完整继承（M003）；
  - lead-scanner 的"共识降级"信号在 Chokepoint 策略层没有保护机制（M004）；
  - reverse-engine 的"邻居节点"回路没进 SOP 链（M005）；
  - 框架固有 5 类风险没在 §4 显式列出（I004）；
  - 资源护栏（搜索次数 / 时长）没写进 registry（m006）。

### B 类（方案/GRV）专项
- **可行性**：registry + 原子化版本解析 + dry_run 强制，落地路径清楚；Chokepoint v1 experimental 阶段 manual-only 是合理最小化。
- **完整性**：Node 2 完整度高；Chokepoint 章节在"输出契约与现有研究纪律的衔接"上有缺口。
- **风险**：见上方 M001-M005、I004-I005。
- **边界**："不做什么"段落写得很清楚；策略选择器"不兜底、不融合、不排序"被显式拒绝。
- **一致性**：节点编号 B001 是最显眼的歧义；strategy.id vs strategy_id 命名不统一（m003）；candidate_id 生成规则缺失（m004）。

---

**最重要的一条建议**

把 **Chokepoint 策略输出契约** 在 §5 顶部从"统一 draft"拆成"中间产物 + 统一候选"两层（`theme_research.v1` → `draft_candidates.v1`），并在 §2 registry 把 Chokepoint 的 `output_schema` 显式标为 `theme_research.v1`，由一个独立的"draft-promoter"模块按门槛转换 — 这是唯一一处不修就让 v1 落地时 lead-scanner / reverse-engine / 主框架三方契约互相打架的根因。其他都是命名/审计/资源护栏的增量修补。

---

**Acceptance Criteria（建议 v1 通过前必须满足）**

AC-1. **节点编号口径闭环**：在 REQ-01 顶部或 §2 顶部加 1 段说明，明确"Node 2 = 策略选择器；Node 4 流程图里的 D2 框 = Chokepoint 策略模块（一个被选中的具体策略），不是 §2 那个选择器"。消除 B001。
AC-2. **双 schema 显式分离**：在 §5 顶部定义 `theme_research.v1` 与 `draft_candidates.v1` 两个 schema 的字段差异、转换规则、转换责任模块；Chokepoint v0.1.0 registry 条目的 `output_schema` 必须改为 `theme_research.v1`。消除 M001。
AC-3. **experimental 退出条件**：`experimental_exit_criteria` 字段在 Chokepoint v0.1.0 registry 条目里写出至少 3 条可验证条件（例如：≥10 次 manual run、0 次 critical thesis_break、自动验证 evidence_ref 覆盖率 ≥ 60%、团队评审通过日期）。消除 M002。
AC-4. **继承 serenity 输出规范**：§4 Chokepoint 章节加一节"输出契约（与 serenity SKILL.md 一致）"，逐条引用（日期后缀、_index.md 同步、≤20 行摘要、T/A/R/O/C 淘汰规则、写入失败告警）。消除 M003。
AC-5. **lead-scanner 共识降级保护**：在 §4 写明 Chokepoint 必须消费 lead-scanner 输出的 `signal_class` 字段，且 `consensus`/`noise` 信号默认出 research 而不进 draft。消除 M004。
AC-6. **reverse-engine 邻居节点回流**：在 §6 候选复选模块加一条分支：`本体评分 = 伪节点/路标` 时自动产生 `neighbor_scan_request`，走 `reverse-engine.md` 流程并把邻居作为新 draft 回灌。消除 M005。
AC-7. **资源护栏进 registry**：在 Chokepoint v0.1.0 registry 条目里加 `resource_budget: { max_searches, max_runtime_minutes, max_evidence_refs }`，并写明超出时 fail closed。消除 m006。
AC-8. **审计链 evidence_ref 闭环**：在 §2 `strategy_dispatch` 加 `evidence_ref: string | null`，v1 强制非 null；audit 链能从 dispatch 追到 evidence store。消除 m005。
AC-9. **术语统一**：`strategy_id` 全文统一（m003）；`candidate_id` 命名规则与去重键在 §5 显式定义（m004）；`non_atomic_request` 加入 §2 拒绝码（m002）。
AC-10. **框架固有风险显式化**：在 §4 加"框架固有风险"小节，引述 thesis-risks.md 的 5 类结构性风险，并写明 stock-picking SOP 在哪些节点对冲（I004）。
AC-11. **零业绩数据进运行逻辑**：在 §4 备注里写明 v1 不消费任何业绩数据（Serenity 自报 / PhotonCap 第三方 / 关注度信号），只作人读参考（I005）。
AC-12. **HEARTBEAT 事件 schema 显式定义**：增加 §1.5（HEARTBEAT event schema），明确字段、写入位置、消费者（I002）。

---

**verdict 决策依据**

- 没有事实错误/幻觉（评分 4）→ 不上 BLOCK/FAIL。
- 缺 1 个 B 类必填字段（输出契约双 schema 分离）→ M001 是 major。
- Node 编号歧义在 SOP 实现层会立刻踩坑 → B001 是 blocker（必须先解决才能进入实现）。
- 其他 majors 都是契约/护栏级增量，可在 S2-S3 滚动修复，不阻塞评审通过。
- 综合：**WARN**（修正 B001 + AC-1 ~ AC-3 后可升级为 PASS）。
