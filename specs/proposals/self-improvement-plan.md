# Agent Factory 自我改进机制落地方案

> 2026-04-28 | 基于行业调研 + 工厂现状分析

---

## 一、现状诊断

当前工厂有 **3 套自我改进设计**，全部未落地：

| 设计 | 位置 | 状态 |
|------|------|------|
| HEARTBEAT 经验检查 | HEARTBEAT.md Step 2-3 | 仅检查文件时间戳，从不写入 |
| FIP-001-R 经验沉淀 | AGENTS.md | 定义了读写规则，但从未触发 |
| corrections/patterns | _runtime/experience/ | 4月8日初始化后无任何记录 |

唯一有实际内容的文件是 `LESSONS.md`（1条GLM-5.1失控事件记录）和 `RULES.md`（协作规则索引），但这俩是人工维护的，不是自动化产出。

## 二、参考方案评估

调研了 ClawHub 5个 Skill + GitHub 6个项目，提取出可借鉴的设计模式：

| 模式 | 来源 | 我们是否需要 |
|------|------|-------------|
| **search-before-log**（写前查重） | actual-self-improvement | ✅ 需要，避免重复记录 |
| **decision table**（什么情况记录什么） | actual-self-improvement | ✅ 需要，过滤噪音 |
| **session-lifecycle**（启动读 → 执行中自检 → 关闭写） | self-improvement-system | ✅ 需要，但适配为 sub-agent lifecycle |
| **promotion**（重复经验提升为规则） | actual-self-improvement | ⚠️ 后续迭代，首版不做 |
| **privacy filter**（不记录用户数据） | self-improvement-system | ✅ 需要 |
| **归档机制**（超量自动归档） | self-improvement-system | ⚠️ 后续迭代 |

## 三、落地方案

### 核心原则

1. **只改必须改的** — 不新增文件，复用现有 _runtime/experience/ 目录
2. **触发点最小化** — 只在 sub-agent 完成时写入，不在心跳中做任何操作
3. **质量优于数量** — 只记录值得记录的（有 decision table 过滤）
4. **写入极简** — 一条经验不超过150字，但必须包含否定决策

### 改动清单

#### 改动1：清理 HEARTBEAT.md

删除 Step 2-3（经验沉淀检查），只保留 Step 1（Sub-Agent 状态检查）。

**原因**：心跳不应该负责经验管理。心跳的职责是监控运行状态，不是管理知识库。

#### 改动2：重写 _runtime/experience/EXPERIENCE.md

清空现有内容，写入干净的模板和 seed 数据。

**文件结构**（只保留1个文件）：
```
_runtime/experience/EXPERIENCE.md
```

废弃 corrections.md、patterns.md、corrections-self-improving.md、patterns-self-improving.md — 这些文件从未被真正使用，造成混淆。

**EXPERIENCE.md 格式**（沿用 FIP-001-R，微调）：
```markdown
## [日期] [类型] [一句话摘要]
- **决策**：选了什么，没选什么，为什么
- **前车之鉴**：下次遇到同类问题应该怎么做
- **上下文**：项目ID、技术栈、环境等关键前提
```

**类型枚举**：
- `[技术]` — 工具/平台/API 的非显而易见的行为
- `[流程]` — 工作流的优化或踩坑
- `[决策]` — 方案选择的否定式记录（"没选X因为Y"）

**Decision Table**（什么情况写）：

| 情况 | 写不写 |
|------|--------|
| 纠正了一个错误假设 | ✅ 写 |
| 发现了项目特有的约定/规则 | ✅ 写 |
| 做了真正的调试/排查（>10分钟） | ✅ 写 |
| 做了否定式决策（"没选X因为Y"） | ✅ 写 |
| 同类问题出现第2次 | ✅ 写 |
| 明显的拼写错误/预期内的验证失败 | ❌ 不写 |
| 立刻就解决了的小问题 | ❌ 不写 |
| 例行的文件创建/提交 | ❌ 不写 |

#### 改动3：更新 AGENTS.md 的 spawn 规则

在 sub-agent spawn 规则中加入两条：

**启动时注入**（已有框架，细化执行）：
```
读取 _runtime/experience/EXPERIENCE.md 最近5条，在 task 中注入：
"工厂经验：[最近5条摘要]"
```

**完成时写入**（已有框架，细化条件）：
- Sub-agent 完成 + 以下任一条件满足时写入：
  1. 任务耗时 >10 分钟
  2. 过程中遇到过阻塞/回退/重试
  3. 做了否定式决策
  4. Evan 明确说"记住这个"
- 写入前先读 EXPERIENCE.md，检查是否已有同类记录
- 如有同类：更新已有条目，不新增
- 如无同类：追加到文件顶部（最新在前）

#### 改动4：写入 seed 数据

从过去几天的实际工作中提取 3-5 条有价值的经验，作为初始 seed：

1. Claude Code 长任务必须 background:true，yieldMs 导致 SIGKILL
2. Codex 必须用 --dangerously-bypass-approvals-and-sandbox（不加 --full-auto）
3. macOS cp 不支持 --parents，用 rsync 替代
4. exec preflight 限制复杂 Python 命令，需写 bash 脚本中转
5. SPBP 执行模型是 Funnel（线性收敛）+ Iterative（循环优化），两者不冲突

### 不做的事

| 项 | 原因 |
|------|------|
| 新增 Python 脚本管理经验 | 不引入新依赖，Agent 直接读写 Markdown 即可 |
| heartbeat 驱动经验管理 | 心跳只管监控，不管知识库 |
| promotion 机制（经验→规则→Skill） | 后续迭代 |
| 归档机制 | 后续迭代（当前记录量远未达到需要归档的程度） |
| 多文件分类存储 | 单文件 EXPERIENCE.md 足够，保持简单 |

## 四、执行步骤

1. 清理 HEARTBEAT.md（删 Step 2-3） — 2分钟
2. 清理 _runtime/experience/（废弃多余文件） — 2分钟
3. 创建 EXPERIENCE.md（模板 + seed数据） — 5分钟
4. 更新 AGENTS.md spawn 规则 — 5分钟
5. 验证：手动触发一次 sub-agent，确认经验注入和写入 — 5分钟

**总耗时：约20分钟**

## 五、验证标准

落地后，以下场景应能正常工作：

1. ✅ spawn sub-agent 时，task 中包含"工厂经验：[最近5条]"
2. ✅ sub-agent 完成后（满足写入条件），EXPERIENCE.md 新增一条
3. ✅ 同类经验不重复（查重机制生效）
4. ✅ 心跳不再报"经验沉淀异常"
5. ✅ 每周至少有 2-3 条新记录（通过正常工作自然产出，不靠人工催促）

---

_方案结束。Evan 确认后开始执行。_
