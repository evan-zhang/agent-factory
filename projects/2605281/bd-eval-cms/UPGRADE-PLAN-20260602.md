# bd-eval-cms Skill 改造计划 v2
**日期**：2026-06-02
**版本**：v2（修订版，基于 Claude Code 审核反馈）
**目标**：将现有 bd-eval-cms Skill 从旧版规范对齐到新版（5月30日-6月1日技能包），同时保留旧版的执行能力

---

## 修订记录

| v1 → v2 变更 | 来源 |
|-------------|------|
| 节点 3 从"新增"改为"验证已就位"，标记已完成 | Claude Code 审核发现 A-5 已存在且一致 |
| 节点 1 明确为拆分方案（SKILL.md + EXECUTION.md） | Claude Code 审核建议，避免 1800 行单文件 |
| 节点 1 增加 Phase↔Step 映射表设计 | Claude Code 审核建议 |
| 节点 4 扩展为包含 Markdown 标记语法 + 转换逻辑 | Claude Code 审核发现 convert-md-to-html.py 需改造 |
| 节点 7 增加专项测试场景 + git tag 回退策略 | Claude Code 审核建议 |
| 否决清单遵循单一信源原则 | Claude Code 审核建议 |
| 工作量从 4~6h 修正为 7~9h | Claude Code 审核评估 |

## 改造原则

1. **新版是规范层，旧版是执行层，两者整合而非替代**
2. **19个技能文件（A-1~E-1）全部无需修改**
3. **SKILL.md 拆分为双文件架构**（规范层 + 执行层），降低 Agent 上下文压力
4. **否决清单单一信源**：只在 SKILL.md Step 9 定义，SOP 和模板引用而非内联
5. **每个节点完成后必须通过验证才能进入下一步**

---

## 前置动作：创建回退点

**操作**：在项目目录创建 git tag
```bash
cd projects/2605281/bd-eval-cms
git tag pre-upgrade-v0.1.0
```

**验证**：
- [ ] git tag pre-upgrade-v0.1.0 存在

---

## 节点清单

### 节点 1：SKILL.md 拆分重写（规范层 + 执行层）

**目标**：将现有 SKILL.md 拆分为两个文件

**架构决策**：**双文件方案**（已确定，不再"考虑"）

| 文件 | 定位 | 预计行数 | 内容来源 |
|------|------|---------|---------|
| SKILL.md | 规范层 | ~600 行 | 新版 Step 1~11 + Phase↔Step 映射表 + 版本信息 |
| EXECUTION.md | 执行层 | ~800 行 | 旧版 Phase 1~5.5 流水线全部内容 |

**SKILL.md（规范层）写入内容**：
- frontmatter：version 升至 "0.2.0"，description 反映"规范层 + 执行层"双层架构
- Step 1：调用 writing 技能（BLOCKING）
- Step 2：产品类型路由决策树（D-0 逻辑）
- Step 3：六大业务主体组合约束规则（互斥约束、红旗框规范、合法组合穷举表）
- Step 4：三阶段 BD 评估流程（含 NDA 弹性节点）
- Step 5：6-Gate 门控路径 + Gate 通用输出格式（6 个必填字段：结论/置信度/支撑证据Top3/需补证据Top5/红旗/下一步）
- Step 6：三类产品财务硬门槛（创新药/仿制药/医美/消费健康）
- Step 7：群组差异化评估维度（A/B/C/D/E 群差异）
- Step 8：M-01~M-10（含 M-09 前置拦截：CP-1/CP-2/CP-3 + 轻触探意愿）
- Step 9：一票否决清单 8 条（含 CP-1/CP-2/CP-3 + 轻触探意愿 + Watch）— **单一信源**
- Step 10：麦肯锡风格 HTML 报告规范（含 Markdown 标记语法约定，供节点 4 使用）
  - 定义 gate-box 标记语法（如 `> **[GATE:N 结论]**`）
  - 定义 conclusion-tag 标记语法（如 `✅通过` / `⚠条件通过` / `❌停止` / `⏳待验证`）
  - 定义 red-flag 标记语法（如 `> 🚩 **红旗**`）
- Step 11：技能串接规则
- Phase↔Step 双向映射表：
  | Phase | 对应 Step | 说明 |
  |-------|----------|------|
  | Phase 1 DISCOVERY | Step 1 + Step 8 | 宽度搜索 + M-01~M-10 |
  | Phase 2 路由 | Step 2 + Step 7 + Step 8 M-09 | 路由决策 + 群组差异 + CP 拦截 |
  | Phase 3 Gate 评估 | Step 3~6 | 互斥约束 + 三阶段BD + Gate门控 + 财务门槛 |
  | Phase 4 Battle | Step 9 | 一票否决审查（含第 8 条）|
  | Phase 5 合并 | Step 10 | 报告规范 |
  | Phase 5.5 HTML | Step 10 | HTML 输出 |
- 引用声明：`EXECUTION.md` 为执行层详细操作手册

