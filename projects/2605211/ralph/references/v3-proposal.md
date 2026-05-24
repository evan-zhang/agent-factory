# Ralph Loop v3 改造方案

> 基于 autoresearch (karpathy/autoresearch) 的设计思想，对现有 Ralph Loop v2.0.0 的改造方案。
> 本文档只做方案设计，不做实施。实施前需 Evan 逐条确认。

---

## 一、现状诊断：v2 的结构性问题

### 问题 1：SKILL.md 角色过载

当前 SKILL.md 同时承担 4 个角色：
- 安装指南（怎么装）
- 协议定义（怎么跑）
- 配置参考（参数表）
- 使用教程（示例和决策树）

后果：核心循环协议被稀释在大量辅助信息中。Agent 每次启动要处理的上下文太多，真正关键的循环规则不突出。对比 autoresearch 的 program.md，200 行只讲一件事：怎么循环。

### 问题 2：state.json 过于复杂

当前 state.json 有 12+ 字段：task、goal、mode、phase、iteration、checklist、route、journal、blockers、decisions、startedAt、completedAt、meta。

autoresearch 证明了：git commit/reset + 一个 results.tsv 就够管理实验循环。state.json 的复杂度带来了：
- Agent 认知负荷重（每次迭代要读写大 JSON）
- 损坏风险高（shell 脚本维护 JSON 本身就不稳健）
- prompt 膨胀（整个 state.json 被塞进 prompt）

### 问题 3：缺少"只读评估器"

autoresearch 的 prepare.py 是只读的，Agent 不能篡改评估标准。这保证了 NEVER STOP 是安全的——即使 Agent 永远不停，最差结果也只是浪费算力，不会产出垃圾。

我们的 Ralph Loop 没有这个隔离。验证命令写在 PROMPT.md 里，Agent 理论上可以改 PROMPT.md（虽然不会）。更关键的是，验证标准不统一——每次任务都要人类手写三要素公式，质量参差不齐。

### 问题 4：缺少 Simplicity Criterion

autoresearch 明确要求"删代码得到同样效果是最佳实验"。我们的 Ralph Loop 只评估"完没完成"，不评估"改动是否值得保留"。这导致 Agent 可能在堆砌复杂度。

### 问题 5：shell 脚本维护 JSON 不可靠

ralph-loop.sh 用 bash 字符串拼接构建 prompt、用 python3 一行式读写 JSON。这在生产中频繁出问题（特殊字符、编码、并发写入）。autoresearch 完全不需要这个——它只有 git 和 grep。

---

## 二、改造目标

1. **极简**：向 autoresearch 靠拢，砍到只剩必要结构
2. **可信**：引入只读评估器，保证循环结果的可靠性
3. **自主**：减少人类干预点，让 Agent 真正自主运行
4. **稳健**：用 git 替代 JSON 做状态管理，避免 shell+JSON 的脆弱性

---

## 三、改造方案：5 项变更

### 变更 1：拆分 SKILL.md → SKILL.md + PROTOCOL.md

**做什么**：
- `PROTOCOL.md`：核心循环协议（类似 autoresearch 的 program.md），只讲规则、不讲安装和配置。约 100-150 行。
- `SKILL.md`：保留作为入口文件（安装、配置、模式选择），但不包含循环细节。

**为什么**：
autoresearch 的 program.md 证明了"纯协议文档"的威力。Agent 每次迭代只需要读 PROTOCOL.md，不需要被安装指南干扰。

**PROTOCOL.md 包含**：
- 可修改范围（哪些文件可以改）
- 只读文件（不能碰）
- 评估标准（怎么判断成功/失败）
- 循环规则（commit 保留、reset 撤回、NEVER STOP）
- Simplicity Criterion
- 结果记录格式

**风险**：低。纯文件拆分，不影响现有功能。

---

### 变更 2：引入 verify.sh（只读评估器）

**做什么**：
每个 Ralph Loop 任务必须提供一个 `verify.sh`（或 verify.py），定义验证标准。这个文件在循环开始后被标记为只读，Agent 不能修改。

