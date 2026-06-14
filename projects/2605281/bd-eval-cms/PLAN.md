# bd-eval-cms Skill 规划文档

> **版本**：v0.1（规划稿）
> **日期**：2026-05-28
> **状态**：待 Evan 确认

---

## 1. 定位

bd-eval-cms 是基于 CMS（康哲药业）投前评估技能包的独立 Skill，与现有 bd-eval（方案A）并列运行。

- bd-eval = 通用 BD 评估，7套模板，自由章节，琥珀金报告
- bd-eval-cms = CMS 专属，19个技能 + 6-Gate 门控，麦肯锡深蓝报告

两套 Skill 各自独立，不共享 SKILL.md，但共享 Phase 1 DISCOVERY 的搜索方法论。

---

## 2. 整体流程（与 bd-eval 同构）

```
用户提供品种名称 + 业务主体信息
    ↓
Phase 1: DISCOVERY（宽度搜索，与 bd-eval 共用方法论）
    ↓
Phase 2: D-0 路由 + 技能确认 Battle
    ↓
Phase 3: GRV 逐 Gate 深度评估（6-Gate 结构）
    ↓
Phase 4: Gate Battle 对抗审查
    ↓
Phase 5: 报告合并 + 质量终检（含置信度审核）
    ↓
Phase 5.5: HTML 生成（麦肯锡深蓝 #1a3a5c）+ 上传归档
```

---

## 3. 目录结构

```
projects/2605152/bd-eval-cms/
├── SKILL.md                              ← 主入口，流程定义
├── QUICKREF.md                           ← 速查卡
├── VERSION                               ← 版本号
├── version.json                          ← 版本元数据
├── references/
│   ├── 00_CMS-投前评估技能体系总规则.md     ← 顶层规范
│   ├── 00_体系总规则增补条款_v1.1.md        ← 增补条款
│   ├── D-0_bd-evaluation-router.md        ← 路由调度器
│   ├── D-1_pharma-bd-due-diligence.md     ← 尽调基座14维度
│   ├── D-2_pharma-market-landscape-report.md ← 市场全景
│   ├── D-3_bd-project-one-pager.md        ← 投委会包
│   ├── A-0_bd-opportunity-intelligence.md ← 商机情报
│   ├── A-1_bd-cn-overseas-unlisted.md     ← 海外引进
│   ├── A-2_bd-cn-agency-rights.md         ← 国内合作
│   ├── A-3_bd-cn-self-rd-pipeline.md      ← 自主研发
│   ├── A-4_bd-cn-biosimilar.md            ← 生物类似药
│   ├── A-5_bd-cn-marketed-product-rights.md ← 已上市代理权
│   ├── A-6_bd-cn-rx-to-otc.md             ← 院内→院外
│   ├── A-7_bd-multi-target-screening.md   ← 多标的筛选
│   ├── A-8_bd-cn-generic-advanced.md      ← 高壁垒仿制药
│   ├── B-1_medical-aesthetics-product-evaluator.md ← 医美单标的
│   ├── B-2_medical-aesthetics-portfolio-audit.md   ← 医美组合
│   ├── B-3_bd-cn-otc-consumer-health.md   ← 消费健康
│   ├── C-1_bd-intl-single-market.md       ← 国际单品
│   ├── C-2_bd-intl-multi-market.md        ← 国际多市场
│   ├── C-3_bd-intl-portfolio-strategy.md  ← 康联达组合
│   ├── E-1_bd-equity-biotech-due-diligence.md ← 股权投资
│   ├── sub-agent-prompt-template.md       ← CMS版子Agent prompt（新建）
│   └── SOP.md                             ← CMS版完整流程规范（新建）
├── scripts/
│   ├── archive-links.sh                   ← 归档脚本（复用 bd-eval 逻辑）
│   ├── sync-to-knowledge-base.sh            ← 产品引进知识库同步
│   └── bd-eval-cms-health-check.sh        ← CMS版健康检测（新建）
└── projects/bd-eval-cms/{品种名}/         ← 运行时工作目录
    ├── state.json
    ├── links.md
    ├── 01-discovery.md
    ├── 02-gate-by-chapter/                ← 逐Gate章节（区别于 bd-eval 的按模板章节）
    ├── battle/
    ├── 03-battle-summary.md
    └── 04-final-report.md
```

