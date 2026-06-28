# Reviewer Brief: 规划书 v1.5 vs BOAG v0.1.8 差异分析报告

## 评审问题
**集团BP生成要求规划书 v1.5 已发布，对 BOAG skill v0.1.8 做完整差异分析，列出需更新内容。**

## 评审上下文
- BOAG skill v0.1.8 已发布（commit d757de4）
- 集团BP生成要求规划书 v1.5 是 BOAG 的业务规则源文件
- v1.5 包含 20 章 + 47 条 R 规则 + 5 个决策图
- 本次评审要分析：哪些规则在 v0.1.8 已覆盖？哪些缺失？哪些需要新版本？

## 必读文件
1. `projects/2606131/_source/集团BP生成要求规划书_v1.5_20260614.md`（源文件 110KB）
2. `projects/2606131/bp-object-audit-generate/SKILL.md`
3. `projects/2606131/bp-object-audit-generate/agents/agent.yaml`
4. `projects/2606131/bp-object-audit-generate/references/core_rules.md`（§ 1-10）
5. `projects/2606131/bp-object-audit-generate/references/dimension_audit_checklist.md`（261 行）
6. `projects/2606131/bp-object-audit-generate/references/interactive_state_machine.md`（11 状态）
7. `projects/2606131/bp-object-audit-generate/references/object_templates.md`（5 模板）
8. `projects/2606131/bp-object-audit-generate/references/output_package.md`
9. `projects/2606131/bp-object-audit-generate/references/source_manifest.md`

## 评审维度

### 维度 1：47 条 R 规则逐条覆盖度检查
- 状态分类：✅ 已覆盖 / ⚠️ 部分覆盖 / ❌ 未覆盖 / — 不适用
- 对每条 ⚠️ / ❌ 状态：判断"该规则是否真的应在 BOAG v0.1.9/v0.2 中落地"或"该规则属于其他范畴（BP 生成、月报、文档族管理）"

### 维度 2：v1.5 新结构元素是否落地
- 承接方式 5 类（完整BP承接/任务轻量跟踪/成果责任派发/协同留痕/不下拆）— v0.1.8 维度 5
- 横向协作关系卡（v1.5 § 7.4.2 增强规则）— v0.1.8 是否需要？
- 单目标完整复盘版（v1.5 § 4.4.1）— v0.1.8 是否需要？
- 集团-中心边界前置预判 4 步法（v1.5 § 5.1.1）— v0.1.8 是否需要？
- 过程型表达 9 动词清单（v1.5 § 9）— v0.1.8 维度 2 是否补充？
- 8 类成果输出对象清单（v1.5 § 三）— v0.1.8 维度 4 是否补充？
- 外来概念本地化（v1.5 § 9.1）— v0.1.8 是否需要？
- 经营责任中心 vs 经营管理中心区分（v1.5 § 7.4）— v0.1.8 维度 6 是否补充？
- 8 类未定项（v1.5 § 11）— v0.1.8 维度 7 是否补充？

### 维度 3：triggers 与 v1.5 业务范围对齐
当前 9 个 triggers（BP 审计 / BP 对象 / 生成 BP / BP 归档 / 康哲 BP / 承接关系 / BP 主责 / 部门 BP / 个人 BP）
- v1.5 新增概念：成果责任派发 / 协同留痕 / 任务轻量跟踪 / 不下拆 / 集团-中心边界 / 单目标复盘 / 完整复盘版 / 占位词反写 / 经营责任中心 / 经营管理中心 / 过程型表达 / 集团事项准入 — 是否需要补 triggers？

### 维度 4：v1.5 决策图与 v0.1.8 文档关系
- v1.5 决策图：承接方式决策图 / 专业责任中心推荐结构 / 经营责任中心推荐结构
- v0.1.8 文档：core_rules § 10（7 维度）/ object_templates § 7（闭合检查表）/ state_machine § 5（7 维度映射）
- v1.5 决策图是否应在 v0.1.8 中引用或独立存档？

### 维度 5：v1.5 附录的价值
- 附录 A 15 个常见结构问题（Q1-Q15）— v0.1.8 维度定义应引用？
- 附录 B 字段模板与冻结优先级 — v0.1.8 object_templates 已包含？需对齐？
- 附录 C 19 项争议直接判断表 — 是否纳入 checklist？
- 附录 D 6 个决策图 — 同维度 4

## 输出

### 输出 1：差异分析报告
- 路径：`projects/2606131/reviews/2026-06-14-H-PLANNING-V15-DIFF.md`
- 包含：47 条 R 规则覆盖度表 + v1.5 新结构元素对齐表 + triggers 补充建议 + 文档关系图
- 不限于规则表，必须给出 v1.5 中"对 BOAG 而言有增量价值但未落地"的具体条款

### 输出 2：v0.1.9 / v0.2 路线建议
- 路径：报告末尾
- 区分：
  - **P0 patch（v0.1.9 即可）**：维度内增补，无需新文件
  - **P1 新模块（v0.2）**：新增 reference 文件
  - **P2 后续版本（v0.3+）**：需要新架构

### 输出 3：每项 P0 的具体改动方案
- 文件路径
- 改动章节
- 预计增加行数
- 评审点（如有）

## 工作目录
/Users/evan/.openclaw/gateways/life/domains/agent-factory

## 红线
- 独立评审，不被引导
- 47 条 R 规则必须逐条核对，不许合并
- 区分"BOAG 审计范围"vs"BP 生成范围"vs"文档族管理范围"
- 路线建议必须可执行
