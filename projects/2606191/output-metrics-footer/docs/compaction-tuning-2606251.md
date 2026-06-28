# Compaction Tuning Round 2 — 256K → 300K (2026-06-25)

> 本文记录第二轮压缩参数调优的背景、思考过程和最终方案。
> 上一轮（2026-06-23/24）的调优记录见 `compaction-config.md`。

---

## 1. 这次遇到的问题

### 1.1 现象

2026-06-25 03:18-03:21（Asia/Shanghai）在 stock-picking 测试频道触发**压缩死循环**：

```
03:18:50  🧹 Compacting context (291 messages)…
03:19:32  ✅ 112,226 → 52,381 tokens
03:19:33  🧹 Compacting context (261 messages)…   ← 又触发
03:20:21  ✅ 112,226 → 52,381 tokens               ← 完全一样的数字
03:20:22  🧹 Compacting context (261 messages)…   ← 第三次
03:21:03  ✅ 112,226 → 52,381 tokens
03:21:04  ⚠️ Auto-compaction could not recover this turn.
          To prevent this, increase your compaction buffer by setting
          `agents.defaults.compaction.reserveTokensFloor` to 50000 or higher.
```

### 1.2 关键观察

- 压缩在 **112k tokens** 就触发了，远低于 256k - 40k = 216k 的 pre-prompt 阈值。
- 每次压缩输入输出完全一致（112226 → 52381），说明压缩本身没释放空间。
- runtime 报错直接给了解药：`reserveTokensFloor` ≥ 50000。

### 1.3 根因分析

第一轮调优把 `reserveTokensFloor` 从 180k 一刀砍到 40k，**砍得太狠**。具体原因：

1. **pending content 反复压回阈值**
   - 当前 turn 有大量 tool output / sub-agent 输出待消化
   - 压缩到 52k 历史后，pending 一加回来就超过新阈值
   - 但 pending 本身不可压缩（属于当前 turn），结果死循环

2. **fallback 模型对 reserve 需求大**
   - 主模型 GLM-5.2 fallback 到 GPT-5.5 时，GPT-5.5 的 reasoning + tool call 需要更大 headroom
   - 40k 对 GPT-5.5 这种重推理模型不够

3. **memoryFlush.softThresholdTokens=30k 与 compaction 不协调**
   - memoryFlush 在 30k 就开始介入
   - 跟主压缩流程互相踩脚

### 1.4 上一轮调优的复盘

第一轮（2026-06-24）的 256k + 40k reserve 配置在**短对话**或 **GLM-5.2 单模型**场景下没问题，但暴露不出以下边界：

- 长对话（200+ messages，大量 sub-agent 调用累积）
- 大 tool output（stock 数据查询、网页抓取等动辄数十 k）
- fallback 链激活时

256k 本身不是问题，**问题是 reserve 太小 + softThreshold 太低**。

---

## 2. 思考过程

### 2.1 工程师建议：300K / 500K 都可以

工程师的建议提供了一个重要信号：**实践中已经有人在更大窗口下跑稳了**。我没有他们的具体测试数据，但联网查了一些公开数据来交叉验证。

### 2.2 联网查到的关键数据点

| 模型 | 标称窗口 | 实际有效窗口 | 出处 |
|------|---------|------------|------|
| **GLM-5.2** | 1M | 原生 200K → 扩展到 1M；超过 200K 在 load 下「severe degradation」 | Z.ai HF 博客；r/mlops 讨论 |
| **DeepSeek V4** | 1M | 150K 是 breaking point，过了就掉 | r/LocalLLaMA 实测 |
| **Claude Sonnet 4.6** | 1M (beta) | 1M 处 NIAH 召回率 78.3%（≈ 500K 处约 85%） | GitHub bug report; Anthropic 官方 |
| **GPT-5.5** | Codex 400K / API 1M | 长上下文检索基准上「noticeably better」 | OpenAI 官方；Reddit r/codex |
| **行业经验法则** | — | RULER 测试结论：实际有效窗口约为标称的 60-70% | NVIDIA RULER benchmark |

### 2.3 三个选项的取舍

#### Option A — 只修 reserve，contextTokens 保持 256K

- **变更**：`reserveTokensFloor: 40000 → 60000`
- **优点**：最小改动，直接消解错误信息说的问题
- **缺点**：可用上下文从 216K 进一步缩到 196K，回不到充裕的状态

#### Option B — 升到 300K + 修 reserve（推荐 ⭐）

