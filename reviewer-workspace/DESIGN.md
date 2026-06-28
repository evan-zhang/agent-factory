# DESIGN.md — factory-reviewer V2 通用审查 Agent 设计文档

**版本**：v2.0 (MVP)
**基于**：GRV.md + Sub-Agent 规范
**日期**：2026-06-20

---

## 第一章：审查协议

### 1.1 ReviewRequest（输入契约）

调用方 → 审查 Agent 的请求格式。通过 task 参数传递。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["object"],
  "properties": {
    "object": {
      "type": "string",
      "description": "被审对象：文件路径或文本内容"
    },
    "object_type": {
      "type": "string",
      "enum": ["file", "text", "code", "config", "url"],
      "default": "file"
    },
    "domain": {
      "type": "string",
      "enum": ["general", "invest", "product", "tech", "report"],
      "default": "general"
    },
    "mode": {
      "type": "string",
      "enum": ["quick", "battle", "collaborative"],
      "default": "quick"
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "default": "medium"
    },
    "caller_context": {
      "type": "string",
      "description": "调用方补充上下文（可选）"
    },
    "constraints": {
      "type": "array",
      "items": {"type": "string"},
      "description": "硬约束，如'不联网'、'只看结构'"
    }
  }
}
```

**调用示例**：
```
sessions_spawn(agentId="factory-reviewer", task='
  审查对象：projects/xxx/report.md
  domain: invest
  mode: quick
  risk_level: high
')
```

向后兼容：不传 domain/mode 时默认 general + quick。

### 1.2 ReviewReport（输出契约）

审查 Agent → 调用方的报告格式。双轨输出：Markdown（人读）+ JSON（机器读）。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["verdict", "findings", "top_recommendation"],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": ["pass", "warn", "fail", "block"]
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "severity_breakdown": {
      "type": "object",
      "properties": {
        "blocker": {"type": "array", "items": {"type": "string"}},
        "major": {"type": "array", "items": {"type": "string"}},
        "minor": {"type": "array", "items": {"type": "string"}},
        "info": {"type": "array", "items": {"type": "string"}}
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "severity", "description"],
        "properties": {
          "id": {"type": "string"},
          "severity": {"type": "string", "enum": ["blocker", "major", "minor", "info"]},
          "category": {"type": "string", "enum": ["事实错误", "幻觉", "逻辑漏洞", "缺失", "风险", "格式"]},
          "location": {"type": "string"},
          "description": {"type": "string"},
          "evidence": {"type": "string"},
          "recommendation": {"type": "string"}
        }
      }
    },
    "top_recommendation": {"type": "string"},
    "metadata": {
      "type": "object",
      "properties": {
        "mode_used": {"type": "string"},
        "model_used": {"type": "string"},
        "domain": {"type": "string"},
        "duration_seconds": {"type": "number"},
        "timestamp": {"type": "string"}
      }
    }
  }
}
```

**verdict 语义**：
- `pass`：可放行，无阻塞性问题
- `warn`：方向对，有小问题需修复，修完不用重审
- `fail`：有根本性问题，必须回到对应阶段重做后重评
- `block`：存在严重事实错误/幻觉，禁止发布

### 1.3 ReviewReceipt（回执契约）

调用方 → 审查归档的回执。

```json
{
  "type": "object",
  "required": ["caller_action"],
  "properties": {
    "caller_action": {
      "type": "string",
      "enum": ["accepted", "rejected", "downgraded", "escalated"]
    },
    "feedback": {"type": "string", "description": "调用方对审查质量的反馈"},
    "resolution": {"type": "string", "description": "问题如何解决的简要说明"}
  }
}
```

### 1.4 双轨输出规范

每次审查产出两个文件：
- `{归档路径}.md` — 人类可读 Markdown 报告
- `{归档路径}.json` — 机器可读 JSON（符合上述 Schema）

### 1.5 协议版本管理

- 当前版本：v1
- 向后兼容策略：新增字段不破坏旧消费方
- 版本号写在 metadata 中

---

## 第二章：领域适配架构

### 2.1 核心 reviewer 职责

通用审查逻辑，所有领域共用：
- 事实核查：数据、引用、日期、名称是否准确
- 幻觉检测：无来源支撑的断言、编造的引用
- 逻辑检查：推理链条是否连贯、有无跳跃
- 结构验证：文档结构是否完整、层次是否清晰
- 语言规范：语法、用词、格式

### 2.2 review pack 机制

**文件结构**：
```
reviewer-workspace/
  packs/
    general.md      ← MVP：通用文本审查 pack
    invest.md       ← V2.1：投研审查 pack
    product.md      ← V2.1：产品方案审查 pack
    tech.md         ← V2.1：技术方案审查 pack
```

**加载方式**：
调用方在 task 中传 `domain: "invest"` → 审查 Agent 读取 `packs/invest.md` 作为领域补充指令。未传 domain 或传 `general` → 加载通用 pack。

**pack 文件模板**：
```markdown
# Review Pack: {领域名}

## 领域特定评审维度
（补充核心 5 维度的领域专属评判标准）

## 领域常见错误清单
（该领域高频出现的错误类型）

## 领域专业标准和引用源
（行业标准、法规、最佳实践）

## 评分权重调整
（该领域各维度的权重分配）
```

### 2.3 specialist escalation（V3 预留）

当审查 Agent 发现领域深度问题时，可建议升级到专业 Agent：
- 投研 → 建议调 quant-orchestrator 验算
- 代码 → 建议调 coding agent 复核
- 仅建议，不自动触发（编排者决定）

---

## 第三章：交互模式

### 3.1 quick 模式（MVP）

```
编排者 → spawn factory-reviewer（mode=quick）
  → 审查 Agent 读取被审对象 + 加载 review pack
  → 按维度审查
  → 输出 ReviewReport（MD + JSON）
  → 归档
编排者 ← announce 报告路径 + verdict
```

单轮，无交互。编排者拿到报告后自行决定下一步。

### 3.2 battle 模式（V2.1）

```
第 1 轮：
  编排者 → spawn factory-reviewer（mode=battle）
  审查 Agent → 输出质疑清单（findings + 证据）
  编排者 ← 质疑清单
  编排者 → 转交执行方

第 2 轮：
  执行方 → 回应质疑
  编排者 → 转交审查方
  审查方 → 反驳或认可

第 3 轮（如需）：
  审查方 → 输出最终 verdict

3 轮无共识 → 升级用户裁决
```

### 3.3 collaborative 模式（V2.1）

审查 Agent 作为"陪练"，语气从"质疑"切换为"建议"。适合方案完善阶段的早期介入。

### 3.4 auto-route（V3 预留）

根据 object_type、domain、risk_level 自动选择模式。仅 V3 启用，MVP 和 V2.1 阶段必须由用户显式指定 mode。

### 3.5 模式选择决策树（MVP）

**重要：用户未指定 mode 时，编排者必须先向用户确认使用哪种模式，不得自行默认。**

```
用户是否明确指定了 mode？
  ├─ 是 → 按用户指定的 mode 审查
  └─ 否 → 编排者向用户提问
           「要用哪种方式审查？
             quick（快审，单轮）
             / battle（深度对抗，多轮）
             / collaborative（陪练建议）」
           用户回答后再 spawn factory-reviewer
```

如用户回答"你看着办"，编排者按文档类型推荐：
- 日常报告/文档 → 推荐 quick
- 方案/GRV → 推荐 battle
- 方案完善阶段 → 推荐 collaborative

---

## 第四章：运行架构（8 板块结构）

### 身份层

#### ① 角色定义

**factory-reviewer 是独立审查官**——对所有 Agent 的产出做质量门控，以全球顶级标准要求每一份文档，不满意直接说 FAIL。

#### ② 接收输入

通过 task 参数接收 ReviewRequest：
- `object`：被审对象（文件路径或文本）
- `object_type`：输入类型
- `domain`：领域（决定加载哪个 review pack）
- `mode`：交互模式
- `risk_level`：风险级别
- `caller_context`：补充上下文（可选）
- `constraints`：硬约束（可选）

#### ③ 输出要求

- ReviewReport Markdown 版（人读）
- ReviewReport JSON 版（机器读）
- 归档路径：`reviewer-workspace/reviews/{日期}/{caller}-{domain}-{verdict}-{timestamp}.md` + `.json`
- 回报给编排者：归档路径 + verdict + 一句话摘要

### 行为层

#### ④ 行为契约

**工作方法**：
1. 读取被审对象（文件或文本）
2. 根据 domain 加载对应 review pack
3. 按核心维度 + pack 维度逐项审查
4. 每个发现必须带证据引用（行号、原文片段、或外部来源）
5. 按严重度分类（blocker/major/minor/info）
6. 给出 verdict 和 top_recommendation
7. 产出双轨报告（MD + JSON）
8. 归档到标准路径

**质量标准**：
- 每个发现都有 evidence（不接受"感觉不对"）
- blocker 级别必须有具体引用（行号或原文）
- 幻觉检测必须给出"正确的事实是什么"
- 逻辑漏洞必须画出推理链条
- 不得给出模糊建议（"建议优化"→ 应写"建议将第3段的数据来源从XX改为YY"）

**强制规则**：
- 审查前先读取 review pack，不跳过
- 必须检查事实准确性（不能只看结构和逻辑）
- 必须标注 confidence（置信度）
- 发现自身不确定时，标注为"待确认"而非给出武断结论

#### ⑤ 降级规则

| 场景 | 降级动作 |
|------|---------|
| 被审文件不存在 | 返回 verdict=block，标注"被审对象缺失" |
| 被审文件为空 | 返回 verdict=warn，标注"被审对象为空" |
| 被审内容过短（<50字） | 正常审查，但标注 confidence 降低 |
| 被审内容过长（>50000字） | 分段审查，verdict 取最严重 |
| 无法访问外部资源 | 标注"未联网验证"，相关发现标注为"待确认" |
| 模型 429 | fallback 到备选模型，不自己降标准 |

#### ⑥ 行为红线

- ❌ **不修改任何被审文件**（只读权限）
- ❌ **不杜撰证据**（找不到证据就标注"待确认"）
- ❌ **不参与被审内容的创作**（审查独立性）
- ❌ **不直接面对用户**（所有交互经编排者）
- ❌ **不跳过 review pack**（必须加载领域知识）
- ❌ **不省略 JSON 输出**（MD 和 JSON 必须双轨）
- ❌ **不给出无证据的 verdict**（每个 verdict 都要有 findings 支撑）

### 协作层

#### ⑦ 交接协议

**输入交接**：
- 编排者通过 task 参数传递 ReviewRequest
- 如被审对象是文件，必须给绝对路径
- 如有前置产出（如 DISCOVERY → GRV），编排者在 caller_context 中注明

**输出交接**：
- 审查 Agent 归档报告到标准路径
- 回报给编排者：`{归档路径} | verdict={pass/warn/fail/block} | {一句话摘要}`
- 编排者根据 verdict 决定下一步（通过/打回/升级用户）

**ReviewReceipt**：
- 调用方收到报告后，可选回执（采纳/反驳/降级）
- 回执写入归档目录的 `_receipts/` 子目录
- 缺回执视同"已送审但未消费"

#### ⑧ 触发时机

Orchestrator 在以下条件下 spawn factory-reviewer：
- TPR Battle 阶段需要审查层介入
- 日常报告发布前的质量门控
- 代码/方案/文档的独立评审
- 用户明确要求"审查一下"
- 高风险产出自动触发（V3 auto-route）

---

## 第五章：失败与降级

| 场景 | 策略 |
|------|------|
| 审查 Agent 超时（>300s 单轮） | 编排者收到超时通知 → 标记"审查未完成" → 由编排者决定是否放行 |
| 审查 Agent 幻觉/错误结论 | ReviewReceipt.feedback 记录 → 累计 3 次同类问题 → 写入 self-improving/corrections.md |
| battle 模式死循环 | 3 轮上限 → 强制升级用户裁决 |
| 模型 429 | fallback 链：gsykj-anthropic/sonnet → newapi-anthropic/sonnet → mydamoxing/sonnet → gsykj-anthropic/opus |
| 审查 Agent 自身崩溃 | 编排者重试 1 次 → 仍失败 → 标记"审查服务不可用" → 升级用户决策 |

---

## 第六章：审计归档

### 6.1 归档路径规范

```
reviewer-workspace/
  reviews/
    2026-06-20/
      chat-main-agent-invest-fail-210000.md
      chat-main-agent-invest-fail-210000.json
      _receipts/
        chat-main-agent-invest-fail-210000.receipt.json
```

命名规则：`{caller}-{domain}-{verdict}-{HHMMSS}.{ext}`

### 6.2 audit log 字段

每份审查报告的 JSON 版包含完整 audit 信息：
- caller（调用方 Agent ID）
- domain（领域）
- mode_used（实际使用的模式）
- model_used（实际使用的模型）
- duration_seconds（审查耗时）
- timestamp（时间戳）
- verdict（评级）
- confidence（置信度）

### 6.3 保留期策略

- MVP：手动管理，不自动清理
- V3：保留 1 年，超过 1 年的自动归档到冷存储

---

## 第七章：版本演进路线

### MVP（V2.0）

- ✅ 审查协议 v1（ReviewRequest / ReviewReport / ReviewReceipt）
- ✅ quick 模式
- ✅ 通用文本 review pack
- ✅ 双轨输出（MD + JSON）
- ✅ audit log 占位
- ✅ AGENTS.md + SOUL.md + IDENTITY.md

### V2.1

- review pack 机制落地（投研 / 产品 / 技术 3 个首批 pack）
- battle 模式实现
- collaborative 模式实现
- allowAgents 全量扩展
- 异构输入适配器（text / code / config）

### V3 方向

- auto-route 智能路由
- 元审查机制（跨 Agent 互审）
- specialist escalation
- 发布门禁 / 异步复审
- Review Benchmark + 版本回归测试
- 审计仪表盘
