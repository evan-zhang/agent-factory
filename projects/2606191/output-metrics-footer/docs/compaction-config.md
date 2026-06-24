# OpenClaw 上下文压缩推荐配置

> **适用范围**：Life Gateway 下所有 Agent（Gateway 级别配置）
> **设计目标**：让 1M 标称的实际模型工作在"甜蜜点"窗口（256k）内，提升模型聪明度、响应速度，并联动 output-metrics-footer 插件正确显示真实使用率
> **维护**：本文档与 install.sh 同步维护；安装插件时可一键应用此推荐配置

---

## 一、设计理念

### 1.1 核心判断：标称 1M ≠ 实际可用 1M

业界共识（Lost in the Middle、NIAH 基准测试反复验证）：

| 模型 | 标称 | 实测高质量区间 | 衰退临界 |
|---|---|---|---|
| GLM-5.2 | 1M | ~128k-256k | 256k 后明显衰退 |
| MiniMax-M3 | 1M | ~128k | 200k+ 检索骤降 |
| DeepSeek-V4 Flash | 1M | ~128k | 200k+ 不可靠 |
| Claude Sonnet 4.6 | 1M | ~200k | 200k 后 recall 下降 |

**关键事实**：几乎所有标称 1M+ 的模型，超过 200k 后 NIAH recall 率会从 95%+ 跌到 50% 以下。中段信息丢失最严重，模型会"假装记得"——这正是用户实际体感「模型变笨」的物理根源。

### 1.2 为什么主动调小窗口反而更好

| 收益 | 说明 |
|---|---|
| 模型更聪明 | 注意力机制集中在小窗口，关键信息不被稀释 |
| 回复更准 | 不出现"我说过的事情你都不记得"的幻觉式遗忘 |
| 响应更快 | input token 少，TTFT 和总时长明显下降 |
| 成本更低 | provider 按 input 计费 |
| 压缩更早触发 | 压缩反而是好事——强迫摘要保留精华，比堆原始历史质量高 |
| KV cache 命中高 | 短上下文更易命中 prompt cache |

### 1.3 风险（在我们的使用场景下基本不存在）

- 一次塞 500k 代码进去做大文档分析 → 我们不做
- 需要保留极长对话历史 → 我们有 MEMORY.md + memory-core 插件托底

---

## 二、源码级触发公式

OpenClaw 实际有**三条独立的压缩触发路径**：

| 路径 | 触发公式 | 说明 |
|---|---|---|
| **preflightCompaction** | `ctx - reserveTokensFloor - softThresholdTokens` | 每轮对话开始前检查 |
| **pre-prompt check** | `ctx - max(reserveTokens, reserveTokensFloor)` | 每次发 prompt 前检查 |
| **transcriptBytes** | `bytes >= 30mb` | transcript 文件大小独立触发 |

**关键参数职责（来自源码）：**

| 参数 | 影响触发？ | 影响压缩后？ |
|------|:---:|:---:|
| `contextTokens`（模型级） | ✅ | ❌ |
| `agents.defaults.contextTokens`（agent 级 cap） | ✅ 取 min | ❌ |
| `reserveTokensFloor` | ✅✅ | ❌ |
| `softThresholdTokens` | ✅ | ❌ |
| `reserveTokens` | ✅（pre-prompt） | ❌ |
| `keepRecentTokens` | ❌ | ✅ |
| `maxHistoryShare` | ❌ | ✅ |

### 2.1 contextTokens 解析优先级（源码 `context-resolution-DvriSJiG.js`）

```
最终 contextWindowTokens = capOverride(
  Math.min,
  agents.defaults.contextTokens,                            // agent 级上限
  models.providers.*.models[].contextTokens || contextWindow // 模型级声明
)
```

**结论：把 `agents.defaults.contextTokens` 设小，可以一次性覆盖所有模型，无需逐个修改 provider 配置。**

### 2.2 maxHistoryShare 的 SAFETY_MARGIN 细节

- `buildHistoryPrunePlan` 判断阈值：`ctx × maxHistoryShare × 1.2`
- `pruneHistoryForContextShare` 实际裁剪：`ctx × maxHistoryShare`

