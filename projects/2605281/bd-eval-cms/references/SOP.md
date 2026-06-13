# CMS 投前评估 Skill - SOP 完整流程规范

> **版本**:v0.2
> **适用**:bd-eval-cms Skill（双层架构：规范层 SKILL.md + 执行层 EXECUTION.md）
> **配合阅读**:`references/00_CMS-投前评估技能体系总规则.md`、`SKILL.md` Step 1~11（规范层）

---

## 目录

1. [总则](#1-总则)
2. [Phase 1: DISCOVERY](#2-phase-1-discovery)
3. [Phase 2: D-0 路由 + 技能确认 Battle](#3-phase-2-d-0-路由--技能确认-battle)
4. [Phase 3: 逐 Gate 深度评估](#4-phase-3-逐-gate-深度评估)
5. [Phase 4: Gate Battle 对抗审查](#5-phase-4-gate-battle-对抗审查)
6. [Phase 5: 报告合并 + 质量终检](#6-phase-5-报告合并--质量终检)
7. [Phase 5.5: HTML 生成 + 上传归档](#7-phase-55-html-生成--上传归档)
8. [异常处理](#8-异常处理)
9. [版本记录](#9-版本记录)

---

## 1. 总则

### 1.1 体系架构

本 Skill 基于CMS投前评估技能包,核心要素:

- **19个技能**:D群(基座×4)+ A群(中国药品×9)+ B群(消费属性×3)+ C群(国际×3)+ E群(股权×1)
- **6-Gate门控**:前提门→定调门→证据门→支付门→成本门→可做门
- **三阶段流程**:阶段A(公开信息)→ 阶段B(双轨并行)→ 阶段C(投委会终审)
- **财务硬门槛**:按产品类型(创新药/仿制药/医美/消费健康)查表,不可降低
- **置信度体系**:A/B/C/D四级,关键财务数据C/D级必须在执行摘要中披露

### 1.2 三框架融合(强制)

| 层级 | 框架 | 作用 |
|------|------|------|
| 骨架层 | 终审模板 v6.2 | 输出结构、必输字段、一票否决 |
| 内容层 | 投前尽调14维度 | 评估维度覆盖完整性 |
| 方法论层 | 麦肯锡8步法 | 问题结构化→假设树→数据驱动 |

三层框架缺一不可,缺失任何一层视为不合规输出。

### 1.3 一票否决清单(8条,体系级,不可豁免)

> **单一信源**：本清单为 SKILL.md Step 9 的摘要引用，完整定义（含例外条件和轻触探意愿机制）以 SKILL.md Step 9 为准。

1. 合规红线:产品存在未披露安全性事件或监管处罚
2. IP障碍:无法获得中国大陆/目标市场必要IP授权
3. 财务不达标:IRR低于对应类别最低门槛
4. 注册路径不可行:NMPA/目标市场无合规注册路径
5. 合作方不可信赖:欺诈记录或财务崩溃风险
6. 排除市场:目标市场为以色列/印度/韩国
7. 战略不协同:产品与现有六大业务主体TA定位完全冲突
8. 合作可能性明显不足:命中CP-1(大型MNC核心管线)/CP-2(国内企业自建商业能力)/CP-3(大集团核心利润品种)，且无例外条件。与1~7条即时关闭不同，本条允许降级为Watch等待窗口

### 1.4 执行模式

本体系支持三种执行模式，由用户在启动评估时指定或由系统自动判断：

| 模式 | 场景 | 流程差异 | 外部资料处理 | 版本管理 |
|------|------|---------|------------|----------|
| **模式 1：全量评估** | 首次评估新品种 | 标准全流程 Phase 1-6 | 无 | 无 |
| **模式 2：全量评估 + 外部资料注入** | 用户提供了补充资料（PDF/报告/内部文档） | Phase 1 开始前先处理外部资料 | Phase 1 之前统一存入 `EXT/` 目录 | 无 |
| **模式 3：增量更新** | 品种已有评估，需更新特定 Gate（如新临床数据公布） | 只重跑指定 Gate + Gate 6 依赖检查 | 补充资料追加到 `EXT/` 目录 | Gate 文件版本化备份到 `history/` |

**外部资料处理流程**（适用于模式 2 和 3）：
1. 用户通过三种渠道提供外部资料：直接上传文件、提供URL（需联网抓取）、提供文本片段
2. 所有外部资料统一提取关键信息，按标准格式存入 `{品种目录}/references/EXT/EXT-XXX.md`（每份资料一个独立文件）
3. EXT/ 目录使用固定前缀 `EXT-`，编号从 EXT-001 开始独立递增
4. 子 Agent 在撰写各 Gate 时，优先使用外部资料覆盖的维度，减少重复搜索

**增量更新流程**（适用于模式 3）：
1. 用户指定需要更新的 Gate（如"只更新 Gate 3 证据门"）
2. 系统备份当前版本到 `{品种目录}/02-gate-by-chapter/history/{Gate文件名}.v{N}.md`
3. 只重跑指定 Gate 的子 Agent，其他 Gate 保持不变
4. 如更新内容影响 Gate 6 结论，必须重跑 Gate 6 可做门
5. Battle 审查只审查变更的 Gate 章节
6. 更新后重新生成最终报告和 HTML

---

## 2. Phase 1: DISCOVERY

### 2.1 输入

用户提供:
- 品种名称(通用名/商品名/代号)
- 合作方信息(可选)
- 目标业务主体(可选)
- 评估阶段(可选,默认阶段A)

### 2.2 操作步骤

**Step 1:标的方画像确认**

向用户询问以下信息(不强制阻塞):

| 字段 | 问题 | 必要性 |
|------|------|--------|
| 合作方名称 | 这个品种的合作方是谁? | 推荐 |
| 业务主体 | 这个品种主要跑哪个业务主体?(深康/德镁/维盛/院外/天津康哲/康联达) | 推荐 |
| 评估阶段 | 目前处于哪个阶段?(A公开信息/B立项后/C投委会) | 推荐 |
| 初步财务意向 | 有没有初步的首付款/里程碑预期? | 可选 |

用户说"不知道"或"先跑"时,允许跳过,但在 discovery 中标注。

**Step 2:创建品种目录**

```bash
mkdir -p projects/bd-eval-cms/{品种名}/02-gate-by-chapter/
mkdir -p projects/bd-eval-cms/{品种名}/battle/
mkdir -p projects/bd-eval-cms/{品种名}/references/P1/
```

**Step 3:宽度搜索 + 参考文献采集**

执行 web_search ≥5 次,覆盖以下维度:

| # | 搜索维度 | 搜索关键词示例 |
|---|---------|--------------|
| 1 | 品种基本信息 | `{品种名} 通用名 适应症` |
| 2 | 原研/合作方 | `{品种名} 原研公司 开发历史` |
| 3 | 作用机制 | `{品种名} 作用机制 靶点 MOA` |
| 4 | 注册状态 | `{品种名} NMPA 注册 临床试验` |
| 5 | 市场规模 | `{品种名} 市场规模 中国 竞争格局` |
| 6 | 专利情况 | `{品种名} 专利 中国 保护期` |
| 7 | 合作历史 | `{品种名} License 中国 合作` |

**参考文献采集规范(强制遵守)**:

搜索后必须对有价值的搜索结果执行 `web_fetch` 抓取内容,存入 `{品种目录}/references/P1/P1-XXX.md`(每篇文章一个独立文件)。

**参考文献编号规则**:
- **Phase 1 使用固定前缀 `P1-`**
- 格式:P1-001, P1-002, P1-003...(三位数字,连续递增)
- 每个子 Agent 使用独立前缀,内部从 001 开始独立递增

**参考文献标准格式**:
```markdown
# [P1-001] 文章标题
- **URL**: https://...
- **抓取时间**: 2026-05-29 11:00 CST
- **来源类型**: 官方|学术|行业媒体|公司公告|监管数据库

## 原文内容
(web_fetch 抓取的完整内容,尽量完整保留)

## 关键数据点
- 具体数字/结论1
- 具体数字/结论2
```

**需要抓取的页面**(有价值):
- 包含具体市场规模/患者人数/销售额等数字
- 包含注册审批/临床试验等事实陈述
- 包含竞品对比/专利信息等结构化内容
- 包含公司公告/财报中的关键财务数据

**不需要抓取的页面**(跳过):
- 纯导航页/目录页
- 广告页/营销软文
- 无实质内容的列表页
- 重复内容(已抓取过同一信息的其他来源)

**引用标注规则**:
- 报告正文中每个数据点后跟 `[{前缀}-XXX]`
- 示例:全球PBC患者约50万人[P1-012],Ocaliva 2024年销售额12亿美元[G3-015]
- 引用其他节点数据时使用对应前缀编号,如 `[P1-003]` `[G1-007]`
- 不允许出现"外网核查""分析推断"等无具体引用编号的标注

**参考文献前缀分配表**:

Orchestrator 在 spawn 子 Agent 时为每个节点分配唯一前缀:

| 节点类型 | 前缀 | 说明 |
|---------|------|------|
| Phase 1 DISCOVERY | P1- | 固定前缀,所有品种都有 |
| One-pager | OP- | 终局先立文件 |
| Gate 1 前提门 | G1- | 标准 6-Gate |
| Gate 2 定调门 | G2- | 标准 6-Gate |
| Gate 3 证据门 | G3- | 标准 6-Gate |
| Gate 4 支付门 | G4- | 标准 6-Gate |
| Gate 5 成本门 | G5- | 标准 6-Gate |
| Gate 6 可做门 | G6- | 标准 6-Gate |
| Gate 7 (A-3 专用) | G7- | A-3 技能的额外 Gate |
| Battle 审查 | BT- | 对抗审查阶段 |
| A-0 L1~L5 扫描 | L1- ~ L5- | A-0 技能的5层扫描 |
| A-7 S1~S3 Stage | S1- ~ S3- | A-7 技能的3个 Stage |
| 外部/用户提供资料 | EXT- | Phase 1 之前或增量更新时（模式 2/3） |
| 其他按技能实际节点命名 | 按需 | Orchestrator 根据技能定义动态分配 |

每个子 Agent 只写自己前缀的目录,不读写其他目录。Phase 5 合并时读取所有前缀目录下的文件,生成纯索引总索引。

**置信度与参考文献的关系**:
| 置信度等级 | 参考文献要求 | 说明 |
|-----------|-------------|------|
| A级 | ≥2个独立引用交叉验证 | 两个不同来源(如 `[P1-003]` `[G1-007]`)证实同一数据 |
| B级 | 1个权威引用 | 单一但来源可信(FDA/EMA/NMPA/学术期刊) |
| C级 | 内部无引用支撑 | 标注 `[C级-待验证]`,必须说明待验证内容 |
| D级 | 无引用的假设 | 标注 `[D级-基于假设]`,必须说明假设前提 |

**Step 4:业务主体初步判断**

根据适应症和产品类型,匹配业务主体:

| 适应症/产品领域 | 优先业务主体 |
|----------------|-------------|
| 心肾代谢/消化肝病/CNS | 深康 |
| 皮肤健康(药品) | 德镁 |
| 医美 | 德镁 |
| 眼科/耳鼻喉 | 维盛 |
| 院外/OTC/消费健康 | 院外业务 |
| 化学仿制药(高壁垒) | 天津康哲 |
| 国际市场 | 康联达 |

**Step 5:产品类型初步判断**

为 D-0 路由准备:

| 关键词/信号 | 产品类型 |
|-----------|---------|
| PCT申请、first-in-class、全球临床 | 创新药 |
| BE试验、一致性评价、首仿 | 化学仿制药 |
| 生物等效性、参照药、生物类似药 | 生物类似药 |
| 肉毒素、玻尿酸、填充剂 | 医美 |
| OTC、保健品、功效护肤 | 消费健康 |
| 平台技术、共同开发、入股 | 平台型战略合作 |
| 多标的、展会、批量筛选 | 多标的比较 |

**Step 6:写入 01-discovery.md**

```markdown
# {品种名} - DISCOVERY

## 基本信息
- 通用名/商品名:...
- 原研公司:...
- 作用机制/靶点:...
- 主要适应症:...
- 海外上市状态:...
- 中国注册状态:...
- 临床阶段:...

## 业务主体判断
- 匹配主体:{深康/德镁/维盛/院外/天津康哲/康联达}
- 判断依据:...

## 产品类型判断
- 初步类型:{创新药/仿制药/生物类似药/医美/消费健康/平台型/多标的}
- 判断依据:...
- 置信度:{高/中/低}

## 搜索记录
- 搜索次数:X
- 搜索来源:[...]

## 待确认信息
- (用户未提供的信息)
```

**Step 7:创建 state.json**

```json
{
  "name": "{品种名}",
  "scheme": "B",
  "businessEntity": "{业务主体}",
  "routedSkill": "待路由",
  "routedChain": [],
  "phase": "discovery_complete",
  "startedAt": "{ISO时间}",
  "financialThresholdType": "{创新药|仿制药|医美|消费健康}",
  "discovery": {
    "searches": 5,
    "sources": ["..."],
    "productType": "{类型}",
    "confidence": "{高/中/低}"
  }
}
```

### 2.3 完成标志

- `01-discovery.md` 存在且包含基本信息、业务主体判断、产品类型判断、**路由决策单**(推荐主技能、串接链路、财务门槛类型、路由依据)
- `state.json` 已创建且 phase = "discovery_complete",**包含 routingDecision 字段**
- `{品种目录}/references/P1/` 目录已创建,包含 Phase 1 搜索采集的参考文献文件

---

## 3. Phase 2: D-0 路由 + 技能确认 Battle

### 3.1 执行 D-0 路由

读取 `references/D-0_bd-evaluation-router.md`,按决策树路由。

**第一层:产品类型识别**

```
标的
├── 自主研发(全球IP持有)→ A-3
├── 国际市场
│   ├── 单品单市场 → C-1
│   ├── 单品多市场 → C-2
│   └── 组合策略 → C-3
├── 多标的横向比选(≥3个)→ A-7
├── 医美
│   ├── 单标的 → B-1
│   └── 组合复盘 → B-2
├── 消费健康/OTC → B-3
├── 国内Biotech(股权+商业化)→ E-1
├── 化学药品
│   ├── 高壁垒仿制药(3/4类)→ A-8
│   ├── 生物类似药(3.3类)→ A-4
│   ├── 海外已上市/中国未上市(5.1/6类)→ A-1
│   ├── 国内合作·成熟阶段 → A-2
│   ├── 已上市代理权 → A-5
│   └── 院内→院外延伸 → A-6
└── 市场深度分析 → D-2
```

**排除规则(路由前必查)**:
- 以色列/印度/韩国 → 一票否决
- 院外与 B-1/A-4/A-3 重叠 → B-3 失败
- E-1 仅限中国大陆 Biotech

**A-2 vs A-5 边界判断**:
- 已在中国上市(有NMPA批文+销售历史)→ A-5
- 在研/NDA阶段/未上市 → A-2

**第二层:业务主体确认**(如用户未指定)

根据 Step 5 判断结果确认。

**第三层:评估阶段判断**

| 用户提供信息量 | 判断为阶段 | 行动 |
|---------------|-----------|------|
| 仅品种名+适应症 | 阶段A | 输出完整路由决策单 |
| 有公开数据+初步财务意向 | 阶段A | 输出完整路由决策单 |
| 有NDA保护数据 | 阶段B | 标注B阶段任务分配 |
| 有TS草案+财务模型 | 阶段C | 标注C阶段终审准备 |

### 3.2 输出路由决策单

```
路由编号:D0-{YYYY}-{NNN}
标的:{品种名}
产品类型:{类型} → 置信度:{高/中/低}
业务主体:{主体}
评估阶段:{A/B/C}
推荐主技能:{编号}
推荐串接链路:{链路}
数据缺口:Top 3~5
```

### 3.3 财务硬门槛初判

从总规则第5节查表,确定本品种适用的财务门槛类型:

| 产品类型 | 门槛表 | 核心指标 |
|---------|--------|---------|
| 创新药 | §5.1 | IRR ≥ 15-25%(按投资额×上市年限6档)|
| 仿制药 | §5.2 | IRR ≥ 25-50%(按类型)|
| 医美 | §5.3 | IRR ≥ 50-60%,毛利率 ≥ 75% |
| 消费健康 | §5.4 + B-3 | IRR ≥ 40%,LTV/CAC ≥ 3 |

### 3.4 技能确认 Battle(强制)

Spawn 审查层子Agent(独立),指令:

```
你是 CMS 投前评估体系的路由审查层。

任务:验证以下路由决策是否正确。

1. 读取品种 discovery 信息:{01-discovery.md 路径}
2. 读取 D-0 路由决策树:{references/D-0_bd-evaluation-router.md 路径}
3. 读取推荐技能定义:{对应技能文件路径}

判断:
- 产品类型识别是否正确?
- 业务主体匹配是否合理?
- 推荐技能是否是最合适的?
- 是否遗漏了串接技能?

输出格式:
- 同意 / 不同意
- 如不同意,说明你认为应该路由到哪个技能及理由
```

输出写入 `battle/ROUTE-SELECTION-AUDITOR.md`。

### 3.5 更新 state.json

```json
{
  "routedSkill": "A-1",
  "routedChain": ["D-1", "D-2", "A-1", "D-3"],
  "phase": "route_confirmed"
}
```

### 3.6 完成标志

- 路由决策单已生成
- `battle/ROUTE-SELECTION-AUDITOR.md` 存在
- `state.json` 的 routedSkill 和 routedChain 已填写

---

## 4. Phase 3: 逐 Gate 深度评估

### 4.1 章节结构来源

根据 Phase 2 确定的技能编号,读取对应技能定义文件中的评估章节结构。

每个技能的「模块四:评估章节结构」定义了该技能覆盖的 Gate 及各 Gate 的评估要点。

### 4.2 执行顺序

```
Step 0: One-pager 终局先立(串行,必须先跑完)
    ↓
Step 1: Gate 1 前提门 | Gate 2 定调门 | Gate 3 证据门(并行×3)
    ↓
验证: 交叉检查 Gate 1-3
    ↓
Step 2: Gate 4 支付门 | Gate 5 成本门(并行×2)
    ↓
验证: 交叉检查 Gate 4-5
    ↓
Step 3: Gate 6 可做门(串行,依赖 Gate 1-5 结论)
    ↓
最终验证: 全量交叉检查
```

### 4.3 子Agent 执行规范

每个 Gate 的子Agent prompt 遵循 `references/sub-agent-prompt-template.md` 的规范,核心要求:

1. **结论卡格式**:每个 Gate 必须输出标准结论卡
2. **置信度标注**:关键数据按 A/B/C/D 四级标注
3. **来源标注**:每个数据点必须标注 `[{前缀}-XXX]` 引用编号(禁止"外网核查""分析推断"等无编号标注)
4. **参考文献采集**:搜索前列出 `{品种目录}/references/{前缀}/` 目录下已有文件避免重复,搜索后对有价值结果做 web_fetch 抓取,写入 `{品种目录}/references/{前缀}/{前缀}-XXX.md`
5. **阶段标签**:标注 [阶段A] 或 [阶段B]
6. **财务缩写**:首次出现标注中文全称
7. **Gate 依赖**:Gate 6 必须引用 Gate 1-5 结论(使用对应前缀编号如 `[P1-001]` `[G3-005]`)
8. **参考文献清单**:报告开头列出本 Gate 使用的参考文献编号清单

### 4.4 评估深度标准

**阶段A(公开信息域)**:
- 信息来源:FDA/EMA审评报告、ClinicalTrials、公司公告、学术文献
- 覆盖 Gate:Gate 1 + Gate 2 + Gate 3
- 深度:结论性判断 + 关键数据 + Top 5 需补证据

**阶段B(双轨并行域)**:
- 信息来源:IQVIA数据、NHSA谈判历史、CMC审计、KOL访谈
- 覆盖 Gate:Gate 4 + Gate 5
- 深度:量化分析 + 三情景财务模型 + 成本拆解

**阶段C(终审域)**:
- 信息来源:完整财务模型、法律尽调、管理层决策
- 覆盖 Gate:Gate 6
- 深度:交易条款分析 + IRR测算 + 止损三件套

### 4.5 默认综合输出

**默认输出阶段A+B综合评估**(一份大报告覆盖全部 Gate)。
仅当用户明确说"只做阶段A快评"时才输出单阶段。

### 4.6 完成标志

- One-pager 存在
- Gate 1-6 各自章节文件存在于 `02-gate-by-chapter/`
- 每个章节包含标准结论卡

---

## 5. Phase 4: Gate Battle 对抗审查

### 5.1 审查层指令

Spawn 审查层子Agent,以 CMS 体系最挑剔评审者身份审查:

**审查检查清单**(8项):

1. **Gate 结论卡完整性**:每个 Gate 是否都有结论卡,格式是否标准
2. **置信度合理性**:标注的置信度等级是否与数据来源匹配
3. **财务硬门槛达标**:IRR/回收期/倍数/毛利率是否达到 §5 标准表
4. **一票否决核查**:8条体系级（含CP-1/CP-2/CP-3合作可能性否决）+ 技能专属否决项是否逐一核查。完整定义见 SKILL.md Step 9
5. **C/D级数据披露**:关键财务假设依赖C/D级数据时,是否在执行摘要中披露
6. **信息冲突标记**:内外部信息不一致时是否正确标记
7. **来源标注覆盖**:四分法标注是否完整
8. **财务缩写规范**:首次出现是否标注中文全称

**输出格式**:
- 3-5个实质性异议
- 每个异议:引用具体 Gate 章节 → 说明问题 → 提出修改建议
- 裁定:APPROVE / REJECT / CONDITIONAL
- 输出:`battle/BATTLE-R1-AUDITOR.md`

### 5.2 执行层指令

Spawn 执行层子Agent:

- 逐条回应审查层异议
- 接受(说明改什么)或拒绝(附证据)
- 更新对应 Gate 章节文件
- 输出:`battle/BATTLE-R1-EXECUTOR.md`

### 5.3 多轮规则

最多 3 轮。生成 `03-battle-summary.md`(结论汇总 + 未解决争议点)。

### 5.4 完成标志

- `battle/BATTLE-R1-AUDITOR.md` 存在
- `battle/BATTLE-R1-EXECUTOR.md` 存在
- `03-battle-summary.md` 存在

---

## 6. Phase 5: 报告合并 + 质量终检

### ⚠️ 核心原则

**合并是程序行为，不是 AI 行为。** 不做任何删除、改写、润色、摘要化。原始评估文档的每个字都必须原样出现在最终报告中。

AI 唯一参与的部分：生成执行摘要（基于所有 Gate 结论卡汇总）。其余全部由 `scripts/merge-report.sh` 脚本完成。

### 6.1 合并流程（程序行为）

**Step 1：运行合并脚本**
```bash
bash scripts/merge-report.sh "{品种目录路径}"
```

脚本逻辑：
1. 从 state.json 读取元信息 → 生成封面
2. 写入执行摘要占位符（`<!-- EXECUTIVE_SUMMARY_PLACEHOLDER -->`）
3. 依次 cat 拼接所有源文件（01-discovery.md → One-pager.md → Gate 1-6 → battle → REFERENCES.md）
4. 内置格式校验（行数比、章节完整性、结论卡存在性）
5. 输出 `04-final-report.md`

**Step 2：AI 生成执行摘要**

AI 读取所有 Gate 结论卡，生成执行摘要，替换报告中的占位符：
- 结论先行（推进/条件推进/停止）
- 核心指标一览
- 关键风险提示（含 C/D 级数据披露）
- 推荐行动

### 6.2 报告结构

```
封面：品种名 | CMS投前评估报告 | 日期 | 评估阶段标注
第一章：执行摘要（AI 生成）
第二章：标的发现（01-discovery.md 原文）
第三章：One-pager 终局先立（原文）
第四章：Gate 1 前提门（原文）
第五章：Gate 2 定调门（原文）
第六章：Gate 3 证据门（原文）
第七章：Gate 4 支付门（原文）
第八章：Gate 5 成本门（原文）
第九章：Gate 6 可做门（原文）
第十章：Gate Battle 对抗审查总结（原文）
附录：参考文献
```

### 6.3 质量终检（10 项）

| # | 检查项 | 标准 | 类型 | 结果 |
|---|--------|------|------|------|
| 1 | TL;DR 5 字段 | 1-6 每个 Gate 章节顶部都有 TL;DR，且包含评级/评分/关键风险/推荐路径/下一步 5 字段 | 形式合规 | PASS/FAIL |
| 2 | 财务硬门槛 | 对照 §5 标准，达标或不达标+说明 | 形式合规 | PASS/FAIL |
| 3 | 一票否决核查 | 8条体系级（含CP-1/CP-2/CP-3）+ 技能专属，逐一核查 | 形式合规 | PASS/FAIL |
| 4 | 置信度标注 | 关键数据 ≤3处缺失 | 形式合规 | PASS/FAIL |
| 5 | 信息冲突汇总 | 附录C非空（”无冲突”也须标注） | 形式合规 | PASS/FAIL |
| 6 | 阶段标签 | [阶段A]/[阶段B] 标注正确 | 形式合规 | PASS/FAIL |
| 7 | 来源标注 | 所有数据点有 [{前缀}-XXX] 引用，无”外网核查”等无编号标注 | 形式合规 | PASS/FAIL |
| 8 | 财务缩写 | 首次出现标注中文全称 | 形式合规 | PASS/FAIL |
| 9 | **Gate 章节体量** | 每个 Gate 章节 ≥ 200 行 | **内容充分性** | PASS/FAIL |
| 10 | **合并完整性** | 报告行数 ≥ 源文件总行数 × 95% | **内容充分性** | PASS/FAIL |

**任一 FAIL → 报告退回修改，不可进入 Phase 5.5。**

### 6.4 完成标志

- `04-final-report.md` 存在
- 脚本格式校验通过（行数比 ≥ 95%）
- 质量终检 10 项全部 PASS
- `state.json` phase = "report_finalized"

---

## 6.5 报告结构与生成规范（v0.7.1 新增）

> **核心思想（"分而治之"）**：报告 = N 个零件文件 + 装配器。
> 每个 Gate 章节是独立 .md 文件，最终报告由 `merge-report.sh` 程序化拼接。
> 改一处只动一个零件文件，改完重跑 merge。
> JMKX003948 这种 v0.7.0 之前的旧案例不在本节约束范围。

### 6.5.1 报告由 N 个零件文件组成

**零件清单**（v0.7.1 标准结构）：

| # | 零件文件 | 来源 | 说明 |
|---|----------|------|------|
| 1 | `01-discovery.md` | Phase 1 产出 | 标的发现 |
| 2 | `02-one-pager.md` | Phase 2 产出 | One-pager 终局先立 |
| 3 | `02-gate-by-chapter/One-pager.md` | Phase 3 产出 | Gate 章节版（详版） |
| 4 | `02-gate-by-chapter/Gate-1-premise.md` | Phase 3 产出 | Gate 1 前提门 |
| 5 | `02-gate-by-chapter/Gate-2-positioning.md` | Phase 3 产出 | Gate 2 定调门 |
| 6 | `02-gate-by-chapter/Gate-3-evidence.md` | Phase 3 产出 | Gate 3 证据门 |
| 7 | `02-gate-by-chapter/Gate-4-payment.md` | Phase 3 产出 | Gate 4 支付门 |
| 8 | `02-gate-by-chapter/Gate-5-cost.md` | Phase 3 产出 | Gate 5 成本门 |
| 9 | `02-gate-by-chapter/Gate-6-feasibility.md` | Phase 3 产出 | Gate 6 可做门 |
| 10 | `03-battle-summary.md` | Phase 4 产出 | Battle 对抗审查总结 |
| 11 | `references/REFERENCES.md` | Phase 3 累积 | 参考文献索引 |
| 12 | `04-final-report.md` | Phase 5 产出 | **装配产物**（程序拼，非手写）|

**零件体量硬性要求**：
- 每个 Gate 章节文件 ≥ 200 行（与 §6.3 第 9 项质量终检一致）
- 例外：One-pager.md 允许 ≤ 200 行（本身就是 1 页摘要）
- 例外：02-one-pager.md（Phase 2 早版）可仅保留结论，待 Phase 3 详细化后归档到 `02-gate-by-chapter/`

**零件文件命名约束**：
- Gate 章节文件名前缀严格为 `Gate-{N}-{语义}.md`（N=1~6，语义用英文短词如 premise/positioning/evidence/payment/cost/feasibility）
- 允许变体（与 `merge-report.sh` 第 108-119 行兼容）：
  - `Gate-1-premise.md` / `Gate-1-precondition.md`（同义）
  - `Gate-6-feasibility.md` / `Gate-6-doability.md`（同义）
- One-pager 仅两个合法名：`02-one-pager.md`（Phase 2 早版）+ `02-gate-by-chapter/One-pager.md`（Phase 3 详版）

### 6.5.2 每章顶部必须有 TL;DR 5 字段

**目的**：取代 v0.7.0 旧版"结论卡"格式（不新增独立字段，直接升级）。

**TL;DR 模板**（每个 Gate 章节文件顶部强制）：

```markdown
# G{N} {章名}

## TL;DR

| 字段 | 值 |
|------|----|
| **评级** | 推进 / 条件推进 / 停止 |
| **评分** | 0-100 分（按技能定义）|
| **关键风险** | 1-3 条最关键风险（含 C/D 级数据披露）|
| **推荐路径** | 推进/调整/终止 + 关键条件 |
| **下一步** | 谁、什么时间、做什么 |

---

## 详细评估

### {N}.1 {子节}
...
```

**强制约束**：
- 5 个 key 必须全部存在（评级/评分/风险/路径/下一步）
- `merge-report.sh` 缺任一字段 → 报警并退出（exit 2）
- 旧版"结论卡"格式（v0.7.0 之前）可作为补充说明保留，但不能替代 TL;DR 5 字段；若缺 TL;DR，merge 报警退出

**TL;DR 与 Battle 总结的关系**：
- TL;DR 在每个零件文件**自身**（自描述）
- Battle 总结在 `03-battle-summary.md`（跨 Gate 对抗）
- 两者不重复：TL;DR = 章节结论；Battle = 章节间的争议与决策

### 6.5.3 merge-report.sh 装配规则

**程序行为红线**（不删不改不润色不摘要）：

1. **不删**：原文章节每个字必须出现在最终报告
2. **不改**：不修改原文任何字符
3. **不润色**：不做风格统一
4. **不摘要**：执行摘要由 AI 单独生成，**不**从 Gate 章节抽取

**merge 流程新增校验**（v0.7.1 起）：

| 校验项 | 触发条件 | 行为 |
|--------|----------|------|
| TL;DR 字段缺失 | 任一零件文件缺 5 字段之一 | 报警退出（exit 2）|
| Gate 章节体量 < 200 行 | 超过 1 个 Gate 不达标 | 报警退出（exit 3）|
| Gate 6 依赖检查 | Gate 1~5 任一文件 mtime 晚于 Gate 6 | 打印 WARN（不退出，由人决定）|
| 行数比 < 95% | 04-final-report.md < 源文件总行数 × 0.95 | 报警退出（exit 4）|

**Gate 6 依赖检查说明**：
- 设计为"软警告"而非"硬退出"——因为 Gate 6 结论是否需要重审，由 BD 团队判断
- 检查逻辑：`stat -f %m 02-gate-by-chapter/Gate-{1-5}-*.md` vs `stat -f %m 02-gate-by-chapter/Gate-6-*.md`
- 行为：WARN 消息写到 stderr，merge 继续（exit 0）

### 6.5.4 增量更新与版本化备份

**版本化备份**（与 §9.5 增量更新 SOP 一致，本节重申要点）：

- 备份位置：`{品种目录}/02-gate-by-chapter/history/`
- 备份命名：`{Gate文件名}.v{N}.md`（N 从 1 开始）
- 备份时机：**任何修改前**先备份（不是改完再备份）
- 备份内容：完整原文 + 头部版本说明（frontmatter）

**参考文献索引自动生成**：

- `references/REFERENCES.md` 是程序化产物
- 每次 Phase 3 累积新引用后，运行 `scripts/generate-references-index.sh {品种目录}` 重新生成
- 生成逻辑：遍历 `references/` 下所有前缀子目录（P1/、OP/、G1/、G2/、...、BT/、EXT/），按编号排序，输出 Markdown 索引
- 禁止 AI 手写 REFERENCES.md（容易漏引或错编号）

**版本号管理**：
- 项目级版本号在 `bd-eval-cms/version.json`（一个数字，如 `0.7.1`）
- 不做"每个 Gate 独立版本号"（过度设计）
- 整体更新 → version + 0.0.1（修订号）
- Gate 级变更 → 在 execution-log.md 记录，不动 version

**JMKX003948 旧案例处理**：
- **不迁移**（Evan 已明确指示）
- 旧案例只有 `04-final-report.md` 单文件，无 `02-gate-by-chapter/` 目录
- merge-report.sh 检测到缺目录 → 跳过校验，按旧模式工作
- 下一个新品种按 v0.7.1 标准结构创建

---

## 7. Phase 5.5: HTML 生成 + 上传归档

### 7.1 核心原则

**HTML 生成是纯程序行为，不依赖 AI。**

使用 `scripts/convert-md-to-html.py` 将合并后的 Markdown 程序化转换为 HTML，套用风格 12 骨架和配色方案。AI 只负责执行脚本命令、选择配色、上传和归档。

### 7.2 报告渲染风格选择

**新增 Style A1（推荐）**：

正式 CMS BD 投前评估报告推荐使用 Style A1，完整覆盖 A-1 原始模板需求和 TRTL-729 示例结构。

**风格对比**：

| 风格 | 特点 | 适用场景 | 推荐度 |
|------|------|----------|--------|
| **A1** | 完整 A-1 模板支持，包含密级栏、互斥规则框、One-pager 结构、Gate 1-6 承载能力 | 正式 CMS BD 投前评估报告 | ⭐⭐⭐⭐⭐ 强烈推荐 |
| **12** | 强风格化 CMS 评估（Gate 卡片 / Battle 框 / 置信度徽章） | 简化版投前评估、快速原型 | ⭐⭐⭐ 可选 |
| **13** | 程序化 Markdown→HTML（保留原结构，加麦肯锡视觉） | 技术审查、内部参考 | ⭐⭐ 备选 |

**使用方式**：
- 默认使用 Style A1（显式参数 `a1`）
- 保持 style-12/style-13 现有行为不变
- 通过 `scripts/render_report.sh` 的第二个参数指定风格

### 7.3 配色方案

| 配色名 | 主色 | 适用场景 |
|--------|------|----------|
| mckinsey-navy | #1a3a5c | 默认，经典咨询风格 |
| investment-blue | #1D4ED8 | 投行/金融报告 |
| burgundy-wine | #7B2D3B | 稳重权威 |
| forest-teal | #1B6B5A | 冷静理性 |

未指定时默认 mckinsey-navy。

### 7.3 生成命令

```bash
python3 scripts/convert-md-to-html.py "{品种目录}" {配色名} "{品种目录}/REPORT.html"
```

脚本自动完成：读取 04-final-report.md → 提取封面元信息 → 识别 CMS 专属结构 → 套用骨架+配色 → 输出 HTML。

### 7.4 上传归档（v0.7.0 起彻底解耦 doc-viewer）

> **架构变更（v0.7.0）**：
> - v0.4.0 接入 doc-viewer 范式 4；v0.7.0 **彻底解耦 doc-viewer skill**，
>   报告渲染全部走本地 `bd-eval-cms/templates/style-12/` 和 `style-13/`
> - v0.7.0 统一入口：`bd-eval-cms/scripts/render_report.sh`（取代调 doc-viewer）
> - 玄关知识库上传仍走 4 步 API（与 v0.6.0 一致），拿 5 年 doc.aishuo.co 链接

**Step 1：读 config.yaml 获取固定参数**

```bash
PROJECT_ID=$(yq '.knowledgeBase.projectId' bd-eval-cms/config.yaml)
PATH_TEMPLATE=$(yq '.knowledgeBase.pathTemplate' bd-eval-cms/config.yaml)
DEFAULT_STYLE=$(yq '.reportRenderer.defaultStyle' bd-eval-cms/config.yaml)
DEFAULT_COLOR=$(yq '.reportRenderer.defaultColorTheme' bd-eval-cms/config.yaml)
```

**Step 2：调本地 render_report.sh 生成 HTML（零网络副作用）**

```bash
# 默认风格 12 + mckinsey-navy（CMS 评估体系标配）
bash bd-eval-cms/scripts/render_report.sh "{品种目录}" "$DEFAULT_STYLE" "$DEFAULT_COLOR"

# 业务指定风格 13（程序化 Markdown→HTML，保留原结构）
# bash bd-eval-cms/scripts/render_report.sh "{品种目录}" "13"
```

脚本自动：
1. 读 `config.yaml` 拿默认风格/配色
2. 调对应风格的转换脚本（`templates/style-12/convert-md-to-html.py` 或 `templates/style-13/report_renderer.py`）
3. 输出 `{品种目录}/REPORT.html`
4. 验证模板变量残留 = 0

**Step 3：自管上传到产品引进知识库**

`projectId` / `path` 走 `config.yaml` 的固定值（不调 getProjectId）：

```bash
# 1. 物理文件上传
RESOURCE_ID=$(curl -s -X POST \
  "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/uploadWholeFile" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  -F "file=@{品种目录}/REPORT.html;filename={品种名}-CMS投前评估报告.html" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# 2. 绑定到产品引进知识库（projectId 走 config.yaml）
FILE_ID=$(curl -s -X POST \
  "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveFileByPath" \
  -H "appKey: $DOCVIEWER_KB_APPKEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"projectId\": $PROJECT_ID,
    \"path\": \"{YYMMDD}/{YYMMDD-XXXX}\",
    \"name\": \"{品种名}-CMS投前评估报告.html\",
    \"fileType\": \"file\",
    \"resourceId\": $RESOURCE_ID,
    \"suffix\": \"html\",
    \"size\": $(stat -f%z {品种目录}/REPORT.html)
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")

# 3. 换 access-token
ACCESS_TOKEN=$(curl -s \
  "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=$DOCVIEWER_KB_APPKEY" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['xgToken'])")

# 4. 拿 5 年公网预览链接
PREVIEW_URL=$(curl -s -X POST \
  "https://sg-al-cwork-web.mediportal.com.cn/doc-preview/api/preview/ticket" \
  -H "access-token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"bizType\": \"kb\",
    \"bizId\": \"$FILE_ID\",
    \"format\": \"html\",
    \"title\": \"{品种名}-CMS投前评估报告.html\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['previewUrl'])")

echo "✅ 已存储到产品引进知识库"
echo "🔗 预览链接：$PREVIEW_URL（公网可访问，有效期 5 年）"
```

**Step 4：回写 state.json**

```json
{
  "reportHtmlUrl": "$PREVIEW_URL",
  "reportHtmlFileId": "$FILE_ID",
  "reportHtmlUploadedAt": "{ISO 时间}",
  "reportHtmlStorage": "kb"  // 标记走的是知识库路径
}
```

**Step 5：归档到 links.md**

```bash
scripts/archive-links.sh "{slug}" "$PREVIEW_URL"
```

**关键约束**：
- AppKey 走 `$DOCVIEWER_KB_APPKEY` 环境变量（OpenClaw 动态注入），**禁止硬编码**
- projectId / path 走 `config.yaml` 固定值，**禁止用户配置或覆盖**
- 路径模板 `{YYMMDD}/{YYMMDD-XXXX}` 由 `scripts/sync-to-knowledge-base.sh` 生成，
  调用方从 state.json.caseCode 读取

### 7.5 知识库自动同步（必执行）

完成 HTML 上传后，自动将品种目录下所有文件同步到玄关知识库（产品引进空间）。

**同步时机**：
- Phase 5.5 HTML 生成完成后自动执行
- 增量更新完成后也触发全量同步

**同步范围**：
- 根目录：state.json、01-discovery.md、03-battle-summary.md、04-final-report.md、links.md、execution-log.md、REPORT.html
- 02-gate-by-chapter/：所有 .md 文件（含 history/ 下的历史版本）
- battle/：所有 .md 文件
- references/：REFERENCES.md + 所有前缀子目录下的 .md 文件（P1/、OP/、G1/、G2/、...、BT/、EXT/ 等）

**知识库目录结构**：
```
产品引进知识库/
└── {YYMM}/                           ← 月份目录（如 2605）
    └── {案件代号}/                    ← 代号目录（如 2605-2901）
        ├── state.json
        ├── 01-discovery.md
        ├── 03-battle-summary.md
        ├── 04-final-report.md
        ├── links.md
        ├── execution-log.md
        ├── REPORT.html
        ├── 02-gate-by-chapter/
        │   ├── One-pager.md
        │   ├── Gate-1-premise.md
        │   ├── ...
        │   └── history/
        │       └── Gate-2-positioning.v1.md
        ├── battle/
        │   ├── ROUTE-SELECTION-AUDITOR.md
        │   ├── BATTLE-R1-AUDITOR.md
        │   └── BATTLE-R1-EXECUTOR.md
        └── references/
            ├── P1/
            │   ├── P1-001.md
            │   └── ...
            ├── G1/
            │   ├── G1-001.md
            │   └── ...
            ├── ...
            ├── EXT/
            │   ├── EXT-001.md
            │   └── ...
            └── REFERENCES.md
```

**调用方式**：
```bash
bash scripts/sync-to-knowledge-base.sh "{品种目录}" "{案件代号}"
# 示例：bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特" "2605-2901"
```

**配置信息**（v0.6.0 起改为运行时注入，不再硬编码）：
- API 地址：`https://sg-al-cwork-web.mediportal.com.cn/open-api/...`（详见 v2.10.0 范式 4）
- appKey：运行时从环境变量 `$DOCVIEWER_KB_APPKEY` 读取（OpenClaw 动态注入，**禁止硬编码**）
- projectId：从 `bd-eval-cms/config.yaml` 的 `knowledgeBase.projectId` 读取（业务固定值）

> 配置信息字段：v0.7.0 起 appKey 从环境变量 `$DOCVIEWER_KB_APPKEY` 读取，projectId 从 `bd-eval-cms/config.yaml` 的 `knowledgeBase.projectId` 读取（业务固定值）
> 环境变量名沿用 doc-viewer 传统协议以便与其他技能兼容

**同步结果记录**：
同步完成后在 state.json 中记录：
```json
{
  "kbSync": {
    "lastSyncAt": "{ISO时间}",
    "syncedFiles": 27,
    "status": "success"
  }
}
```

**同步失败处理**：
- 单文件失败不阻塞其他文件，继续同步
- 全部完成后记录失败文件列表
- 如果超过50%文件失败，报告错误给用户

---

## 8. 异常处理

### 8.1 子Agent 超时

1. 记录完成到第几个 Gate
2. 主会话补全未完成 Gate
3. 严重时手工编译最终报告

### 8.2 路由争议

审查层不同意路由时:
1. 双方理由记录在 `battle/ROUTE-SELECTION-AUDITOR.md`
2. 如争议无法解决,提交用户裁定
3. 用户裁定后继续执行

### 8.3 Gate 未通过

任一 Gate 结论为"停止"时:
1. 记录停止原因
2. 评估是否可通过补充证据继续
3. 如不可继续,输出"停止评估报告"并终止

### 8.4 质量终检失败

1. 标注失败项
2. 返回 Phase 3 或 Phase 4 修正
3. 修正后重新终检

---

## 9.5 增量更新 SOP（模式 3）

本节适用于品种已有评估报告，需针对特定 Gate 进行增量更新的场景。

### 9.5.1 触发条件

- 用户新增了补充资料（如新临床数据、竞品新信息、政策变化）
- 用户指定需要更新的 Gate（如"只更新 Gate 3 证据门"）
- 外部资料通过三种渠道提供：直接上传文件、提供URL（需联网抓取）、提供文本片段

### 9.5.2 执行步骤

**Step 1：状态确认**

1. 读取 `{品种目录}/state.json`，确认当前评估状态
2. 读取 `{品种目录}/04-final-report.md`，理解当前报告结构和结论
3. 确认用户指定的更新范围（哪些 Gate 需要更新）

**Step 2：处理补充资料**

1. 用户通过三种渠道提供外部资料：
   - 直接上传文件（PDF/Word/Excel）：提取关键信息和数据
   - 提供URL：联网抓取内容并提取关键信息
   - 提供文本片段：直接使用
2. 所有外部资料统一提取关键信息，按标准格式存入 `{品种目录}/references/EXT/EXT-XXX.md`（每份资料一个独立文件）
3. EXT/ 目录使用固定前缀 `EXT-`，编号从 EXT-001 开始独立递增（追加已有编号）
4. 参考文献格式：
   ```markdown
   # [EXT-001] 资料标题
   - **来源**: 用户上传 / 联网抓取 / 文本片段
   - **原始URL/文件路径**: （如有）
   - **获取时间**: YYYY-MM-DD HH:MM TZ

   ## 原文内容
   （提取的关键信息，尽量完整保留）

   ## 关键数据点
   - 具体数字/结论1
   - 具体数字/结论2
   ```

**Step 3：版本备份**

1. 对需要更新的 Gate 文件，备份当前版本到 `{品种目录}/02-gate-by-chapter/history/{Gate文件名}.v{N}.md`
2. 版本号 N 从 1 开始递增（首次备份为 v1，第二次为 v2，依此类推）
3. 备份文件保持完整的原始内容和格式
4. 在备份文件头部添加版本说明：
   ```markdown
   ---
   版本: v{N}
   备份时间: {ISO时间}
   备份原因: 增量更新前的版本备份
   ---
   ```

**Step 4：重跑指定 Gate**

1. 只对用户指定的 Gate 启动子 Agent 重跑
2. 子 Agent prompt 中注入版本信息：
   - 当前版本号：v{N+1}
   - 上一版文件路径：`{品种目录}/02-gate-by-chapter/history/{Gate文件名}.v{N}.md`
3. 子 Agent 必须先读取上一版文件，理解内容和结论
4. 新版本中必须明确标注与上一版的差异：
   - **新增数据点**：标注 `[新增]`
   - **修正数据点**：标注 `[修正: 旧值 → 新值]`
   - **删除数据点**：标注 `[删除: 原值]`
5. 如果新数据与上一版结论矛盾，必须在结论卡中说明变更原因
6. 如果存在外部资料（EXT/ 目录非空），子 Agent 优先使用外部资料覆盖的维度，减少重复搜索

**Step 5：Gate 6 依赖检查**

1. 检查更新的 Gate 是否影响 Gate 6 可做门的结论
2. 如影响（如 Gate 3 证据门的新数据改变了峰值销售预测），必须重跑 Gate 6
3. 如不影响，Gate 6 保持原版本不变
4. Gate 6 重跑时，必须在结论卡中说明"因 Gate X 更新触发重跑"

**Step 6：Battle 审查（只审变更）**

1. 启动 Battle 审查子 Agent，只审查变更的 Gate 章节
2. 审查重点：
   - 新增/修正/删除的数据点是否有充分依据
   - 版本变更是否合理，是否与外部资料一致
   - 结论变更是否符合逻辑，是否有充分支撑
3. 输出 `battle/BATTLE-U{N}-AUDITOR.md`（N 为更新轮次，从 1 开始）
4. 执行层子 Agent 逐条回应，输出 `battle/BATTLE-U{N}-EXECUTOR.md`

**Step 7：更新最终报告**

1. 合并所有 Gate 章节（更新的 + 未更新的）
2. 更新 `{品种目录}/04-final-report.md`
3. 在报告开头增加版本说明：
   ```markdown
   ---
   版本: v{N+1}
   更新时间: {ISO时间}
   更新范围: {更新的 Gate 列表}
   更新原因: {用户提供的更新原因}
   外部资料: EXT-XXX ~ EXT-XXX
   ---
   ```

**Step 8：重新生成 HTML**

1. 调用 `bd-eval-cms/scripts/render_report.sh`，传入更新后的报告内容
2. 使用麦肯锡深蓝风格生成 HTML
3. 上传归档，更新 `state.json` 的 `reportHtmlUrl`

**Step 9：更新 state.json**

1. 更新 `state.json` 的版本字段：
   ```json
   {
     "currentVersion": {N+1},
     "lastUpdatedAt": "{ISO时间}",
     "updatedGates": ["Gate 3", "Gate 6"],
     "updateReason": "{用户提供的更新原因}",
     "externalReferences": ["EXT-001", "EXT-002"]
   }
   ```

**Step 10：追加 execution-log.md**

1. 在 `{品种目录}/execution-log.md` 末尾追加本次增量更新的记录
2. 记录格式：
   ```markdown
   ## 增量更新记录 v{N+1} - {YYYY-MM-DD}
   - 更新范围: {更新的 Gate 列表}
   - 更新原因: {用户提供的更新原因}
   - 外部资料: EXT-XXX ~ EXT-XXX
   - 主要变更: {简要说明新增/修正/删除的关键数据点}
   - 结论变更: {如有结论变更，说明原因}
   - 执行时间: {开始时间} → {结束时间}
   ```

### 9.5.3 完成标志

- `{品种目录}/04-final-report.md` 已更新，版本说明清晰
- `{品种目录}/02-gate-by-chapter/history/{Gate文件名}.v{N}.md` 备份文件存在
- `{品种目录}/references/EXT/` 目录已更新（如有外部资料）
- `battle/BATTLE-U{N}-AUDITOR.md` 和 `battle/BATTLE-U{N}-EXECUTOR.md` 存在（N 为更新轮次）
- `state.json` 已更新，版本字段正确
- `{品种目录}/execution-log.md` 已追加本次更新记录

### 9.5.4 注意事项

- 增量更新时，只重跑用户指定的 Gate，其他 Gate 保持不变
- 如果更新内容影响 Gate 6 结论，必须重跑 Gate 6
- Battle 审查只审查变更的 Gate 章节，提高效率
- 外部资料统一管理在 EXT/ 目录，避免数据孤岛
- 版本备份确保可追溯，支持回滚到历史版本

---

## 9. 版本记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1 | 2026-05-28 | 初始版本,骨架搭建 |
| v0.2 | 2026-06-02 | 双层架构对齐：否决清单8条(含CP-1/CP-2/CP-3) + 引用SKILL.md单一信源 |
| v0.5 | 2026-06-04 | 报告增强 4 项方法：P1 临床五维度评分 + P3 终局五问 + P4 互斥规则框 + P6 置信度分级 |
| v0.6 | 2026-06-08 | 玄关知识库接入：4 步 Stage 2 API + 5 年长链接 + config.yaml 业务固定参数 |
| v0.7 | 2026-06-11 | 彻底解耦 doc-viewer：模板/配色/转换脚本全内联 + render_report.sh 统一入口 |
| v0.7.1 | 2026-06-12 | SOP 报告零件化：SOP.md §6.5 (4 子节) + sub-agent-prompt-template.md TL;DR 5 字段表格 + merge-report.sh 预检 3 项 (TL;DR/体量/Gate6 依赖) |