verify.sh 规范：
```bash
#!/bin/bash
# exit 0 = 通过，exit 1 = 失败
# 可以包含多条验证，全部通过才 exit 0
# 标准输出最后一行是分数（用于比较，数字越小越好，类似 val_bpb）
```

**为什么**：
autoresearch 的 prepare.py 是整个设计中最精妙的部分。它保证了一个不可篡改的评估标准。有了这个，NEVER STOP 才安全。

对比现有方案：v2 的验证命令分散在 PROMPT.md 的 checklist 里，每个任务格式不同，Agent 理解成本高。统一成一个 verify.sh 后：
- Agent 只需要 `bash verify.sh`，不需要理解复杂的验证逻辑
- 评估标准不可篡改，Agent 不能自己降低标准
- 所有任务的验证方式一致，降低 prompt 复杂度

**输出格式约定**：
```
verify.sh 输出:
score: 0.234          ← 用于比较（越小越好，类似 val_bpb）
status: PASS          ← PASS 或 FAIL
details: 3/3 tests passed
```

**风险**：中。需要每个任务都准备 verify.sh，增加了启动成本。但好处是验证质量大幅提升。可以提供模板和生成工具降低门槛。

---

### 变更 3：简化 state.json → results.tsv + git

**做什么**：
用 git commit/reset 管理代码状态，用 results.tsv 记录实验历史。大幅简化 state.json。

**新 state.json（精简版）**：
```json
{
  "task": "一句话任务描述",
  "mode": "executor | autonomous",
  "phase": "working | done",
  "iteration": 0,
  "checklist": { "条件": true/false }
}
```

砍掉的字段：route、journal、decisions、blockers、startedAt、completedAt、meta。

替代方案：
- route/journal/decisions → results.tsv（每行一条实验记录）
- blockers → 检查 git log 和 results.tsv 就能看出卡在哪
- 时间信息 → git commit timestamp

**results.tsv 格式**（借鉴 autoresearch）：
```
iteration\tscore\tstatus\tdescription
1\t0.234\tkeep\tbaseline
2\t0.198\tkeep\t改用 AdamW
3\t0.245\tdiscard\t增加层数
4\t0.187\tkeep\t简化 attention
```

**为什么**：
autoresearch 证明了 git + TSV 就够了。state.json 的复杂度在 v2 中是最大的维护负担——shell 脚本维护 JSON 频繁出问题（特殊字符、编码、损坏恢复）。

**风险**：中。砍掉 journal 和 route 会失去一些自主者模式的能力（比如"避免重复走错路"需要查 journal）。但 results.tsv + git diff 可以部分替代。可以保留 journal 为可选字段。

**要不要完全砍掉 journal？这个需要讨论。** autoresearch 不需要 journal 因为它只看一个指标。我们的任务可能更复杂，可能需要记录"为什么这么做"。但可以精简格式。

---

### 变更 4：加入 Simplicity Criterion

**做什么**：
在 PROTOCOL.md 中明确加入简化准则：
- 如果一个改动删代码且验证通过 → 必须保留（简化胜利）
- 如果一个改动加了 20 行但只带来微小改善（score 下降 < 阈值）→ 撤回
- "更简单的代码 + 同样效果" 永远优先于 "更复杂的代码 + 微小改善"

**为什么**：
防止 Agent 在无限循环中堆砌复杂度。autoresearch 的这个设计直接解决了 Ralph Loop 的"过度烘焙"问题。

**如何量化**：
- 改动行数：`git diff --stat`（新增行数 vs 删除行数）
- 效果：verify.sh 的 score 差值
- 判定规则：`新增行数 > 10 且 score 改善 < 0.01` → 自动 discard

**风险**：低。只是增加一条评估规则，不影响现有功能。

---

### 变更 5：NEVER STOP 模式（可选）

**做什么**：
增加一种"永不停止"的运行模式。Agent 不问人类"要不要继续"，一直跑到被手动中断。

