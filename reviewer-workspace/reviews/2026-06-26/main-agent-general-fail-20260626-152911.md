## 审查结论

**总体评级**：FAIL
**置信度**：0.86
**审查对象**：OpenClaw 系统优化方案 — bd-eval-reviewer idle timeout/fallback cost 修复方案
**审查时间**：2026-06-26 15:29 CST
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 根因准确性 | 4 | 120s idle watchdog 与 fallback 触发链路基本成立。 |
| 修复入口正确性 | 2 | `model.requestTimeoutMs` 是运行期入口，但当前提议写在 `agent.model` 下不被 schema 接受/传播。 |
| 副作用评估 | 3 | 识别了成本收益，但没有区分 provider 级、model 级、agent 运行超时边界。 |
| 完整性 | 3 | 未覆盖 config schema、provider timeoutSeconds、上游 proxy/stream idle 超时验证。 |
| 可执行性 | 2 | 按现有 JSON 直接加 `agent.model.requestTimeoutMs` 风险较高，建议改为 provider 或显式 model 配置。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 配置路径错误 | 方案 A | 方案声称在 `bd-eval-reviewer agent` 的 `model` 对象加 `requestTimeoutMs: 600000`。但 agent runtime schema 的 `AgentModelSchema` 是 strict object，仅允许 `primary` 与 `fallbacks`，未包含 `requestTimeoutMs`。这意味着该配置很可能验证失败，或至少不会作为 agent model 字段进入解析。 | `~/.npm-global/lib/node_modules/openclaw/dist/zod-schema.agent-runtime-BTWfpsXE.js:14-17`：`object({ primary, fallbacks }).strict()`；当前配置 `openclaw.json:775-781` 仅有 primary/fallbacks。 | 不要把 `requestTimeoutMs` 放在 `agent.model`。优先使用 `models.providers.<id>.timeoutSeconds: 600`；若要只作用于单模型/单 agent，需要确认 OpenClaw 是否支持 agent 级 per-model metadata override，否则需新增专用 provider 或修改源码支持。 |
| F002 | major | 修复入口表述不完整 | 方案 A/C | `requestTimeoutMs` 确实是 idle watchdog 的直接输入，但源码显示它来自已解析的 `params.model.requestTimeoutMs`，而 provider 配置的 `timeoutSeconds` 会被转换成这个字段。官方 runtime schema 文档也明确 `models.providers.*.timeoutSeconds` 会提高 LLM idle/stream watchdog ceiling。 | `selection-BP0T9R9I.js:13155-13160` 把 `params.model.requestTimeoutMs` 传入 idle resolver；`model-Cp9whgWq.js:560-561,774-809` 将 `providerConfig.timeoutSeconds` 解析为 `requestTimeoutMs`；`runtime-schema-BjT8eJxD.js:593` 文档说明 provider timeoutSeconds 会 raise idle watchdog。 | 将推荐方案改为：对 `newapi-anthropic-vip` 设置 `timeoutSeconds: 600`，或创建 `newapi-anthropic-vip-slow-reviewer` 专用 provider 设置 `timeoutSeconds: 600` 并让 bd-eval-reviewer 使用该 provider。 |
| F003 | major | fallback 问题不能保证完全消除 | 方案 A 预期效果 | 提高 idle timeout 能显著降低“无响应超过 120s”导致的 fallback，但不能消除所有 fallback 重启。源码还会因 rate_limit、billing/auth、overloaded、format、context overflow、profile rotation、显式 run timeout、工具执行 timeout 等路径重试或 fallback。 | `embedded-agent-L9tQiaO-.js:710-720` 将 idle/timedOut 作为 assistant timeout failure；`:942-955` fallback_model 会 throw FailoverError；`:3870-3880` 当 fallbackConfigured=true 时不会 same-model idle retry。 | 预期改为“消除该类 120s idle timeout 引发的 fallback”，不要承诺消除所有 fallback。上线后用 trajectory 统计 `reason=timeout`、`session_started=2` 和 provider/model 分布确认。 |
| F004 | minor | 超时边界未充分说明 | 方案 A | `requestTimeoutMs` 不是无条件扩展。`resolveLlmIdleTimeoutMs` 对显式 run timeout 和 agent default timeout 有 `Math.min(modelRequestTimeoutMs, ...timeoutBounds)`，如果调用方设置了更低的 run timeout/agent timeout，600s 会被更低值截断。 | `selection-BP0T9R9I.js:11141-11148`：requestTimeoutMs 与 timeoutBounds 取最小。 | 同时检查 `agents.defaults.timeoutSeconds`、任务/cron/run-specific timeout 是否低于 600s；确保 agent 总运行超时大于 idle timeout。 |
| F005 | minor | 10分钟合理但需灰度验证 | 方案 A | 对 Claude/大工具载荷/代理可能“静默思考”的场景，600s 是合理首选；但会让真正卡死的请求更晚失败，并可能占用并发/线程更久。 | `selection-BP0T9R9I.js:11160-11162` 说明 idle watchdog 对 stream creation 和 iterator progress 生效，每次成功 next 会重置。 | 建议先设 600s 灰度 1-3 个 case；若仍出现 `LLM idle timeout (600s)` 再升 900s，而不是直接更长。并监控 wall time、并发占用、用户等待时间。 |
| F006 | minor | 上游超时源未验证 | 问题 5 | OpenClaw 只能控制本进程请求/stream idle watchdog。new-api.mediportal.com.cn、上游 Anthropic-compatible 网关、负载均衡器或 SDK transport 也可能有 header/body/idle timeout。 | 当前 provider `newapi-anthropic-vip` 是远端 `https://new-api.mediportal.com.cn`，api=`anthropic-messages`；Anthropic transport 会把 `options.timeoutMs` 传给 SDK request timeout（`anthropic-CMNCM8N0.js:281-285`）。 | 打开/采集模型 transport debug 或 provider 网关日志，确认 600s 后是否由 OpenClaw、SDK、newapi 网关还是上游模型先断开。 |

