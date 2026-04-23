---
name: pharma-market-landscape-report
version: "v1.0.3"
skillcode: pharma-market-landscape-report
description: 药品市场全景报告生成技能。采用固定 15 章、3 部分结构，输出单一 HTML 报告，适用于多治疗领域与多市场的市场洞察、KOL 映射、渠道策略与准入分析。
tags:
  - pharmaceutical
  - market-landscape
  - kol-mapping
  - channel-strategy
  - market-intelligence
category: professional-skill
author: Agent Factory
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604232/pharma-market-landscape-report
date: "2026-04-23"
changelog: |
  - v1.0.0 (2026-04-23): 初始版本，已验证皮肤科/肾脏科/精神科 × 港台新马场景
  - v1.0.1 (2026-04-23): 完成 P0 修复，增强 research schema 字段约束与章节证据完整性要求
  - v1.0.3 (2026-04-23): 新增多语言（zh-CN/zh-TW/en/ms）i18n 支持，模板 UI 标签全部通过 CSS 变量化，SKILL.md 增加多语言处理规范
---

# 药品市场全景报告技能

## 技能目标
为指定产品、治疗领域与目标市场生成高可信度的药品市场全景报告。报告必须遵循固定的 15 章、3 部分结构，输出为单一 HTML 文件，并包含表格、引用、callout box、参考文献与章节级证据映射。

## 适用场景
- 用户需要某个药品或品牌在特定市场的完整市场全景报告。
- 用户希望在一份报告内同时查看流行病学、治疗格局、竞争格局、患者分布、KOL 映射、准入与渠道策略。
- 输出需要达到可交付、可审阅、可追溯的 HTML 报告质量，而不是聊天式摘要。

## 不适用场景
- 用户仅需要简短摘要、单页结论或幻灯片内容。
- 用户只问一个单点市场问题，例如价格、注册状态或单一竞品信息。
- 无法获取可靠来源，且用户不接受“先调研、后成文”的执行方式。

## 必填输入
- `product_name`：品牌名 + 通用名
- `therapy_area`：治疗领域 / 疾病领域
- `target_market`：目标市场 / 国家 / 地区
- `language`：输出语言，支持以下值：
  - `zh-CN`：简体中文（默认）
  - `zh-TW`：繁体中文
  - `en`：English
  - `ms`：Bahasa Melayu
  - 执行时需根据该值设置 HTML `lang` 属性（`<html lang="{{LANG}}">`），模板将自动切换 UI 标签语言
  - 对于新加坡、马来西亚，默认准备双语版本（`en` 为主版本），除非用户明确要求单语输出

## 选填输入
- `local_brand_name`：当地品牌名
- `license_holder`：许可持有方 / 商业化主体
- `assessment_mode`：`market-only` 或 `company-specific`
- `special_notes`：额外限制、优先来源、关注渠道
- `output_mode`：`full-report` | `research-pack` | `outline-first`

## 硬规则
- 严禁编造事实。
- 任何未找到的数据必须明确写为 `[未找到]`。
- 所有市场特异、定量、准入、KOL、定价、注册、医保相关结论都必须带来源。
- 来源优先级固定为：监管 / 政府 > 指南 / 期刊 > 医院 / 学会 > 企业 > 媒体。
- 在章节级证据收集完成前，不得开始撰写最终报告正文。
- 除非用户明确要求缩减结构，否则必须保持完整的 15 章 / 3 部分骨架。

## 执行模型
严格按 `workflow.md` 的 7 个阶段执行：信息采集、调研规划、证据收集、组装规划、报告撰写、QA 验证、发布。

## 输入校验行为
仅当以下任一核心输入缺失时，才停止并请求补充：
- `product_name`
- `therapy_area`
- `target_market`
- `language`

如果输出语言与当地常用业务语言不一致，可继续执行，但需在执行摘要元信息中标注语言适配风险。
若目标市场为新加坡或马来西亚，默认按双语交付兼容性准备，除非用户明确要求单语输出。

## 调研轨道
必须建立且仅建立 3 条调研轨道：
1. 市场全景
2. 患者分布
3. 渠道深挖

每条轨道都必须显式绑定产品、治疗领域与目标市场，不允许脱离场景写通用内容。

## 证据 schema 最低要求
每章证据文件应至少覆盖以下信息块：
- 章节元数据：章节编号、章节名称、市场、产品、更新时间
- `key_findings`：不少于 3 条、逐条带来源
- `data_tables`：不少于 1 张结构化表格
- `callout_candidates`：不少于 1 条，可映射为 `highlight-box`、`insight` 或 `action-box`
- `references`：章节参考文献列表，包含标题、机构、年份、URL
- `data_gaps`：所有缺口统一记录为 `[未找到]`
- `kol_notes`：如适用，记录 KOL 姓名、机构、职称、影响力判断与来源
- `confidence_note`：说明证据质量、时间口径、样本限制或推断边界

