# CMS 投前评估 Skill — 执行层

> 本文件定义 Phase 1~5.5 流水线的完整操作细节，包括子 Agent 并行策略、Battle 对抗审查、报告合并脚本、HTML 生成、知识库同步、断点续跑等。
> 规范层规则（Step 1~11）详见 [SKILL.md](./SKILL.md)。

---

## 快速开始

**用户说**：`CMS投前评估：CG-0255、RHOFADE`

**Agent 响应**：
```
收到。开始执行 CMS 投前评估流水线。

评估品种：CG-0255、RHOFADE
预计耗时：约 60-80 分钟/品种

我将按以下阶段执行：
Phase 1: DISCOVERY（宽度搜索 + 业务主体识别）
Phase 2: D-0 路由调度 + 技能确认 Battle
Phase 3: 逐 Gate 深度评估（6-Gate 结构）
Phase 4: Gate Battle 对抗审查
Phase 5: 报告合并 + 质量终检
Phase 5.5: HTML 生成（麦肯锡深蓝风格）+ 上传归档

开始执行...（稍后回报结果）
```

---

## 核心文件索引

| 文件 | 路径 | 用途 |
|------|------|------|
| 本 Skill | `projects/2605281/bd-eval-cms/SKILL.md` | 主入口（规范层） |
| 本文件 | `projects/2605281/bd-eval-cms/EXECUTION.md` | 执行层操作细节 |
| SOP 规范 | `references/SOP.md` | Phase 1-5 完整流程 |
| 总规则 | `references/00_CMS-投前评估技能体系总规则.md` | 顶层规范 |
| 增补条款 | `references/00_体系总规则增补条款_v1.1.md` | 增补规范 |
| 路由器 | `references/D-0_bd-evaluation-router.md` | D-0 路由决策树 |
| 子Agent Prompt | `references/sub-agent-prompt-template.md` | Gate 章节撰写规范 |
| 19个技能定义 | `references/A-*.md` `B-*.md` `C-*.md` `D-*.md` `E-*.md` | 各产品类型评估框架 |
| 归档脚本 | `scripts/archive-links.sh` | 归档到 links.md |
| 合并脚本 | `scripts/merge-report.sh` | Phase 5 纯程序合并报告 |

---

## 触发判断

当用户消息包含以下任一关键词时，Agent 应读取本 SKILL.md 并执行：

**触发词**：`CMS投前评估`、`CMS评估`、`投前评估`

**辅助触发信号**：
- 提到康哲/CMS/深康/德镁/维盛/天津康哲/康联达等业务主体
- 提到 A-0/A-1/A-2/A-3/A-4/A-5/A-6/A-7/A-8/B-1/B-2/B-3/C-1/C-2/C-3/D-0/D-1/D-2/D-3/E-1 等技能编号
- 提到"帮康哲评估""康哲引进分析""投委会决策包"

**排除规则**：以下情况不触发本 Skill，应路由到 bd-eval（方案A）：
- 用户说"BD评估""跑品种"但未提及 CMS 相关业务主体
- 通用 BD 评估需求（非康哲专属）

---

## 执行模式

本 Skill 支持三种执行模式，根据用户输入自动判断：

### 模式判断规则

| 用户输入 | 判断为 | 说明 |
|---------|--------|------|
| `CMS投前评估：{品种名}` | 全量评估 | 从 Phase 1 跑到 Phase 5.5 |
| `CMS投前评估：{品种名}` + 上传文件/指定路径 | 全量评估 + 外部资料 | 同上，但先读取外部资料，搜索策略调整为补充验证 |
| `更新{品种名} Gate 2、Gate 6` + 可选补充资料 | 增量更新 | 只重跑指定 Gate，更新合并报告 |

### 模式 1：全量评估（默认）

即下方"完整流水线执行（默认）"章节描述的流程。从 Phase 1 DISCOVERY 开始，一直执行到 Phase 5.5 HTML 生成。

### 模式 2：全量评估 + 外部资料注入

当用户在发起评估时同时提供了参考资料（上传文件、知识库链接、项目目录内文档），执行全量评估流程，但做以下调整：

**Phase 1 调整**：
1. 先处理外部资料（见下方"外部资料处理流程"）
2. 基于 EXT- 资料内容，调整搜索策略：已有确切数据的维度减少搜索，缺少数据的维度加强搜索
3. Discovery 文件中标注"本评估基于 N 份外部资料 + M 次联网搜索"

**Phase 3 调整**：
1. Gate 子 Agent 在搜索前先列出 EXT/ 目录下已有文件
2. EXT- 资料优先于联网搜索，联网搜索仅用于交叉验证和补充
3. 引用外部资料时使用 `[EXT-XXX]` 编号

### 模式 3：增量更新

当品种目录已存在（state.json 中 phase 不是空），且用户明确指定要更新某些 Gate 时触发。

**前置条件**：
- `{品种目录}/state.json` 存在
- 用户指定了要更新的 Gate 编号

**执行流程**：

