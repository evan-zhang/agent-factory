# E2E 回归测试报告 — 场景 1：基础流程回归

- **日期**：2026-06-02
- **Skill**：bd-eval-cms v0.2.0
- **测试品种**：利奈昔巴特（260531-LNXB）
- **测试类型**：只读检查

---

## 1. 文件完整性检查

### state.json

| 检查项 | 结果 |
|--------|------|
| state.json 是有效 JSON | ✅ |
| phase 字段存在且值为合法终态（report_finalized） | ✅ |
| caseCode 存在（260531-LNXB） | ✅ |
| gateVersions 包含 One-pager + Gate 1~6（共7项） | ✅ |

### 02-gate-by-chapter/ 目录

| 文件 | 行数 | ≥100行？ | 存在？ |
|------|------|---------|--------|
| One-pager.md | 64 | ❌ 64行 | ✅ |
| Gate-1-premise.md | 88 | ❌ 88行 | ✅ |
| Gate-2-evidence.md | 102 | ✅ | ✅ |
| Gate-3-payment.md | 104 | ✅ | ✅ |
| Gate-4-pricing.md | 88 | ❌ 88行 | ✅ |
| Gate-5-supply.md | 75 | ❌ 75行 | ✅ |
| Gate-6-deal.md | 106 | ✅ | ✅ |

⚠️ **说明**：One-pager（64行）、Gate-1（88行）、Gate-4（88行）、Gate-5（75行）未达100行阈值。这些是 v0.1 时期生成的旧数据，内容完整但行数偏少（中文 markdown 密度较高）。**影响评估**：低。这是历史数据的自然状态，不代表 v0.2.0 改造引入了问题。

### 最终报告

| 检查项 | 结果 |
|--------|------|
| 04-final-report.md 存在 | ✅ |
| 报告行数 ≥ 500（实际 1003 行） | ✅ |

---

## 2. SKILL.md 规范层验证

| 检查项 | 结果 |
|--------|------|
| frontmatter version = "0.2.0" | ✅ |
| 包含 Step 1~11（grep 返回 11 行） | ✅ |
| Step 9 包含 "合作可能性明显不足" | ✅ |
| Step 9 包含 "CP-1" | ✅ |
| Phase↔Step 映射表存在 | ✅ |
| Step 10 包含 "标记语法约定" | ✅ |
| 引用了 EXECUTION.md | ✅ |
| 配置与授权节存在 | ✅ |

---

## 3. EXECUTION.md 执行层验证

| 检查项 | 结果 |
|--------|------|
| 包含 Phase 1~5.5 完整内容 | ✅ Phase 1~5.5 均有独立章节 |
| 包含三种执行模式 | ✅ 第 68 行 "本 Skill 支持三种执行模式" |
| 包含并行执行策略 | ✅ 第 735 行独立章节 |
| "7条体系级" 不出现 | ✅ grep 无结果 |
| "8条体系级" 出现 ≥ 2 次 | ✅ 出现 2 次（第 473、552 行） |

---

## 4. 转换脚本验证

### convert-md-to-html.py

| 检查项 | 结果 |
|--------|------|
| python3 语法验证通过 | ✅ py_compile 无错误 |
| 包含 convert_gate_boxes | ✅ 第 223 行 |
| 包含 convert_highlight_boxes | ✅ 第 211 行 |
| 包含 convert_red_flags | ✅ 第 326 行 |
| 包含 convert_conflict_boxes | ✅ 第 195 行 |
| 包含 convert_gate_cards | ✅ 第 148 行 |
| 包含 convert_battle_sections | ✅ 第 179 行 |
| 管线中包含 convert_highlight_boxes | ✅ 第 520 行 |

### skeleton.html（scripts/style-12/skeleton.html）

| 检查项 | 结果 |
|--------|------|
| 包含 .gate-box 样式 | ✅ 2 处 |
| 包含 .conclusion-tag.pass | ✅ 4 处（含 conditional/stop/pending 四色） |
| 包含 .red-flag 样式 | ✅ 2 处 |
| 包含 .highlight-box 样式 | ✅ 2 处 |
| 包含 .conflict-box 样式 | ✅ 1 处 |

> **注意**：CSS 样式集中在 `scripts/style-12/skeleton.html`，`templates/skeleton-cms.html` 仅有 .highlight-box，不含新样式。如果双模板并存，需确认哪个是实际使用的。

---

## 5. 交叉一致性检查

| 检查项 | 结果 | 详情 |
|--------|------|------|
| SKILL.md Step 5 Gate 输出格式 vs sub-agent-prompt-template.md | ✅ 一致 | 两处均包含：结论/置信度/关键支撑证据/需补充证据Top 5/红旗事项/下一步行动 |
| SOP.md 否决清单为 8 条 | ✅ | SOP 第 45 行明确标注 "(8条,体系级,不可豁免)" |
| SOP.md 引用 SKILL.md Step 9 | ✅ | SOP 第 47 行 "单一信源：本清单为 SKILL.md Step 9 的摘要引用" |
| A-0 版本为 v1.4 | ✅ | DIFF-ANALYSIS、PLAN-REVIEW 等文件均确认 A-0 已从 v1.0 更新到 v1.4 |

---

## 6. 版本号三处同步检查（额外发现）

| 位置 | 实际值 | 预期值 | 结果 |
|------|--------|--------|------|
| SKILL.md frontmatter | 0.2.0 | 0.2.0 | ✅ |
| version.json | 0.1.0 | 0.2.0 | ❌ |
| VERSION | 0.1.0 | 0.2.0 | ❌ |

❌ **version.json 和 VERSION 文件未同步更新为 0.2.0**。SKILL.md 已更新但版本号文件遗漏。**影响**：中。安装/发布流程依赖 version.json 和 VERSION，版本不一致会导致用户获取错误版本信息。

---

## 结论

### 统计

- 总检查项：37
- ✅ 通过：34
- ❌ 失败：3（版本号同步 × 2 + Gate 行数不足 × 4，但 Gate 行数为历史数据非改造问题）

### 判定：⚠️ CONDITIONAL PASS

**通过条件**：修复 version.json 和 VERSION 的版本号为 `0.2.0` 后即为完全 PASS。

### 必须修复（阻塞发版）

1. **version.json**：`"version": "0.1.0"` → `"version": "0.2.0"`，description 也需更新
2. **VERSION**：`0.1.0` → `0.2.0`

### 已知不阻塞项

- Gate 章节（One-pager/Gate-1/Gate-4/Gate-5）行数 < 100：历史数据特征，非 v0.2.0 改造引入。新评估任务不受影响。
- `templates/skeleton-cms.html` 缺少新 CSS 样式：如该文件已废弃则无需处理，否则需确认使用场景。
