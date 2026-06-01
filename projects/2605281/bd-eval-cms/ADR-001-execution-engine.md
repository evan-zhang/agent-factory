# ADR-001: 执行引擎架构 — Ralph Loop 集成方案

> **状态**: DRAFT（草稿）
> **作者**: 造物（Agent Factory Orchestrator）
> **日期**: 2026-05-31
> **等待**: 第 1 批 4 个品种执行数据 + Evan 审批

---

## 一、背景

bd-eval-cms Skill 当前执行方式：Orchestrator spawn 子 Agent，子 Agent 一次性跑完 Phase 1-5.5（60-80 分钟/品种）。

**已识别问题**：
1. 子 Agent 内部无自愈能力——某 Phase 失败不会自动修正
2. 60-80 分钟长任务，模型可能超时或上下文溢出
3. 断点续执行依赖 Orchestrator 临时逻辑，未标准化
4. 模型失败无自动回退机制

## 二、方案对比

### 方案 A：当前方式（Orchestrator + spawn）

```
Orchestrator → spawn 子Agent（品种级）→ 一口气跑 Phase 1-5.5
```

| 维度 | 评估 |
|------|------|
| 并发能力 | ✅ 品种级可并发（4 个同时） |
| 自愈能力 | ❌ 无，失败即停 |
| 断点续跑 | ⚠️ 依赖 Orchestrator 临时逻辑 |
| 复杂度 | 低 |
| 上下文风险 | 高（单次 60-80 分钟，token 累积） |

### 方案 B：纯 Ralph Loop

```
Orchestrator → goal_launch（单品种）→ Loop 直到完成
```

| 维度 | 评估 |
|------|------|
| 并发能力 | ❌ 单 Loop 串行（不能 goal_launch 多个品种并行） |
| 自愈能力 | ✅ 每轮 verify，不通过自动修正 |
| 断点续跑 | ✅ 天然支持（goal 不变，下次继续） |
| 复杂度 | 中 |
| 上下文风险 | 低（每轮只跑一个 Phase） |

### 方案 C：混合模式（推荐）

```
Orchestrator（品种级并发 spawn）
  └── 子Agent（单品种）
        └── Phase 1 → verify → 失败则重试（换模型）
        └── Phase 2 → verify → ...
        └── Phase 3 → verify → ...
        └── Phase 5.5 → verify → 完成
```

| 维度 | 评估 |
|------|------|
| 并发能力 | ✅ 品种级可并发 |
| 自愈能力 | ✅ Phase 级 verify + 重试 |
| 断点续跑 | ✅ 每个 Phase 完成即持久化 |
| 复杂度 | 中 |
| 上下文风险 | 低（按 Phase 拆分，每个 Phase 独立） |

## 三、方案 C 详细设计

### 3.1 执行流程

```
Orchestrator 接到评估请求
  │
  ├─ 检查 _runtime/batch-progress.json → 是否有未完成品种？
  │   ├─ 有 → 从断点继续
  │   └─ 无 → 创建新品种
  │
  ├─ 为每个品种 spawn 子 Agent（最多 4 个并发）
  │   │
  │   └─ 子 Agent 内部执行：
  │       │
  │       ├─ Phase 1 Discovery
  │       │   ├─ 执行搜索 + 分析
  │       │   ├─ 写入 01-discovery.md
  │       │   ├─ 创建 state.json (phase="discovery_complete")
  │       │   └─ verify: 01-discovery.md 存在 + state.json 正确
  │       │       ├─ PASS → 继续
  │       │       └─ FAIL → 重试（最多 2 次，换模型）
  │       │
  │       ├─ Phase 2 路由
  │       │   ├─ D-0 路由 + Battle
  │       │   ├─ 写入 battle/ROUTE-SELECTION-AUDITOR.md
  │       │   ├─ 更新 state.json
  │       │   └─ verify
  │       │
  │       ├─ Phase 3 Gate 评估（内部并行）
  │       │   ├─ One-pager → verify
  │       │   ├─ Gate 1-3 并行 → 各自 verify
  │       │   ├─ Gate 4-5 并行 → 各自 verify
  │       │   └─ Gate 6 串行 → verify
  │       │
  │       ├─ Phase 4 Battle
  │       │   └─ verify
  │       │
  │       ├─ Phase 5 合并 + 执行摘要
  │       │   └─ verify: 报告行数 ≥ 源文件 × 95%
  │       │
  │       └─ Phase 5.5 HTML 生成
  │           └─ verify: REPORT.html 存在 + 无残留模板变量
  │
  └─ 全部品种完成后汇报
```

