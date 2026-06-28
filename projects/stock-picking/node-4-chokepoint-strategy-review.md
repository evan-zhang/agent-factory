# Node 4 Review Context — Chokepoint 策略插件

## Project

`stock-picking` 正在从单体 skill 重构为模块化 SOP 编排层。

- Node 0（外部触发入口）：原子请求，v1 拒绝 multi/mixed/full/monitor/dry_run=false（已确认）
- Node 1（交易日与运行上下文）：输出 `run_context.decision`，日历 unknown 必须 override（已确认）
- Node 2（策略选择器）：registry/router，输出 `strategy_dispatch`，单策略单版本（已确认）
- **Node 4（本评审）：Chokepoint Strategy 插件**

## Node 4 To Review

### 基线文本（REQ-01.md §4）
- serenity/chokepoint 方法论已收集：
  - 异常信号扫描
  - A 类趋势量级校验
  - BOM 拆解
  - 三高验证（高增长→高壁垒→高利润）
  - 龙头定位
  - 崩塌条件
- 还没有作为正式 strategy skill 独立实现
- 优点：补 TAROC 短板，发现非共识卡脖子节点
- 缺点：执行成本高、误判技术路径整条失效、人物资料只作参考
- 建议：作为独立 `chokepoint-strategy`，输出 `research/_themes` 优先，只有满足证据门槛才转 draft；每条线索带 `break_conditions` 和 `uncertainty_level`

### 源材料
- `~/.agents/skills/serenity-skill/SKILL.md` — 卡脖子选股框架（核心方法论）
- `~/.agents/skills/serenity-skill/lead-scanner.md` — 异常扫描引擎
- `~/.agents/skills/serenity-skill/reverse-engine.md` — 逆向引擎
- `~/.agents/skills/serenity-skill/references/thesis-risks.md` — 框架结构性风险与批评

---

## 一、Boundary（职责边界）

### Node 4 是什么

**Chokepoint Strategy 是一个 strategy plugin（Layer 2 策略模块），不是 SOP 节点。**
- 输入：Node 2 派发的 `strategy_dispatch` + `run_context` + `universe` + `dry_run`
- 输出：统一 draft schema（`draft_candidates.v1`）或 `research/_themes` 主题分析
- 行为：执行 serenity/chokepoint 六步流程（BOM 拆解→三高验证→龙头定位→崩塌条件），或调用 lead-scanner 扫描候选线索

### Node 4 不做什么

| 不做 | 为什么 |
|------|-------|
| 不做 registry 路由 | 属于 Node 2 职责，重复会破坏单点真相 |
| 不做日历判断 | Node 1 已输出 `run_context`，直接消费 |
| 不做多策略融合/排序 | 单策略只产自己观点，融合在 SOP 外层 |
| 不做"看一只股给不给买"的研究终点输出 | 输出"研究起点 + 证据链"，不输出买卖指令 |
| 不做持仓监控/止损 | 属于 `position-monitor` 模块 |
| 不把 serenity 战绩/履历当运行逻辑 | 框架可参考，credentials 不进入 dispatch 决策（thesis-risks.md §3） |
| 不接受用户自由文本描述策略 | 必须用 Node 2 的 `custom_ref`，禁止路径穿越 |
| 不直接写 `candidates_{market}.csv` | 只输出 draft，复选入池由 `selection-validation` 负责 |
| 不替用户决定 `tracking_horizon` | 由本节点建议并写入 draft，但 `position-tracker` 才是消费方 |

### Node 4 与其它节点的关系

```
Node 0 (入口原子请求)
   ↓
Node 1 (run_context.decision=proceed)
   ↓
Node 2 (strategy_dispatch → chokepoint@0.1.0, entrypoint)
   ↓
[Node 4] Chokepoint Strategy
   ├─ 分支 A: lead-scanner 主动扫描 → themes
   ├─ 分支 B: reverse-engine 逆向个股 → themes/draft
   └─ 分支 C: SKILL.md 六步深挖 → draft
   ↓
统一 draft schema (draft_candidates.v1)
   ↓
Node 5 复选 / Node 8 追踪（消费 draft，不回调本节点）
```

