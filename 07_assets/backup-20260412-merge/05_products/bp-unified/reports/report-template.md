# {{BP_CODE}} 两级联动审计报告模板

> BP ID：`{{BP_ID}}`
> BP 名称：{{BP_NAME}}
> 审计时间：{{AUDIT_TIME}}
> 审计范围：两级联动（根 BP + 下级承接 BP）
> 审计依据：GRV v3.0 + BP 评估分析规范 v1.0

---

## 审计概览

| 项目 | 内容 |
|------|------|
| 根 BP | {{ROOT_BP_CODE}} — {{ROOT_BP_NAME}} |
| 根 BP 层级 | {{ROOT_BP_LEVEL}} |
| 下级承接 BP 数量 | {{DOWNSTREAM_BP_COUNT}} |
| P0 问题数 | {{P0_COUNT}} |
| P1 问题数 | {{P1_COUNT}} |
| P2 问题数 | {{P2_COUNT}} |

---

## 第一级：{{ROOT_BP_CODE}} 自身评估

### 1.1 目标层评估

| 维度 | 检查项 | 实际值 | 判定 | 证据 |
|------|--------|--------|------|------|
| 清晰性 | description 是否明确 | {{goal.description}} | P0/P1/PASS | — |
| 可衡量性 | measureStandard 含数字 | {{goal.measureStandard}} | P0/PASS | — |
| 对齐性 | upwardTaskList 是否非空 | {{goal.upwardCount}} 个上游 | P1/PASS | — |
| 完整性 | 业务方向覆盖是否完整 | {{goal.businessCoverage}} | P1/PASS | — |

**目标层结论**：{{GOAL_LAYER_CONCLUSION}}

### 1.2 KR 层评估

{{REPEAT_PER_KR_START}}

#### {{KR_CODE}}：{{KR_NAME}}

| 维度 | 检查项 | 实际值 | 判定 | 证据 |
|------|--------|--------|------|------|
| 充分性 | KR 是否覆盖 BP 目标 | — | PASS/P0 | — |
| 独立性 | 与其他 KR 边界是否清晰 | — | PASS/P0 | — |
| SMART-S | measureStandard 是否定义业务边界 | {{KR.ms}} | PASS/P0 | — |
| SMART-M | measureStandard 是否含数字 | {{KR.ms}} | PASS/P0 | — |
| 匹配性 | 责任人是否与 KR 方向匹配 | {{KR.people}} | PASS/P0 | — |
| 支撑性 | 是否有举措或下游承接 | {{KR.actionCount}}举措 / {{KR.downCount}}下游 | PASS/P0 | — |

**{{KR_CODE}} 结论**：{{KR_CONCLUSION}}

{{REPEAT_PER_KR_END}}

### 1.3 举措层评估

{{REPEAT_PER_ACTION_START}}

#### {{KR_CODE}} 举措

| 举措ID | 名称 | 承接人 | 截止日期 | 状态 | 延期天数 | 判定 | 证据 |
|--------|------|--------|---------|------|---------|------|------|
| {{ACTION_ID}} | {{ACTION_NAME}} | {{ACTION_PEOPLE}} | {{ACTION_PLAN}} | {{ACTION_STATUS}} | {{ACTION_EXPIRED_DAYS}}天 | P0/P1/PASS | — |

{{REPEAT_PER_ACTION_END}}

**举措层结论**：{{INITIATIVE_LAYER_CONCLUSION}}

### 1.4 第一级问题汇总

| 编码 | 问题 | 严重度 | 所属层级 | 整改建议 |
|------|------|--------|---------|---------|
| ... | ... | P0 | 第一级 | ... |

**第一级 P0 小计**：{{LEVEL1_P0_COUNT}} 项

---

## 第二级：下级承接 BP 评估

{{REPEAT_PER_DOWNSTREAM_BP_START}}

### 2.{{INDEX}} {{DOWNSTREAM_BP_CODE}}（{{DOWNSTREAM_BP_DEPT}}，{{DOWNSTREAM_BP_PEOPLE}}）

