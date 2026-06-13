# AF-REVIEW-SOP 独立评审标准流程

- 版本：v1.2
- 状态：STABLE
- 适用范围：工厂所有需求方案、设计方案、代码、上线验收的独立评审
- 关联文档：AF-SOP_Skill生产全流程规范（v5.2）、specs/agents/reviewer.md、specs/agents/validator.md

---

## 0. 为什么需要这份 SOP

工厂已有 `reviewer.md` 和 `validator.md` 两个角色定义，但缺一套统一的「什么时候评、评什么、谁来评、产出什么、评完怎么办」的标准路径。本 SOP 解决这个缺口。

核心原则：评审是质量门控，不是走过场。Reviewer 给结论，Orchestrator 据此决策，不绕过、不妥协。

---

## 1. Reviewer 与 Validator 的边界（最关键）

两者职责必须分清，否则会互相做对方的事。

| 维度 | Validator（门下省 / 合规门控） | Reviewer（独立外部评审） |
|---|---|---|
| 关注点 | 必填项、格式、合规、规范符合度 | 设计质量、风险、合理性、外部视角 |
| 判断标准 | 客观清单，有没有 | 主观判断，好不好 |
| 输出 | PASS / FAIL + 缺失项清单 | PASS / CONDITIONAL_PASS / FAIL + 维度评分 |
| 触发频率 | 每步完成后强制 | 关键节点 / 高风险产出 / 用户要求时 |
| 立场 | 检查"是否达标" | 评判"是否优秀、是否有隐患" |

一句话区分：Validator 查「缺不缺」，Reviewer 评「好不好、有没有坑」。

---

## 2. 四类评审对象

不同对象评审维度不同，混在一起会失效。

| 评审对象 | 主评角色 | 是否需要 Validator 配合 | 产出 |
|---|---|---|---|
| A. 需求方案 / 业务设计（REQ-01） | Reviewer | 否 | 评级 + 关键风险 |
| B. Agent / Skill 规范文档（DESIGN-01、SKILL.md） | Validator 先行 + Reviewer 后评 | 是 | 合规清单 + 设计评级 |
| C. 代码改动（CODE-01） | Reviewer（代码视角） | 是 | diff review + 评级 |
| D. 上线前最终验收 | Reviewer + Validator 联合 | 是 | 综合评级 |

---

## 3. 触发条件（什么时候必须走 Reviewer）

强制触发：
- L1 Step 2（GRV 治理评审）、Step 7（最终验收）
- L2 的 S3 方案设计完成后（B 类）、S5 质量验证（C 类）、S7 交付确认（D 类）
- 任何涉及外部 API 对接的设计方案（高风险）。外部 API 指工厂外部的第三方服务（如 longbridge、玄关开放平台等），不含 OpenClaw 内建工具调用
- 任何破坏性变更 / 安全相关改动

建议触发：
- 用户在设计上反复犹豫，需要外部客观意见
- 方案涉及成熟方法论领域，需独立视角校验

用户可主动要求：
- 任何时候说「评审一下」「找茬」「独立看看」

---

## 4. 评审维度（按对象分）

### A 类：需求方案 / 业务设计
1. 需求完整性（用户画像、场景、边界是否清晰）
2. 可行性（技术 / 资源 / 时间是否现实）
3. 价值合理性（是否值得做，有没有更轻的替代）
4. 风险识别（最大的 2-3 个隐患）
5. 边界明确性（"不做什么"是否写清楚）

### B 类：Agent / Skill 规范文档
1. 设计与需求的一致性（DESIGN 是否回应了 REQ）
2. 唯一真相源（外部 API 是否引用官方文档）
3. 三层披露合理性（Token 经济学，SKILL.md 80-200 行按复杂度浮动）
4. 触发词设计（3-5 个，覆盖口语化）
5. 失败兜底与错误处理

### C 类：代码改动
1. 正确性（逻辑是否实现了设计意图）
2. 安全性（凭证泄露、注入、权限）
3. 健壮性（错误处理、边界输入）
4. 可维护性（结构、命名、是否过度设计）
5. 测试覆盖（关键路径有没有测）

### D 类：上线前最终验收
1. 功能符合需求（对照 REQ-01 逐项）
2. 质量门控全过（Validator 清单清零）
3. 文档完整（SKILL.md、design/ 档案齐全）
4. 版本号三处同步（VERSION、frontmatter、version.json）
5. 安装与使用说明可用

每个维度按 1-5 分评分，关键问题不超过 5 个。

---

## 5. 产出格式（统一）

Reviewer 必须输出：

总体评级：PASS / CONDITIONAL_PASS / FAIL

关键问题（3-5 个，每个含：严重度 高/中/低 + 一句话描述 + 修复建议）

维度评分表（本次评审对象对应的 5 个维度，各 1-5 分）

一条最重要的建议

CONDITIONAL_PASS 的含义：方向对，但有必须修复的问题，修完不用重评即可放行。FAIL 必须回到对应阶段重做后重评。

---

## 6. 评审执行流程

1. Orchestrator 判断评审对象类型（A/B/C/D），确定主评角色和是否需要 Validator 配合
2. 如需 Validator：先跑 Validator，FAIL 则不进入 Reviewer，直接退回修复
3. Orchestrator spawn Reviewer（factory-reviewer agent），task 中明确：评审对象、对象类型、对应维度、项目背景、模型档级（标准 / 高风险）
4. Reviewer 独立评审，输出标准格式结论，回报 Orchestrator
5. Orchestrator 据结论决策：
   - PASS → 解锁下一步，向用户展示摘要请求确认
   - CONDITIONAL_PASS → 列出必修项，由 Orchestrator 执行修复后，对照评审结论中的必修项逐项勾选确认，将确认记录写入 DISCUSSION-LOG.md（格式：`{日期} CONDITIONAL_PASS 修复确认：[必修项1 ✓] [必修项2 ✓] → 放行`），确认完成后解锁下一步，无需重评
   - FAIL → 退回对应阶段，记录原因，修复后重评