**关键边界**：Node 4 输出 draft 后不主动调用后续节点。SOP 编排层决定何时启动 Node 5/8/9/11。

---

## 二、Contracts（接口契约）

### v1 输入契约（来自 Node 2 dispatch）

```yaml
request_id: uuid                # 透传
correlation_id: uuid            # 透传
strategy_dispatch:              # 来自 Node 2，不可变
  strategy_id: chokepoint
  strategy_version: 0.1.0
  entrypoint: strategies.chokepoint:run
  output_schema: draft_candidates.v1
  registry_version: string
  registry_record_hash: string
  policy_flags: []

run_context:                    # 来自 Node 1，只读
  decision: proceed
  market: US | HK | CN
  market_session: regular | ...
  calendar_checked_at: ISO8601

run_mode: discovery | validation | tracking
universe:
  scope: market | sector:{name} | watchlist:{name} | candidates:{market}
  filters: {sector?, market_cap_min?, market_cap_max?, exclude_list?}
dry_run: true                   # v1 强制 true
budget:
  max_searches: integer         # 防止无界联网
  max_runtime_seconds: integer
  max_drafts: integer
risk_profile:
  max_position_size_pct: number # 仅用于评分参考，不下指令
  liquidity_floor: string       # "ADV_USD_1M" 之类
```

### v1 输出契约（draft_candidates.v1）

每个 draft 必须包含：

```yaml
draft_id: uuid                  # 本次 run 内唯一
candidate_id: null              # 入池前为空
strategy_id: chokepoint
strategy_version: 0.1.0
produced_at: ISO8601
run_id: uuid                    # 关联 request_id

market: US | HK | CN
ticker: string
company_name: string
exchange: NYSE | NASDAQ | HKEX | SSE | SZSE
currency: USD | HKD | CNY

thesis:
  one_liner: string             # ≤ 120 字符
  chokepoint_layer: integer     # BOM 树第几层（1=终端，向上递增）
  upstream: [string]            # 上游层供应商
  downstream: [string]          # 下游层客户
  chokepoint_type: string       # 物料/工艺/设备/认证/数据
  three_high:
    growth_score: 1-5
    moat_score: 1-5             # 5维壁垒打分（技术/认证/规模/资源/网络）
    margin_score: 1-5
    three_high_pass: boolean    # 增长≥3 且 moat≥3 且 margin≥2

  lead_source: string           # lead_scanner/reverse_engine/manual
  evidence:                     # 证据链
    - source_id: string
      source_type: primary | secondary | community | ai_inference
      source_url: string | null
      claim: string             # ≤ 200 字符
      observed_at: ISO8601 | null
      confidence: 0.0-1.0

  negative_evidence:            # 负面证据（同结构）
    - source_id: string
      claim: string
      observed_at: ISO8601 | null

  lead_signals:                 # 异常信号（如来自 lead-scanner）
    - signal: price | lead_time | capital | patent | talent | regulation
      strength: 0.0-1.0
      evidence_url: string | null

  trend_anchor:                 # A 类量级校验
    trend_type: tech_transition | penetration_inflection | policy_mandate | geopolitics
    trend_size: string          # "TAM $XB by 2028"
    trend_persistence: short | medium | long

  break_conditions:             # 崩塌条件（强制 ≥1）
    - condition: string        # 例: "CoWoS-S 替代光互连被 NVDA 公开采用"
      trigger_evidence: string  # 触发后需要观察的信号
      severity: thesis_breaking | position_breaking

  uncertainty_level: low | medium | high
  tracking_horizon: trading_days:integer  # 建议追踪窗口

pricing:
  reference_price: number | null
  ref_price_as_of: ISO8601 | null
  market_cap: number | null
  avg_daily_volume_usd: number | null

risk_flags:                     # 框架级风险
  - micro_cap_stampede_risk: boolean
  - single_path_dependency: boolean  # thesis-risks.md §1
  - data_provenance_weak: boolean    # 一手证据 < 2 条时
  - consensus_overlap: boolean       # 与其它策略/公开共识重合
```

### v1 主题级输出（不进 draft，先进 research）

当 lead-scanner 扫描产出主题级分析时（不是具体 draft），写入：