---

**对 5 个问题的直接回答**

1. **`requestTimeoutMs: 600000` 是正确运行期入口，但不是按方案 A 所写的配置入口。** 源码确认 idle resolver 读取的是已解析模型对象 `params.model.requestTimeoutMs`。但 `agent.model` schema 不接受 `requestTimeoutMs`。可执行入口应优先用 `models.providers.<provider>.timeoutSeconds: 600`，或给 reviewer 建一个专用 provider 并设置 provider timeout。
2. **能解决“120s idle timeout 导致 fallback”的主要问题，但不能保证解决所有 fallback。** 对你观测到的 8 个 `LLM idle timeout (120s)`，如果真实原因是模型/网关 120-600s 之间才开始输出，600s 会避免这类重启；如果上游在 120s 左右也会主动断，或请求永远无输出，则仍会超时，只是变成 600s 后失败/再 fallback。
3. **不存在 `agent.model.requestTimeoutMs` 与 provider 的优先级冲突，因为前者当前不合法/不生效。** provider 的 `timeoutSeconds` 会转换为 `model.requestTimeoutMs`。如未来源码支持模型级/agent级字段，应验证其覆盖顺序；当前证据显示 providerConfig.timeoutSeconds 是实际路径。
4. **10 分钟合理，建议灰度。** 对高 token、大工具面、Claude-like reasoning 静默场景，600s 比 120s 更合适；不建议一开始超过 900s。总 run timeout 必须高于它，否则会被截断或被 run timeout 先杀。
5. **还需考虑上游 provider/proxy/SDK/stream idle。** OpenClaw 的 watchdog 只是本地一层；newapi 网关、Anthropic-compatible adapter、HTTP 代理/LB 都可能有自己的 timeout。上线后要用日志区分错误来源。

---

**明确修复建议**

推荐把方案 A 改为 **A'：为 reviewer 使用的 provider/model 设置 provider timeoutSeconds，而不是 agent.model.requestTimeoutMs**。

最小全局 provider 改法（影响所有使用 `newapi-anthropic-vip` 的 agent）：

```json
"models": {
  "providers": {
    "newapi-anthropic-vip": {
      "timeoutSeconds": 600
    }
  }
}
```

更稳妥的低副作用改法：复制/新增一个 `newapi-anthropic-vip-reviewer` provider，baseUrl/apiKey/api/models 与 `newapi-anthropic-vip` 一致，但加 `timeoutSeconds: 600`；然后只把 `bd-eval-reviewer.model.primary/fallbacks` 指到这个 provider。这样不会改变其他 agent 的失败等待时间。

配合建议：
- 保留 fallback，但上线后统计 `LLM idle timeout (120s/600s)`、`session_started=2`、reason=timeout 的数量。
- 若仍出现 600s idle timeout，再判断是否需要压缩 prompt/tool surface，而不是继续加长 timeout。
- 方案 B（tool call ≤8）可作为降本措施，但它解决的是冗余工具调用，不是 idle fallback 根因；建议单独灰度和统计。
- 方案 C 当前不应作为首选；源码/文档指向 provider timeoutSeconds 已可解决，不必改全局默认。

---

**最重要的一条建议**

把方案 A 从“在 `agent.model` 下加 `requestTimeoutMs`”改为“给 reviewer 专用 provider 设置 `models.providers.<id>.timeoutSeconds: 600`”，否则修复很可能不生效或配置校验失败。