---

## 4. 各 Phase 设计

### Phase 1: DISCOVERY

**与 bd-eval 共用方法论，但有 CMS 专属扩展。**

- 宽度搜索（≥5次 web_search）→ 不变
- 新增：识别业务主体（深康/德镁/维盛/院外/天津康哲/康联达）
- 新增：初步判断产品类型（为 D-0 路由准备）
- 新增：标的方画像确认（如用户知道合作方是谁）
- 产出：`01-discovery.md` + `state.json`（含业务主体和初步产品类型）

### Phase 2: D-0 路由 + 技能确认 Battle

**替代 bd-eval 的"模板选择 Battle"。**

1. 读取 D-0 路由决策树，根据 discovery 结果自动推荐技能编号
2. 输出路由决策单（技能编号 + 串接链路 + 置信度）
3. Spawn 审查层子 Agent：独立验证路由判断
4. 如同意 → 确认技能；如不同意 → 记录争议
5. 财务硬门槛初判：根据产品类型对照财务内控标准表

**产出**：`battle/ROUTE-SELECTION-AUDITOR.md` + 更新 `state.json`

### Phase 3: GRV 逐 Gate 深度评估

**核心差异：6-Gate 结构替代自由章节。**

按选定技能的评估章节结构，逐 Gate 深度搜索+撰写：

```
章0: One-pager 终局先立（必须先跑完）
    ↓
批次1: Gate 1 前提门 | Gate 2 定调门 | Gate 3 证据门（3个子Agent并行）
    ↓
批次2: Gate 4 支付门 | Gate 5 成本门（2个子Agent并行）
    ↓
Gate 6 可做门（需要前面所有Gate结论，串行跑）
    ↓
验证: 批量交叉检查
```

**子Agent prompt 按 CMS 标准模板**：
- 每个 Gate 章节必须输出结论卡（通过/条件通过/停止 + 置信度 + 需补证据Top5）
- 章节间需标注阶段标签 [阶段A] / [阶段B]
- 关键数据必须标注置信度等级（A/B/C/D）
- 信息来源按四分法标注（内部评估/外网核查/待确认/分析推断）

### Phase 4: Gate Battle 对抗审查

**与 bd-eval 的 Battle 逻辑一致，但校验标准不同。**

1. 审查层子Agent：以 CMS 体系标准审查全部 Gate 章节
   - 每个Gate结论卡的置信度是否合理
   - 财务指标是否达到硬门槛
   - 一票否决清单是否完整核查
   - 置信度标注是否合规（C/D级数据是否在执行摘要中披露）
   - 信息冲突是否正确标记
2. 执行层逐条回应
3. 最多3轮

### Phase 5: 报告合并 + 质量终检

1. 合并 One-pager + 全部 Gate 章节 + Battle summary → `04-final-report.md`
2. 质量终检（CMS版，8项）：
   - ① Gate 1-6 结论卡完整性
   - ② 财务硬门槛达标情况
   - ③ 一票否决清单核查（7条体系级 + 技能专属）
   - ④ 置信度标注完整性（关键数据不超过3处缺失）
   - ⑤ 信息冲突汇总表（附录C）非空
   - ⑥ 阶段标签标注正确
   - ⑦ 来源四分法标注覆盖
   - ⑧ 财务缩写首次出现标注中文全称

### Phase 5.5: HTML 生成 + 上传归档

**与 bd-eval 的差异：麦肯锡深蓝风格，非琥珀金。**

- 主色：深蓝 `#1a3a5c`
- 风格：麦肯锡（结论先行、数据驱动、无装饰）
- 禁止灰色字体
- 禁止元描述
- 财务缩写首次出现标注中文全称
- Gate 结论卡用统一的视觉样式
- 信息冲突用琥珀色边框标记

---

