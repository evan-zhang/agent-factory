## 审查结论

**总体评级**：WARN
**置信度**：0.90
**审查对象**：OpenClaw 系统优化方案 — bd-eval-reviewer 120s idle timeout / fallback 成本修复方案（二轮 GPT-5.5 交叉复核）
**审查时间**：2026-06-26 15:44 CST
**使用模型**：openai/gpt-5.5 + gsykj-anthropic/claude-sonnet-4-6 汇总

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 根因准确性 | 5 | 34 个 trajectory 中 8 个 fallback session 均含 `LLM idle timeout (120s)`，与源码 hard-coded 默认 idle watchdog 一致。 |
| 修复入口正确性 | 4 | `models.providers.<id>.timeoutSeconds` 可转换为 `model.requestTimeoutMs`，并在 idle resolver 中绕过 120s implicit clamp；但会受 run/agent timeoutBounds 上限约束。 |
| schema 可行性 | 5 | `gateway config.schema.lookup models.providers` 明确支持 provider `timeoutSeconds`，且描述说明会提高 LLM idle/stream watchdog ceiling。 |
| 副作用控制 | 3 | 复制 provider 可缩小影响面；但若 Claude 和 GLM fallback 都指向同一专用 provider，GLM 也会被延长等待。 |
| 替代方案合理性 | 4 | 改源码/cron/分段 streaming 都不是首选；provider timeout 是当前最小可维护修复。 |
| 600s 参数合理性 | 3 | 600s 可作为灰度起点，但历史“约 7m18s 后 timeout”提示仍可能不足，需要监控 `LLM idle timeout (600s)` 后再调。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 生效范围 | Claude 修正版 provider 复制方案 | Claude 推荐的“新增专用 provider + timeoutSeconds:600”方向正确，但当前 `openclaw.json` 尚未实际配置 `newapi-anthropic-vip-reviewer`，`bd-eval-reviewer` 仍使用 `newapi-anthropic-vip/claude-sonnet-4-6` 与 `newapi-anthropic-vip/glm-latest-cloud`。 | 当前配置读取结果：`bd-eval-reviewer.model.primary = newapi-anthropic-vip/claude-sonnet-4-6`；`newapi-anthropic-vip.timeoutSeconds = null`；`newapi-anthropic-vip-reviewer` 不存在。 | 若要落地修正，必须真正新增/复制 provider 并把 reviewer agent 的 primary/fallbacks 指过去；否则不会修复 120s 问题。 |
| F002 | major | 参数上限 | `resolveLlmIdleTimeoutMs` | `model.requestTimeoutMs` 确实绕过 `clampImplicitTimeoutMs(...120s)`，但不是无条件 600s：代码执行 `Math.min(modelRequestTimeoutMs, ...timeoutBounds)`。若显式 run timeout 或 agents.defaults.timeoutSeconds 低于 600s，会被截断。 | `selection-BP0T9R9I.js:11145-11147` 构造 timeoutBounds 并取最小值；`13155-13160` 将 `params.model.requestTimeoutMs` 传入 resolver。当前 `agents.defaults.subagents.runTimeoutSeconds=1800`，未见 `agents.defaults.timeoutSeconds`，因此通常不会截断 600s。 | 配置前确认 reviewer 的 runTimeout / agent default timeout ≥ 600s；当前 1800s 对 subagent 足够。 |
| F003 | major | fallback 范围 | 专用 provider 同时承载 Claude 与 GLM | 如果把 `claude-sonnet-4-6` 和 `glm-latest-cloud` fallback 都放入同一个 `*-reviewer` provider 且 provider 级 `timeoutSeconds=600`，则 GLM fallback 也会等待 600s；在一个已发现链路中 GLM 第二步也发生 120s idle timeout，但这会拉长真正失败时的 tail latency。 | trajectory 核验：8 个 fallback session，均有 fallback_step 与 idle timeout；其中 1 个 chain_exhausted，第二步 `glm-latest-cloud` 也 idle timeout。 | 更精细做法：优先只给 Claude slow provider 600s；fallback GLM 是否也需要 600s 取决于是否接受更长 chain exhaustion。若保留同 provider，需监控耗时。 |
| F004 | minor | 预期管理 | “消除 fallback 浪费”表述 | 提高 timeout 只能减少/消除“120s 静默误杀”导致的 fallback，不能消除 rate limit、context overflow、stream protocol error、auth/billing、上游 5xx 等路径。 | 本次 8/8 fallback session 的直接证据均为 `LLM idle timeout (120s)`，但源码和运行时仍存在其他失败/fallback 路径。 | 文案改为“消除本 case 已验证的 120s idle timeout 类 fallback 浪费”，上线后按错误原因分桶监控。 |
| F005 | minor | 运维风险 | 600s 长静默请求 | 600s 会让真实卡死请求更晚失败，占用一个模型请求/agent 并发更久；不过不会拖死主进程，主要风险是并发槽、上游配额、用户等待与成本尾部。 | schema 描述 `timeoutSeconds` 作用于 provider HTTP fetch/connect/headers/body/total request abort，并提高 idle watchdog；`agents.defaults.subagents.maxConcurrent=8`。 | 先对 reviewer 专用 provider 灰度；观察并发、wall time、fallback 数和费用。必要时降低 reviewer 并发或拆分任务。 |
| F006 | info | 替代方案 | 改源码 / cron / streaming | 直接改 `DEFAULT_LLM_IDLE_TIMEOUT_MS` 属全局 monkey patch，升级会丢且扩大影响；cron 分支确实可绕开 120s，但改变任务架构；“streaming + 分段 output”若模型思考期不产 token，无法保证避免 idle。 | `selection-BP0T9R9I.js:11150` cron 用 runTimeoutMs；`11140-11157` 默认/非 cron 的 implicit clamp。 | 不建议作为第一修复路径；provider timeout 是最小、schema 支持、可灰度的路径。 |

