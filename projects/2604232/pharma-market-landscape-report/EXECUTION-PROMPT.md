执行提示词：

输入：
产品名称：{产品名称（品牌名+通用名）}
当地品牌名：{当地品牌名，如无则填"同上"}
治疗领域：{治疗领域/疾病}
目标市场：{目标市场/国家/地区}
语言：{输出语言}
许可公司：{许可公司，如无则填"无"}
评估角度：market-only / company-specific
输出模式：full-report / research-pack / outline-first
执行日期：2026-04-23

请按照 pharma-market-landscape-report Skill 定义执行市场全景报告生成。不要跳过任何阶段，不要并行执行不同阶段。

全局执行要求：
1. 必须按以下7个阶段严格顺序执行，不跳步、不合并：
   Phase 1 信息采集 → Phase 2 调研规划 → Phase 3 证据收集 → Phase 4 组装规划 → Phase 5 报告撰写 → Phase 6 QA验证 → Phase 7 发布
2. 必须先读取 Skill 定义文件获取完整规范：
   - SKILL.md（技能定义、硬规则、CSS样式系统）
   - workflow.md（7步执行流程）
   - templates/report_template.html（HTML模板，用于最终报告）
   - schemas/research_note_schema.json（调研笔记结构）
   - checklists/qa_checklist.md（QA检查清单）
3. 硬规则：
   - 绝不编造数据。未找到的数据必须标记为 [未找到]
   - 所有定量数据、准入信息、KOL信息、定价信息必须有来源引用
   - 来源优先级：政府/监管机构 > 指南/期刊 > 医院/学会 > 企业 > 媒体
   - 不在证据收集完成前开始撰写最终报告
4. 输出目录统一为：_runtime/projects/2604232/{market_code}_{product_code}/
5. 每个阶段的输出写入独立文件，不修改其他阶段的文件

请按以下阶段逐步执行：

=== Phase 1：信息采集 ===
采集并确认所有输入参数，如缺少产品名/治疗领域/目标市场/语言中的任何一个，立即停止并请求补充。
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/01-intake.json
格式：JSON，包含所有输入参数、市场命名规范、术语风格

=== Phase 2：调研规划 ===
规划3个调研轨道：
- 轨道A 市场全景：流行病学+医疗体系+治疗格局+竞争格局+KOL+推广渠道
- 轨道B 患者分布：地理分布+治疗渠道+医保/处方集+患者人口统计
- 轨道C 渠道深度：服务提供者+关键机构+KOL分层+费用结构+X+Y+N策略
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/02-research-plan.md

=== Phase 3：证据收集 ===
按15章逐一收集证据，每章存为一个独立的 JSON 文件（遵循 research_note_schema.json 结构）。
每章必须包含：
- 3+条有来源的关键发现
- 1+个结构化表格
- 1+个 Callout 候选（highlight-box/insight/action-box）
- 章节参考文献
- 未找到的数据记入 data_gaps

输出目录：_runtime/projects/2604232/{market_code}_{product_code}/evidence/
文件列表：
  ch01_epidemiology.json
  ch02_healthcare_system.json
  ch03_treatment_landscape.json
  ch04_competitive_landscape.json
  ch05_kol_identification.json
  ch06_promotional_channels.json
  ch07_geographic_distribution.json
  ch08_treatment_channels.json
  ch09_reimbursement_formulary.json
  ch10_patient_demographics.json
  ch11_provider_overview.json
  ch12_top_institutions.json
  ch13_kol_tiering.json
  ch14_cost_economics.json
  ch15_coverage_strategy.json

=== Phase 4：组装规划 ===
撰写报告前验证：
- 全部15章是否有证据（缺失章节标注）
- 参考文献去重
- X+Y+N策略是否基于实际发现的机构和KOL
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/04-assembly-check.md

=== Phase 5：报告撰写 ===
基于 templates/report_template.html 模板撰写最终 HTML 报告。
按以下顺序组装：封面 → 执行摘要 → 目录 → Part I (Ch1-6) → Part II (Ch7-10) → Part III (Ch11-15) → 参考文献。
严格使用 SKILL.md 中定义的 CSS 类，不自行发明新的 HTML 结构。
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/{market_code}_{product_code}_market_report_{lang}.html

=== Phase 6：QA验证 ===
逐项执行 checklists/qa_checklist.md 中的检查清单。
结构性检查：15章完整、3个分隔符、section id正确、参考文献存在
内容检查：每章有表格、引用完整、KOL分层正确、X+Y+N具名、[未找到]标记
格式检查：CSS类一致、HTML标签闭合、引用锚点匹配、URL完整
最低门槛：15+参考文献、15+表格、10+Callout框
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/06-qa-report.md
格式：每项检查记录 PASS/FAIL，FAIL 项附修复说明

=== Phase 7：发布 ===
QA 全部通过后，将最终 HTML 报告复制到发布目录。
输出文件：_runtime/projects/2604232/{market_code}_{product_code}/publish/{market_code}_{product_code}_market_report_{lang}.html

全部阶段完成后，只简要告诉我：
1. 7个阶段是否全部完成
2. 15个证据JSON文件是否齐全
3. 最终HTML报告文件大小和行数
4. QA检查有多少项PASS/FAIL
5. 有多少数据点标记为[未找到]
