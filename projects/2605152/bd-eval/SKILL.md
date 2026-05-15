---
name: bd-eval
description: "BD品种评估 TPR 自动化流水线 — 从品种名称到在线报告的完整执行链路。触发词：BD评估、跑品种、评估新药、BD品种筛选"
version: "1.3.0"
homepage: projects/bd-eval/SOP.md
dependencies:
  - tpr-framework (optional, for battle protocol reference)
  - doc-viewer (required, for 整体报告HTML generation)
  - multi-search (required, for web_search infrastructure)
---

# BD品种评估 Skill

> **本 Skill 可被任何 Agent 独立执行**。当收到 BD 评估请求时，
> 读取本文件，按 Phase 1~5.5 顺序执行即可。
> 所有流程规范、模板、子Agent prompt 均在 `~/.openclaw/skills/bd-eval/references/` 下，
> 无需额外配置即可开始。

## 快速开始

**用户说**：`BD评估：CG-0255、RHOFADE、门冬氨酸钙片`

**Agent 响应**：
```
收到。开始执行 BD 品种评估流水线。

评估品种：CG-0255、RHOFADE、门冬氨酸钙片
预计耗时：约 60-80 分钟/品种

我将按以下阶段执行：
Phase 1: DISCOVERY（宽度搜索 + 模板匹配）
Phase 2: 模板选择 Battle
Phase 3: GRV 逐章节深度评估
Phase 4: GRV Battle 对抗
Phase 5: 报告合并 + 质量终检
Phase 5.5: HTML生成（整体报告→doc-viewer琥珀金；Battle→蓝白对阵）
归档 → doc.20100706.xyz

开始执行...（稍后回报结果）
```

## 核心文件索引

| 文件 | 路径 | 用途 |
|------|------|------|
| 本 Skill | `~/.openclaw/skills/bd-eval/SKILL.md` | 主入口 |
| SOP 规范 | `~/.openclaw/skills/bd-eval/references/SOP.md` | Phase 1-5 完整流程 |
| 子Agent Prompt | `~/.openclaw/skills/bd-eval/references/sub-agent-prompt-template.md` | GRV 章节撰写规范 |
| 7套评估模板 | `~/.openclaw/skills/bd-eval/references/bd_report_templates_full.md` | 模板匹配依据 |
| 归档脚本 | `~/.openclaw/skills/bd-eval/scripts/archive-links.sh` | 归档到 links.md |
| 品种目录 | `projects/bd-eval/{品种名}/` | 所有品种的工作目录 |

## 触发判断

当用户消息包含以下任一关键词时，Agent 应读取本 SKILL.md 并执行：

### 触发词一：执行评估（完整流水线）

**触发词**：`BD评估`、`跑品种`、`评估新药`、`BD品种筛选`、`新批次`

```
用户: BD评估：CG-0255、RHOFADE、门冬氨酸钙片
  ↓
本 Agent: 读取 ~/.openclaw/skills/bd-eval/SKILL.md
  ↓
执行 Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 5.5
  ↓
返回：每个品种的最终报告链接（doc.20100706.xyz）
```

### 触发词二：健康检测 + 自动配置

**触发词**：`检测 skill`、`配置 skill`、`健康检查`、`安装检测`、`skill 状态`

→ **立即执行健康检测**：
```bash
~/.openclaw/skills/bd-eval/scripts/bd-eval-health-check.sh
```

**检测内容（5大类）**：
1. **Skill 安装完整性**：bd-eval / doc-viewer / multi-search / tpr-framework 是否存在
2. **关键文件存在性**：SOP / 7套模板 / 子Agent prompt / 琥珀金模板是否完整
3. **OpenClaw 工具可用性**：curl / python3 / ~/.openclaw 目录
4. **外部 API 连通性**：doc.20100706.xyz 上传服务是否可达
5. **环境变量配置**：XGJK_API_KEY / Z_AI_API_KEY

**自动修复**：`bash bd-eval-health-check.sh --fix`

