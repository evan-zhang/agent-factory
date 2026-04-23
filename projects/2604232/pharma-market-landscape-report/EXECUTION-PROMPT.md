执行提示词

## 输入参数
请将以下变量替换为真实值后执行：

```text
产品名称：{产品名称（品牌名 + 通用名）}
当地品牌名：{当地品牌名；如无则填“同上”}
治疗领域：{治疗领域 / 疾病}
目标市场：{目标市场 / 国家 / 地区}
语言：{输出语言}
许可公司：{许可公司；如无则填“无”}
评估角度：market-only / company-specific
输出模式：full-report / research-pack / outline-first
执行日期：2026-04-23
```

请按照 `pharma-market-landscape-report` Skill 定义执行市场全景报告生成。必须严格串行执行，不跳步、不并行合并阶段。

## 全局执行要求
1. 必须严格按以下 7 个阶段顺序执行：
   `Phase 1 信息采集 → Phase 2 调研规划 → Phase 3 证据收集 → Phase 4 组装规划 → Phase 5 报告撰写 → Phase 6 QA 验证 → Phase 7 发布`
2. 开始前必须先读取：
   - `SKILL.md`
   - `workflow.md`
   - `templates/report_template.html`
   - `schemas/research_note_schema.json`
   - `checklists/qa_checklist.md`
3. 硬规则：
   - 不得编造数据；缺口统一写为 `[未找到]`
   - 所有定量数据、准入信息、KOL 信息、定价信息必须带来源
   - 来源优先级：政府 / 监管机构 > 指南 / 期刊 > 医院 / 学会 > 企业 > 媒体
   - 证据未完成前，不得撰写最终 HTML 报告
4. 输出目录固定为：
   `_runtime/projects/2604232/{market_code}_{product_code}/`
5. 每个阶段必须输出独立文件；除当前阶段文件外，不回写前一阶段文件。
6. 所有输出统一使用中文；专业术语保留英文原文，例如 KOL、JAK、ESRD、CKD、HD、PD、SHS、HA、NSC、TFDA、NHI。

## Phase 1：信息采集
目标：确认任务边界、标准化命名与术语口径。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/01-intake.json`

格式要求：
- 必须为合法 JSON
- 顶层字段必须包含：`product_name`、`local_brand_name`、`therapy_area`、`target_market`、`language`、`license_holder`、`assessment_mode`、`output_mode`、`execution_date`
- 必须补充：`market_code`、`product_code`、`naming_rules`、`terminology_rules`、`priority_sources`
- 若输入缺失，必须增加 `blocking_issues` 数组并停止后续阶段

示例：
```json
{
  "product_name": "Velphoro (sucroferric oxyhydroxide)",
  "local_brand_name": "Velphoro",
  "therapy_area": "肾脏科 / CKD / 高磷血症",
  "target_market": "台湾",
  "language": "繁體中文",
  "license_holder": "Rxilient Medical Taiwan",
  "assessment_mode": "market-only",
  "output_mode": "full-report",
  "execution_date": "2026-04-23",
  "market_code": "tw",
  "product_code": "velphoro",
  "naming_rules": {
    "currency": "TWD",
    "date_format": "YYYY-MM-DD",
    "institution_name_style": "官方中文名称优先，首次出现可附英文"
  },
  "terminology_rules": [
    "KOL 保留英文缩写",
    "TFDA、NHI 保留英文缩写"
  ],
  "priority_sources": ["TFDA", "NHI", "台湾肾脏医学会", "医学中心官网"],
  "blocking_issues": []
}
```

## Phase 2：调研规划
目标：将任务拆为 3 条调研轨道，并映射到 15 章。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/02-research-plan.md`

格式要求：
- 使用 Markdown
- 必须包含“目标”“调研轨道”“章节映射”“优先来源”“风险与缺口预判”五部分
- 每条轨道必须列出对应章节编号、核心问题、拟用来源、预期表格类型
- 必须显式说明哪些章节需要重点收集 KOL 信息

示例：
```md
# 调研规划

## 目标
- 产出台湾市场 Velphoro 全景报告

## 调研轨道
### 轨道 A：市场全景
- 对应章节：1, 2, 3, 4, 5, 6
- 核心问题：高磷血症患者规模、透析场景治疗路径、竞品与注册状态
- 预期表格：流行病学表、竞品注册表、KOL 映射表

### 轨道 B：患者分布
- 对应章节：7, 8, 9, 10
- 核心问题：HD / PD 渠道占比、NHI 给付路径、诊断缺口

### 轨道 C：渠道深挖
- 对应章节：11, 12, 13, 14, 15
- 核心问题：重点医学中心、肾脏科 KOL 分层、X+Y+N 策略
```

## Phase 3：证据收集
目标：逐章完成结构化证据沉淀。

输出目录：
`_runtime/projects/2604232/{market_code}_{product_code}/evidence/`

输出文件列表：
- `ch01_epidemiology.json`
- `ch02_healthcare_system.json`
- `ch03_treatment_landscape.json`
- `ch04_competitive_landscape.json`
- `ch05_kol_identification.json`
- `ch06_promotional_channels.json`
- `ch07_geographic_distribution.json`
- `ch08_treatment_channels.json`
- `ch09_reimbursement_formulary.json`
- `ch10_patient_demographics.json`
- `ch11_provider_overview.json`
- `ch12_top_institutions.json`
- `ch13_kol_tiering.json`
- `ch14_cost_economics.json`
- `ch15_coverage_strategy.json`