1. **读取现有状态**：读取 state.json，确认品种存在 + 当前版本
2. **处理补充资料**（如有）：存入 EXT/EXT-XXX.md（每份资料一个独立文件）
3. **版本备份**：将待更新 Gate 的当前文件复制到 `02-gate-by-chapter/history/`，命名 `{Gate文件名}.v{N}.md`
4. **重跑指定 Gate**：spawn Gate 子 Agent（注入已有上下文 + EXT 资料 + 对应前缀）
5. **Gate 6 依赖检查**：如果更新了 Gate 1-5 中的任何一个，必须检查 Gate 6 是否需要同步更新（Orchestrator 判断，基于 Gate 6 是否引用了被更新 Gate 的结论）
6. **Battle 审查**：只审查更新的 Gate 的变更（不重审未变更的 Gate）
7. **更新最终报告**：合并为 `04-final-report.md`（版本 +1）
8. **重新生成 HTML**：生成 `REPORT.html`（版本 +1）
9. **更新 state.json**：版本号 +1，记录更新历史
10. **追加 execution-log.md**

**版本管理规则**：
- 全量评估产生的 Gate 文件版本号为 1
- 增量更新时，被更新的 Gate 版本 +1，未更新的保持不变
- 最终报告版本 = max(所有 Gate 版本)
- history/ 目录只保留被更新过的 Gate 的历史版本
- 历史报告文件命名：`04-final-report.v{N}.md`、`REPORT.v{N}.html`
- 每次更新必须触发 Battle 审查（只审更新的 Gate）

**Battle 命名规则**：
- 首次全量评估：`BATTLE-R1-AUDITOR.md` / `BATTLE-R1-EXECUTOR.md`
- 第1轮增量更新：`BATTLE-U1-AUDITOR.md` / `BATTLE-U1-EXECUTOR.md`
- 第2轮增量更新：`BATTLE-U2-AUDITOR.md` / `BATTLE-U2-EXECUTOR.md`

### 外部资料处理流程

适用于模式 2 和模式 3。当用户提供参考资料时：

**资料来源识别**：

| 来源方式 | 处理方法 | 示例 |
|---------|---------|------|
| 上传文件（PDF/Word/Excel/图片） | 用对应工具读取内容（pdf/excel/image） | 用户上传 GLISTEN_临床报告.pdf |
| 在线链接（知识库/网页） | 用 web_fetch 抓取内容 | 用户给 https://docs.xxx.com/yyy |
| 项目目录内文档 | 直接读取，不复制 | {品种目录}/合作方资料/xxx.pdf |

**统一存入 EXT/EXT-XXX.md**（前缀 `EXT-`，从 EXT-001 递增，每份资料一个独立文件）：

```markdown
# [EXT-001] {标题/文件名}
- **来源方式**: 上传文件 / 在线链接 / 项目目录内
- **原始位置**: 文件名 或 URL 或 项目内路径
- **获取方式**: 文件读取 / web_fetch / 直接引用
- **提供方**: 用户 / 合作方 / 内部部门
- **资料类型**: 临床数据 / 市场调研 / 财务测算 / 注册文件 / 竞品分析 / 其他
- **覆盖Gate**: Gate 2 / Gate 3（AI自动判断，基于内容与Gate评估维度的匹配度）
- **提供时间**: 2026-05-29

## 原文内容
（提取的关键信息，尽量完整保留）

## 关键数据点
- 具体数字/结论1
- 具体数字/结论2
```

**正文引用**：统一使用 `[EXT-XXX]` 格式。

**搜索策略调整**：当 EXT- 资料已覆盖某维度的确切数据时，联网搜索减少为 1-2 次交叉验证（而非原本的 3+ 次）。当 EXT- 资料缺少某维度数据时，联网搜索加强补充。

---

## 完整流水线执行概览

```
用户提供品种名称列表 + 业务主体信息
    ↓
Phase 1: DISCOVERY（宽度搜索 + 业务主体识别 + 产品类型初判）
Phase 2: D-0 路由调度（自动匹配技能编号）+ 技能确认 Battle
Phase 3: GRV 逐 Gate 深度评估（6-Gate 结构，批次并行）
Phase 4: Gate Battle 对抗审查（审查层 vs 执行层）
Phase 5: 报告合并 + 质量终检（8项）
    ↓
HTML 生成（麦肯锡深蓝 #1a3a5c）+ 上传 doc.20100706.xyz + 归档
```

---

## Phase 1: DISCOVERY

### 执行者
主会话（TPR Orchestrator）

### 操作步骤

**1. 标的方画像确认（不强制阻塞）**
向用户询问：
- 合作方是谁？（原研公司/Biotech/代理商）
- 目标业务主体？（深康/德镁/维盛/院外/天津康哲/康联达）
- 评估阶段？（A公开信息 / B立项后 / C投委会）

如果用户说"不知道"或"先跑吧"，允许跳过，但 Gate 1 标注"⚠️ 基于公开信息"。

**1.5 生成案件代号**

案件代号格式：`YYMMDD-XXXX`（日期 + 4字母品种缩写）