### 触发词三：重新生成 HTML / 更新链接

**触发词**：`重新生成 HTML`、`更新链接`、`上传报告`

→ 跳到 Phase 5.5 执行 HTML 生成 + 上传 + 归档

```
Step 1: 读取 SOP.md（核心流程规范）
  → 路径：~/.openclaw/skills/bd-eval/references/SOP.md
  → 或：projects/bd-eval/SOP.md

Step 2: 读取子Agent prompt模板（章节撰写规范）
  → 路径：~/.openclaw/skills/bd-eval/references/sub-agent-prompt-template.md

Step 3: 读取BD评估模板（7套模板）
  → 路径：~/.openclaw/skills/bd-eval/references/bd_report_templates_full.md

Step 4: 品种目录创建
  → 路径：projects/bd-eval/{品种名}/

Step 5: 按 Phase 执行（Phase 1~4 用 sessions_spawn 调度子Agent）

Step 6: Phase 5 合并报告 + 质量终检

Step 7: Phase 5.5 HTML生成
  → 整体报告：调用 doc-viewer skill，风格03琥珀金
  → Battle报告：本 Skill 自生成蓝白对阵风

Step 8: 上传到 doc.20100706.xyz + 归档
  → 脚本：~/.openclaw/skills/bd-eval/scripts/archive-links.sh
```

---

## 完整流水线执行（默认）

### 流程概览

```
用户提供品种名称列表
    ↓
Phase 1: DISCOVERY（宽度搜索 + 模板匹配）
Phase 2: 模板选择 Battle（两个AI对抗）
Phase 3: GRV（逐章节深度搜索+撰写）
Phase 4: GRV Battle（审查层 vs 执行层对抗）
Phase 5: 报告合并 + 质量终检
    ↓
HTML生成（整体报告 + Battle报告）
上传到 doc.20100706.xyz
归档到 links.md
```

---

## Phase 1: DISCOVERY

### 执行者
TPR Orchestrator（主会话）

### 操作步骤

**0. 标的方画像确认（v5.3 新增）**

在开始搜索之前，向用户确认标的方信息：
- 标的方是谁？（公司/机构名称）
- 合作模式是什么？（自研/License-in/代理权/技术平台/其他）
- 标的方现有产能？（有/无/计划中）
- 标的方核心优势？（成本控制/渠道/注册能力/其他）

用户回复后写入 `00-target-profile.md`。如用户说"先跑吧"，标记"待确认"，但财务模型必须标注"⚠️ 基于行业平均"。

**1. 创建品种目录**
```bash
mkdir -p projects/bd-eval/{品种名}/
mkdir -p projects/bd-eval/{品种名}/02-grv-by-chapter/
mkdir -p projects/bd-eval/{品种名}/battle/
```

**2. 宽度搜索（web_search ≥5 次）**
覆盖：通用名/代号、原研公司、作用机制、适应症、注册状态、临床阶段、市场规模、竞争格局、专利、合作历史

**3. 写入 `01-discovery.md`**
包含：品种基本信息、模板初步判断（附理由）

**4. 初步模板匹配**
按 SOP 的「模板匹配规则」判断属于哪套模板：
- 模板一：海外已上市·中国未上市
- 模板二：代理权引进
- 模板三：早期创新药
- 模板四：生物类似药
- 模板五：战略平台合作
- 模板六：院外/消费健康
- 模板七：多标的横向筛选

**5. 创建 `state.json`**
```json
{
  "name": "{品种名}",
  "template": "模板X",
  "phase": "discovery_complete",
  "startedAt": "{ISO时间}",
  "discovery": {
    "searches": 5,
    "sources": ["搜索来源列表"]
  }
}
```

**✅ Phase 1 完成标志**：`01-discovery.md` 存在 + `state.json` 已更新

---

## Phase 2: 模板选择 Battle

### 执行者
TPR Orchestrator 调度独立子Agent

### 操作步骤