---

## 三、推荐配置

### 3.1 完整配置（256k 目标窗口）

```json
{
  "agents.defaults.contextTokens": 256000,
  "agents.defaults.compaction": {
    "mode": "safeguard",
    "reserveTokensFloor": 40000,
    "reserveTokens": 32768,
    "keepRecentTokens": 50000,
    "maxHistoryShare": 0.65,
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 30000
    },
    "midTurnPrecheck": { "enabled": true },
    "recentTurnsPreserve": 4,
    "notifyUser": false,
    "truncateAfterCompaction": true,
    "maxActiveTranscriptBytes": "30mb",
    "timeoutSeconds": 120,
    "postIndexSync": "async"
  }
}
```

### 3.2 触发点验证（代入 256k 公式）

| 路径 | 公式 | 触发点 | 占模型% |
|---|---|---|---|
| preflight | 256k - 40k - 30k | **186k** | 73% |
| pre-prompt | 256k - max(32.768k, 40k) | **216k** | 84% |

**最先触发的是 preflight，触发点 186k = 占模型 73% — 合理区间。**

### 3.3 压缩后空间分配

```
总空间: 256,000 tokens
├─ system prompt: ~30,000  (AGENTS.md + MEMORY.md + SOUL.md + TOOLS.md + 插件注入)
├─ 历史摘要预算: 最多 166,400 (256k × 0.65)
├─ 近期对话保留: 50,000 (keepRecentTokens, 独立预算)
├─ 回复+工具空间: 40,000 (reserveTokensFloor)
└─ 缓冲: ~20,000
```

实际压缩后历史 = 摘要 + 近期保留，两者合计不超过 166k 裁剪预算。

### 3.4 参数说明

| 参数 | 推荐值 | 理由 |
|---|---|---|
| `agents.defaults.contextTokens` | **256,000** | 落入模型甜蜜点，提升智能与速度 |
| `reserveTokensFloor` | **40,000** | 配合小窗口，留够回复空间但不浪费 |
| `keepRecentTokens` | **50,000** | 小窗口下 50k 已是 ~10 轮对话 |
| `maxHistoryShare` | **0.65** | 历史预算占比合理，压缩后保留充分 |
| `softThresholdTokens` | **30,000** | 配合小窗口下推 preflight 触发点 |
| `notifyUser` | **false** | 不打扰，安静压缩 |
| `timeoutSeconds` | **120** | 给压缩留足时间 |
| `reserveTokens` | 32,768 | 默认值，被 floor 自动覆盖 |
| `midTurnPrecheck.enabled` | true | turn 中工具大输出时截断 |
| `recentTurnsPreserve` | 4 | 至少保留最近 4 轮 |
| `maxActiveTranscriptBytes` | "30mb" | 文件大小兜底 |
| `mode` | "safeguard" | 推荐模式 |

---

## 四、与 output-metrics-footer 插件的联动

### 4.1 footer 如何取分母

footer 显示 `%ctx` 的优先级是：

```typescript
const win = (usage.contextTokenBudget && usage.contextTokenBudget > 0)
  ? usage.contextTokenBudget   // 1. runtime 传入的实际窗口（最准）
  : tableWin;                  // 2. fallback 到 MODEL_CONTEXT 表
```

**runtime 传入的 `contextTokenBudget` 已经包含了 `agents.defaults.contextTokens` 的封顶逻辑**（源码 `resolveContextWindowInfo`）。

也就是说：**应用本推荐配置后，footer 会自动用 256000 算分母，无需改插件代码。** MODEL_CONTEXT 表里的 1M 默认值仅在 runtime 没传 budget 的极端 fallback 场景才用到。

### 4.2 应用前后对比

| 场景 | 应用前 footer | 应用后 footer |
|---|---|---|
| 对话累积到 100k token | 10% ctx（按 1M 算，"看起来很轻松"但模型已开始变笨） | **39% ctx**（按 256k 算，反映真实负担） |
| 对话累积到 180k token | 18% ctx（虚假的"安全"） | **70% ctx**（贴近 preflight 阈值，提醒该压缩了） |
| 触发 preflight 压缩 | ~76% ctx 才触发（760k） | **~73% ctx 触发**（186k） |