- 取当前日期生成 YYMMDD（6位）
- 从品种名生成 4 字母缩写（参见知识库同步章节的映射表）
- 英文品种名：取前 4 个辅音字母，大写。如 Gvoke HypoPen → GVHP
- 中文品种名：取每个字拼音首字母，最多 4 个。如 乌司他丁 → WSTD
- 示例：`260531-LNXB` = 2026年5月31日，利奈昔巴特

此代号用于知识库目录命名，全局唯一，不会冲突。

**2. 创建品种目录**
```bash
mkdir -p projects/2605281/bd-eval-cms/{品种名}/
mkdir -p projects/2605281/bd-eval-cms/{品种名}/02-gate-by-chapter/history/
mkdir -p projects/2605281/bd-eval-cms/{品种名}/battle/
mkdir -p projects/2605281/bd-eval-cms/{品种名}/references/P1/
```

**3. 宽度搜索（web_search ≥5 次）+ 参考文献采集**
覆盖：通用名/代号、原研公司、作用机制、适应症、注册状态、临床阶段、市场规模、竞争格局、专利、合作历史

**参考文献采集（强制）**：
- 每次搜索后，对每个搜索结果中有价值的页面执行 `web_fetch` 抓取内容
- 有价值的判断标准：包含具体数据、结论、事实陈述的页面
- 不抓取：纯导航页、广告页、无实质内容的列表页
- 抓取内容存入 `{品种目录}/references/P1/P1-XXX.md`（每篇文章一个独立文件）
- 参考文献格式：
  ```markdown
  # [P1-001] 文章标题
  - **URL**: https://...
  - **抓取时间**: 2026-05-29 11:00 CST
  - **来源类型**: 官方|学术|行业媒体|公司公告|监管数据库

  ## 原文内容
  （web_fetch 抓取的完整内容，尽量完整保留）

  ## 关键数据点
  - 具体数字/结论1
  - 具体数字/结论2
  ```
- **Phase 1 使用固定前缀 `P1-`，编号从 P1-001 起连续递增**

**4. 写入 `01-discovery.md`**
包含：品种基本信息、业务主体初步判断、产品类型初步判断（为 D-0 路由准备）

**必须包含路由决策单**：
```
## 路由决策单
- 推荐主技能：{技能编号，如 A-1}
- 串接链路：{技能编号列表，如 D-1 → D-2 → A-1 → A-6 → D-3}
- 财务门槛类型：{创新药/仿制药/医美/消费健康}
- 路由依据：{一句话说明为什么选这个技能}
```

**5. 创建 `state.json`**
```json
{
  "caseCode": "YYMMDD-XXXX",
  "name": "{品种名}",
  "displayName": "{显示名}",
  "scheme": "B",
  "businessEntity": "待确认",
  "routedSkill": "待路由",
  "routedChain": [],
  "phase": "discovery_complete",
  "startedAt": "{ISO时间}",
  "currentVersion": 1,
  "gateVersions": {
    "One-pager": 1,
    "Gate-1": 1,
    "Gate-2": 1,
    "Gate-3": 1,
    "Gate-4": 1,
    "Gate-5": 1,
    "Gate-6": 1
  },
  "financialThresholdType": "待判断",
  "routingDecision": {
    "recommendedSkill": "{技能编号}",
    "chain": ["D-1", "D-2", "{主技能}", "D-3"],
    "thresholdType": "创新药|仿制药|医美|消费健康",
    "rationale": "{路由依据}"
  },
  "discovery": {
    "searches": 5,
    "sources": ["搜索来源列表"],
    "productType": "创新药|仿制药|医美|消费健康|平台型",
    "confidence": "高|中|低",
    "referenceCount": 0
  },
  "updateHistory": [],
  "references": {
    "file": "references/REFERENCES.md",
    "count": 0,
    "prefixes": ["P1"]
  }
}
```

**✅ Phase 1 完成标志**：`01-discovery.md` 存在 + `state.json` 已更新

---

## Phase 2: D-0 路由调度 + 技能确认 Battle

### 执行者
主会话调度 + 审查层子Agent

### 操作步骤

**1. 执行 D-0 路由决策树**

读取 `references/D-0_bd-evaluation-router.md`，根据 discovery 结果按决策树匹配：

```
标的输入
├── 自主研发（全球IP持有）→ A-3
├── 国际市场（港澳台/东南亚/GCC/澳新/拉美）
│   ├── 单品单市场 → C-1
│   ├── 单品多市场 → C-2
│   └── 组合策略 → C-3
├── 多标的横向比选（3个以上）→ A-7
├── 医美产品 → B-1（单标的）/ B-2（组合）
├── 消费健康/OTC → B-3
├── 国内Biotech（股权+商业化）→ E-1
├── 化学药品
│   ├── 高壁垒仿制药（3/4类）→ A-8
│   ├── 生物类似药（3.3类）→ A-4
│   ├── 海外已上市/中国未上市（5.1/6类）→ A-1
│   ├── 国内合作·成熟阶段 → A-2
│   ├── 已上市代理权 → A-5
│   └── 院内→院外延伸 → A-6
└── 需要市场深度分析 → D-2
```

