# REQ-v0.9.1 - bd-eval-cms 质量固化版需求草案

- 日期：2026-06-13
- 阶段：AF-SOP S2 需求固化草案
- 状态：DRAFT，待 Evan 确认
- 上一版本：v0.9.0
- 目标版本：v0.9.1

## 1. 背景

bd-eval-cms v0.9.0 已发布，完成了 Style A1 通用模板内核与 A-1 / A-5 / A-7 三个代表 profile。

v0.9 证明了 profile-driven 的技术路线可行，但仍存在四类生产化风险：

1. profile 体系尚未 schema 化
2. 上游 Markdown 输入契约不稳定
3. renderer 失败策略不明确
4. 测试体系仍偏组件覆盖，缺少真实案例验收入口

因此 v0.9.1 不应急于扩展 20 个 profile，而应先做质量固化。

## 2. 用户画像

主要用户：Evan / CMS BD 投前评估流程负责人 / 后续自动化报告生产链路维护者。

使用场景：

- 持续迭代 bd-eval-cms Skill
- 自动生成 CMS BD 投前评估报告
- 在多个技能 profile 间保持统一质量标准
- 为后续年产上千份报告建立工程底座

## 3. 核心目标

v0.9.1 的目标是：

**把 v0.9 的可验证模板内核固化为可持续演进的工程底座。**

具体包括：

1. 建立 profile schema
2. 建立 profile registry
3. 明确上游 Markdown 输出契约
4. 明确 renderer fail-fast / fail-soft 策略
5. 增加真实案例验收入口
6. 明确工作区清理与发布边界治理

## 4. 功能需求

### 4.1 Profile schema

需要定义 profile 的最小结构，例如：

- profile id
- 适用技能
- 业务场景
- 必选模块
- 可选模块
- 必选组件
- Gate 结构要求
- 引用 / 证据链要求
- fail policy

目标：任何新增 profile 都必须能被 schema 检查。

### 4.2 Profile registry

需要建立一个统一索引，管理已有和未来 profile。

至少包含：

- A-1
- A-5
- A-7
- 其余 CMS BD 技能的占位映射或待定义状态

目标：避免 profile 分散在文件中，后续不知道哪些技能已覆盖、哪些未覆盖。

### 4.3 Markdown 输出契约

需要定义上游报告 Markdown 应该输出什么结构。

至少约束：

- One-pager
- Gate 结论
- conclusion-box
- risk-box
- exclusion-box（适用时）
- confidence-badge
- references
- 信息不足时的显式表达

目标：把“报告生成端”和“HTML 渲染端”的接口固定下来。

### 4.4 Renderer 失败策略

需要明确什么时候失败、什么时候降级。

建议：

- 缺 profile：fail-fast
- profile schema 不合法：fail-fast
- 必选组件缺失：fail-fast
- 模板变量残留：fail-fast
- 可选组件缺失：warning
- 非关键展示字段缺失：fail-soft，但输出 warning

目标：避免生成“看起来完成但结构残缺”的报告。

### 4.5 真实案例验收入口

需要增加一个面向真实案例的验收入口。

要求：

- 不修历史脏数据
- 选择 1 个新案例或已相对干净案例作为 golden smoke case
- 能一键运行 style-a1 profile 渲染
- 输出 HTML 与校验报告

目标：在 fixture 之外验证真实报告链路。

### 4.6 工作区治理

需要明确哪些历史改动属于下一版本，哪些必须隔离。

重点处理：

- `dependencies/doc-viewer` 删除是否另开版本处理
- 老脚本改动是否保留 / 废弃 / 迁移
- 历史案例目录不进入发布
- memory 文件不进入发布
- 每次发布继续使用白名单 staging

目标：降低误提交风险。

## 5. 非目标 / 不做什么

v0.9.1 不做：

1. 不覆盖全部 20 个 CMS BD profile
2. 不实现完整 Gate 规则引擎
3. 不实现财务阈值自动判定
4. 不做全量证据链审计系统
5. 不做 PDF / PPT 出版级能力
6. 不修复所有历史案例数据
7. 不重构整个 bd-eval-cms Skill
8. 不修改 style-12 / style-13 既有行为

## 6. 验收标准

v0.9.1 只有满足以下条件才可发布：

1. profile schema 文件存在，并可被测试读取
2. profile registry 文件存在，至少覆盖 A-1 / A-5 / A-7
3. A-1 / A-5 / A-7 三个 profile 继续通过 100% 组件覆盖测试
4. 缺 profile 时测试必须失败
5. 缺必选组件时测试必须失败
6. 模板变量残留时测试必须失败
7. 至少 1 个真实案例验收入口可运行
8. style-12 / style-13 不回归
9. 版本号三处一致：SKILL.md / VERSION / version.json
10. 发布前 git staging 范围经过白名单确认

## 7. 风险

### 7.1 过度设计风险

如果 v0.9.1 试图一次性抽象完整规则引擎，会拖慢交付，并偏离“质量固化”的目标。

控制方式：只做 schema / registry / contract / fail policy，不做完整业务规则执行器。

### 7.2 历史脏工作区误入版本

当前本地工作区仍有大量历史未提交改动。

控制方式：继续白名单 staging；必要时为工作区清理单独建任务，不混入 v0.9.1。

### 7.3 上游输出契约落不到执行端

如果只写 contract，不修改测试与 renderer，那么契约不会生效。

控制方式：contract 必须绑定测试用例和 renderer 校验逻辑。

## 8. 建议执行方法

按 Agent Factory AF-SOP 执行：

1. S2：确认本 REQ-v0.9.1
2. S3：生成 DESIGN-v0.9.1
3. S3 Review：Reviewer 独立评审设计方案
4. S4：小步开发
5. S5：Validator + Reviewer 双门控
6. S6：发布 v0.9.1
7. S7：交付确认
8. S8：归档沉淀

## 9. 下一步

如 Evan 确认本需求草案，则进入 S3：

产出 `design/DESIGN-v0.9.1.md`，重点设计：

- profile schema 文件结构
- registry 文件结构
- Markdown contract 规则
- renderer 校验策略
- 测试矩阵
- 发布白名单
