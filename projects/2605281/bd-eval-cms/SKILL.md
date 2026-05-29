---
name: bd-eval-cms
description: "CMS（康哲药业）投前评估体系 — 基于19个技能 + 6-Gate门控的完整BD评估流水线。触发词：CMS投前评估、CMS评估、投前评估"
version: "0.1.0"
homepage: projects/2605152/bd-eval-cms/PLAN.md
dependencies:
  - doc-viewer (required, for HTML report generation)
  - multi-search (required, for web_search infrastructure)
---

# CMS 投前评估 Skill

> **本 Skill 可被任何 Agent 独立执行**。当收到 CMS 投前评估请求时，
> 读取本文件，按 Phase 1~5.5 顺序执行即可。
> 所有技能定义文件均在 `references/` 下，无需额外配置即可开始。

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

## 核心文件索引

| 文件 | 路径 | 用途 |
|------|------|------|
| 本 Skill | `projects/2605152/bd-eval-cms/SKILL.md` | 主入口 |
| SOP 规范 | `references/SOP.md` | Phase 1-5 完整流程 |
| 总规则 | `references/00_CMS-投前评估技能体系总规则.md` | 顶层规范 |
| 增补条款 | `references/00_体系总规则增补条款_v1.1.md` | 增补规范 |
| 路由器 | `references/D-0_bd-evaluation-router.md` | D-0 路由决策树 |
| 子Agent Prompt | `references/sub-agent-prompt-template.md` | Gate 章节撰写规范 |
| 19个技能定义 | `references/A-*.md` `B-*.md` `C-*.md` `D-*.md` `E-*.md` | 各产品类型评估框架 |
| 归档脚本 | `scripts/archive-links.sh` | 归档到 links.md |

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

## 完整流水线执行（默认）

### 流程概览

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

**2. 创建品种目录**
```bash
mkdir -p projects/bd-eval-cms/{品种名}/
mkdir -p projects/bd-eval-cms/{品种名}/02-gate-by-chapter/
mkdir -p projects/bd-eval-cms/{品种名}/battle/
```

**3. 宽度搜索（web_search ≥5 次）+ 参考文献采集**
覆盖：通用名/代号、原研公司、作用机制、适应症、注册状态、临床阶段、市场规模、竞争格局、专利、合作历史

**参考文献采集（强制）**：
- 每次搜索后，对每个搜索结果中有价值的页面执行 `web_fetch` 抓取内容
- 有价值的判断标准：包含具体数据、结论、事实陈述的页面
- 不抓取：纯导航页、广告页、无实质内容的列表页
- 抓取内容存入 `{品种目录}/references/REFERENCES.md`
- 参考文献格式：
  ```
  ## [REF-001] 标题
  - **URL**: https://...
  - **抓取时间**: 2026-05-28 23:00 CST
  - **来源类型**: 官方/学术/行业媒体/公司公告
  - **内容摘要**: （200-500字摘要，保留关键数据和原文表述）
  - **关键数据点**: （列出可用于报告的具体数字/结论）
  ```
- 编号从 REF-001 起连续递增

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
  "name": "{品种名}",
  "scheme": "B",
  "businessEntity": "待确认",
  "routedSkill": "待路由",
  "routedChain": [],
  "phase": "discovery_complete",
  "startedAt": "{ISO时间}",
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
每个 Gate 子Agent 的 task 指令必须包含以下参考文献要求：
1. 搜索前先读取现有 `{品种目录}/references/REFERENCES.md`，避免重复抓取已有URL
2. 每次搜索后，对有价值的结果执行 `web_fetch` 抓取内容
3. 新的参考文献追加到 `REFERENCES.md`（编号续接现有最大编号）
4. 报告正文中每个数据点必须标注 `[REF-XXX]` 引用编号
5. 不允许出现“外网核查”“分析推断”等无具体引用的标注
6. 报告开头列出本 Gate 使用的参考文献编号清单

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
   - 一票否决清单是否完整核查（7条体系级 + 技能专属）
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
主会话

### 操作步骤

1. 将 One-pager、全部 Gate 章节、battle summary 合并为 `04-final-report.md`
2. **参考文献合并（强制）**：
   - 合并时保留所有 Gate 章节中的 `[REF-XXX]` 引用编号
   - 从 `{品种目录}/references/REFERENCES.md` 提取所有被引用的参考文献
   - 报告末尾自动生成完整参考文献表（按编号排序）
   - 参考文献表格式：`[REF-XXX] 标题 — URL（抓取时间）`
3. 报告结构：
   ```
   第一章：执行摘要（结论先行，核心指标一览）
   第二章：公司基本信息（M-01~M-10）
   第三章：产品基本面
   Gate 1~6 各自独立章节
   第X章：财务模型
   第Y章：风险登记表（红旗台账）
   第Z章：评估结论与推荐（推进/条件推进/停止）
   附录A：数据来源
   附录B：DRL资料需求清单
   附录C：信息冲突汇总表
   参考文献
   ```

3. 执行质量终检（8项）：
   - ① Gate 1-6 结论卡完整性（每Gate都有结论卡）
   - ② 财务硬门槛达标情况（对照总规则第5节）
   - ③ 一票否决清单核查（7条体系级 + 技能专属）
   - ④ 置信度标注完整性（关键数据不超过3处缺失）
   - ⑤ 信息冲突汇总表（附录C）非空
   - ⑥ 阶段标签标注正确（[阶段A]/[阶段B]）
   - ⑦ 来源四分法标注覆盖
   - ⑧ 财务缩写首次出现标注中文全称

