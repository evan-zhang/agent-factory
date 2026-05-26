---
archive: K-260508-002
source: unknown
created_at: 2026-05-08T13:37:02.654668
tags: []
---
# PRD：Instinct 持续学习 OpenClaw Skill

## 项目名称

`instinct-learner` — OpenClaw 的会话经验自动提取与复用 Skill

## 背景

Everything Claude Code (ECC, 175K Stars) 有一个 Instinct 持续学习系统：Agent 在每次会话中自动提取行为模式，形成带置信度评分的"本能"，可跨会话复用、演化成 Skill、导入导出。

OpenClaw 目前有 Memory 系统（MEMORY.md + memory/*.md），但是**手动维护**的。缺少自动化的"从会话中学习"机制。

本 Skill 的目标：**用 OpenClaw 的 Hook + 脚本实现类似 ECC Instinct 的自动化持续学习**。

---

## 核心概念

### Instinct（本能）

一个 Instinct 是一条从会话经验中提取的结构化学习记录：

```yaml
---
id: instinct-20260508-001
created: 2026-05-08T13:00:00+08:00
confidence: 0.85       # 0-1，使用次数越多、验证越多则越高
times_used: 5          # 被实际参考的次数
times_validated: 4     # 参考后效果良好的次数
last_used: 2026-05-08T20:00:00+08:00
tags: [memory-search, embedding, ollama]
status: active         # active | dormant | expired
---

## 触发条件
当 memory_search 失败（embedding 服务不可用）时

## 行动建议
回退到 grep + 文件时间排序作为本地搜索降级方案，
不要直接告诉用户"记忆不可用"

## 证据
- 2026-05-08: memory_search 挂了，用 grep 找到了相关文件，用户满意
- 2026-05-07: 类似情况，也用了 grep 降级
```

### Instinct 生命周期

```
会话结束 → Hook 触发提取 → 写入 instinct/*.md → 下次会话加载 → 
命中触发条件 → 参考执行 → 验证成功/失败 → 更新 confidence
→ 达到阈值 → 演化成 Skill
```

---

## 功能需求

### F1：自动提取（Hook 触发）

**触发时机**：`afterResponse`（每次 Agent 回复后）或 `heartbeat`（心跳时）

**实现方式**：Python 脚本 `scripts/extract_instinct.py`

**输入**：当前会话的最近 N 轮对话（通过 stdin 传入 JSON）

**逻辑**：
1. 分析最近 N 轮对话中是否有"值得记住"的模式
2. "值得记住"的判断标准：
   - 用户纠正了 Agent 的错误 → 记录"不要做 X"
   - Agent 尝试了某个方法失败后换了一个成功的方法 → 记录"方法 A 失败时用方法 B"
   - Agent 自己发现了某个有用的模式 → 记录"在 Y 场景下用 Z"
   - 用户给出了明确的偏好/规则 → 记录偏好
3. 如果有新的学习点，生成一个 Instinct 文件写入 `instincts/YYYY-MM-DD-{NNN}.md`

**输出**：Instinct 文件（YAML frontmatter + Markdown body）

**约束**：
- 每次提取最多生成 1 个 instinct（避免膨胀）
- 提取逻辑用 LLM 还是规则？建议用**简单的关键词+模式匹配**，不依赖额外 LLM 调用（省 token）
- 如果没有值得提取的内容，不生成任何文件

### F2：会话加载（注入到上下文）

**触发时机**：`beforePromptBuild`（每次 Agent 处理消息前）

**实现方式**：Python 脚本 `scripts/load_instincts.py`

**逻辑**：
1. 读取 `instincts/` 目录下所有 active 状态的 instinct
2. 按与当前用户消息的相关性排序（简单的关键词/标签匹配）
3. 取 Top-K（默认 K=5）个 instinct
4. 格式化为 Markdown 注入到 Hook 输出中

**输出格式**：
```markdown
## 🧠 Active Instincts (相关度最高的 5 条)

1. **[memory-search 降级]** 当 memory_search 失败时，用 grep + 文件时间排序降级（置信度 0.85，使用 5 次）
2. **[Link Archivist 完整性]** 处理链接后必须确认已同步到 Obsidian（置信度 0.9，使用 3 次）
...
```

**约束**：
- Top-K 默认 5，不超过 10（控制 token 消耗）
- 只加载 active 状态的 instinct
- 如果没有匹配的 instinct，不注入任何内容（不要浪费 token）

### F3：验证与置信度更新

**触发时机**：`afterResponse`（Agent 回复后）

**实现方式**：Python 脚本 `scripts/validate_instinct.py`

**逻辑**：
1. 检查本次回复是否参考了某个 instinct
2. 如果参考了：
   - `times_used += 1`
   - `last_used = now()`
   - 如果用户没有纠正/不满意 → `times_validated += 1`，`confidence = min(1.0, confidence + 0.05)`
   - 如果用户纠正了 → `confidence = max(0.0, confidence - 0.1)`
3. 写回 instinct 文件的 YAML frontmatter

### F4：清理过期 Instinct

**触发时机**：`heartbeat`（心跳时，低频执行）

**实现方式**：Python 脚本 `scripts/prune_instincts.py`

**规则**：
- 30 天未使用 → `status: dormant`
- 60 天未使用 → `status: expired`
- confidence < 0.3 且 times_used > 5 → `status: expired`（反复验证失败的）
- expired 文件移动到 `instincts/archived/`

### F5：状态查看（CLI）

**命令**：`python3 scripts/instinct_status.py`

**输出**：
```
Instinct 状态概览
=================
总计: 12 条 active, 3 条 dormant, 5 条 archived

Top 5 高置信度:
1. [memory-search 降级] 置信度 0.95 (使用 12 次)
2. [Link Archivist 完整性] 置信度 0.90 (使用 8 次)
...

最近 5 条:
1. [subagent 回传] 2026-05-08 置信度 0.60
2. ...
```

---

## 目录结构

```
skills/instinct-learner/
├── SKILL.md                          # Skill 定义（触发规则、工作流）
├── scripts/
│   ├── extract_instinct.py           # F1: 自动提取
│   ├── load_instincts.py             # F2: 加载注入
│   ├── validate_instinct.py          # F3: 验证更新
│   ├── prune_instincts.py            # F4: 清理过期
│   └── instinct_status.py            # F5: 状态查看
├── instincts/                        # Instinct 存储目录（自动创建）
│   └── archived/                     # 过期 instinct
├── config.json                       # 配置文件
└── references/
    └── ecc-instinct-analysis.md      # ECC Instinct 系统的参考分析
```

---

## OpenClaw Hook 配置

需要在 OpenClaw 的 agent hooks 中添加以下配置：

```json5
{
  hooks: {
    beforePromptBuild: [
      {
        command: "python3 ${workspace}/skills/instinct-learner/scripts/load_instincts.py",
        timeout: 5000
      }
    ],
    // 注意：OpenClaw 目前可能不支持 afterResponse hook
    // 如果不支持，降级为 heartbeat 触发提取
  }
}
```

**降级方案**：如果 `afterResponse` hook 不可用，把 F1（提取）和 F3（验证）合并到 **heartbeat** 中执行——每次心跳时检查最近会话记录，提取新 instinct。

---

## 配置项

```json
{
  "max_instincts_load": 5,       // 每次加载的最大 instinct 数
  "confidence_threshold": 0.3,   // 低于此值标记为 expired
  "dormant_days": 30,            // 多少天未使用变为 dormant
  "expired_days": 60,            // 多少天未使用变为 expired
  "max_active_instincts": 50,    // 最大 active instinct 数
  "extraction_mode": "keyword"   // keyword | llm（提取方式）
}
```

---

## 约束与边界

1. **不依赖额外 LLM 调用**——提取逻辑用关键词匹配，不调用 API（省 token 省钱）
2. **Token 预算**：每次注入不超过 500 tokens（约 5 个 instinct 的摘要）
3. **幂等性**：同一模式不重复创建 instinct（按内容 hash 去重）
4. **不与现有 Memory 冲突**——instinct 是 Memory 的补充，不是替代。instinct 存自动提取的模式，Memory 存手动维护的长期知识
5. **不与 HEARTBEAT.md 冲突**——heartbeat 中的 memory 维护是手动操作，instinct 是自动操作

---

## 参考实现

ECC 的 Instinct 系统相关文件路径（需要 clone 仓库查看）：
- `skills/continuous-learning-v2/` — Instinct 的 Skill 定义
- `commands/instinct-status.md` — 状态查看命令
- `commands/instinct-import.md` — 导入命令
- `commands/instinct-export.md` — 导出命令
- `commands/evolve.md` — 演化成 Skill
- `commands/prune.md` — 清理命令

---

## 验收标准

1. ✅ 安装后，Agent 每次会话自动加载相关 instinct
2. ✅ 会话中发现新模式时自动创建 instinct 文件
3. ✅ Instinct 被参考后自动更新置信度
4. ✅ 过期 instinct 自动清理
5. ✅ `instinct_status.py` 可正常查看状态
6. ✅ 不增加每次会话超过 500 tokens 的额外消耗
7. ✅ 不依赖额外 API 调用
8. ✅ 与现有 Memory 系统共存不冲突