**排除规则（路由前必查）**：
- 以色列/印度/韩国市场 → 一票否决，停止路由
- 院外品种与 B-1/A-4/A-3 重叠 → B-3 品类筛选失败

**2. 输出路由决策单**
```
路由编号：D0-YYYY-NNN
标的：{品种名}
产品类型：{判断结果} → 置信度：{高/中/低}
业务主体：{匹配结果}
推荐主技能：{技能编号}
推荐串接链路：{技能编号列表}
数据缺口：Top 3~5
```

**3. 财务硬门槛初判**

根据产品类型，从总规则第5节查表确认财务门槛类型（创新药/仿制药/医美/消费健康）。

**4. 技能确认 Battle（强制，不可跳过）**

Spawn 审查层子Agent（独立）：
- 读取 01-discovery.md + D-0 路由决策树 + 对应技能定义
- 独立判断路由是否正确
- 如同意 → 确认
- 如不同意 → 争议点写入 `battle/ROUTE-SELECTION-AUDITOR.md`

**5. 更新 state.json**
```json
{
  "routedSkill": "A-1",
  "routedChain": ["D-1", "D-2", "A-1", "D-3"],
  "financialThresholdType": "创新药"
}
```

**✅ Phase 2 完成标志**：`battle/ROUTE-SELECTION-AUDITOR.md` 存在 + `state.json` 已更新

---

## Phase 3: 逐 Gate 深度评估

### 执行者
GRV子Agent（Sessions Spawn，批次并行）

### 执行策略

**One-pager 先跑，后续 Gate 每3个一批并行。**

```
章0: One-pager 终局先立（必须先跑完）
    ↓
批次1: Gate 1 前提门 | Gate 2 定调门 | Gate 3 证据门（3个子Agent并行）
    ↓
批次2: Gate 4 支付门 | Gate 5 成本门（2个子Agent并行）
    ↓
Gate 6 可做门（串行，依赖前面所有Gate结论）
    ↓
验证: 批量交叉检查
    ↓
修正
```

**并行约束**：
- 最大并发 3 个子Agent
- Gate 6 必须串行（需要 Gate 1-5 结论）
- 并行 Gate 各自独立搜索

**参考文献采集（每个 Gate 子Agent 强制）**：
每个 Gate 子Agent 在 spawn 时由 Orchestrator 分配唯一前缀，task 指令必须包含：
1. **你的参考文献前缀：{前缀}**（如 G1-、G2-、G3-、G4-、G5-、G6-、OP-、BT- 等）
2. **你的参考文献目录：{品种目录}/references/{前缀}//**
3. **搜索前**：先列出 `{品种目录}/references/{前缀}/` 目录下已有文件，了解已抓取 URL 避免重复，以及引用前面节点的数据时使用对应前缀编号（如 `[P1-001]`、`[G3-005]`）
4. 每次搜索后，对有价值的结果执行 `web_fetch` 抓取内容
5. 新的参考文献写入 `{品种目录}/references/{前缀}/{前缀}-XXX.md`（编号从 {前缀}-001 开始独立递增）
6. 报告正文中每个数据点必须标注 `[{前缀}-XXX]` 引用编号（如 `[G1-003]`）
7. 不允许出现"外网核查""分析推断"等无具体引用的标注
8. 报告开头列出本 Gate 使用的参考文献编号清单

**预计耗时**：串行 20-28 min → 并行 12-18 min（提速 ~40%）

### 操作步骤

1. 读取 `references/sub-agent-prompt-template.md` 作为子Agent prompt 模板
2. 读取对应技能定义文件（如 A-1）获取评估章节结构
3. **One-pager 必写**：终局五问（成功定义/价值主张/最大风险/止损边界/决策人）
4. Gate 1-3 批次并行执行
5. Gate 4-5 批次并行执行
6. Gate 6 串行执行
7. 每批完成后派验证子Agent批量交叉检查
8. 根据验证结果修正

**每个 Gate 必须输出结论卡**：
```
【Gate N：XXX门】
结论：通过 / 条件通过 / 停止
置信度：高 / 中 / 低
关键支撑证据：
  1. ...
  2. ...
  3. ...
需补充证据 Top 5：
  1. ...
红旗事项：（如有）
下一步行动：
```

**章节标签要求**：
- 阶段A内容标注 `[阶段A]`
- 阶段B内容标注 `[阶段B]`

**置信度标注要求**：
- A级（≥2个独立来源交叉验证）：无需标注
- B级（单一权威来源）：标注来源名称
- C级（仅内部/合作方提供）：标注 `[C级-待验证]`
- D级（基于假设推算）：标注 `[D级-基于假设]`

**信息来源标注要求**（四分法）：
- `来源：内部评估——[文件名]（日期）`
- 正文内引用标注 `[N]`，附参考文献
- `需进一步与[对象]沟通/确认`
- `分析推断` 或 `综合分析`

**✅ Phase 3 完成标志**：One-pager + Gate 1-6 全部章节文件存在于 `02-gate-by-chapter/`