## 5. state.json 结构

```json
{
  "name": "{品种名}",
  "scheme": "B",
  "businessEntity": "深康|德镁|维盛|院外|天津康哲|康联达",
  "routedSkill": "A-1",
  "routedChain": ["D-1", "D-2", "A-1", "D-3"],
  "phase": "discovery_complete",
  "startedAt": "{ISO时间}",
  "financialThresholdType": "创新药|仿制药|医美|消费健康",
  "discovery": {
    "searches": 5,
    "sources": ["..."],
    "productType": "创新药",
    "confidence": "高"
  }
}
```

---

## 6. 需要新建的核心文件

| 文件 | 用途 | 工作量 |
|------|------|--------|
| SKILL.md | 主入口，流程定义 | 中 |
| QUICKREF.md | 速查卡 | 小 |
| SOP.md | CMS版完整流程规范 | 大（核心） |
| sub-agent-prompt-template.md | CMS版子Agent prompt（Gate结构） | 中 |
| bd-eval-cms-health-check.sh | 健康检测 | 小 |
| version.json + VERSION | 版本管理 | 小 |

references/ 下的 22 个 md 文件直接从方案B技能包复制，不需要重写。

---

## 7. 与 bd-eval 的关系

```
bd-eval (方案A)                    bd-eval-cms (方案B)
├── SKILL.md                       ├── SKILL.md
├── references/                    ├── references/
│   ├── SOP.md                     │   ├── SOP.md（新建）
│   ├── bd_report_templates_full.md│   ├── 00_总规则.md（从技能包复制）
│   └── sub-agent-prompt-template  │   ├── D-0 ~ E-1 共22个技能文件（复制）
│                                  │   ├── sub-agent-prompt-template（新建）
│                                  │   └── 00_增补条款.md（复制）
├── scripts/                       ├── scripts/
│   ├── archive-links.sh           │   ├── archive-links.sh（复用）
│   ├── sync-to-knowledge-base.sh   │   ├── sync-to-knowledge-base.sh（知识库同步）
│   └── health-check.sh            │   └── health-check-cms.sh（新建）
└── projects/bd-eval/{品种}/       └── projects/bd-eval-cms/{品种}/
```

**共享规则**：
- Phase 1 DISCOVERY 的搜索方法论相同（web_search ≥5次，覆盖相同维度）
- HTML 报告统一同步到产品引进知识库（doc.aishuo.co 长链接）
- 品种目录结构对齐（01-discovery / 02-gate-by-chapter / battle / 04-final-report）

**独立规则**：
- 各自独立的 SKILL.md 和触发词
- 各自独立的子Agent prompt 模板
- 各自独立的报告风格（琥珀金 vs 麦肯锡深蓝）
- 各自独立的健康检测脚本

---

## 8. 版本计划

**v0.1（本次）**：骨架搭建
- SKILL.md + QUICKREF.md + SOP.md
- references/ 全部文件就位
- scripts/ 就位
- 首次提交

**v0.2（首次可用）**：完整流程验证
- sub-agent-prompt-template.md 完成
- 单品种端到端跑通
- 修复发现的问题

**v1.0（正式版）**：发布
- 至少3个品种验证通过
- 健康检测脚本完善
- 文档定稿

---

## 9. 待确认事项

1. **触发词**：bd-eval-cms 的触发词怎么定？建议「CMS评估」「康哲评估」「CMS投前评估」
2. **与 doc-viewer 的关系**：方案B要求调用 writing skill（SKILL.md Step 1），但 doc-viewer 也有 HTML 生成能力。是继续用 doc-viewer 生成，还是按方案B要求先调 writing skill？
3. **A-5 vs bd-eval 模板二**：方案B的 A-5（已上市产品推广权引进）与方案A模板二高度重叠，用户可能混淆。是否需要在路由时给提示？
4. **writing skill**：方案B的 SKILL.md 要求先 `load_skill(skill_name="writing")`，这个 writing skill 是 CMS 体系自带的还是需要另外安装？

---

_规划稿，待 Evan 确认后进入实施。_