### 3.2 Verify 规则

| Phase | 验证条件 | 类型 |
|-------|---------|------|
| Phase 1 | `01-discovery.md` 存在 + 行数 ≥ 50 + `state.json` phase="discovery_complete" | 文件 + 内容 |
| Phase 2 | `battle/ROUTE-SELECTION-AUDITOR.md` 存在 + `state.json` 含 `routingDecision` + `routedSkill` 非"待路由" | 文件 + 状态 |
| Phase 3 | `02-gate-by-chapter/` 下 One-pager + Gate 1-6 共 7 个文件全部存在 + 每个 ≥ 100 行 | 文件 + 体量 |
| Phase 4 | `03-battle-summary.md` 存在 + `battle/BATTLE-R1-AUDITOR.md` 存在 | 文件 |
| Phase 5 | `04-final-report.md` 存在 + 行数 ≥ 源文件总行数 × 0.95 | 文件 + 完整性 |
| Phase 5.5 | `REPORT.html` 存在 + `grep -c '{{' REPORT.html` = 0 | 文件 + 质量 |

### 3.3 失败重试规则

```
Phase verify 失败
  │
  ├─ 第 1 次重试：
  │   ├─ 重新执行该 Phase
  │   ├─ 使用相同模型
  │   └─ 记录到 execution-log.md
  │
  ├─ 第 2 次重试：
  │   ├─ 切换到 fallback 模型
  │   └─ 记录到 execution-log.md
  │
  └─ 2 次重试仍失败：
      ├─ 暂停该品种
      ├─ 更新 state.json phase = "error"
      ├─ 记录失败原因
      └─ 通知 Orchestrator → 通知用户
```

### 3.4 模型 Fallback Chain

```
主力: evan-openai/glm-5.1
  ↓ 超时/报错
回退 1: evan-openai/MiniMax-M2.7-highspeed
  ↓ 超时/报错
回退 2: evan-openai/deepseek-v4-flash
  ↓ 超时/报错
回退 3: evan-openai/deepseek-v4-pro
  ↓ 仍然失败
暂停，报告用户
```

### 3.5 断点续执行

**场景 1：子 Agent 中途崩溃**
- 每个 Phase 完成后 state.json 已持久化
- Orchestrator 读 state.json，找到当前 phase
- 重新 spawn，指令为"从 Phase X 继续"

**场景 2：整个 session 断了（隔天）**
- `_runtime/batch-progress.json` 记录全局进度
- 启动时扫描所有品种目录的 state.json
- 识别 phase ≠ "report_finalized" 的品种
- 从断点处重新 spawn

**场景 3：某品种 Phase 3 跑了 Gate 1-3 后挂了**
- Gate 1-3 文件已存在于磁盘
- state.json phase = "evaluation"（或 "discovery_complete" 取决于更新时机）
- Orchestrator 检查 02-gate-by-chapter/ 目录，发现 Gate 1-3 已完成
- spawn 时指令为"Gate 1-3 已完成，从 Gate 4 开始"

### 3.6 执行日志格式

每个品种的 `execution-log.md` 增强为：