---

## Phase 4: Gate Battle 对抗审查

### 执行者
两个独立子Agent（审查层 + 执行层），主会话串行调度

### 操作步骤

1. **审查层子Agent**：以 CMS 体系标准审查全部 Gate 章节 → 输出异议清单
   - 每个 Gate 结论卡的置信度是否合理
   - 财务指标是否达到硬门槛（对照总规则第5节）
   - 一票否决清单是否完整核查（8条体系级（含CP-1/CP-2/CP-3合作可能性否决）+ 技能专属）
   - 置信度标注是否合规（C/D级数据是否在执行摘要中披露）
   - 信息冲突是否正确标记
   - 来源标注是否覆盖
   - 财务缩写首次出现是否标注中文全称
   - 输出：`battle/BATTLE-R1-AUDITOR.md`

2. **执行层子Agent**：逐条回应审查层异议
   - 接受（说明改什么）或拒绝（附证据）
   - 更新对应 Gate 章节文件
   - 输出：`battle/BATTLE-R1-EXECUTOR.md`

3. **审查层重审**：如有多轮，最多 3 轮

4. 生成 `03-battle-summary.md`（结论汇总 + 未解决争议点）

**✅ Phase 4 完成标志**：`03-battle-summary.md` + `03-battle.md` 存在

---

## Phase 5: 报告合并 + 质量终检

### 执行者
主会话（调度）+ 合并脚本（程序行为）+ AI（仅执行摘要）

### ⚠️ 核心原则：合并是程序行为，不是 AI 行为

**合并 = 纯文件拼接**。不做任何删除、改写、润色、摘要化。
原始评估文档的每个字都必须原样出现在最终报告中。

AI 唯一参与的部分：生成执行摘要（基于所有 Gate 结论卡汇总）。
其余全部由 `scripts/merge-report.sh` 脚本完成。

### 操作步骤

**Step 1：参考文献索引生成（程序行为）**
- 遍历 `{品种目录}/references/` 下所有前缀目录（P1/、OP/、G1/、G2/、...、BT/、EXT/ 等）
- 读取每个 `{前缀}/` 目录下所有 .md 文件的头部元数据（标题、URL、抓取时间）
- 生成 `{品种目录}/references/REFERENCES.md` 纯索引文件（只含标题+URL+摘要，不含原文）
- 参考文献表格式：`[P1-001] 标题 — URL（抓取时间）`、`[G1-003] 标题 — URL（抓取时间）`

**Step 2：执行合并（程序行为）**

运行合并脚本：
```bash
bash scripts/merge-report.sh "{品种目录路径}"
```

脚本执行逻辑：
1. 从 state.json 读取案件代号、品种名等元信息 → 生成封面
2. 写入执行摘要占位符（`<!-- EXECUTIVE_SUMMARY_PLACEHOLDER -->`）
3. 依次 cat 拼接所有源文件（01-discovery.md → One-pager.md → Gate 1-6 → battle → REFERENCES.md）
4. 输出 `04-final-report.md`

**Step 3：AI 生成执行摘要（唯一需要 AI 的步骤）**

AI 读取所有 Gate 结论卡，生成执行摘要，替换占位符：
- 结论先行（推进/条件推进/停止）
- 核心指标一览
- 关键风险提示（含 C/D 级数据披露）
- 推荐行动

**Step 4：格式校验（程序行为）**

合并脚本内置格式校验，自动检查：

| 检查项 | 标准 | 说明 |
|--------|------|------|
| 报告/源文件行数比 | ≥ 95% | 纯合并应接近 100%，封面和章节标题行会使比例略高 |
| 章节完整性 | 所有 Gate 章节标题存在 | 检查报告内是否包含所有必要章节 |
| 结论卡存在 | 每个 Gate 区域内含"结论卡"关键词 | 防止空章节 |

**如果报告/源文件比 < 90%，脚本报警，说明合并可能丢内容。**

**Step 5：质量终检（8+2 项）**

原有 8 项（AI 执行）：
- ① Gate 1-6 结论卡完整性（每Gate都有结论卡）
- ② 财务硬门槛达标情况（对照总规则第5节）
- ③ 一票否决清单核查（8条体系级（含CP-1/CP-2/CP-3合作可能性否决）+ 技能专属）
- ④ 置信度标注完整性（关键数据不超过3处缺失）
- ⑤ 信息冲突汇总表（附录C）非空
- ⑥ 阶段标签标注正确（[阶段A]/[阶段B]）
- ⑦ 来源四分法标注覆盖
- ⑧ 财务缩写首次出现标注中文全称

新增 2 项内容充分性检查：
- ⑨ **Gate 章节体量**：每个 Gate 章节 ≥ 200 行（低于此标准说明评估不充分）
- ⑩ **合并完整性**：最终报告行数 ≥ 源文件总行数 × 95%（确保无内容丢失）