## 报告骨架
### 第一部分：市场全景
1. 流行病学与疾病负担
2. 医疗体系概览
3. 当前治疗格局
4. 竞争格局与注册状态
5. KOL 识别
6. 推广渠道分析

### 第二部分：患者分布
7. 患者地理分布与渠道结构
8. 治疗渠道分布
9. 医保 / 处方集 / 费用结构
10. 患者人口统计学与诊断缺口

### 第三部分：渠道深挖
11. 服务提供者总览
12. 重点机构逐院拆解
13. KOL 分层与学术网络
14. 费用结构与健康经济学
15. X+Y+N 覆盖策略与分阶段行动方案

## 全量报告最低交付标准
- 1 个 HTML 文件
- 15 个章节
- 至少 15 条参考文献
- 至少 15 张表格
- 至少 10 个 callout box
- 全文关键结论均带行内引用
- 参考文献区提供可访问 URL

## 每章最低内容要求
- 至少 1 张表格
- 至少 1 处引用
- 至少 1 个 callout box
- 如章节适用，必须提供 KOL 信息
- 涉及数字、比例、市场规模、价格、医保、机构、KOL 的段落必须可追溯

## 样式系统
最终 HTML 必须使用模板中已定义的 CSS 类，不得擅自创造平替类名。关键类如下：
- `highlight-box`
- `insight`
- `action-box`
- `tier-1`
- `tier-2`
- `tier-3`
- `patient-flow`
- `num-highlight`
- `pct-bar`
- `exec-summary`
- `part-divider`

## 多语言规范
模板 `templates/report_template.html` 内置 i18n（国际化和本地化）支持，通过 CSS 变量实现 UI 标签语言切换。

### 支持的语言
| 语言代码 | 名称 | 说明 |
|---------|------|------|
| `zh-CN` | 简体中文 | 默认语言 |
| `zh-TW` | 繁体中文 | 台湾、香港市场 |
| `en` | English | 新加坡、马来西亚（默认主版本） |
| `ms` | Bahasa Melayu | 马来西亚市场 |

### 语言切换机制
- Phase 5（报告撰写）阶段，执行者需将 `{{LANG}}` 替换为实际语言代码
- HTML `<html lang="{{LANG}}">` 属性控制 CSS 语言选择器
- CSS 变量 `--ui-*` 根据 `[lang="{{LANG}}"]` 属性选择器自动切换

### UI 变量清单（模板内使用）
| 变量名 | 用途 |
|--------|------|
| `{{UI_CONFIDENTIAL}}` | 保密标识文字 |
| `{{UI_EXEC_SUMMARY}}` | 执行摘要标题 |
| `{{UI_TOC}}` | 目录标题 |
| `{{UI_PART1/2/3}}` | 第一/二/三部分名称 |
| `{{UI_MARKET_LANDSCAPE}}` | 市场全景 |
| `{{UI_PATIENT_DISTRIBUTION}}` | 患者分布 |
| `{{UI_CHANNEL_TYPE}}` | 渠道深度报告 |
| `{{UI_REFERENCES}}` | 参考文献 |
| `{{UI_REPORT_DATE}}` | 报告日期（标签） |
| `{{UI_PRODUCT_CENTER}}` | 产品中心（标签） |
| `{{UI_VERSION}}` | 版本（标签） |
| `{{UI_CORE_QUESTION}}` | 核心问题（标签） |
| CSS var `--ui-*` | callout 框标签（highlight-box/insight/action-box/tier-1/2/3） |

### 新加坡 / 马来西亚双语策略
- 默认以 `en` 为主语言，HTML 标签、章节标题均使用英文
- 若用户要求双语，同时输出 `{{TARGET_MARKET}}_product_market_report_en.html` 和 `{{TARGET_MARKET}}_product_market_report_zh-CN.html`（或 `ms`）
- 双语版本共享同一套证据文件（JSON），仅 UI 标签语言不同

## 不同输出模式的行为
### `outline-first`
返回：
- 15 章提纲
- 每章的数据需求清单
- 风险点与优先调研来源建议

### `research-pack`
返回：
- 章节级证据文件集合
- 汇总参考文献清单
- 组装规划说明

### `full-report`
返回：
- 完整 HTML 报告
- 章节级证据文件
- QA 验证结果

## 失败与降级策略
- 若关键数据来源缺失，先记录为 `[未找到]`，同时保留来源搜索痕迹。
- 若某章节只有低可信度来源，必须在该章节显式标注证据等级风险。
- 若 KOL 无法实名确认，不得虚构姓名；可记录机构级学术影响力线索并说明限制。

## 成功判定
只有在以下条件全部满足时，才视为任务完成：
- 7 个阶段全部完成
- 15 个章节证据文件齐全
- HTML 报告结构完整且可渲染
- QA 清单完成逐项验证
- 所有缺失数据均已规范标注为 `[未找到]`