4. 更新 `state.json`：
   ```json
   {
     "phase": "report_finalized",
     "finalReport": "04-final-report.md",
     "conclusion": "推进/条件推进/停止",
     "qualityCheck": {
       "gateCards": "PASS",
       "financialThreshold": "PASS/FAIL",
       "vetoCheck": "PASS/FAIL",
       "confidenceAnnotation": "PASS/FAIL",
       "conflictSummary": "PASS",
       "stageLabels": "PASS",
       "sourceAnnotation": "PASS",
       "financialAbbreviation": "PASS"
     },
     "completedAt": "{ISO时间}"
   }
   ```

**✅ Phase 5 完成标志**：`04-final-report.md` 存在 + 质量终检通过

---

## Phase 5.5: HTML 生成 + 上传归档

### 报告风格：麦肯锡深蓝

**与 bd-eval 的差异**：bd-eval 用琥珀金/蓝白对阵两套，本 Skill 只用麦肯锡深蓝一种。

**视觉规范**：
- 主色：深蓝 `#1a3a5c`
- 辅色：白色背景，浅灰背景 `#f5f7fa`
- 字体：思源黑体 / Arial
- 风格：结论先行、数据驱动、无装饰、无多余图片
- **禁止**：灰色字体、元描述、修订说明

**Gate 结论卡样式**：
```css
.gate-card {
  border-left: 4px solid #1a3a5c;
  background: #f5f7fa;
  padding: 16px;
  margin: 16px 0;
}
.gate-pass { border-left-color: #34A853; }
.gate-conditional { border-left-color: #FBBC05; }
.gate-stop { border-left-color: #EA4335; }
```

**信息冲突标记样式**：
```css
.conflict-box {
  background: #fff8e1;
  border-left: 4px solid #f9a825;
  padding: 12px 16px;
  margin: 16px 0;
}
```

**中立审查框样式**：
```css
.neutral-review {
  background: #f3f4f6;
  border-left: 4px solid #607d8b;
  padding: 12px 16px;
  margin: 16px 0;
}
```

### 生成方式：调用 doc-viewer skill

1. 读取 `projects/bd-eval-cms/{品种}/04-final-report.md`
2. 切换到 doc-viewer skill 上下文
3. 生成麦肯锡深蓝风格 HTML
4. 保存到 `/tmp/report-cms-{slug}.html`
5. 上传到 doc.20100706.xyz
6. 返回 raw_url

### 归档操作

```bash
scripts/archive-links.sh \
  "{品种slug}" \
  "https://doc.20100706.xyz/raw/{report_id}"
```

同时更新 `state.json` 的 `reportHtmlUrl`。

**注意**：本 Skill 只生成一份报告（整体评估报告），不单独生成 Battle 报告。Battle 内容合并到最终报告的风险登记表章节中。

---

## 并行执行策略

多个品种同时跑时：

```
品种A: Phase1 → Phase2 → Phase3 → Phase4 → Phase5
品种B: Phase1 → Phase2 → Phase3 → Phase4 → Phase5  （并行）
品种C: Phase1 → Phase2 → Phase3 → Phase4 → Phase5  （并行）
```

**最大并发**：5个子Agent（sessions_spawn 上限）

**推荐策略**：5个品种并行跑完 Phase 1-2，再启动 Phase 3-5

---

## 子Agent 超时应对

与 bd-eval 相同策略：
1. 记录完成到第几个 Gate
2. 主会话补全未完成 Gate
3. 严重时手工编译最终报告

---

## 执行日志

每个品种在 `projects/bd-eval-cms/{品种}/execution-log.md` 中维护：

```
## Phase 1 DISCOVERY
- 时间: YYYY-MM-DD HH:MM
- 搜索次数: X
- 产品类型判断: {类型}
- 业务主体判断: {主体}

## Phase 2 D-0 路由
- 时间: YYYY-MM-DD HH:MM
- 路由技能: {编号}
- 路由置信度: {高/中/低}
- 争议: （如有）

...（每Phase记录）
```

---

## 健康检测

触发词：`检测CMS skill`、`CMS健康检查`

```bash
bash scripts/bd-eval-cms-health-check.sh
```

检测内容：
1. Skill 安装完整性（bd-eval-cms / doc-viewer / multi-search）
2. 22个技能定义文件存在性
3. SOP / sub-agent-prompt-template / 总规则完整性
4. 外部 API 连通性（doc.20100706.xyz）

---

## 配置与授权

### 必须安装的 Skill

**1. doc-viewer（必须）**
- 用途：Phase 5.5 HTML 报告生成（麦肯锡深蓝风格）
- 安装路径：`~/.openclaw/skills/doc-viewer/SKILL.md` 或 `~/.agents/skills/doc-viewer/SKILL.md`

**2. multi-search（必须）**
- 用途：Phase 1/3 多源搜索基础设施
- 安装路径：`~/.openclaw/skills/multi-search/SKILL.md` 或 `~/.agents/skills/multi-search/SKILL.md`

### API Key 配置

| Key | 必要性 | 用途 |
|-----|--------|------|
| MINIMAX_API_KEY | ✅ 必须 | web_search 默认搜索引擎 |
| TAVILY_API_KEY | ⚠️ 推荐 | 搜索降级 fallback |

### 一键检测

```bash
bash scripts/bd-eval-cms-health-check.sh
```

---

## 问题反馈

- **Issue 地址**：https://github.com/evan-zhang/agent-factory/issues
- **标题格式**：`[bd-eval-cms] 简述问题`
- **建议包含**：
  1. 重现步骤（品种名称、执行到哪个 Phase）
  2. 环境信息（健康检测脚本输出）
  3. 相关日志（`projects/bd-eval-cms/{品种名}/execution-log.md`）