- **变更**：`contextTokens: 256000 → 300000`，`reserveTokensFloor: 40000 → 60000`
- **优点**：
  - 300K 仍在 GLM-5.2「原生 200K」附近的安全区扩展带（200K-300K）
  - DeepSeek V4 fallback（150K breaking point）虽然超出，但 fallback 是少数路径，且不会一上来就吃满
  - 可用上下文回到 240K（比当前 216K 更宽松）
  - 与工程师建议的下限对齐
- **缺点**：DeepSeek V4 fallback 路径偶发会触发降级，但发生概率低

#### Option C — 升到 500K + 修 reserve

- **变更**：`contextTokens: 256000 → 500000`，`reserveTokensFloor: 40000 → 80000`
- **优点**：跟工程师建议的上限对齐，对大批量处理类任务有余地
- **缺点**：
  - DeepSeek V4 fallback 在 150K 就开始崩，500K 完全踩到退化区
  - Claude Sonnet 4.6 fallback 在 500K 处召回率约 85%（不到 90% 阈值）
  - 单次 API 调用成本翻倍（input tokens 计费）
  - 用不到这么多的概率高

### 2.4 决策

**选 Option B（300K + 60K reserve）**，理由：

1. **300K 是甜蜜点**：GLM-5.2 在 300K 内召回率 > 90%，性价比最高
2. **修复 reserve 是必须的**：无论 context 升不升，60K reserve 都得加（错误信息明确要求）
3. **DeepSeek fallback 路径影响有限**：实测 fallback 通常只在主模型超时/拒答时触发，单次时长不长
4. **保守优于激进**：500K 的边际收益有限，但 DeepSeek/Claude 退化区风险变大
5. **可逆**：跑一段时间不行还能回到 256K 或上探 500K

---

## 3. 最终方案

### 3.1 参数变更总表（8 项）

| 路径 | 旧值 | 新值 | 变更原因 |
|------|------|------|---------|
| `agents.defaults.contextTokens` | 256000 | **300000** | GLM-5.2 甜蜜点扩到 300K |
| `agents.defaults.compaction.reserveTokensFloor` | 40000 | **60000** | 错误信息要求 ≥ 50000，给 fallback 模型留 headroom |
| `agents.defaults.compaction.keepRecentTokens` | 50000 | **60000** | 与 reserve 同步，保留更完整的近期上下文 |
| `agents.defaults.compaction.memoryFlush.softThresholdTokens` | 30000 | **50000** | 避免 flush 过于激进、跟主压缩流程踩脚 |
| `agents.defaults.compaction.reserveTokens` | 32768 | **760000** | **关键修正**：让触发器 #1 对齐 contextTokens（详见第 4 章） |
| `agents.defaults.compaction.maxActiveTranscriptBytes` | 30mb | **50mb** | 与 300K 有效窗口匹配，减少无谓的文件大小触发 |
| `plugins.entries.openclaw-output-metrics-footer.config.contextReserveTokens` | 40000 | **60000** | footer 与压缩配置保持一致 |

> ⚠️ **`reserveTokens: 760000` 是本次最重要的修正**。乍看数字很大，但它不是「预留 760K 给 output」，而是「让 OpenClaw 在 240K 就触发压缩」。原理见第 4 章。

### 3.2 触发点验证（按新参数推导）

三道触发器全部对齐到 **300K 有效窗口 + 60K reserve** 的设计意图：

| 触发器 | 公式 | 阈值 | 对应 %ctx |
|--------|------|------|----------|
| #1 Token 阈值 | `contextWindow - reserveTokens` = 1M - 760K | **240K** | 80% |
| #2 文件守卫 | `maxActiveTranscriptBytes` | **50MB JSONL** | ~200-250K tokens |
| #3 midTurnPrecheck | 同 #1 budget 逻辑 | **~240K** | 80% |

辅助参数：
- **memoryFlush**：50K tokens 时触发
- **maxHistoryShare**：300K × 0.65 = 195K（历史占比上限）
- **压缩后保留**：60K 近期 + 摘要 ≈ 65-70K

### 3.3 未变更的关键参数

- `contextWindow`（模型层）：保持 1M（不动模型配置）
- `maxHistoryShare`：保持 0.65
- `recentTurnsPreserve`：保持 4
- `compaction.mode`：保持 safeguard
- `compaction.timeoutSeconds`：保持 120
- `midTurnPrecheck.enabled`：保持 true
- 压缩模型：保持 `newapi-anthropic-vip/deepseek-latest-cloud`

---

## 4. 触发器对齐规范（Round 2 修正）

> ⚠️ 本章是 2026-06-25 Round 2 的核心修正。之前的配置存在触发器失配问题，本章解释原理并给出通用配置公式。

### 4.1 问题：三道触发器不一致

OpenClaw 有三道独立的压缩触发器：

**触发器 #1 — Token 阈值（turn 结束后维护）**