```markdown
## Phase 1 DISCOVERY
- 开始时间: 2026-05-31 14:00:00
- 结束时间: 2026-05-31 14:08:23
- 耗时: 8min 23s
- 模型: evan-openai/glm-5.1
- Token: 输入 12,340 / 输出 3,567
- 工具调用: web_search ×5, web_fetch ×3
- 搜索次数: 5
- 失败重试: 0
- Verify: PASS

## Phase 3 Gate 评估 — Gate 1
- 开始时间: ...
- 结束时间: ...
- 耗时: ...
- 模型: ...
- Token: ...
- 工具调用: ...
- 失败重试: 1（第 1 次 verify 失败：结论卡缺失，自动修正后通过）
- Verify: PASS（第 2 次尝试）
...
```

## 四、风险审计

### 4.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 模型上下文溢出（单 Phase token 过多） | 中 | Phase 失败 | Phase 3 每个 Gate 独立 spawn，单 Gate 上下文可控 |
| 死循环（verify 反复失败） | 低 | 浪费 token | max_retries = 2，超过暂停 |
| 文件锁冲突（并发品种写同一文件） | 极低 | 文件损坏 | 每个品种独立目录，无共享写文件 |
| 并发竞态（4 个品种同时搜索同一主题） | 低 | 搜索结果重复 | 可接受，不影响正确性 |
| Ralph Loop 嵌套 spawn 限制 | 待确认 | Phase 内部无法再 spawn | 需要测试 OpenClaw 的嵌套 spawn 深度限制 |

### 4.2 边界条件

| 场景 | 处理方式 |
|------|---------|
| OTC 品种（如滴眼液）Gate 评估内容少 | Skill 已有 B 系列技能定义，Gate 体量自然小 |
| Gate 6 结论为"停止" | 按 SOP 8.3 处理：输出停止评估报告，Phase 4-5 不执行 |
| Battle 争议无法解决 | 按 SOP 8.2 处理：提交用户裁定 |
| 品种信息极度匮乏 | Discovery 置信度低，Phase 3 标注 D 级 |
| 子 Agent 在 Phase 3 中途超时（Gate 3 跑了 20 分钟没完） | Orchestrator 15 分钟超时检测，kill 后从断点续 |

### 4.3 成本估算

| 项目 | 估算 |
|------|------|
| 单品种 token 消耗（无重试） | ~80-120k（输入 ~60-90k + 输出 ~20-30k） |
| 单品种 verify 额外消耗 | ~5-10k/Phase × 6 Phase = ~30-60k |
| 重试额外消耗（假设 1 个 Phase 重试 1 次） | ~15-25k |
| 10 个品种总 token（含 verify + 重试） | ~1.1-1.8M |
| 执行时间（4 并发） | ~3-4 小时 |

### 4.4 与现有 Skill 的兼容性

| 改动范围 | 文件 | 改动内容 |
|---------|------|---------|
| SOP.md | 新增"执行引擎"章节 | verify 规则 + 重试规则 + fallback chain |
| SKILL.md | 更新"执行日志"章节 | 增强日志格式 |
| state.json | 新增 phase 值 | "error" 状态 |
| execution-log.md | 格式增强 | 新增 token、模型、工具调用、重试记录 |
| _runtime/batch-progress.json | 新增文件 | 全局进度跟踪 |

**不需要改动的部分**：
- Phase 1-5.5 的业务逻辑完全不变
- 19 个技能定义文件不变
- Gate 结论卡格式不变
- 报告合并脚本不变
- HTML 生成脚本不变

## 五、待确认事项

1. **OpenClaw 嵌套 spawn 深度**：子 Agent 内部能否再 spawn（Phase 3 并行 Gate）？需要测试
2. **第 1 批执行数据**：等 4 个品种跑完，拿实际失败率、耗时、token 数据校准方案
3. **verify 颗粒度**：Phase 级 vs Gate 级？Phase 级更简单，Gate 级更精细
4. **max_retries 数值**：2 次 vs 3 次？取决于第 1 批数据
5. **并发上限**：4 个 vs 更多？取决于模型 API 限流

## 六、决策时间线

1. **现在 → 第 1 批完成**：收集执行数据
2. **第 1 批完成后**：用数据校准方案，出正式版 ADR
3. **Evan 审批后**：写入 SOP.md + SKILL.md，第 2 批用新架构执行
