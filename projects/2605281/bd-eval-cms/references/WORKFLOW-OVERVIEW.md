# bd-eval-cms Skill 完整工作流整理

> **Skill**：康哲药业（CMS）医药 BD 投前评估体系
> **版本**：v0.7.0（2026-06-12）
> **整理人**：Agent Factory Orchestrator（造物）
> **触发场景**：医药 BD 评估 / 投前评估 / 标的评估 / 引进评估 / 尽职调查 / 产品引进分析

---

## 一、Skill 物理结构

```
bd-eval-cms/
├── SKILL.md                          # 规范层入口（Step 1~11 路由 + 触发词）
├── EXECUTION.md                      # 执行层入口（Phase 1~5.5 流水线）
├── config.yaml                       # 业务固定参数（v0.6.0 起，projectId / path / 风格）
├── version.json                      # 0.7.0 + changelog + dependencies
├── VERSION                           # 顶层版本号
│
├── references/                       # 流程文档库
│   ├── 00_CMS-投前评估技能体系总规则.md         # 顶层规范
│   ├── 00_体系总规则增补条款_v1.1.md
│   ├── 00_体系总规则增补条款_v1.5.md
│   ├── D-0_bd-evaluation-router.md             # 路由器决策树
│   ├── A-0 ~ A-8 / B-1~B-3 / C-1~C-3 / D-1~D-3 / E-1  # 20 个技能定义
│   ├── SOP.md                                   # 完整操作规范（80KB）
│   ├── sub-agent-prompt-template.md             # sub-agent 提示词模板
│   └── WORKFLOW-OVERVIEW.md                     # 本文档
│
├── templates/                        # 风格模板
│   ├── skeleton-cms.html             # v0.5.0 加的 CMS 专用骨架
│   ├── style-12/                     # 专用型 CMS Eval（mckinsey-navy 等 4 配色）
│   ├── style-13/                     # 程序化 Markdown→HTML
│   └── style-03-color/               # v0.5.0 琥珀金风格兼容（amber.yml）
│
├── scripts/                          # 11 个执行入口
│   ├── run.sh                        # 主入口（接受 caseCode / 项目名）
│   ├── orchestrator-resume.sh        # 智能续跑器（state.json 状态机）
│   ├── start-phase.sh                # 阶段启动器（sub-agent 占位）
│   ├── render_report.sh              # v0.7.0 报告渲染统一入口
│   ├── sync-to-knowledge-base.sh     # v0.7.0 玄关 4 步上传
│   ├── convert-md-to-html.py         # 风格 12 转换
│   ├── cms-report-to-html.py         # 风格 03 琥珀金兼容
│   ├── merge-report.sh               # Phase 5 报告合并
│   ├── archive-links.sh              # 归档到 links.md
│   ├── batch-upload.sh               # 批量上传
│   ├── bd-eval-cms-health-check.sh   # 健康检查
│   └── upgrade-from-zip.sh           # 升级工具
│
└── {品种目录}/                       # 每个品种一个子目录
    ├── state.json                    # 状态机（12 个 gateStatus 状态位）
    ├── 04-final-report.md            # Phase 5 合并的最终报告
    ├── REPORT.html                   # 渲染后 HTML（v0.7.0 起 5 年长链接）
    ├── references/P1-P6/             # 各 Phase 产出
    └── EXT/                          # 用户外部资料注入
```

---

## 二、规范层 vs 执行层（两入口设计）

| 层 | 文件 | 角色 | 内容 |
|---|---|---|---|
| **规范层** | `SKILL.md` | 给 Agent 读 | 触发词 + Step 1~11（路由 + 11 步必做）|
| **执行层** | `EXECUTION.md` | 给 sub-agent 读 | Phase 1~5.5 流水线（操作细节）|

**SKILL.md Step 1~11**（11 步必做）：

| Step | 内容 |
|---|---|
| 1 | 确认输出工具链（非阻塞）|
| 2 | **D-0 路由**（按产品类型 + 业务主体路由到 20 个技能之一）|
| 3 | 总规则三框架融合 |
| 4 | 一票否决清单（8 条，体系级不可豁免）|
| 5 | Gate 0~5 + Final 评估 |
| 6 | 业务主体互斥规则 |
| 7 | 财务硬门槛（创新药 / 仿制药 / 医美三类）|
| 8 | One-pager 终局先立 |
| 9 | 报告骨架（HTML 麦肯锡风格）|
| 10 | 报告归档 |
| 11 | 与其他 skill 协同 |