1. Orchestrator 给出初步模板判断 + 理由
2. Spawn 审查层子Agent（独立）：读取 01-discovery.md + 全部7套模板 → 判断是否同意
3. 如审查层同意 → 确认模板
4. 如不同意 → 争议点保留，双方理由写入 `battle/TEMPLATE-SELECTION-AUDITOR.md`

**⚠️ 强制要求**：每个品种都必须经过审查层子Agent确认，不得跳过。

**✅ Phase 2 完成标志**：`battle/TEMPLATE-SELECTION-AUDITOR.md` 存在

---

## Phase 3: GRV 逐章节深度评估

### 执行者
GRV子Agent（Sessions Spawn，并行或串行）

### 子Agent超时问题（已知风险）
- 默认超时对逐章搜索任务严重不足
- **解决方案A**：每个品种按模板选择章节数（如模板一只做8-10章，模板三做13章）
- **解决方案B**：子Agent自主判断次要章节并跳过（保留记录）

### 操作步骤

1. 读取 `sub-agent-prompt-template.md` 作为子Agent prompt 模板
2. **第0章必写**：品种概述 + 模板选择理由 + 投资视角
3. 对模板的每个章节：
   - web_search ≥3 次（每次必须记录搜索词和结果URL）
   - 写章节内容（中文）
   - 正文关键数据标注 [1] [2]，章节末尾附参考来源（含完整URL）
   - 写入 `02-grv-by-chapter/{序号}-{章节名}.md`
4. 每完成3-5章，派验证子Agent批量交叉检查
5. 根据验证结果修正

**✅ Phase 3 完成标志**：模板规定的全部章节文件存在于 `02-grv-by-chapter/`

---

## Phase 4: GRV Battle 对抗

### 执行者
两个独立子Agent（审查层 + 执行层），由 Orchestrator 串行调度

### 操作步骤

1. **审查层子Agent**：以最挑剔评审者身份审查全部GRV章节 → 输出异议清单
   - 3-5个实质性异议
   - 每个异议：引用具体章节 → 说明为什么有问题 → 提出修改建议
   - 裁定：APPROVE / REJECT / CONDITIONAL
   - 输出：`battle/BATTLE-R1-AUDITOR.md`

2. **执行层子Agent**：逐条回应审查层异议
   - 接受（说明改什么）或拒绝（附证据）
   - 更新对应章节文件
   - 输出：`battle/BATTLE-R1-EXECUTOR.md`

3. **审查层重审**：如有多轮，最多3轮

4. 生成 `03-battle-summary.md`（红绿灯总览 + 裁定 + 未解决争议点）

**✅ Phase 4 完成标志**：`03-battle-summary.md` + `03-battle.md` 存在

---

## Phase 5: 报告合并 + 质量终检

### 执行者
TPR Orchestrator

### 操作步骤

1. 将 `01-discovery.md`、全部 GRV 章节、`03-battle-summary.md` 合并为 `04-final-report.md`
2. 执行质量终检（7项，见 SOP）
3. 更新 `state.json`：
   ```json
   {
     "phase": "report_finalized",
     "finalReport": "04-final-report.md",
     "conclusion": "🟢/🟡/🔴 + 结论",
     "grade": "B+/A-/C+ 等",
     "completedAt": "{ISO时间}"
   }
   ```

**✅ Phase 5 完成标志**：`04-final-report.md` 存在 + 质量终检通过

---

## Phase 5.5: 调用 Doc-Viewer 生成整体报告 HTML

> **重要**：整体报告必须调用 `doc-viewer` skill 生成琥珀金风格（风格03），而非自行生成。
> Battle 报告可由本 Skill 自行生成蓝白风格 HTML（对阵感更强）。

### 触发 doc-viewer（风格03 琥珀金版）

在 Phase 5 完成后，对每个品种执行以下步骤：