```
data/research/_themes/<theme-name>.md
data/research/_themes/<theme-name>-<YYYY-MM-DD>.md  (更新)
```

并在 `_index.md` 加索引。**主题级输出必须有"何时转 draft"的升级条件**，否则永远停在主题层。

### v1 强制行为

- `dry_run: false` 一律拒绝（Node 0 已被拒绝，Node 4 仍要二次防御）
- `correlation_id` 必须透传到 evidence 记录和输出文件
- 任何 draft 写入前必须通过 evidence 阈值门控（见下文 §3）
- `break_conditions` 为空或 `uncertainty_level=high` 且 `tracking_horizon` 未给 → 拒绝写入 draft，落入 research 观察池
- 联网搜索必须真实执行；搜不到标"未发现信号"，禁止用旧记忆补全
- `policy_flags` 含 `no_buybox` 时禁止输出"建议入场价"

---

## 三、Evidence Thresholds（证据门槛）

Chokepoint 框架本身是"研究起点生成器"，但 Node 4 必须防止它把噪音包装成 thesis。下表是 v1 强制门控。

### 3.1 升级到 draft 的最低证据门槛

| 维度 | 最低要求 | 不满足的处理 |
|------|---------|-------------|
| 一手来源数 | ≥ 2 条 | 留在 research 观察池 |
| 证据类型 | ≥ 1 条 `primary`（财报/招股书/官方公告/专利/工信部文件） | 留在 research 观察池 |
| 负向证据 | ≥ 1 条（强制负面搜索） | 必须显式标注"未发现负面证据"并标高不确定性 |
| 三高通过 | `three_high_pass=true`（增长≥3 且 moat≥3 且 margin≥2） | 落回 lead 阶段，重新验证 |
| 崩塌条件 | ≥ 1 条结构化 `break_conditions` | 拒绝写入 draft |
| 不确定性 | `uncertainty_level` 必须填写 | 拒绝写入 |
| 供应商集中度 | BOM 节点供应商数 ≤ 5 才记为"卡脖子候选"；>5 时降级为"普通节点" | 不写 draft |
| 趋势量级 | A 类趋势必须有可引用的市场规模/政策/技术路线图 | 仅 ai_inference 支撑的趋势 → 拒绝 |

### 3.2 升级到 candidates 复选窗口的额外门槛

| 维度 | 要求 |
|------|-----|
| Lead signal 强度 | 至少一个 lead_signals.strength ≥ 0.6 |
| 趋势持久性 | `trend_persistence` ≠ short |
| 流动性 | `avg_daily_volume_usd` ≥ `risk_profile.liquidity_floor`（默认 1M USD） |
| 单路径依赖披露 | `single_path_dependency=true` 时必须显式声明替代技术路线监控点 |
| 微型股提示 | `market_cap < 500M USD` 时强制 `micro_cap_stampede_risk=true`，并加 warn 标签 |

### 3.3 升级到 target pool 的建议（由下游模块消费，本节点只标）

- 三高评分 ≥ 4/5
- 趋势持久性 = long
- 至少 1 条 `break_conditions` 已被反向证据 weaken（说明主要风险已被市场吸收）
- 12 周内未被本框架"标红"（catalog of red flags）

### 3.4 异常扫描（lead-scanner）信号筛选

每条 lead signal 落进候选前必须经过 A×B 交叉过滤：
- B 信号 = 异常强度（来自价格/交货期/资本/专利/人才/监管）
- A 信号 = 系统性趋势支撑（tech_transition / penetration / policy / geopolitics）
- 只有 A 与 B 同时成立的才升级

> 引用 `lead-scanner.md` §三：黄金线索（B 强 A 强）/ 噪音（B 强 A 弱）/ 共识（B 弱 A 强）/ 无效（B 弱 A 弱）。
> Node 4 在 v1 阶段只输出"黄金 + 共识"两类（共识降级为观察），不直接生成 draft。

---

## 四、Risks（Chokepoint 框架的结构性风险与 Node 4 防御措施）

来源：`references/thesis-risks.md`

### 4.1 单路径依赖（Critical）