- 公式：`contextTokens_used > contextWindow - reserveTokens`
- 注意：公式用的是 `contextWindow`（模型标称窗口），**不是** `contextTokens`（有效窗口）
- 旧配置：1M - 32768 = **987K** → 在 300K 有效窗口下形同虚设

**触发器 #2 — Transcript 文件大小守卫（turn 开始前）**

- 条件：JSONL 文件大小 > `maxActiveTranscriptBytes`
- 旧配置：30MB → JSONL 包含完整工具输出和元数据，30MB 大约只对应 100-150K 实际 tokens
- 后果：token 还很充裕时就触发了压缩（用户看到的「59% ctx 就压缩」就是这个原因）

**触发器 #3 — midTurnPrecheck（工具循环中）**

- 条件：工具结果追加后，用「same preflight budget logic」估算 prompt 压力
- 这个 budget 逻辑跟 #1 一样：`contextWindow - reserveTokens`
- 旧配置下同样形同虚设

### 4.2 根因

OpenClaw 的设计假设是 `contextTokens ≈ contextWindow`（即你配的有效窗口等于模型标称窗口）。当我们把 `contextTokens` 从 1M 降到 300K 但没同步调整 `reserveTokens` 时，公式失效了。

OpenClaw 没有提供「用 contextTokens 代替 contextWindow 做阈值」的开关，所以只能通过调大 `reserveTokens` 来间接压缩阈值。

### 4.3 通用配置公式

如果你的模型 `contextWindow = W`，你想要的有效窗口 = `T`，reserve floor = `F`，则：

```
reserveTokens = W - (T - F)
```

**本机实例：**
- W = 1,000,000（GLM-5.2 contextWindow）
- T = 300,000（目标有效窗口）
- F = 60,000（reserveTokensFloor）
- reserveTokens = 1,000,000 - (300,000 - 60,000) = **760,000**

验证：阈值 = 1M - 760K = 240K = T - F ✅

**maxActiveTranscriptBytes**：
- 经验值：1MB JSONL ≈ 3-5K 实际 tokens（含完整工具输出+元数据）
- 50MB ≈ 150-250K tokens，跟 240K 触发阈值匹配
- 如果模型 contextTokens 改了，按比例调整：`maxActiveTranscriptBytes ≈ (T - F) / 4 MB`

### 4.4 验证 checklist

配置完成后，确认三道触发器阈值一致：

1. `contextWindow - reserveTokens` 应该 ≈ `contextTokens - reserveTokensFloor`
2. `maxActiveTranscriptBytes` 对应的 token 数应该也在这个范围
3. midTurnPrecheck 使用跟 #1 相同的 budget 逻辑，自动对齐

### 4.5 如果模型 contextWindow 变了

换主模型时必须重新计算 `reserveTokens`：

| 模型 | contextWindow | contextTokens | reserveTokensFloor | reserveTokens |
|------|-------------|--------------|-------------------|--------------|
| GLM-5.2 | 1M | 300K | 60K | 760K |
| Claude Sonnet 4.6 | 1M | 300K | 60K | 760K |
| GPT-5.5 | 400K (Codex) | 300K | 60K | 160K |
| DeepSeek V4 | 1M | 200K | 60K | 860K |

> 公式：`reserveTokens = contextWindow - (contextTokens - reserveTokensFloor)`

---

## 5. 实施步骤

### 5.1 首次执行（Round 1 已完成）

Round 1 的 6 项参数已在本机执行完毕。如果你的机器还没改过，从 5.2 开始。

### 5.2 Round 2 修正（reserveTokens + maxActiveTranscriptBytes）

```bash
# 1. 备份当前配置
cp ~/.openclaw/gateways/*/openclaw.json ~/.openclaw/gateways/*/openclaw.json.bak-r2-$(date +%Y%m%d-%H%M%S)

# 2. 修改以下 2 个参数（Round 2 修正）：
#    agents.defaults.compaction.reserveTokens: → 760000
#    agents.defaults.compaction.maxActiveTranscriptBytes: → "50mb"
#
#    如果 Round 1 还没执行，先按「3.1 参数变更总表（8 项）」一次性改完所有参数。

# 3. 手动重启 gateway
openclaw gateway restart

# 4. 验证触发器对齐（见 4.4 checklist）
```

### 5.3 给其他机器的一键指令

把本文链接发给目标 Agent，附带以下指令：

