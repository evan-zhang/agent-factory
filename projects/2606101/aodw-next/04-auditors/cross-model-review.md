# Cross-Model Review（双模型交叉审核）— AODW 融合版

> 来源：通用 Cross-Model Review 方法论 v1.0（2026-04-30）
> 融合日期：2026-04-30
> 适用：AODW Spec-Full Profile 的 Gate 3（方案审核）和 Gate 4（代码审核）

---

## 1. 为什么引入交叉审核

AODW 现有的 Gate 3/4 要求"Claude Code 独立审查"。单模型审查存在盲区重合（约 30-40%），尤其在复杂设计文档中。

**双模型交替审核的核心价值**：利用不同厂商模型的盲区互补，将遗漏率降至 <5%。

**实战证据**（2283 行 Platform 设计文档）：
- R1 Codex 发现 6 个 P0 → R2 Claude 又找到 Codex 漏掉的 5 个 P0
- R3 发现最多 P0（8个），因为 R2 的修复引入了新问题
- 前 3 轮消灭 ~80% 缺陷，之后指数收敛

---

## 2. 适用范围

| Profile | 是否使用交叉审核 | 说明 |
|---------|-----------------|------|
| **Spec-Full** | ✅ 推荐 | 设计文档（spec.md / plan.md）和代码审查 |
| **Spec-Lite** | ❌ 不使用 | Lite 本身是轻量流程，交叉审核成本过高 |

**注意**：交叉审核不替代 Gate 机制，而是作为 Gate 3/4 的**执行方式升级**。Evan 仍然是最终决策者。

---

## 3. 在 AODW 中的嵌入方式

### 3.1 Gate 3（方案审核）升级

```
现在：Gate 3 → Claude Code 审一次 → 报告给 Evan
升级：Gate 3 → Codex 审一轮 + Claude 审一轮 → 合并报告 → 报告给 Evan
```

Gate 本身不变，决策权不变。

### 3.2 Gate 4（代码审核）升级

```
现在：Gate 4 → Claude Code 审查 → 报告给 Evan
升级：Gate 4 → Codex + Claude 各审一轮（可并行）→ 合并报告 → 报告给 Evan
```

---

## 4. 问题分级标准

审核者必须按以下分级报告所有问题：

| 级别 | 含义 | 处理方式 |
|------|------|---------|
| **P0** | 阻断性错误：逻辑矛盾、字段缺失、会导致运行时故障 | ✅ 必须修复，本轮不关不进入下一轮 |
| **P1** | 正确性风险：边界条件遗漏、语义不一致 | ✅ 必须修复 |
| **P2** | 文档一致性：标题版本号未更新、注释与代码矛盾 | ✅ 建议修复 |
| **P3** | 建议：命名风格、可读性、更优写法 | ⬜ 可选 |

**与 AODW 审计官分级的映射**：

| 交叉审核 | AODW 审计官 |
|---------|------------|
| P0 | Blocking |
| P1 | Critical |
| P2 | Warning |
| P3 | — （AODW 审计官不输出建议，但交叉审核可以） |

---

## 5. 交替策略（AODW 精简版）

**核心原则**：前 2-3 轮严格交替，之后根据问题数量决定是否继续交替。

```
Round 1: Codex（擅长逻辑/代码/边界条件）
Round 2: Claude（擅长架构/语义/设计矛盾）
Round 3: 看情况（如果 R2 还有 P0，换模型继续；否则进入验证）
```

**决策树**：

```
R1-R2: 严格交替（Codex → Claude）
R3+: 
  - 上轮还有 P0 → 继续审核，优先换模型
  - 上轮只有 P1/P2 → 可以不换模型，快速收尾
  - 上轮 0 P0 → 进入验证轮
```

**轮数上限**：默认 3 轮（2 轮交替 + 1 轮验证），不超过 5 轮。AODW 核心原则是"先做垃圾出来验证"，过度打磨违背初衷。

---

## 6. 单轮审核流程