区别于现有的 MAX_ITERATIONS=20 安全上限：
- 默认模式：MAX_ITERATIONS 保护（和现在一样）
- NEVER STOP 模式：无上限，人类手动中断

**为什么**：
autoresearch 的核心体验是"人类睡觉，Agent 跑 100 次实验"。但这个模式必须配合"只读评估器"（变更 2）才能安全。没有只读评估器的 NEVER STOP 是危险的。

**前提条件**：
- 变更 2（verify.sh）必须先完成
- 变更 4（Simplicity Criterion）必须先完成
- 有明确的成本预估（每次迭代的 API 成本）

**风险**：高。无限制循环意味着无限制成本。必须配合严格的成本控制。

---

## 四、变更依赖关系

```
变更 1（拆分 SKILL.md）   ← 独立，可先做
变更 2（verify.sh）       ← 独立，可先做
变更 3（简化 state.json） ← 依赖变更 1（新结构需要 PROTOCOL.md）
变更 4（Simplicity）      ← 依赖变更 2（需要 score 来量化）
变更 5（NEVER STOP）      ← 依赖变更 2 + 4（必须先有可信评估）
```

**建议实施顺序**：1 → 2 → 4 → 3 → 5

---

## 五、不变的部分

以下内容在 v3 中保持不变：
- 两种运行模式（执行者/自主者）的概念
- ralph-loop.sh 作为执行引擎（但会简化）
- 每次迭代全新上下文的核心设计
- git 作为代码版本管理
- 三要素公式（范围 + 证据 + 测试）用于定义完成条件

---

## 六、需要讨论的决策点

### D1：journal 要不要保留？

autoresearch 不需要 journal，但我们的任务可能更复杂。选项：
- A) 完全砍掉，用 results.tsv + git log 替代
- B) 保留但精简（只记 action + result，砍掉 reason/learned/nextFocus）
- C) 保留但移到 git commit message 中（`git commit -m "action | result | score"`）

**我的建议**：B。精简到一句话，不要 v2 那种 7 个字段的 journal 条目。

### D2：verify.sh 的 score 标准化

autoresearch 只看 val_bpb（越小越好）。我们是否需要统一方向？
- A) 统一为"越小越好"（0 = 完美，类似 loss）
- B) 统一为"越大越好"（1 = 完美，类似 accuracy）
- C) 不统一，verify.sh 自定义方向，但在输出中标注

**我的建议**：A。"越小越好"在实验循环中更直观（看数字下降就知道在进步）。

### D3：shell 脚本是否继续维护？

ralph-loop.sh 用 bash 维护 JSON 是脆弱性的根源。选项：
- A) 继续用 bash + python3（和现在一样，但精简 state.json）
- B) 用 Python 重写核心引擎
- C) 直接用 OpenClaw 的 goal_launch（原生支持 Ralph Loop）

**我的建议**：先 A，如果 state.json 精简后还是频繁出问题，再考虑 B 或 C。

### D4：执行者模式 vs 自主者模式是否保留区分？

autoresearch 只有一种模式（自主实验）。选项：
- A) 保留两种模式
- B) 合并为一种模式（更接近 autoresearch）
- C) 保留概念但简化区分（去掉自主者模式的 awaiting_approval 暂停点）

**我的建议**：A。执行者模式在很多场景下够用，砍掉会损失现有用户。

---

## 七、版本规划

如果决定推进：
- v3.0.0：变更 1 + 2（拆分文件 + verify.sh）
- v3.1.0：变更 4（Simplicity Criterion）
- v3.2.0：变更 3（简化 state.json）
- v4.0.0：变更 5（NEVER STOP，如果决定做）

---

## 八、参考资料

- autoresearch program.md: https://github.com/karpathy/autoresearch/blob/master/program.md
- autoresearch README: https://github.com/karpathy/autoresearch
- Geoffrey Huntley Ralph Loop: https://ghuntley.com/loop/
- OpenClaw goal_launch: 原生 Ralph Loop 支持