**Step 6：更新 state.json**
```json
{
  "phase": "report_finalized",
  "finalReport": "04-final-report.md",
  "conclusion": "推进/条件推进/停止",
  "currentVersion": 1,
  "qualityCheck": {
    "gateCards": "PASS",
    "financialThreshold": "PASS/FAIL",
    "vetoCheck": "PASS/FAIL",
    "confidenceAnnotation": "PASS/FAIL",
    "conflictSummary": "PASS",
    "stageLabels": "PASS",
    "sourceAnnotation": "PASS",
    "financialAbbreviation": "PASS",
    "gateVolume": "PASS/FAIL",
    "mergeIntegrity": "PASS/FAIL"
  },
  "completedAt": "{ISO时间}"
}
```

**✅ Phase 5 完成标志**：`04-final-report.md` 存在 + 格式校验通过 + 质量终检 10 项通过

---

## Phase 5.5: HTML 生成 + 上传归档

### 核心原则：程序化生成，不依赖 AI

HTML 报告生成是**纯程序行为**——用 Python 脚本将合并后的 Markdown 转换为 HTML，套用风格 12 骨架和配色。
AI 不参与 HTML 内容生成，只负责：
1. 选择配色方案
2. 执行脚本命令
3. 上传和归档

### 报告风格：风格 12（CMS 投前评估专用）

**4 套配色方案可选**：

| 配色名 | 主色 | 适用场景 |
|--------|------|----------|
| mckinsey-navy | #1a3a5c | 默认，经典咨询风格 |
| investment-blue | #1D4ED8 | 投行/金融报告 |
| burgundy-wine | #7B2D3B | 稳重权威 |
| forest-teal | #1B6B5A | 冷静理性 |

用户未指定配色时，默认使用 **mckinsey-navy**。

### CMS 专属组件（已内置于风格 12 骨架）

- Gate 结论卡：`.gate-pass`（绿）/ `.gate-conditional`（黄）/ `.gate-stop`（红）
- 置信度徽章：`.conf-a` / `.conf-b` / `.conf-c` / `.conf-d`
- Battle 对抗审查：`.battle-auditor` / `.battle-executor`
- 信息冲突框：`.conflict-box`
- 一票否决框：`.veto-box`
- 阶段标签：`.stage-a` / `.stage-b`
- DRL 优先级：`.drl-p0` / `.drl-p1` / `.drl-p2`
- 风险等级：`.risk-high` / `.risk-medium` / `.risk-low`
- 中立审查框：`.neutral-review`

### 生成命令

```bash
python3 scripts/convert-md-to-html.py \
  "{品种目录}" \
  {配色名} \
  "{品种目录}/REPORT.html"
```

示例：
```bash
python3 scripts/convert-md-to-html.py \
  MB-001-Mage-Biologics \
  mckinsey-navy \
  MB-001-Mage-Biologics/REPORT.html
```

脚本自动完成：
1. 读取 `04-final-report.md`
2. 从 `state.json` 提取封面元信息
3. 识别 Gate 结论卡、Battle 框、置信度标注等 CMS 专属结构
4. 套用 skeleton.html 骨架 + 配色方案
5. 输出完整 HTML 文件

### 上传到 doc.20100706.xyz

```bash
curl -s -X POST https://doc.20100706.xyz/upload \
  -F "file=@{品种目录}/REPORT.html;filename={品种名}-CMS投前评估报告.html"
```

返回 `raw_url`，记录到 `state.json` 的 `reportHtmlUrl`。

### 归档操作

```bash
scripts/archive-links.sh \
  "{品种slug}" \
  "https://doc.20100706.xyz/raw/{report_id}"
```

### 知识库自动同步（Phase 5.5 必执行）

完成 HTML 上传后，自动将品种目录下所有文件同步到玄关知识库。

**配置**：
- API 地址：`https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/uploadContent`
- appKey：`mN6bVc2Xz9Lk4Jh7Gt5Rf3Wp1Yq8As0D`
- projectId：`2060176831872499713`（产品引进知识库）

**案件代号命名规范（v2026.5.31）**：

格式：`YYMMDD-XXXX`（日期 + 4字母品种缩写）

| 部分 | 说明 | 示例 |
|------|------|------|
| YYMMDD | 评估执行日期（6位） | 260531 |
| XXXX | 品种4字母缩写（见下方映射表） | LNXB |

**4字母缩写生成规则**：
- 英文品种名：取前4个字母（去空格和连字符），大写。如 Gvoke HypoPen → GVHP
- 中文品种名：取每个字拼音首字母，最多4个。如 乌司他丁 → WSTD
- 已有缩写映射表（子Agent 必须使用此表中的缩写）：

| 品种 | 缩写 | 品种 | 缩写 |
|------|------|------|------|
| 利奈昔巴特 | LNXB | 乌司他丁 | WSTD |
| Gvoke HypoPen | GVOK | FABIOR | FABI |
| 硫酸氢氯吡格雷片 | LSQL | 非索非那定干混悬剂 | FSFN |
| DYX116 | DYXX | Humatrope | HUMA |
| 馥霖安 | FLAA | 马来酸非尼拉敏滴眼液 | MLSF |
| 注射用心肌肽 | ZSYX | | |