格式要求：
- 每个文件必须符合 `schemas/research_note_schema.json`
- 每章至少包含：3 条 `key_findings`、1 个 `data_tables`、1 个 `callout_candidates`、1 组 `references`
- 如章节适用，必须包含 `kol_notes`
- 未找到的数据必须进入 `data_gaps`
- 关键发现中不得只写结论，必须写“结论 + 数值 / 事实 + 来源”

示例：
```json
{
  "chapter_id": "ch05",
  "chapter_title": "KOL 识别",
  "key_findings": [
    {
      "claim": "台湾肾脏科 KOL 主要集中在医学中心与大型教学医院",
      "source": "台湾肾脏医学会、医学中心官网",
      "evidence_level": "中高"
    }
  ],
  "data_tables": [
    {
      "title": "重点 KOL 名单",
      "columns": ["机构", "姓名", "职称", "专长", "来源"]
    }
  ],
  "callout_candidates": [
    {
      "type": "insight",
      "text": "高影响力 KOL 与大型透析中心高度重合，可作为学术覆盖优先对象。"
    }
  ],
  "kol_notes": [
    {
      "name": "[未找到]",
      "institution": "某医学中心肾脏科",
      "note": "机构层级可确认，但实名未完成交叉验证"
    }
  ],
  "references": [
    {
      "title": "台湾肾脏医学会会员资料",
      "url": "https://example.org"
    }
  ],
  "data_gaps": ["部分 KOL 学术头衔缺少二次来源验证"]
}
```

## Phase 4：组装规划
目标：在写 HTML 前完成证据完备性与引用一致性检查。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/04-assembly-check.md`

格式要求：
- 使用 Markdown
- 必须包含“章节完整性”“引用去重”“关键缺口”“X+Y+N 可落地性”“进入写作结论”五部分
- 每一章都要标记 `READY` / `GAP`
- 如存在 GAP，必须写清缺什么、如何在正文中暴露为 `[未找到]`

示例：
```md
## 章节完整性
- Ch01：READY
- Ch05：GAP（KOL 学术职称缺少二次来源）

## X+Y+N 可落地性
- X：已识别 8 家重点机构
- Y：已实名确认 5 位核心 KOL
- N：已识别 3 类连锁 / 网络渠道

## 进入写作结论
- 条件满足，可进入 HTML 撰写；Ch05 缺口须在正文中标记 `[未找到]`
```

## Phase 5：报告撰写
目标：基于模板产出最终 HTML 报告。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/{market_code}_{product_code}_market_report_{lang}.html`

格式要求：
- 必须使用 `templates/report_template.html` 作为骨架
- 必须包含封面、执行摘要、目录、3 个部分分隔页、15 个章节、参考文献
- 每章必须包含：表格、引用、callout box、KOL 信息（如适用）
- 只能使用模板中已有的 CSS 类：`highlight-box`、`insight`、`action-box`、`tier-1/2/3`、`patient-flow`、`num-highlight`、`pct-bar`、`exec-summary`、`part-divider`
- 若某数据缺失，正文中直接写 `[未找到]`，不得省略该字段

示例：
```html
<section id="s5">
  <div class="section-header">
    <div class="section-id">第五章</div>
    <h2 class="section-title">KOL 识别</h2>
  </div>
  <div class="insight">核心 KOL 主要集中于医学中心肾脏科与大型透析网络。</div>
  <table>
    <thead>
      <tr><th>机构</th><th>KOL</th><th>职称</th><th>来源</th></tr>
    </thead>
    <tbody>
      <tr><td>台大医院</td><td>[未找到]</td><td>教授</td><td>[1]</td></tr>
    </tbody>
  </table>
</section>
```

## Phase 6：QA 验证
目标：逐项执行 QA 清单并形成可复检报告。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/06-qa-report.md`

格式要求：
- 使用 Markdown
- 每个检查项必须有：检查项名称、结果、验证方法、发现问题、修复动作、复检结果
- 结果只能使用 `PASS` 或 `FAIL`
- 统计汇总必须包含 PASS 数、FAIL 数、`[未找到]` 数据点数量

示例：
```md
## QA 汇总
- PASS：18
- FAIL：2
- [未找到]：7

## 检查项：每章至少有 1 张表格
- 结果：PASS
- 验证方法：统计全文 `<table>` 共 17 张
- 发现问题：无
- 修复动作：无
- 复检结果：PASS
```

## Phase 7：发布
目标：输出最终交付物并固化结果。

输出文件：
`_runtime/projects/2604232/{market_code}_{product_code}/publish/{market_code}_{product_code}_market_report_{lang}.html`

格式要求：
- 发布前确认最终 HTML 与 QA 通过版一致
- 若存在发布目录，复制最终 HTML 到 `publish/`
- 同目录保留 `06-qa-report.md` 与 `evidence/` 供审计追溯

示例：
```text
publish/
├── tw_velphoro_market_report_zh-TW.html
├── 06-qa-report.md
└── evidence/
    ├── ch01_epidemiology.json
    └── ...
```

## 完成后仅返回的摘要
全部阶段完成后，只简要返回以下 5 项：
1. 7 个阶段是否全部完成
2. 15 个证据 JSON 文件是否齐全
3. 最终 HTML 报告文件大小与行数
4. QA 检查 PASS / FAIL 数量
5. 标记为 `[未找到]` 的数据点数量