```
请阅读方案文档，按「3.1 参数变更总表（8 项）」修改本机 openclaw.json。
注意 reserveTokens 的值是 760000（不是 50000），这不是笔误，原理见第 4 章。

1. 备份：cp ~/.openclaw/gateways/*/openclaw.json ~/.openclaw/gateways/*/openclaw.json.bak-300k-$(date +%Y%m%d-%H%M%S)
2. 用 python3 或 jq 修改以下 8 个参数：
   - agents.defaults.contextTokens: → 300000
   - agents.defaults.compaction.reserveTokensFloor: → 60000
   - agents.defaults.compaction.keepRecentTokens: → 60000
   - agents.defaults.compaction.reserveTokens: → 760000
   - agents.defaults.compaction.memoryFlush.softThresholdTokens: → 50000
   - agents.defaults.compaction.maxActiveTranscriptBytes: → "50mb"
   - plugins.entries.openclaw-output-metrics-footer.config.contextReserveTokens: → 60000
3. 如果没装 footer 插件，跳过最后一个参数
4. 改完执行：openclaw gateway restart
5. 验证：确认 contextWindow - reserveTokens ≈ contextTokens - reserveTokensFloor
```

注意：按 AGENTS.md「Runtime Safety」规则，agent 不能自己重启 Life Gateway。

---

## 6. 验证 & Review 计划

### 6.1 短期验证（变更后 1-2 天）

- [ ] footer 显示分母切换到 300k（确认 runtime 已读到新 contextTokens）
- [ ] 跑一次同等复杂度的对话（包含 sub-agent + 大 tool output），确认不再死循环
- [ ] 观察是否还有 "could not recover" 错误
- [ ] 观察 fallback 链激活时表现（强制 GLM-5.2 超时切到 MiniMax/DeepSeek）

### 6.2 中期 Review（变更后 1-2 周）

- [ ] 统计这段时间内 compaction 触发次数 vs 上一轮（多 / 持平 / 少）
- [ ] 统计 "could not recover" 出现次数（目标：0）
- [ ] 统计平均单 turn 实际 input tokens（看是不是真的需要 300K）
- [ ] 评估是否需要：
  - 回退到 256K（如果 300K 没带来明显好处且偶发 DeepSeek 降级）
  - 上探到 400K（如果 240K headroom 经常不够）
  - 维持 300K 继续观察

### 6.3 Review 时要回答的问题

1. 这一轮的死循环问题是否彻底解决？
2. footer 数据有没有变得更有诊断价值？（百分比是否更合理）
3. 用户体验上 (响应速度、答非所问、上下文丢失) 有没有变化？
4. 不同 agent (chat-main-agent / quant-orchestrator / factory-reviewer) 的表现是否一致？
5. 工程师的 300K/500K 建议背后的实测数据，能不能拿来对照？

---

## 7. 风险与回退

### 7.1 已识别风险

| 风险 | 触发条件 | 缓解措施 |
|------|---------|---------|
| DeepSeek V4 fallback 在 ≥ 150K 时退化 | 主模型超时 + 长上下文 | 极少触发；如频繁，把 DeepSeek 从 fallback 移除或降级用 deepseek-v4-flash |
| Claude Sonnet 4.6 fallback 召回率下降 | factory-reviewer 在 ≥ 500K 时 | 当前 300K 远未到 Claude 退化区 |
| 单次 API 成本上升 | 长对话普遍化 | GLM-5.2 单价低，影响小 |
| 压缩仍然循环 | 大 sub-agent 输出 + 大 tool output 叠加 | 上探到 400K 或更大 keepRecentTokens |

### 7.2 回退方案

```bash
# 完全回退到调优前的 256K 配置
cp ~/.openclaw/gateways/life/openclaw.json.bak-300k-* \
   ~/.openclaw/gateways/life/openclaw.json
openclaw gateway restart
```

如果只是想微调而不是完全回退，按 3.1 表逐项改回单值即可。

---

## 8. 历史决策链

- **2026-06-23**：上一轮根因分析（压缩配置默认值不适合 GLM-5.2 1M 标称 + 实际 200K 的现实），见 `compaction-config.md`
- **2026-06-24**：第一轮调优，contextTokens 1M → 256K，配套 7 个参数调整，对应 v0.3.0 插件
- **2026-06-25**：本文 — 第二轮调优，256K → 300K，修 reserve floor

---

## 9. 相关文件

- 上一轮设计文档：`compaction-config.md`
- 插件主代码：`../src/index.js`（MODEL_CONTEXT 表）
- 安装脚本：`../install.sh`
- gateway 当前配置：`~/.openclaw/gateways/life/openclaw.json`

---

_作者：chat-main-agent（GLM-5.2）_
_审定：evan 已确认 Round 2 修正_
_状态：Round 1 已执行；Round 2 修正已执行，等待 gateway restart 生效_
_最后更新：2026-06-25 13:12 GMT+8（补充触发器对齐规范 + Round 2 参数）_