```
1. Author 准备文档/代码（确认版本号）
2. spawn Reviewer（指定模型）
3. Reviewer 读取内容，输出问题清单（P0/P1/P2/P3）
4. Author 按优先级修复：P0 全修 → P1 全修 → P2 尽量修
5. 更新版本号（如适用）
6. 进入下一轮（按交替策略换模型）
```

---

## 7. Prompt 模板

### 7.1 设计文档审核 Prompt

用于 Gate 3（方案审核），spawn 时填入实际文件路径。

```markdown
你是文档审核者。请审核以下设计文档。

## 审核文档
文件路径：{spec.md 或 plan.md 的路径}

## 审核要求
1. 逐节通读，找出所有逻辑错误、遗漏、矛盾
2. 特别关注：
   - 字段/变量/表名的一致性（定义处 vs 使用处）
   - 状态机/流程的完备性（是否有未覆盖的转移路径）
   - 原子性保证（事务边界是否正确）
   - 边界条件（空值、并发、超时、取消）
3. 每个问题必须分级：P0（阻断）/ P1（正确性风险）/ P2（文档一致性）/ P3（建议）

## 输出格式

### 结论
[通过 / 条件通过 / 拒绝]（有 P0 = 拒绝，仅 P1 = 条件通过，无 P0P1 = 通过）

### P0 问题
| # | 位置 | 问题描述 | 建议修复 |
|---|------|----------|----------|
（无则写"无"）

### P1 问题
（格式同上，无则写"无"）

### P2 问题
（格式同上，无则写"无"）

### P3 建议
（格式同上，无则写"无"）

### 总体评价
一句话总结文档质量。

如果真的无问题，必须逐节确认，不能只写一句"没问题"。
```

### 7.2 代码审核 Prompt

用于 Gate 4（代码审核）。

```markdown
你是代码审核者。请审核以下代码变更。

## 审核范围
项目目录：{项目路径}
变更文件：{变更文件列表，或指定 git diff}

## 审核要求
1. 检查代码是否与设计方案（rt-lite.md §2 / plan.md）一致
2. 特别关注：
   - 修改范围是否超出方案声明的文件
   - 是否引入了未在方案中声明的依赖
   - 边界条件和错误处理
   - 测试是否覆盖了关键路径
3. 每个问题必须分级：P0/P1/P2/P3

## 输出格式
（同 7.1）
```

### 7.3 验证轮 Prompt

最后一轮使用，只验证上轮问题是否修复。

```markdown
你是最终验证者。上轮审核提出了以下问题，作者已修复。

## 上轮问题
（粘贴上轮问题清单）

## 验证要求
逐项验证上轮每个问题是否已正确修复。
- 已修复 → ✅
- 未修复 → ❌ 并说明

## 验证文档/代码
文件路径：{文件路径}

## 输出格式
逐项列出，每项给出结论。最后给出总体判断：PASS / FAIL。
```

---

## 8. 实操参数（OpenClaw 环境）

### Spawn Codex 审核者

```json
{
  "runtime": "acp",
  "agentId": "codex",
  "mode": "run",
  "task": "<7.1 或 7.2 的 Prompt，填入实际路径>",
  "timeoutSeconds": 300
}
```

### Spawn Claude 审核者

```json
{
  "runtime": "acp",
  "agentId": "claude",
  "mode": "run",
  "task": "<7.1 或 7.2 的 Prompt，填入实际路径>",
  "timeoutSeconds": 300
}
```

也可以使用 `coding-agent` Skill spawn。

> ⚠️ spawn 前请先确认 ACP 链路已通（见 §9 ACP 链路打通）。

### 模型选择建议

| 审核对象 | 推荐首轮模型 |
|---------|------------|
| 设计文档（spec/plan） | Claude（擅长架构/语义） |
| 代码审查 | Codex（擅长逻辑/边界条件） |
| 不确定 | Codex 先跑，Claude 第二轮 |

---

## 9. ACP 链路打通（前置条件）

交叉审核的前提是能 spawn 起 Codex/Claude。在执行前必须确认链路畅通。

### 9.1 前置条件检查