**风险**：整套 CPO/硅光 thesis 假设光互连胜出。如果 NVDA 或其他超大规模厂商转向薄膜铜缆，或 TSMC/Intel 集成掉离散光器件层，**整个 Layer 3-6 同时崩盘**。

**Node 4 防御**：
- 强制每条 draft 填 `single_path_dependency` 字段
- 当 `single_path_dependency=true` 时，必须在 `break_conditions` 至少列出 1 条替代技术路线监控点
- 当监控点出现"风险放大"信号时（人工或后续模块判定），draft 状态由 `active` 转 `watching`
- 强制要求 trend_anchor.trend_size 必须 ≥ "TAM $1B by 2028"，避免在虚假 TAM 上押注单路径

### 4.2 微型股流动性踩踏风险

**风险**：Serenity 公开 40 万粉丝，X-FAB 单日 +76% 即是典型案例。本 SOP 用户（Evan）虽无此流量，但任何公开发布（Discord/Telegram）都会引入类似效应。

**Node 4 防御**：
- `market_cap < 500M USD` 强制 `micro_cap_stampede_risk=true`
- 流动性门槛 `avg_daily_volume_usd ≥ 1M USD` 是一票否决（v1 默认）
- draft 不输出"建议入场价"区间，只给 `reference_price` 作为参考（除非 `policy_flags` 含 `price_guidance`）
- 用户最终入场价由 `target_pool` 的人工确认步骤决定，不在本节点完成

### 4.3 不可验证的履历/战绩

**风险**：方法论的可信度被人格光环放大，credentials 全为自报。

**Node 4 防御**：
- 任何来源是"Serenity said / PhotonCap said"的 claim 标 `source_type=community`、confidence ≤ 0.5
- 框架判断只看 evidence 链，不看背书（thesis-risks.md §3 明确："Judge the framework on its own merits"）
- registry 里 `owner: stock-picking`，不写 `based_on: serenity`，避免把外部人物信誉耦合进 dispatch 决策

### 4.4 幸存者偏差

**风险**：公开战绩偏向赢家，亏的 thesis 经常被悄悄删除。

**Node 4 防御**：
- 任何 draft 必须保留 `negative_evidence` 字段
- 失败 case 也要写入 `data/research/_themes/<theme>-<date>-rejected.md`，原因结构化
- v1 阶段要求 `data/research/_themes/_index.md` 维护"在册主题 vs 淘汰主题"双向表，避免淘汰无痕

### 4.5 集中度与杠杆

**风险**：原作者跑 ~1.4x 杠杆 + 集中持仓；不适合 Evan 的"个人投资者 + dry_run + 人工确认"画像。

**Node 4 防御**：
- Node 4 不输出杠杆建议；不输出仓位金额
- `risk_profile` 只是"评分参考"，不是"建仓指令"
- 集中度（portfolio correlation）由下游 `position-monitor` 处理，不在本节点

### 4.6 技术路径误判（行业认知门槛）

**风险**：framework 的真正 edge 是"在实验室摸过器件"（PhotonCap 标准）。Evan 没有光子学/半导体工程背景，机械套用会放大误判概率。

**Node 4 防御**：
- v1 把 Chokepoint 在 registry 标 `status: experimental`、`allowed_callers: [manual]`，禁止 cron/sop
- Node 4 输出强制 `uncertainty_level`，高不确定性时主动建议"列入观察"而非"进入复选"
- 强烈鼓励在 `evidence` 中保留 `source_type=primary` 的物理层证据（专利文本、IEEE 论文、设备 spec sheet），不全是二手报道

### 4.7 与 TAROC 的重复命中

**风险**：TAROC 跑热门赛道，Chokepoint 跑卡脖子节点，但同一只股票可能被两个策略都覆盖。

**Node 4 防御**：
- 同一 ticker 允许多条 strategy thesis 并存，由 SOP 编排层聚合
- 当 `consensus_overlap=true`（TAROC 也在看），chokepoint 输出的 confidence 必须低于 0.7，避免双策略叠加制造虚假高信心
- 聚合视图由下游复选模块生成，本节点不重复实现

### 4.8 AI 联网搜索的诚实性

**风险**：lead-scanner 要求"必须真实联网搜索，搜不到标'未发现信号'"，但 LLM 容易"用旧记忆补全"。