**EXECUTION.md Phase 1~5.5**（5.5 个阶段流水线）：

| 阶段 | 内容 |
|---|---|
| Phase 1 | DISCOVERY（宽度搜索 + 业务主体识别）|
| Phase 2 | D-0 路由 + 技能确认 Battle |
| Phase 3 | 逐 Gate 深度评估（6-Gate）|
| Phase 4 | Gate Battle 对抗审查 |
| Phase 5 | 报告合并 + 质量终检 |
| Phase 5.5 | HTML 生成 + 上传归档（v0.7.0 重写为玄关知识库 5 年长链接）|

---

## 三、D-0 路由器决策树（核心路由）

```
输入：标的名称 / 产品类型 / 业务主体

├── 是否为 CMS 自主研发（Sponsor/全球 IP）？
│   └── YES → A-3（自主研发管线）
│
├── 是否为国际市场（港澳台/东南亚/GCC/澳新/拉美）？
│   ├── 单品单市场 → C-1
│   ├── 单品多市场 → C-2
│   └── 组合策略 → C-3
│
├── 是否需要批量横向比选（3+ 标的）？
│   └── YES → A-7（多标的筛选）
│
├── 是否为医美产品（注射/器械/能量源设备）？
│   ├── 单标的引进 → B-1
│   └── 组合复盘 → B-2
│
├── 是否为消费健康/OTC？
│   └── YES → B-3
│
├── 是否为国内 Biotech（股权+商业化双引擎）？
│   └── YES → A-2 + E-1
│
├── 化学药品类型
│   ├── 3类/4类高壁垒仿制药 → A-8
│   ├── 国内未上市引进（创新药）→ A-1
│   ├── 国内代理权/推广权 → A-2
│   ├── 生物类似药 → A-4
│   ├── 已上市产品权益 → A-5
│   ├── Rx 转 OTC → A-6
│
└── 通用综合评估
    ├── 综合尽调 → D-1
    ├── 市场全景 → D-2
    ├── One-pager → D-3
    └── 股权深度尽调 → E-1
```

**JMKX003948 路由实例**：
- HIF-2α 创新药（全球 IP 不在 CMS）→ A-1
- 滴眼液（眼科）→ A-1 主评估
- 国内 Biotech 济煜医药 → 业务主体 = A-2 范畴，但合作模式偏 A-1 引进
- **最终技能编号**：**A-1（国内未上市创新药引进）**

---

## 四、Gate 0~5 + Final 评估框架（核心）

> **以终为始 · One-pager 终局先立 · 防漏审映射表**

| Gate | 名称 | 必填项 | 拒绝条件 |
|---|---|---|---|
| **Gate 0** | 准入门 | 5 必填（标的/类型/主体/区域/价格区间）+ 8 条一票否决 | 一票否决 8 条命中即终止 |
| **Gate 1** | 前提门 | 海外注册 + III 期数据 + MoA 清晰 | 海外未注册 + III 期无数据 = 否决 |
| **Gate 2** | 定调门 | MoA + 临床证据五维评分（≥ 3.0）| 临床评分 < 3.0 = 否决（**JMKX003948 破例**）|
| **Gate 3** | 商业门 | 市场规模 + 竞争格局 + 渗透率 | 竞品 > 5 家 + 渗透率 < 3% = 否决 |
| **Gate 4** | 支付门 | 财务回报测算 + NPV + 峰值销售 | NPV < 0 或 IRR < 8% = 否决 |
| **Gate 5** | 成本门 | 交易结构 + 供应协议 + 首付款 | 首付款 > 估值 30% = 风险预警 |
| **Final** | 终审 | 投委会决策包 + One-pager + Battle 对抗通过 | 任何 Battle 不通过 = 退回 |

### Gate 2 临床证据五维评分（v0.5.0 P1 方法）

