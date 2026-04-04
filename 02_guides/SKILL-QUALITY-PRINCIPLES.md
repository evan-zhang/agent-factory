# Skill 质量原则 v1.1
> 来源：clawhub skill-builder / lean-skill-builder / Anthropic Claude Code 规范整合
> 建立时间：2026-03-31 | 最后更新：2026-03-31 v1.1（合并 lean-skill-builder 10维 Audit Checklist）
> 适用范围：工厂所有 Skill 的开发、修改、发布流程

---

## 六大核心原则

### 原则 1 — 单一职责
一个 Skill 只做一件事，边界必须清晰。
"发汇报"和"管理草稿"是两个独立 Skill，不合并。
如果 Skill 名字里有"管理"、"处理"、"workflow"等模糊词，先拆分再说。

### 原则 2 — 三层披露（Token 经济学）
| Tier | 内容 | 加载时机 | 预算 |
|------|------|----------|------|
| 1 | frontmatter description | 每次对话都加载 | ~100 词 |
| 2 | SKILL.md 正文 | Skill 触发后加载 | 80 行以内 |
| 3 | references/ 辅助文件 | 按需加载，SKILL.md 指引 | 不限 |

细节只能向下移，不能向上堆。

### 原则 3 — description 要"有点激进"
LLM 默认不触发 Skill，宁可自己回答。
description 必须包含 3-5 个具体触发词，覆盖口语化表达。
可以加 "even if they don't say XXX" 强制触发。
不要以 "Use when..." 开头，改用动词开头。

### 原则 4 — 粒度判断

**应该拆分的情况：**
- 需要不同权限集
- 可以独立完成，不互相依赖
- 触发条件根本不同
- 完成时间超过 5 分钟

**应该合并的情况：**
- 步骤不可分割
- 共享完全相同的权限和上下文

### 原则 5 — 写法：命令式 + 解释原因
❌ 不要：ALWAYS/NEVER/CRITICAL 大写强调
✅ 要：说清楚"为什么"，LLM 理解原因比遵守规则更可靠

例：
❌ "ALWAYS 先存草稿，NEVER 直接发送"
✅ "先存草稿再发送，因为直接发没有确认机会，出错无法撤回"

### 原则 6 — Smoke Test（发布前必做）
每个 Skill 发布前必须过三类测试：
1. **正常触发**：标准场景，应该触发且行为正确
2. **边界触发**：边缘场景，应该触发并能处理
3. **不应触发**：相似但不属于该 Skill 的请求，不应触发

---

## 颗粒度决策树

```
收到新需求
    │
    ├─ 一次性任务？ → 直接执行，不建 Skill
    │
    ├─ 已有 Skill 可以覆盖？ → 复用或微调，不新建
    │
    ├─ 工作量大，需要探索多文件？ → 用 subagent，不建 Skill
    │
    └─ 可复用、有特定工作流、需要进阶披露？
           → 建 Skill，从最小结构开始
```

最小结构：只有 `SKILL.md`，够用就停。

---

## 完整 Audit Checklist（10 维度 × 发布前必过）

> 来源：lean-skill-builder audit-checklist.md + 工厂安全规范合并
> 审核结论只有 5 种：**保持不变 / 精简 / 轻量重构 / 最小化重建 / 退休或合并**

### 维度 1 — 触发质量
- [ ] description 说清楚了做什么、什么时候用？
- [ ] 含 3-5 个具体触发词，覆盖口语化表达？
- [ ] 用动词开头，不以 "Use when..." 开头？
- [ ] 和其他已有 Skill 没有明显重叠？
- [ ] 描述足够"激进"，能在用户不说关键词时也能触发？

### 维度 2 — 是否真的需要建 Skill
- [ ] 这是可复用的需求，不是一次性任务？
- [ ] 没有现成工具或 Skill 可以直接覆盖？
- [ ] 不是 subagent 任务（工作量大、需要探索多文件）？
- [ ] 不是"为了建 Skill 而建 Skill"？

### 维度 3 — SKILL.md 纪律
- [ ] SKILL.md ≤ 80 行，容易扫描？
- [ ] 只包含核心工作流和规则，细节已推入 references/？
- [ ] 引用的辅助文件路径明确列出，可发现？
- [ ] 没有政策宣言或使命陈述式的废话段落？

### 维度 4 — 写法质量
- [ ] 命令式语气（"读取文件" 不是 "可以考虑读取"）？
- [ ] 关键步骤解释了"为什么"，不只是"是什么"？
- [ ] ALWAYS/NEVER/CRITICAL 大写附带了原因解释？
- [ ] 示例 1-2 个，简洁具体，不堆砌？
- [ ] 需要固定格式的输出，定义了模板？

### 维度 5 — 最小化原则
- [ ] 目录是能满足需求的最小结构？
- [ ] references/ 文件 ≤ 3 个？
- [ ] assets/ 只在需要捆绑静态文件时才存在？
- [ ] scripts/ 只在确实需要确定性执行时才存在？

### 维度 6 — 文件卫生
- [ ] 无 README/CHANGELOG 等对 AI 无用的人类文档？
- [ ] 无 SKILL.md 和 references/ 之间的重复内容？
- [ ] 无废弃的占位文件或实验残留？

### 维度 7 — 规范漂移检查
- [ ] 引用的文件路径真实存在？
- [ ] 示例代码/命令仍然准确有效？
- [ ] Skill 没有悄悄扩展到多个目的（"越界"）？
- [ ] 指令与当前工具/工作流仍然匹配？

### 维度 8 — Smoke Test（三场景必过）
- [ ] 正常触发：标准场景，触发且行为正确？
- [ ] 边界触发：边缘场景，触发且能处理？
- [ ] 不应触发：相似但不属于该 Skill 的请求，不触发？

### 维度 9 — Do-nothing Check（防过度工程）
- [ ] 改一个文件能解决的，没有错误地建 Skill？
- [ ] 这不是 subagent 问题（而非 Skill 问题）？
- [ ] 新增内容真的在承担自己的 token 成本？

### 维度 10 — 安全与元数据（工厂专项）
- [ ] 无 process.env 写入或读取凭证（用 runtime 模块替代）？
- [ ] External Endpoints 在 setup.md 中明确声明？
- [ ] frontmatter metadata.requires.env 已声明必需变量？
- [ ] 无 "silently/secretly/automatically/monitor/track" 等扫描触发词？
- [ ] LLM 凭证由调用方注入，Skill 内部不存储？
- [ ] 发布后检查 clawhub suspicious 标记，确认无 blocked？

---

## 开发过程中的持续检查点

| 阶段 | 检查内容 |
|------|----------|
| 设计 | 颗粒度决策树 → 确认是否需要建 Skill |
| 开发中 | 每次新增内容 → 确认是否超过 Tier 预算，是否该推入 references/ |
| 代码 Review | 安全检查 + External Endpoints 声明 |
| 发布前 | 完整 Checklist + Smoke Test |
| 发布后 | 检查扫描结果（suspicious 标记），确认无 blocked |

---

## 参考资料
- clawhub skill-builder v1.0.5（ivangdavila）
- lean-skill-builder（zurbrick）
- Anthropic Claude Code Best Practices 2025
- OpenClaw Skill 粒度规范（meta-intelligence.tech）

---
*最后更新：2026-03-31 | 工厂 Skill 质量标准 v1.0*