6. 评审结论以独立文件存档到 `projects/{id}/reviews/`，DISCUSSION-LOG.md 记一行指针

---

## 7. 评审结论存档规范

每次评审产出一个独立文件。

目录：`projects/{id}/reviews/`

命名格式：`{日期}-{类型}-{评审对象简称}-{评级}.md`

示例：
```
reviews/2026-06-13-B-DESIGN-01-PASS.md
reviews/2026-06-14-C-CODE-01-CONDITIONAL_PASS.md
reviews/2026-06-15-D-v1.2.0-PASS.md
```

DISCUSSION-LOG.md 对应一行：
```
2026-06-13 S3 方案评审完成，结论 PASS → 见 reviews/2026-06-13-B-DESIGN-01-PASS.md
```

---

## 8. Reviewer Sub-Agent 配置（已核实，基于 OpenClaw 本地文档）

### 8.1 Agent 定义

factory-reviewer 是独立预配置 agent，不临时继承 Orchestrator 模型。

在 `~/.openclaw/gateways/life/openclaw.json` 的 `agents.list` 中新增：

```json5
{
  id: "factory-reviewer",
  workspace: "/Users/evan/.openclaw/gateways/life/domains/agent-factory/reviewer-workspace",
  // 模型分档：默认标准档，高风险评审由 orchestrator spawn 时 model 参数覆盖
  model: {
    primary: "newapi-anthropic/claude-sonnet-4-6"
  },
  // 注意：sub-agent 只加载 AGENTS.md + TOOLS.md，不加载 SOUL.md
  // Reviewer 人格规则必须写入 reviewer-workspace/AGENTS.md
}
```

### 8.2 allowAgents（factory-orchestrator 层）

在 `agents.list` 中 factory-orchestrator 条目添加：

```json5
{
  id: "factory-orchestrator",
  // ... 现有配置 ...
  subagents: {
    allowAgents: ["factory-reviewer"]
  }
}
```

### 8.3 模型分档规则

- 默认档（A/B/D 类常规评审）：factory-reviewer 自身 `model.primary = newapi-anthropic/claude-sonnet-4-6`
- 高风险档（C 类代码 / 涉及外部 API / 安全相关 / 关键 Skill 最终验收）：spawn 时显式传 `model: "newapi-anthropic/claude-opus-4-8"`

**Provider 选择理由**：`newapi-anthropic` 走 `anthropic-messages` 原生 API，OpenClaw 会附加 `cache_control` 标记，支持 prompt caching（来源：`/opt/homebrew/lib/node_modules/openclaw/docs/providers/anthropic.md` §Prompt caching；`/opt/homebrew/lib/node_modules/openclaw/docs/concepts/model-providers.md` §openai-completions proxy 行为）。评审场景（大段文档输入 + 重复结构）缓存命中率高，长期成本优于 `mydamoxing`（openai-completions 无缓存）。注意：代理是否真实透传缓存折扣计费，需上线后首批评审时核查 cacheRead 命中情况。

**运行时**：embedded runtime（不走 ACP）。ACP_TURN_FAILED 会拖死评审流程；评审是只读任务，不需要外部 CLI 工具能力。

### 8.4 Reviewer 权限边界（写入 reviewer-workspace/AGENTS.md）

允许：读工作区文件、只读命令（cat/ls/grep/find/head/tail/wc）、只读 git（status/diff/log）、web_search/web_fetch

禁止：修改任何被评审文件、启动 ACP、执行破坏性命令、写入评审对象目录

### 8.5 spawn 调用规范

task 参数不超过 500 字，详细评审材料写入临时文件，通过路径传递，必须指定 `cwd`。

task 中必须注入：
- 评审对象路径
- 对象类型（A/B/C/D）及对应维度
- 项目 ID 和背景
- 最近 5 条工厂经验（EXPERIENCE.md 路径）
- 明确指令："只读评审、禁止修改文件、禁止启动 ACP、按标准格式输出结论、结论写入 projects/{id}/reviews/{文件名}"

第一次失败 → 重试一次（精简 task、检查 cwd）；第二次失败 → 降级为 Orchestrator 自评，记录原因告知用户。

---

## 9. 配置完成记录（v1.1 落地状态）

以下配置已于 2026-06-13 全部完成：

1. ✅ `reviewer-workspace/AGENTS.md` 已创建（Reviewer 人格 + 评审规则 + 权限边界）
2. ✅ life gateway `openclaw.json` 已更新：factory-reviewer agent 定义 + factory-orchestrator allowAgents + agents.defaults.subagents.allowAgents（对全局 agent 开放）
3. ⏳ newapi-anthropic 缓存折扣透传待验证：首批评审跑完后查看 cacheRead 命中情况

---

## 修订记录

| 版本 | 日期 | 变更摘要 |
|---|---|---|
| v1.0 | 2026-06-13 | 初始草案，定义四类评审对象、Reviewer/Validator 边界、触发条件、维度、产出格式、sub-agent 配置要求 |
| v1.1 | 2026-06-13 | 按四项决策更新：Q1 独立 agent（方案A）、Q2 模型分档+newapi-anthropic、Q3 统一 Reviewer、Q4 独立存档；移除待确认节；转 STABLE |
| v1.2 | 2026-06-13 | 按评审反馈修复：补 CONDITIONAL_PASS 修复确认机制（第6节）；技术引用补具体文档路径（第8.3节）；第9节改为已完成记录；外部 API 定义补边界说明（第3节） |
