# REVIEW-DESIGN-v0.9.1 - 独立评审记录

- 日期：2026-06-13
- 评审对象：design/DESIGN-v0.9.1.md
- 对象类型：B 类，Skill 方案设计
- 评审结论：CONDITIONAL_PASS

## 1. 总体结论

DESIGN-v0.9.1 与 REQ-v0.9.1、v0.9 复盘结论一致。方案方向正确、范围克制、治理思路清晰，适合作为 v0.9.1 质量固化版的方案基础。

但在进入 S4 开发前，必须补齐 5 个落地级缺口。这些问题不是方向性问题，而是代码与文档同步时必然会遇到的实现陷阱。

## 2. 维度评分

- 一致性：3.5 / 5
- 真相源：4 / 5
- 披露：4 / 5
- 触发与契约：3.5 / 5
- 失败兜底：3.5 / 5

总分：17.5 / 25

## 3. 条件项

### P0-1：字段命名不一致

问题：设计中 common profile 使用 `expected_components`，而现有 common.json / render.py / test_render.py 使用的是 `required_components`。

要求：进入 S4 前必须明确字段命名决策。建议采用零迁移方案：common 与 skill profile 都统一沿用 `required_components`。

### P0-2：profile version 迁移未披露

问题：现有 A-1 / A-5 / A-7 / common profile 的 version 是 0.9.0，而 v0.9.1 方案示例要求 0.9.1。

要求：S4 第一步统一将 4 个既有 profile version 升级为 0.9.1，并写入实施顺序。

### P1-3：default_profile fallback 与 fail-fast 冲突

问题：自动检测失败后 fallback 到 default_profile + warning，仍可能导致未知报告被错误套用 A-1。

要求：未知 profile 必须 fail-fast，不允许自动套用 default_profile。default_profile 只用于 registry 元数据或人工提示。

### P1-4：strict 策略存在双路径

问题：方案同时提出 CLI `--strict` 与 render.py 默认 strict，可能造成实现分叉。

要求：v0.9.1 采用 renderer 默认 strict，不新增 CLI flag；render_report.sh 继续只负责透传 profile。

### P2-5：负向测试与 fail-fast 分类不对齐

问题：fail-fast 有 7 类，但负向测试只列 5 类。

要求：负向测试补齐到 7 类，并明确每类对应 fixture / case 名称。

## 4. 最重要建议

进入 S4 前，必须在 DESIGN-v0.9.1 中新增“字段命名与版本迁移决策”或“S4 落地前置条件”章节，明确：

1. common 与 skill profile 统一使用 `required_components`
2. 4 个既有 profile version 在 S4 第一步升级到 0.9.1
3. 未知 profile 不允许 fallback
4. renderer 默认 strict，不新增 CLI flag
5. 负向测试覆盖全部 fail-fast 条件

## 5. Orchestrator 处理结论

评审结论为 CONDITIONAL_PASS。上述条件修订进 DESIGN-v0.9.1 后，可视为设计门控通过，进入 S4 小步开发。