1. 读取 `projects/bd-eval/{品种}/04-final-report.md`
2. 切换到 `doc-viewer` skill 上下文（读取 skill 文件）
3. **目标风格**：风格03 琥珀金版（`templates/style-03/reference-amber.html`）
4. **配色**：琥珀金（amber），深金 #C9920A
5. **文件输出路径**：`/tmp/report-{slug}.html`
6. **上传**：`doc.20100706.xyz`（raw_url）
7. 返回 raw_url 供归档

**doc-viewer 调用示例（内部逻辑）**：
```
读取 style-03 reference-amber.html 作为骨架
读取 style-03/color-themes/amber.yml 获取颜色 token
将 04-final-report.md 内容填入 body 占位符
生成完整 HTML → 保存到 /tmp/report-{slug}.html
curl POST 上传 → 拿到 raw_url
```

**为什么不用 doc-viewer 生成 Battle 报告**：
- Battle 报告需要左/右对阵布局，风格03是标准章节报告，不适合
- 蓝白对阵风格（#1A73E8 为主色）是本 Skill 自带的 Battle 专用样式

---

## HTML 生成 + 上传 + 归档

**两个报告，两种生成方式**：

| 报告 | 生成方式 | 风格 |
|------|---------|------|
| 整体评估报告 | **调用 doc-viewer skill** | 风格03 琥珀金（深金 #C9920A）|
| Battle对抗报告 | **本 Skill 自生成** | 蓝白对阵风（#1A73E8 为主）|

---

### 整体报告 HTML → doc-viewer（琥珀金）

**执行者**：TPR Orchestrator（调用 doc-viewer skill）

**操作**：
1. 读取 `projects/bd-eval/{品种}/04-final-report.md`
2. 读取 `~/.agents/skills/doc-viewer/templates/style-03/reference-amber.html`
3. 读取 `~/.agents/skills/doc-viewer/templates/style-03/color-themes/amber.yml`
4. 将报告内容填入骨架，生成完整 HTML
5. 保存到 `/tmp/report-{slug}.html`
6. 上传并拿到 raw_url
7. 归档到 `links.md` + `state.json`

---

### Battle 报告 HTML → 自生成（蓝白对阵风）

**执行者**：TPR Orchestrator（子Agent或主会话生成）

**操作**：
1. 读取 `projects/bd-eval/{品种}/03-battle.md`
2. 按蓝白对阵风格生成 HTML（结构见下方规范）
3. 保存到 `/tmp/battle-{slug}.html`
4. 上传并拿到 raw_url
5. 归档到 `links.md` + `state.json`

**Battle HTML 规范**（蓝白对阵风）：
- 主色：#1A73E8（蓝），辅色：#34A853/#FBBC05/#EA4335
- 字体：PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif
- 单文件HTML，内联CSS，无JS框架

**页面结构**：
1. 顶部：品种名称 + Battle报告标题 + 日期 + 模板类型
2. 红绿灯概览：大号圆角指标卡（🟢绿/#34A853 🟡黄/#FBBC05 🔴红/#EA4335）
3. 异议vs答辩：每个异议一个卡片，左审查层质疑（红边框 #EA4335）右执行层答辩（蓝边框 #1A73E8）
4. 最终裁定区：醒目展示结论
5. 页脚：品种名 | Battle报告 | 日期

**CSS要求**：
```css
:root { --primary:#1A73E8; --green:#34A853; --yellow:#FBBC05; --red:#EA4335; --text:#202124; --subtext:#5F6368; --border:#E5E7EB; --bg:#FFFFFF; --surface:#F8F9FA; }
@page { size: A4 portrait; margin: 20mm; }
@media print { .table-wrap { overflow-x: visible; } th { -webkit-print-color-adjust: exact; } }
```
- PC双栏grid（1fr 1fr），≤768px缩窄，≤480px单栏
- 正文pt单位，page-break-inside:avoid，print-color-adjust:exact
- 表格外包裹 `.table-wrap { overflow-x: auto; }`
- 文件 < 1MB

---

### 归档操作

两个报告上传后，执行归档：