**承接关系**：
- 上游来源：{{ROOT_BP_CODE}}.{{SOURCE_KR_CODE}}
- 承接方式：{{承接方式（直接承接KR / 通过举措承接）}}
- 承接 BP ID：`{{DOWNSTREAM_BP_ID}}`

#### 2.{{INDEX}}.1 目标层评估

| 维度 | 检查项 | 实际值 | 判定 | 与上游对齐性 |
|------|--------|--------|------|------------|
| 清晰性 | description | {{DS.goal.description}} | P0/P1/PASS | — |
| 可衡量性 | measureStandard | {{DS.goal.measureStandard}} | P0/PASS | — |
| 对齐性 | 是否承接上游 KR/举措 | — | PASS/P1 | {{ALIGNMENT_CHECK}} |
| 完整性 | 业务方向覆盖 | {{DS.goal.businessCoverage}} | P1/PASS | — |

**对齐性分析**：{{DS_GOAL_ALIGNMENT_ANALYSIS}}

**目标层结论**：{{DS_GOAL_CONCLUSION}}

#### 2.{{INDEX}}.2 KR 层评估

{{REPEAT_PER_DS_KR_START}}

**{{DS_KR_CODE}}**：{{DS_KR_NAME}}

| 维度 | 检查项 | 实际值 | 判定 | 证据 |
|------|--------|--------|------|------|
| 充分性 | KR 是否覆盖 BP 目标 | — | PASS/P0 | — |
| SMART-M | measureStandard 含数字 | {{DS_KR.ms}} | PASS/P0 | — |
| 匹配性 | 责任人是否匹配 | {{DS_KR.people}} | PASS/P0 | — |
| 支撑性 | 有无举措/下游 | {{DS_KR.actionCount}}举措 / {{DS_KR.downCount}}下游 | PASS/P0 | — |

{{REPEAT_PER_DS_KR_END}}

**KR 层结论**：{{DS_KR_CONCLUSION}}

#### 2.{{INDEX}}.3 举措层评估（如有）

| 举措ID | 名称 | 承接人 | 截止日期 | 状态 | 延期天数 | 判定 |
|--------|------|--------|---------|------|---------|------|
| ... | ... | ... | ... | ... | ... | P0/P1/PASS |

**举措层结论**：{{DS_INITIATIVE_CONCLUSION}}

#### 2.{{INDEX}}.4 承接有效性评估

- 上游举措完成 → 下游 BP 目标是否能支撑：**{{UPSTREAM_TO_GOAL_VALIDITY}}**
- 下游 BP 目标 → 下游 KR 是否能支撑上游举措：**{{GOAL_TO_KR_VALIDITY}}**
- 下游 KR → 下游举措是否可执行：**{{KR_TO_ACTION_VALIDITY}}**

**承接有效性结论**：{{DS_VALIDITY_CONCLUSION}}

#### 2.{{INDEX}} 问题汇总

| 编码 | 问题 | 严重度 | 整改建议 |
|------|------|--------|---------|
| ... | ... | P0/P1 | ... |

{{REPEAT_PER_DOWNSTREAM_BP_END}}

---

## 问题汇总总表

| 编码 | 问题 | 严重度 | 所属层级 | 所在 BP | 整改建议 |
|------|------|--------|---------|---------|---------|
| {{PROBLEM_CODE}} | {{PROBLEM}} | P0/P1/P2 | 第一级/第二级 | {{BP_CODE}} | {{SUGGESTION}} |

**总计**：P0 = {{TOTAL_P0}} 项，P1 = {{TOTAL_P1}} 项，P2 = {{TOTAL_P2}} 项

---

## 总体结论

### 可实现性评估

{{FEASIBILITY_ASSESSMENT}}

### 整改优先级

**优先级 1（立即整改）**：
{{PRIORITY_1_ITEMS}}

**优先级 2（7 天内整改）**：
{{PRIORITY_2_ITEMS}}

**优先级 3（14 天内整改）**：
{{PRIORITY_3_ITEMS}}

### 建议下一步行动

{{NEXT_ACTIONS}}

---

*报告生成时间：{{REPORT_TIME}}*
*审计人：BP Agent（基于 GRV v3.0 + BP 评估分析规范 v1.0）*