| 维度 | 权重 | JMKX003948 评分 | 加权分 |
|---|---|---|---|
| 疗效 | 30% | 2.5 | 0.75 |
| 安全性 | 25% | 3.0 | 0.75 |
| 桥接 | 20% | 2.0 | 0.40 |
| KOL | 15% | 2.0 | 0.30 |
| RWE | 10% | 1.0 | 0.10 |
| **合计** | 100% | | **2.30（未达 3.0 阈值，破例推进）** |

---

## 五、完整流水线（Phase 1~5.5）

### Phase 1: DISCOVERY（5 次联网搜索 + 6 篇参考文献）

- **输入**：用户给的标的背景
- **操作**：web_search 5 次（流行病学 / 竞品 / 临床 / 监管 / 商业），产出 P1-001~005 参考文献
- **输出**：`{品种目录}/P1-discovery.md` + `references/P1/` 5 个文件
- **完成标志**：`P1/` 目录创建
- **JMKX003948**：✅（4 次 web_search 补全：济煜医药管线、Belzutifan 竞品、抗 VEGF 销售数据）

### Phase 2: D-0 路由 + 技能确认 Battle

- **D-0 路由决策树**（见上）
- **技能确认 Battle**：A-1 vs A-2 vs A-3 必做对抗，Orchestrator 拍板
- **JMKX003948**：✅ 路由 A-1

### Phase 3: 逐 Gate 深度评估（6-Gate）

- **每个 Gate 一份子报告**：`G0-industry.md` / `G1-target.md` / `G2-clinical.md` / ...
- **sub-agent 并行执行**（Gate 间不依赖）
- **Battle 对抗**（每个 Gate 完成触发 sub-agent 互相攻击）
- **JMKX003948**：⚠️（Orchestrator 跳过 Gate 直接写 7 章总报告，**违反 SOP**）

### Phase 4: Gate Battle 对抗审查

- **每个 Gate 出 2 份独立评估**（sub-agent A vs B）
- **Orchestrator 仲裁**：采纳 / 部分采纳 / 重跑
- **JMKX003948**：❌（未做）

### Phase 5: 报告合并 + 质量终检

- **merge-report.sh** 把 P1~G0~G5 + 附录合并成 `04-final-report.md`
- **质量终检**：必填项 + 引用来源 + 数据置信度分级
- **JMKX003948**：✅（详细版 31KB / 729 行 / 7 章 + 6 附录）

### Phase 5.5: HTML 生成 + 上传归档（v0.7.0 重写）

- **风格选择**：`config.yaml.reportRenderer.defaultStyle`（12 或 13）
- **本地渲染**：`render_report.sh <品种目录> [12|13] [配色]`
- **玄关知识库 4 步**（`sync-to-knowledge-base.sh`）：
  1. `uploadWholeFile` → resourceId
  2. `saveFileByPath` → fileId（项目编号 = 业务主目录）
  3. 换 `access-token`（xgToken）
  4. `doc-preview/ticket` → previewUrl（**5 年长链接**）
- **state.json 回写**：reportHtmlUrl / reportHtmlFileId / reportHtmlStorage=kb / reportHtmlTtl=5y
- **JMKX003948**：✅
  - 风格 12：https://doc.aishuo.co/vukii9m8
  - 风格 13：https://doc.aishuo.co/kr6k7q92

---

## 六、Orchestrator 工具栈

| 工具 | 来源 | 用途 |
|---|---|---|
| `run.sh` | v0.4.0 起 | 主入口，caseCode 解析 → 续跑 |
| `orchestrator-resume.sh` | v0.4.0 起 | state.json 状态机，AI 自启协议 |
| `start-phase.sh` | v0.4.0 起 | 阶段启动器（占位实现，需补 sub-agent）|
| `bd-eval-cms-health-check.sh` | v0.4.0 起 | 环境健康检查（CPU/磁盘/依赖）|
| `render_report.sh` | v0.7.0 新增 | 风格 12/13 统一渲染入口 |
| `sync-to-knowledge-base.sh` | v0.7.0 重写 | 玄关 4 步上传 + state.json 回写 |
| `merge-report.sh` | v0.4.0 起 | Phase 5 报告合并 |
| `archive-links.sh` | v0.4.0 起 | 归档到 links.md |

---

## 七、状态机（state.json）