```
□ OpenClaw 版本 ≥ 2026.4.x（支持 ACP）
□ acp.backend = "acpx" 已配置
□ acpx 插件已启用：plugins.entries.acpx.enabled = true
□ acp.allowedAgents 包含 ["codex", "claude"]
□ Claude Code CLI 已安装：which claude 有输出
□ Claude Code permissions 已配置（避免权限弹窗卡住 spawn）
□ （可选）Codex CLI 已安装：which codex 有输出
```

快速验证：
```bash
which claude && claude --version
openclaw status 2>&1 | grep -i acp
```

### 9.2 OpenClaw ACP 最小配置

```json
{
  "acp": {
    "backend": "acpx",
    "defaultAgent": "codex",
    "allowedAgents": ["codex", "claude"]
  },
  "plugins": {
    "allow": ["acpx"],
    "entries": {
      "acpx": { "enabled": true }
    }
  }
}
```

⚠️ 配置修改后需要重启 OpenClaw 才能生效。

### 9.3 Claude Code 权限配置

`~/.claude/settings.json` 中必须配好 permissions，否则 spawn 会因权限弹窗卡住：

```json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]
  }
}
```

### 9.4 常见失败排查

| 错误现象 | 原因 | 解法 |
|----------|------|------|
| `ACP not enabled` | openclaw.json 缺 acp 配置 | 加上 9.2 的配置并重启 |
| `agent "codex" not in allowedAgents` | allowedAgents 列表缺 codex | 添加到列表 |
| spawn 后超时无输出 | Claude Code 权限弹窗卡住 | 配置 permissions.allow |
| `claude: command not found` | Claude Code 未安装 | npm install -g @anthropic-ai/claude-code |
| spawn 成功但输出为空 | task Prompt 太长被截断 | 缩短 Prompt 或分块审核 |

### 9.5 链路验证

在正式审核前，先测试 spawn 是否正常：

```
sessions_spawn({
  runtime: "acp",
  agentId: "claude",
  mode: "run",
  task: "回复 OK 两个字",
  timeoutSeconds: 60
})
```

收到回复 = 链路畅通，可以开始正式审核。

---

## 10. 审核链记录

在 RT 目录下维护 `cross-review-log.md`，记录每轮审核的发现和修复：

```markdown
# Cross-Model Review Log: RT-XXX

## R1 — Codex（2026-04-30）
- P0: 6 个 → 全部修复
- P1: 3 个 → 全部修复
- 修复后版本: v2.4

## R2 — Claude（2026-04-30）
- P0: 1 个 → 全部修复
- P1: 2 个 → 全部修复
- 修复后版本: v2.5

## R3 — 验证轮（Codex）
- 上轮问题逐项验证: 全部 PASS ✅
```

---

## 11. 终止条件

满足以下**任一**条件即可终止：

| 条件 | 含义 |
|------|------|
| **零 P0 轮** | 某轮审核 0 P0 |
| **验证轮 PASS** | 验证轮确认上轮问题全部修复 |
| **达到轮数上限** | 已达 5 轮，即使还有 P0 也暂停，报告给 Evan 决策 |

**推荐**：零 P0 轮 → 1 轮验证确认 → 终止 → 报告给 Evan。

---

## 12. 注意事项

1. **成本控制**：每轮审核约 5-15 分钟（取决于文档长度），3 轮约 30-40 分钟。在 AODW 中，这不是每个 RT 都需要走的标准流程，只在 Spec-Full 且设计文档 > 500 行时推荐。
2. **不替代测试**：代码审查用交叉审核有价值，但测试覆盖率才是质量底线。交叉审核不能替代 Gate 5 的验收测试。
3. **P1 可以带着走**：零 P0 即可终止，P1 不阻断（这点和原文不同，原文要求 P1 也全修）。
4. **文档太长时**：分块审核，或指定"重点审核第 X-Y 节"，避免截断。
5. **模型偷懒说"无问题"**：Prompt 里强制要求"逐节确认，不能只写一句'没问题'"。

---

*融合自：Cross-Model Review v2.0（含 ACP 链路打通指南）| 融合日期：2026-04-30 | 融合者：Codex (aodw_codex)*