**核心改善**：footer 显示的百分比从此真实反映"距离压缩还有多远 + 模型当前负担"。

---

## 五、安装时的交互（install.sh 行为）

`install.sh` 在装完插件后会：

1. 读取当前 `agents.defaults.contextTokens` 和 `agents.defaults.compaction`
2. 对比本文档的推荐配置，列出差异
3. **询问用户三选一**：
   - **A. 全部应用推荐配置**（一键 patch，自动备份原配置）
   - **B. 跳过，保持当前配置**（footer 会按当前的 contextTokens 算分母）
   - **C. 打开文档查看说明**（显示本文档路径，用户手动决定）
4. 如选 A，生成时间戳备份，写入新配置，提示重启

**非交互模式**：通过 `bash install.sh --apply-recommended` 或 `--keep-current` 跳过提问，适合 CI/脚本批量安装。

---

## 六、风险与回退方案

### 6.1 风险评估

| 风险 | 严重度 | 缓解 |
|---|---|---|
| 256k 不够用，长对话被频繁压缩 | 低 | 配合 keepRecentTokens=50k + maxHistoryShare=0.65，压缩后仍保留充足上下文 |
| 大文档分析任务做不了 | 低 | 我们不做这类任务；如临时需要可单 session 改 contextTokens |
| 压缩质量下降导致信息丢失 | 中 | customInstructions 已配置九段式摘要；MEMORY.md 托底 |
| 工具大输出（如 doc-viewer）撑爆 reserveTokensFloor=40k | 中 | midTurnPrecheck 会在 turn 中截断；contextPruning 会裁剪老工具输出 |

### 6.2 回退路径

如果出现问题，按以下顺序回退：

1. **第一档**：`contextTokens: 256000 → 384000`，其他参数保持
   - 触发点：384k - 40k - 30k = 314k（占 82%）
   - 适合发现 256k 真的不够用的场景

2. **第二档**：`reserveTokensFloor: 40000 → 60000`
   - 推迟 preflight 触发：256k - 60k - 30k = 166k（占 65%）
   - 适合发现回复+工具空间不够的场景

3. **完全回退**：恢复 install.sh 自动生成的备份文件

备份位置：`<openclaw.json>.bak-footer-install-YYYYMMDD-HHMMSS`

---

## 七、参考来源

OpenClaw 源码（v2026.6.8 验证）：
- `agent-runner.runtime-BapylDFW.js:1255` — preflightCompaction 触发公式
- `agent-runner.runtime-BapylDFW.js:1420` — memoryFlush 触发公式
- `selection-kQiC501t.js:14140` — pre-prompt check
- `attempt.tool-run.context-CT5r1Qgk.js:126-175` — pre-prompt check 公式
- `agent-settings-R-XbC6UK.js:35` — `reserveTokens = max(reserveTokens_config, reserveTokensFloor_config)`
- `context-resolution-DvriSJiG.js:119-149` — contextTokens 解析逻辑
- `compaction-planning-BD_0nYm1.js:184` — `budgetTokens = maxContextTokens × maxHistoryShare`
- `compaction-planning-BD_0nYm1.js:219` — `maxHistoryTokens = contextWindowTokens × maxHistoryShare × 1.2`
- `compaction-planning-BD_0nYm1.js:17` — `SAFETY_MARGIN = 1.2`
- `extensions/memory-core/index.js:78-91` — memoryFlushPlan 构建
- `agent-settings-R-XbC6UK.js:9` — DEFAULT_AGENT_COMPACTION_RESERVE_TOKENS_FLOOR = 20000

业界研究：
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)
- [Needle in a Haystack (NIAH) benchmark](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)
- [RULER: What's the Real Context Size of Your Long-Context Language Models?](https://arxiv.org/abs/2404.06654)

---

## 八、致谢

本方案的源码触发公式分析基础，来自 kangzhe-tg-cpzx001 workspace 的小龙虾 Agent（2026-06-24）。原方案针对 272k 模型反推参数；本文档在其源码分析基础上，针对 1M 标称模型的实际能力做了重新推导。