**EXECUTION.md（执行层）写入内容**：
- 从现有 SKILL.md 中提取 Phase 1~5.5 全部执行内容
- Phase 1 DISCOVERY 宽度搜索 SOP
- Phase 2 技能确认 Battle
- Phase 3 子Agent并行策略
- Phase 4 Gate Battle 对抗审查
- Phase 5 报告合并 + 10 项质量终检
- Phase 5.5 HTML 生成 + 知识库同步
- state.json 版本管理 + 断点续跑
- 模型 fallback chain
- 案件代号（YYMMDD-XXXX）
- 执行日志规范

**验证标准**：
- [ ] SKILL.md 包含完整 Step 1~11 内容
- [ ] SKILL.md 行数 ≤ 700 行
- [ ] frontmatter version 为 "0.2.0"
- [ ] description 反映双层架构
- [ ] Step 3 包含六大业务主体组合约束规则 + 合法组合穷举表
- [ ] Step 5 包含 Gate 通用输出格式（6 个必填字段）
- [ ] Step 9 包含 8 条否决（含 CP-1/CP-2/CP-3 + 轻触探意愿 + Watch）
- [ ] Step 10 包含 HTML 报告规范 + Markdown 标记语法约定（gate-box / conclusion-tag / red-flag）
- [ ] Phase↔Step 双向映射表存在且完整（6 行映射关系）
- [ ] EXECUTION.md 存在且包含完整 Phase 1~5.5 执行内容
- [ ] EXECUTION.md 行数 ≤ 900 行
- [ ] 两文件无内容重复（DRY 原则）

---

### 节点 2：A-0 更新（v1.0 → v1.4）

**目标**：将 references/A-0_bd-opportunity-intelligence.md 更新到 v1.4

**具体操作**：
- 直接用 /tmp/skill-update/A-0_bd-opportunity-intelligence.md 替换现有文件

**验证标准**：
- [ ] 文件版本号为 v1.4
- [ ] 否决快扫数量为 7 项（含 V-7 合作可能性否决）
- [ ] 分级体系为 A/B/C/Watch 四级
- [ ] 分拨去向包含 Watch 清单选项
- [ ] 包含合作可行性评分模块
- [ ] 与 /tmp/skill-update/A-0_bd-opportunity-intelligence.md 内容完全一致

---

### 节点 3：验证 A-5 已就位 ✅ 已完成

**状态**：已完成，0 工作量

**事实核查结果**（Claude Code 审核确认）：
- references/A-5_bd-cn-marketed-product-rights.md 已存在（2026-05-28 创建）
- 与新版 /tmp/skill-update/A-5_bd-cn-marketed-product-rights.md 内容完全一致（diff 无输出）
- D-0 路由器第 97 行已包含 A-5 路由路径
- D-0 路由器第 103~109 行已包含 A-2 vs A-5 边界判断逻辑

**验证**（已通过）：
- [x] A-5 文件与新版一致
- [x] D-0 路由器包含 A-5 路由

---

### 节点 4：报告模板与转换链改造

**目标**：补齐缺失的 HTML 样式 + Markdown 标记语法转换逻辑

**现状盘点**（已核实）：

| 样式 | skeleton.html | convert-md-to-html.py | 状态 |
|------|--------------|----------------------|------|
| gate-box | ❌ 缺失 | ❌ 缺失 | 需新增 |
| conclusion-tag | ❌ 缺失 | ❌ 缺失 | 需新增 |
| red-flag | ❌ 缺失 | ❌ 缺失 | 需新增 |
| conflict-box | ✅ 已有 | ✅ 已有（第199行） | 无需修改 |
| highlight-box | ✅ 已有（2处） | ❌ 未检查 | 需确认 |

**具体操作**：
1. **skeleton.html 补充 CSS**：
   - 新增 gate-box 样式（蓝色边框 #1a3a5c，圆角，浅蓝背景 #f8fafc）
   - 新增 conclusion-tag 四色标签（.pass 绿 #d4edda / .conditional 黄 #fff3cd / .stop 红 #f8d7da / .pending 灰 #e2e8f0）
   - 新增 red-flag 样式（浅红背景 #fff5f5，红色左边框 #c53030）
   - 规范来源：TRTL-729 HTML 报告中的 CSS 定义

2. **convert-md-to-html.py 新增转换逻辑**：
   - gate-box：识别 Markdown 标记（在节点 1 Step 10 中定义），转为 `<div class="gate-box">...</div>`
   - conclusion-tag：识别标记（如 `✅通过`），转为 `<span class="conclusion-tag pass">通过</span>`
   - red-flag：识别标记（如 `> 🚩 **红旗**`），转为 `<div class="red-flag">...</div>`
   - 具体标记语法以节点 1 Step 10 定义为准

3. **单元测试**：
   - 用 TRTL-729 报告的 Markdown 源码做回归测试，确保转换输出与原 HTML 一致

**验证标准**：
- [ ] skeleton.html 包含 gate-box、conclusion-tag（4色）、red-flag 三个 CSS 类定义
- [ ] convert-md-to-html.py 包含 gate-box、conclusion-tag、red-flag 三个转换规则
- [ ] 转换脚本能将 Markdown 标记正确渲染为 HTML 样式
- [ ] 用 TRTL-729 的 Markdown 源码做回归测试，输出与原 HTML 样式一致