```bash
~/.openclaw/skills/bd-eval/scripts/archive-links.sh \
  "{品种slug}" \
  "https://doc.20100706.xyz/raw/{report_id}" \
  "https://doc.20100706.xyz/raw/{battle_id}"
```

同时更新 `state.json` 的 `reportHtmlUrl` 和 `battleHtmlUrl`。

---

## 并行执行策略

多个品种同时跑时：

```
品种A: Phase1 → Phase2 → Phase3 → Phase4 → Phase5
品种B: Phase1 → Phase2 → Phase3 → Phase4 → Phase5  （并行）
品种C: Phase1 → Phase2 → Phase3 → Phase4 → Phase5  （并行）
```

**最大并发**：5个子Agent（sessions_spawn 上限）

**推荐策略**：5个品种并行跑完 Phase1-2，再启动 Phase3-5

---

## 子Agent 超时应对方案

当 Phase 3 子Agent 超时时：

1. **记录**：在 `state.json` 中记录完成到第几章
2. **补跑**：主会话补全未完成章节（减少章节数）
3. **手工编译**：如超时严重，手工从已有章节编译最终报告

---

## 执行日志

每个品种在 `projects/bd-eval/{品种}/execution-log.md` 中维护：

```
## Phase 1 DISCOVERY
- 时间: 2026-05-15 HH:MM
- 搜索次数: X
- 模板判断: 模板X

## Phase 2 模板Battle
- 时间: 2026-05-15 HH:MM
- 裁定: 同意/不同意
- 争议: （如有）

...（每Phase记录）
```

---

## 配置与授权

### 必须安装的 Skill

本 Skill 依赖以下三个 Skill，缺少则无法执行完整流程：

**1. doc-viewer（必须）**
- 用途：Phase 5.5 整体报告 HTML 生成（琥珀金风格）
- 安装：随分发包安装，或单独获取
- 安装后路径：`~/.openclaw/skills/doc-viewer/SKILL.md` 或 `~/.agents/skills/doc-viewer/SKILL.md`
- 关键文件：`templates/style-03/reference-amber.html`（琥珀金骨架）

**2. multi-search（必须）**
- 用途：Phase 1/3 多源搜索基础设施（搜索降级链）
- 安装：随分发包安装，或单独获取
- 安装后路径：`~/.openclaw/skills/multi-search/SKILL.md` 或 `~/.agents/skills/multi-search/SKILL.md`

**3. tpr-framework（建议安装）**
- 用途：Phase 2/4 Battle/GRV 规范参考
- 安装：随分发包安装，或单独获取
- 缺少时：流程仍可执行，但 Phase 2/4 Battle 质量会降低

### API Key 配置

| Key | 必要性 | 用途 | 获取方式 |
|-----|--------|------|----------|
| MINIMAX_API_KEY | ✅ 必须 | OpenClaw web_search 默认搜索引擎 | OpenClaw 配置 |
| TAVILY_API_KEY | ⚠️ 推荐 | multi-search 搜索降级 fallback | https://tavily.com 免费注册 |
| EXA_API_KEY | 可选 | multi-search 另一个搜索 fallback | https://exa.ai 免费注册 |

**最低配置**：只需 MINIMAX_API_KEY，web_search 即可运行。Tavily 和 Exa 是搜索降级链的备份，有则更好。

### 一键检测

安装后运行健康检测，确认所有依赖就绪：

```bash
bash ~/.openclaw/skills/bd-eval/scripts/bd-eval-health-check.sh
```

或对 Agent 说「检测 skill」「配置 skill」「健康检查」。

`--fix` 参数会输出每个缺失项的详细修复指引。

---

## 问题反馈

- **Issue 地址**：https://github.com/evan-zhang/agent-factory/issues
- **标题格式**：`[bd-eval] 简述问题`
- **建议包含**：
  1. 重现步骤（品种名称、执行到哪个 Phase）
  2. 环境信息（`bash bd-eval-health-check.sh` 输出）
  3. 相关日志（`projects/bd-eval/{品种名}/execution-log.md`）
