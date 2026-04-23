# pharma-market-landscape-report

`pharma-market-landscape-report` 是一个用于生成药品市场全景报告的多文件 Skill 包，当前版本为 `v1.0.2`。

## 包结构
- `SKILL.md`：技能定义、适用边界、硬规则、报告骨架与样式约束。
- `workflow.md`：7 阶段执行流程与阶段交付要求。
- `templates/report_template.html`：最终 HTML 报告模板。
- `checklists/qa_checklist.md`：发布前 QA 检查清单与验证方法。
- `schemas/research_note_schema.json`：章节级证据文件 schema。
- `examples/input_example.md`：输入示例与预期行为说明。
- `EXECUTION-PROMPT.md`：可直接执行的阶段化提示词。

## 推荐执行方式
1. 完成信息采集与输入校验。
2. 规划 3 条调研轨道并映射到 15 章。
3. 逐章沉淀证据文件。
4. 进行组装前检查与引用去重。
5. 按模板生成 HTML 报告。
6. 按 QA 清单逐项验证。
7. 输出发布版 HTML、QA 报告与证据文件。

## 设计原则
- 结构固定：15 章、3 部分，不随意缩减。
- 证据优先：先收集证据，后撰写报告。
- 全文可追溯：关键数字、KOL、准入与定价信息必须带来源。
- 缺口显式化：未找到的数据统一标记为 `[未找到]`。
- 样式统一：仅使用模板预置 CSS 类，不新增随意样式。

## 适合的交付物
- 单一市场的药品市场全景报告
- 覆盖流行病学、治疗格局、竞争格局、KOL、渠道与准入的综合报告
- 需审阅、归档、打印或正式交付的 HTML 成品