**依赖**：依赖节点 1 中 Step 10 的 Markdown 标记语法定义

---

### 节点 5：SOP 对齐

**目标**：确保 SOP.md 与新版 SKILL.md 的规范层保持一致

**具体操作**：
- SOP 中一票否决清单更新为 8 条（当前 7 条，需增加第 8 条 CP-1/CP-2/CP-3）— **引用 SKILL.md Step 9，不内联**
- Phase 1 技能列表从 19 个更新为 20 个（含 A-5）
- 版本号更新
- 检查 Phase 2 路由流程是否包含 M-09 前置拦截逻辑
- 检查报告合并流程是否包含互斥约束框检查

**验证标准**：
- [ ] SOP 中一票否决引用 SKILL.md Step 9 的 8 条（不内联重复）
- [ ] 技能列表为 20 个（含 A-5）
- [ ] Phase 2 路由包含 M-09 前置拦截判断
- [ ] Phase 流程名与 SKILL.md 的 Phase↔Step 映射表一致
- [ ] 版本号已更新

---

### 节点 6：sub-agent-prompt-template 更新

**目标**：确认子 Agent prompt 模板与新版规范一致

**具体操作**：
- 确认 Gate 输出格式 6 个必填字段（已确认存在）
- 确认否决清单的引用方式（引用 SKILL.md Step 9，不内联）
- 如需调整，更新引用方式

**验证标准**：
- [ ] Gate 输出格式包含 6 个必填字段（已确认 ✅）
- [ ] 模板引用 SKILL.md/SOP 中的否决清单（而非内联重复）
- [ ] 模板与新版 SKILL.md Step 5 定义一致

---

### 节点 7：端到端验证

**目标**：用测试案例验证改造后的 Skill 能正常工作

**测试场景**：

**场景 1：基础流程验证（回归测试）**
- 用"利奈昔巴特"案例走一遍完整流程
- 验证旧版执行能力未回归：Phase 流水线、Battle、HTML 生成、state.json

**场景 2：新增规范验证（专项测试）**
- 构造一个能命中 CP-1（大型 MNC 核心管线）的测试输入
- 验证 Step 9 第 8 条否决逻辑是否生效
- 验证 Watch 分级是否正确触发

**验证标准**：
- [ ] 场景 1：完整流程正常运行，所有 Phase 正常通过
- [ ] 场景 1：Gate 输出包含 6 个必填字段
- [ ] 场景 1：报告 HTML 包含 gate-box / conclusion-tag / highlight-box / red-flag 样式
- [ ] 场景 1：Battle 机制正常运行
- [ ] 场景 1：state.json 状态管理正常
- [ ] 场景 1：报告合并脚本正常运行
- [ ] 场景 1：HTML 生成脚本正常运行
- [ ] 场景 2：CP-1 否决逻辑正确触发
- [ ] 场景 2：Watch 分级正确输出
- [ ] git tag pre-upgrade-v0.1.0 存在，可回退

---

## 执行顺序与依赖

```
前置：创建 git tag pre-upgrade-v0.1.0

节点 1（SKILL.md 拆分）──┐
节点 2（A-0 更新）───────┤ 可并行
节点 3（A-5 验证）✅已完成┘
         ↓
节点 4（报告模板 + 转换链）← 依赖节点 1 Step 10 的标记语法定义
         ↓
节点 5（SOP 对齐）← 依赖节点 1
         ↓
节点 6（prompt 模板）← 依赖节点 1
         ↓
节点 7（端到端验证）← 依赖所有前置节点
```

---

## 工作量估计

| 节点 | 预计时间 | 说明 |
|------|---------|------|
| 前置（git tag） | 5min | |
| 节点 1 | 3~4h | 拆分 + 映射表 + frontmatter + 标记语法设计 |
| 节点 2 | 0.5h | 直接替换 |
| 节点 3 | 0h ✅ | 已完成 |
| 节点 4 | 1.5~2h | CSS + 转换逻辑 + 回归测试 |
| 节点 5 | 0.5h | 引用更新 + 版本号 |
| 节点 6 | 0.5h | 确认引用方式 |
| 节点 7 | 1.5h | 两个场景 |
| **合计** | **7~9h** | |

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 拆分后 Agent 找不到 EXECUTION.md | 低 | 高 | SKILL.md 中明确引用 EXECUTION.md 路径 |
| Markdown 标记语法与 Agent 输出习惯不匹配 | 中 | 中 | 用 TRTL-729 源码验证，必要时调整标记 |
| 否决清单在三处维护不同步 | 高 | 中 | 单一信源：Step 9 定义，其余引用 |
| convert-md-to-html.py 转换逻辑未覆盖所有变体 | 中 | 中 | 节点 4 增加单元测试 |
| 新版 Step 10 与旧版 Phase 5.5 HTML 生成冲突 | 中 | 高 | 以 TRTL-729 样例为准，旧版脚本适配 |

---

*计划修订时间：2026-06-02 15:10 GMT+8*
*预计总工作量：7~9 小时*