**Node 4 防御**：
- 任何 evidence 必须带 `source_url` 或显式标 `claim=unverified`
- 当搜索预算耗尽（`budget.max_searches` 用完）时，未完成的 lead 必须显式标 `partial_scan=true`
- 输出文件中加 disclaimer："本节点为研究起点生成器，不构成投资建议；所有 claim 需独立验证"

---

## 五、Acceptance Criteria（验收标准）

### 5.1 边界（Boundary）
- [ ] Node 4 是策略插件，调用入口来自 Node 2 的 `strategy_dispatch`
- [ ] Node 4 不重新实现日历判断、registry 路由、复选逻辑、持仓监控
- [ ] Node 4 输出 draft 不直接写 `candidates_{market}.csv`
- [ ] Node 4 不输出"建议入场价"区间（除非 `policy_flags` 含 `price_guidance`）
- [ ] Node 4 不输出杠杆或仓位金额

### 5.2 契约（Contract）
- [ ] 输入必须透传 `request_id` / `correlation_id`，不断审计链
- [ ] `run_context.decision != proceed` 时立即拒绝，不进入流程
- [ ] `dry_run=true` 强制；收到 `dry_run=false` 必须 fail closed
- [ ] draft 全部字段按 `draft_candidates.v1` schema 输出
- [ ] `strategy_id=chokepoint` / `strategy_version=0.1.0` 必须从 dispatch 读取，不允许硬编码
- [ ] 主题级输出路径符合 `data/research/_themes/...` 规范

### 5.3 证据门槛（Evidence Threshold）
- [ ] 一手来源 ≥ 2 条才能升 draft
- [ ] 至少 1 条 `source_type=primary` 才能升 draft
- [ ] 强制执行负面搜索，无结果时显式标注
- [ ] `break_conditions` ≥ 1 条结构化条目才能升 draft
- [ ] 供应商集中度 ≤ 5 才能记为卡脖子候选
- [ ] A×B 交叉过滤在 lead-scanner 阶段强制

### 5.4 风险防御（Risk）
- [ ] `single_path_dependency=true` 时强制列出替代技术路线监控点
- [ ] `market_cap < 500M USD` 强制 `micro_cap_stampede_risk=true`
- [ ] 流动性 < `risk_profile.liquidity_floor` 一票否决
- [ ] 失败 case 写入 `_index.md` 双向表，淘汰有痕
- [ ] 高不确定性 draft 主动建议"观察"而非"入池"
- [ ] `consensus_overlap=true` 时 confidence < 0.7
- [ ] registry `status=experimental` / `allowed_callers=[manual]`，cron/sop 拒绝

### 5.5 可审计性（Auditability）
- [ ] 每次 run 写 `audit.json`，含 `request_id` / `correlation_id` / `dispatch_hash` / `produced_at` / `budget_used`
- [ ] `evidence` 链可独立回放：每个 claim 可追溯到 source_url 或 source_id
- [ ] `negative_evidence` 与正面 thesis 同级保存
- [ ] draft 拒绝原因结构化（`reject_code` / `reject_reason`），不能静默丢弃

### 5.6 升级路径（Path to Maturity）
- [ ] v1 阶段 Chokepoint 仅 manual 调用，禁止 cron/sop
- [ ] 当 6 个月内 manual 调用 ≥ 10 次且未触发任何 `break_conditions` 重大修订时，进入 v1.1 评审
- [ ] v1.1 才考虑支持 `tracking` run_mode 与 `validation` run_mode
- [ ] v2 才考虑开放给 `sop` 调用（多策略编排场景）
- [ ] 任何"自动买入"路径都先经过 `position-monitor` 的 dry-run 验证与人工确认

### 5.7 与 serenity 资料的引用纪律
- [ ] `SKILL.md` / `lead-scanner.md` / `reverse-engine.md` 作为**方法论参考**进入策略实现
- [ ] `references/thesis-risks.md` 作为**框架风险档案**进入策略实现的防御设计
- [ ] **不**将 serenity 战绩/履历/具体 call 复制到 dispatch 决策、registry metadata 或 dry-run 默认值
- [ ] 任何引用 serenity 内容的位置都注明"framework reference only, not a signal to copy"