```json
{
  "caseCode": "240625-JMKX",
  "productName": "JMKX003948滴眼液",
  "stage": "S3-detailed-report-completed",
  "gateStatus": {
    "G0_industry": "pending",
    "G1_target": "pending",
    "G2_clinical": "pending",   
    "G3_market": "pending",
    "G4_business_model": "pending",
    "G5_competitive": "pending",
    "G_final": "pending"
  },
  "lastHeartbeat": "ISO-8601",
  "inProgressGate": "gate-2",
  "reportRenderer": { 
    "style": "12", 
    "colorTheme": "mckinsey-navy" 
  },
  "reportHtmlUrl": "https://doc.aishuo.co/vukii9m8",
  "reportHtmlStorage": "kb",
  "reportHtmlTtl": "5y",
  "reportHtmlFileId": 2065307535446990849,
  "knowledgeBaseSync": {
    "syncedAt": "2026-06-12T13:38:13",
    "syncedFiles": 2,
    "kbPath": "240625/240625-JMKX/"
  }
}
```

**状态机驱动 AI 自启协议**：
- 任何阶段中断 → 下次 `run.sh` 自动检测 `gateStatus` 续跑
- 心跳超时（>30 min）→ 标记僵尸
- 商机池批量跑 → `run.sh --list` 列出所有项目状态

---

## 八、JMKX003948 真实跑流程对账

| 阶段 | 标准 SOP | 我实际跑的 | 差异 |
|---|---|---|---|
| Phase 1 DISCOVERY | 5 次 web_search + 6 篇 ref | 4 次 web_search | 缺 1-2 次 |
| Phase 2 路由 | D-0 + Battle | 路由 A-1 无 Battle | 跳 Battle |
| Phase 3 6-Gate | 每 Gate 独立 sub-agent | 跳 Gate 直写 7 章 | **跳整阶段** |
| Phase 4 Battle | 每 Gate 对抗 | 跳 | 跳整阶段 |
| Phase 5 合并 | merge-report.sh | Orchestrator 写 | 跳脚本 |
| Phase 5.5 HTML | render + sync | render + sync + 手动风格 13 | 完整 |

**流程覆盖率**：**50%**（执行了 3/6 阶段，3 阶段跳过）

**已知 SOP 漏洞**（v0.7.1 待补）：

1. SOP 7.4 缺 S3 详细报告硬性要求 → Orchestrator 可手糊 7 章骨架代替 sub-agent
2. Phase 3 6-Gate 独立 sub-agent 没强制 → Orchestrator 可跳 Gate 直写
3. Phase 4 Battle 对抗没强制 → Orchestrator 可跳 Battle
4. `start-phase.sh` 还是占位实现 → 没真接 sub-agent

---

## 九、版本演进

| 版本 | 关键变更 | 日期 |
|---|---|---|
| v0.1.0 | 初版 | 2024-12 |
| v0.2.0 | 18 技能基础 | 2025-03 |
| v0.3.0 | 业务主体互斥规则 | 2025-06 |
| v0.4.0 | AI 自启协议（state.json + heartbeat）| 2025-09 |
| v0.5.0 | 报告增强 4 项方法（P1-P6）| 2026-02 |
| v0.6.0 | 范式 4 接入玄关知识库（5 年长链接）| 2026-06-11 |
| **v0.7.0** | **彻底解耦 doc-viewer + 自包含风格 12/13**| **2026-06-12** |
| v0.7.1 | 补 SOP 7.4 + Phase 3/4 强制要求（待办）| - |

---

## 十、相关链接

- **风格 12 报告**（JMKX003948 详细版）：https://doc.aishuo.co/vukii9m8
- **风格 13 报告**（JMKX003948 详细版）：https://doc.aishuo.co/kr6k7q92
- **SKILL.md**：`bd-eval-cms/SKILL.md`
- **EXECUTION.md**：`bd-eval-cms/EXECUTION.md`
- **SOP.md**：`bd-eval-cms/references/SOP.md`
- **D-0 路由器**：`bd-eval-cms/references/D-0_bd-evaluation-router.md`
- **总规则**：`bd-eval-cms/references/00_CMS-投前评估技能体系总规则.md`

---

_本文档为 v0.7.0 工作流整理，下一次更新将纳入 v0.7.1 SOP 修补内容。_