新品种由子Agent 按规则自动生成（pypinyin 拼音首字母），写入 state.json 的 caseCode 字段。sync-to-knowledge-base.sh 会自动从 state.json 读取或从目录名生成，不需要手动指定。

**同步目录**：`{YYMMDD}/{YYMMDD-XXXX}/`
例如：`260531/260531-LNXB/`

**调用方式**：

```bash
bash scripts/sync-to-knowledge-base.sh "{品种目录路径}"
# 案件代号自动生成，无需手动指定
# 也可手动指定：
bash scripts/sync-to-knowledge-base.sh "{品种目录路径}" "260531-LNXB"
```

脚本会自动：
1. 从 state.json 读取品种名
2. 生成 `YYMMDD-XXXX` 格式的案件代号
3. 将 caseCode 写入 state.json
4. 上传所有文件
5. 回写同步结果到 state.json 的 knowledgeBaseSync 字段

**同步文件清单**（遍历品种目录，逐文件上传）：

| 本地路径 | 知识库 folderName | fileName | fileSuffix |
|---------|------------------|----------|-----------|
| state.json | `{YYMMDD}/{YYMMDD-XXXX}` | state | json |
| 01-discovery.md | `{YYMMDD}/{YYMMDD-XXXX}` | 01-discovery | md |
| One-pager.md | `{YYMMDD}/{YYMMDD-XXXX}` | One-pager | md |
| Gate 1-6 文件 | `{YYMMDD}/{YYMMDD-XXXX}` | Gate-N-{名称} | md |
| 03-battle-summary.md | `{YYMMDD}/{YYMMDD-XXXX}` | 03-battle-summary | md |
| 04-final-report.md | `{YYMMDD}/{YYMMDD-XXXX}` | 04-final-report | md |
| REPORT.html | `{YYMMDD}/{YYMMDD-XXXX}` | REPORT | html |
| references/*.md | `{YYMMDD}/{YYMMDD-XXXX}/references` | {前缀}-{序号} | md |
| EXT/*.md | `{YYMMDD}/{YYMMDD-XXXX}/EXT` | EXT-{序号} | md |

---

## 并行执行策略

### 批次规划

| 批次 | Gate | 并行数 | 依赖关系 |
|------|------|--------|---------|
| 章0 | One-pager | 1（先跑） | 无 |
| 批次1 | Gate 1 + Gate 2 + Gate 3 | 3 | One-pager 完成 |
| 批次2 | Gate 4 + Gate 5 | 2 | 批次1 完成 |
| 批次3 | Gate 6 | 1 | 批次2 完成 |

### 参考文献前缀分配

| Gate | 前缀 | 目录 |
|------|------|------|
| One-pager | OP- | references/OP/ |
| Gate 1 | G1- | references/G1/ |
| Gate 2 | G2- | references/G2/ |
| Gate 3 | G3- | references/G3/ |
| Gate 4 | G4- | references/G4/ |
| Gate 5 | G5- | references/G5/ |
| Gate 6 | G6- | references/G6/ |
| Battle | BT- | references/BT/ |

---

## 子Agent 超时应对与断点续跑

### 超时阈值

| 阶段 | 单次超时 | 建议动作 |
|------|---------|---------|
| Phase 1 DISCOVERY | 10 min | 减少搜索次数到 3 次，继续 |
| Phase 3 Gate 子Agent | 15 min/个 | 先完成能完成的，其他重跑 |
| Phase 4 Battle | 20 min | 减少审查轮次到 1 轮 |
| Phase 5 合并 | 5 min | 通常不超时 |

### 断点续跑（状态位机制 · v2026.6.11）

**核心设计**：`state.json.gateStatus` 字段记录每个阶段的独立状态位，实现"AI 自启协议"。

**状态位枚举**：
- `pending` — 未开始
- `in_progress` — 子Agent 正在跑（带 `lastHeartbeat` 时间戳）
- `completed` — 已完成
- `failed` — 执行失败

**标准 12 个状态位**：
```
phase-1, phase-2, one-pager, gate-0, gate-1, gate-2, gate-3, gate-4, gate-5, phase-4-battle, phase-5-merge, phase-5-5-html
```

**故障检测**：某个状态位为 `in_progress` 但 `lastHeartbeat` > 30 min 未更新 → 视为僵尸，自动标记为 `failed` → 续跑。

### 智能续跑入口

**商机池场景**（全自动静默）：

```bash
# 1. 商机入池
mkdir bd-opportunities/260615-FOO/
cp 合作方资料/* bd-opportunities/260615-FOO/

# 2. 调度器（人不定时）抽出商机
./scripts/run.sh 260615-FOO
# → AI 读 state.json → 不存在 → 从 phase-1 全量启动
# → 全程静默，跑完上传 doc.20100706.xyz
```

**手动场景**（指定重跑）：
```bash
./scripts/run.sh 260611-EPIO --status         # 查看状态
./scripts/run.sh 260611-EPIO --rerun=Gate-3   # 显式重跑 Gate 3（同时置下游 pending）
./scripts/run.sh 260611-EPIO --rerun=all      # 强制全量重跑
./scripts/run.sh 260611-EPIO --mode=semi      # 半自动（每阶段后 push 确认）
./scripts/run.sh --list                        # 列出所有项目状态
```

### AI 自启协议（必须遵循）

当 AI 重新被调用运行某个项目时，必做 3 步（**不要向用户询问起点**）：

1. **读 `state.json`**：检查是否存在 + 读 `gateStatus` + 读 `lastHeartbeat`
2. **判定起点**：
   - state.json 不存在 → 从 `phase-1` 全量启动
   - 有 `in_progress` 且 heartbeat < 30min → 续跑该 Gate
   - 有 `in_progress` 但 heartbeat > 30min → 标记 `failed`，续跑
   - 有 `failed` → 续跑该 Gate
   - 全部 `completed` → 报告"已完成"，等显式指令
   - `--rerun=Gate-X` → 强制重跑该 Gate，同时把下游所有 Gate 置 `pending`
3. **执行 + 更新状态**：启动对应 sub-agent，启动时写 `in_progress` + 更新 `lastHeartbeat`，完成时写 `completed` + 写 `lastHeartbeat`

### 与旧版断点续跑的差异

| 旧版（仅超时重跑） | 新版（状态位机制） |
|---|---|
| 只在子Agent 超时时触发 | 任何中断场景都可触发（包括商机池） |
| 需要人判断"从哪里续" | AI 自动判定 |
| 没有僵尸检测 | heartbeat > 30min 自动 fail |
| state.json 改不改动 | state.json 加 `gateStatus` + `lastHeartbeat` + `inProgressGate` |
| 不支持下游联动 | 重跑 Gate X → 下游全部 pending（保证一致性） |

### 当某个子Agent 超时时

1. **state.json 状态位保持 `in_progress`**（不重置为 pending）
2. **Spawn 新子Agent 重跑**（注入 `本次是断点续跑，请从 checkpoint 继续`）
3. **保留已抓取的参考文献**（不重新搜索已抓取的 URL）
4. **更新 state.json**：状态位改 `completed`，`lastHeartbeat` 写新时间戳
5. **下游联动**：如果当前 Gate 的下游也是 `pending` 状态，自动续跑下游

---

## Verify 规则

### Phase 级 verify

| Phase | Verify 条件 | FAIL 时动作 |
|-------|-----------|-----------|
| Phase 1 | `01-discovery.md` 存在 + `state.json` 更新 | 暂停，要求补充 |
| Phase 2 | `battle/ROUTE-SELECTION-AUDITOR.md` 存在 + 路由结论被确认 | 暂停，审查争议 |
| Phase 3 | One-pager + Gate 1-6 全部文件存在 | 只重跑缺失的 Gate |
| Phase 4 | `03-battle-summary.md` + `03-battle.md` 存在 | 重跑 Battle |
| Phase 5 | `04-final-report.md` 存在 + 格式校验通过 + 10项质量终检通过 | 重跑对应步骤 |

### Gate 章节 verify（每批次完成后）

1. **文件存在性**：每个 Gate 文件存在
2. **结论卡完整性**：每个 Gate 文件包含 `【Gate N：` 和 `结论：` 关键词
3. **置信度合规**：C级数据有 `[C级-待验证]`，D级数据有 `[D级-基于假设]`
4. **引用完整性**：关键数据点有 `[{前缀}-XXX]` 引用标注
5. **章节体量**：每个 Gate 章节 ≥ 200 行

---

## 执行日志格式

每次 Phase 完成后，主会话在品种目录下创建 `execution-log.md`：

```markdown
# {品种名} 执行日志

## Phase 1 DISCOVERY
- 开始时间：2026-05-29 14:00 CST
- 结束时间：2026-05-29 14:35 CST
- 搜索次数：6
- 参考文献：P1-001 ~ P1-008（8篇）
- 产物：01-discovery.md
- 异常：无

## Phase 2 路由
- 开始时间：2026-05-29 14:35 CST
- 结束时间：2026-05-29 14:50 CST
- 路由结果：A-1（海外已上市·中国未上市）
- Battle 结果：审查层同意路由结论
- 产物：battle/ROUTE-SELECTION-AUDITOR.md
- 异常：无

## Phase 3 批次1（Gate 1+2+3）
- 开始时间：2026-05-29 14:50 CST
- 结束时间：2026-05-29 15:40 CST
- 并行子Agent：3
- 产物：Gate 1/2/3 章节文件
- 异常：无

...
```

---

## 健康检测

在每次 Phase 3 批次执行前，执行以下健康检测：

```bash
# CPU 使用率
ps aux --sort=-%cpu | head

# 磁盘使用率
df -h

# 异常进程检测
ps aux | grep -E "(python3|node|openclaw)" | grep -v grep
```

**触发暂停的条件**：
- CPU 使用率持续 > 90%（超过 5 min）
- 磁盘使用率 > 90%
- 异常进程检测到 zombie 进程

**处理方式**：暂停子Agent，报告给用户，等待清理后继续。