---

## 六、Independent Proposer Comments（独立提案人意见）

### 6.1 三个开放问题，请决策方回答

1. **Chokepoint 是否需要在 v1 强制 `market=US`？**
   - 理由：serenity 的案例库（AXTI/RPI/XFAB/Coherent）几乎全在美股。CN/HK 市场的卡脖子节点拓扑不同（更多政策/认证驱动，少市场化技术跃迁）。
   - 建议：v1 仅 `market: US`，v1.1+ 再扩展。

2. **lead-scanner 触发频率与预算上限**
   - 建议：v1 manual 调用每次 `max_searches=30` / `max_runtime_seconds=300` / `max_drafts=10`
   - 触发时机：用户显式发起"扫描一次"或"扫描 watchlist"

3. **当 lead-scanner 黄金线索与既有 draft 候选重合时，Node 4 应该 update 旧 draft 还是新增？**
   - 建议：update 旧 draft（保留 `produced_at` 历史链），避免 draft 数量爆炸
   - 落地：draft 加 `previous_draft_id` 字段

### 6.2 我不同意 REQ-01 草案的两点

1. **"作为独立 chokepoint-strategy"** — 同意拆模块，但反对 v1 就给独立 skill。建议 v1 把 Chokepoint 作为 `stock-picking` 内的一个 strategy plugin（Node 4 内部模块），待 6 个月 manual 跑稳后再考虑提升为独立 skill。**理由**：v1 独立 skill 意味着独立注册、独立调度、独立 owner，与"先观察再扩展"的实验性定位矛盾。

2. **"输出优先进入 research/_themes，只有满足证据门槛才转 draft"** — 同意主流程，但建议补一条：**主题级输出必须带"何时升级为 draft"的 trigger 条件**。否则研究主题会无限堆积，没有回路回到 SOP。建议在主题 markdown 末尾加 `## Upgrade Triggers` 段。

### 6.3 三个被 REQ-01 漏掉的风险

1. **模型失配风险**：Chokepoint framework 假设执行者有工程背景；Evan 没有。Node 4 必须把"诚实标注不确定性"提到比"产出 draft 数量"更高的优先级。
2. **语言/语境风险**：原 framework 是英文/美股语境；CN/HK 卡脖子议题往往涉及政策术语和监管细节，搜索模板需要本地化，否则会扫出一堆翻译稿而不是一手政策文件。
3. **时间尺度风险**：Chokepoint 假设的"12-18 个月"交货期、"2 年建厂周期"在美股语境合理；在 A 股/H 股，政策催化可能在几天内改变供需面（典型如 2023-2024 国产存储行情），追踪窗口需要按市场调整。

---

## 七、Summary（独立提案人结论）

**Node 4 定位**：Chokepoint Strategy 是实验性（v1 manual-only）策略插件，输出 research theme 与 draft candidate，**不**输出买卖建议。

**核心纪律**：
1. 严守边界：策略插件不做 SOP 编排，不做风控，不做持仓监控
2. 证据先行：升 draft 必须有 ≥ 2 条一手来源 + 强制负面搜索 + 结构化崩塌条件
3. 诚实标注：framework reference only，不复制战绩/履历
4. 风险前置：单路径依赖、微型股流动性、不可验证履历、幸存者偏差都要在 draft 字段里显式暴露
5. 慢步推进：v1 限定 manual + US 市场，6 个月评审后决定是否扩展

**最大风险**：把 Chokepoint 框架当"研究终点"而非"研究起点"用，会同时放大 framework 自身的偏差（单路径、幸存者、人物光环）和个人投资者的认知短板（无工程背景）。Node 4 的全部设计目标是**让这些偏差在 draft 字段里显形**，由下游模块和人工做最终判断。

**下一步建议**：
1. 与决策方对齐 §6.1 三个开放问题
2. 启动 v1 实现，仅 `market=US` / `run_mode=discovery` / `caller=manual`
3. 6 个月 manual 跑够 10 次后做 v1.1 评审
4. v1.1 才考虑开放 HK/CN 市场、`tracking` run_mode