---

**关键证据摘要**

1. 源码：`selection-BP0T9R9I.js:11083` 定义 `DEFAULT_LLM_IDLE_TIMEOUT_MS = 120 * 1e3`；`11140-11151` 显示无 explicit model request timeout 时，非 cron run timeout 会被 clamp 到 120s；`11147` 显示 explicit `modelRequestTimeoutMs` 走 `clampTimeoutMs(Math.min(modelRequestTimeoutMs, ...timeoutBounds))`，不经过 120s implicit clamp。
2. 源码：`model-Cp9whgWq.js:560-561` 将 provider `timeoutSeconds` 转为毫秒；`653`、`774` 读取 provider timeout；`700`、`809` 写入模型对象 `requestTimeoutMs`。
3. schema：`openclaw gateway call config.schema.lookup --params '{"path":"models.providers"}'` 返回 `timeoutSeconds` 为合法 integer；说明文字明确“also raises the LLM idle/stream watchdog ceiling”。
4. trajectory：`/Users/evan/.openclaw/gateways/life/state/agents/bd-eval-reviewer/sessions` 下 34 个 trajectory，8 个含 `model.fallback_step`；这 8 个全部同时含 `LLM idle timeout (120s): no response from model`；1 个最终 `chain_exhausted`。
5. 当前配置：`bd-eval-reviewer` 仍指向 `newapi-anthropic-vip/claude-sonnet-4-6` 和 `newapi-anthropic-vip/glm-latest-cloud`；该 provider 未设置 `timeoutSeconds`，因此现状不会修复。

---

**最终 verdict**

⚠️ **部分可行但需要增量修正**。

Claude 修正版的核心方向成立：使用 `models.providers.<id>.timeoutSeconds = 600` 通过 `model.requestTimeoutMs` 提高 idle watchdog，是 schema 和源码均支持的正确入口；比原始 `agent.model.requestTimeoutMs` 可行。

但建议落地为更精确版本：

```json
{
  "models": {
    "providers": {
      "newapi-anthropic-vip-reviewer": {
        "baseUrl": "同 newapi-anthropic-vip",
        "apiKey": "同 newapi-anthropic-vip，建议用同一 secret/env 引用而非复制明文",
        "api": "anthropic-messages",
        "timeoutSeconds": 600,
        "models": [
          { "id": "claude-sonnet-4-6", "...": "复制原模型元数据" }
        ]
      }
    }
  },
  "agents": {
    "list": [
      {
        "id": "bd-eval-reviewer",
        "model": {
          "primary": "newapi-anthropic-vip-reviewer/claude-sonnet-4-6",
          "fallbacks": ["newapi-anthropic-vip/glm-latest-cloud"]
        }
      }
    ]
  }
}
```

如果你确认 GLM fallback 也会长时间静默且愿意接受更长失败等待，可把 GLM 也放进 reviewer provider；否则建议先只延长 Claude primary。

---

**最重要的一条建议**

按 Claude 修正版落地，但把作用面收窄：新建 reviewer 专用 slow Claude provider 设置 `timeoutSeconds: 600`，先不要全局提高 `newapi-anthropic-vip` 或所有 fallback 模型的 timeout；上线后按 `LLM idle timeout (600s)`、fallback session 数、wall time 和费用做灰度验证。