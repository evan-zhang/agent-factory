# OpenClaw 工具循环检测配置指南

> 本文档由 Agent Factory（造物）产出，供所有 OpenClaw Agent 共享。
> 最后更新：2026-04-03

## 为什么需要这个配置

AI 模型在处理复杂推理时，可能陷入内部推理循环——同一段分析重复数百遍，导致：
- 大量 token 被浪费（可能消耗数千元）
- 用户收到几十条无意义的重复消息
- 如果用户不在手机旁，循环会持续到 token 上限

**这是真实发生过的事故，不是假设。**

## 配置方法

在 `openclaw.json` 的 `tools` 字段下加入 `loopDetection`：

```json
{
  "tools": {
    "loopDetection": {
      "enabled": true,
      "warningThreshold": 8,
      "criticalThreshold": 15,
      "globalCircuitBreakerThreshold": 25,
      "detectors": {
        "genericRepeat": true,
        "knownPollNoProgress": true,
        "pingPong": true
      }
    }
  }
}
```

## 参数说明

| 参数 | 默认值 | 推荐值 | 说明 |
|------|--------|--------|------|
| `enabled` | false | **true** | 总开关。**默认关闭，必须手动启用** |
| `warningThreshold` | 10 | 8 | 连续 N 次无进展工具调用后发出警告 |
| `criticalThreshold` | 20 | 15 | 连续 N 次无进展后阻断循环 |
| `globalCircuitBreakerThreshold` | 30 | 25 | 连续 N 次无进展后强制终止整个会话 |
| `detectors.genericRepeat` | true | true | 检测同工具同参数的重复调用 |
| `detectors.knownPollNoProgress` | true | true | 检测 poll 类工具无进展 |
| `detectors.pingPong` | true | true | 检测两个工具来回切换 |

## 三层保护机制

```
正常工作
  ↓
连续 8 次无进展 → ⚠️ 警告（记录日志，提醒 Agent）
  ↓
连续 15 次无进展 → 🔴 阻断（中止当前循环，Agent 必须换个策略）
  ↓
连续 25 次无进展 → 🛑 硬停（强制终止整个会话，保护用户）
```

## 为什么推荐值比默认值更激进

- 默认值（10/20/30）偏保守，循环 20 次才阻断
- 推荐值（8/15/25）更早介入，减少 token 浪费
- 对于国产模型（GLM、MiniMax 等），thinking 循环是已知风险，需要更早刹车

## 启用方式

方式一：直接编辑 `openclaw.json`，加入上述配置，然后重启 gateway。

方式二：用 OpenClaw config.patch（推荐，自动重启）：

在 Agent 对话中请求："请帮我启用 tools.loopDetection，阈值设为 8/15/25。"

## 注意事项

1. **此配置默认关闭**。OpenClaw 不会自动启用，每个 Agent 都需要手动配置
2. **此配置只防工具调用循环**。如果模型在 thinking（内部推理）阶段循环，但没调用工具，loopDetection 无法检测
3. **此配置不是 token 预算**。它限制的是行为模式（重复），不是总量。OpenClaw 目前没有原生的 token 预算功能
4. **可以在 per-agent 级别覆盖**。在 `agents.list` 中为特定 Agent 设置不同的阈值

## 已知局限

- 模型在 thinking 阶段的循环（不调用工具）无法被检测
- 没有"单会话最多花 X 元"的硬限制
- 没有"每日 token 配额"的限制
- 这些功能在 OpenClaw 官方路线图中，但尚未实现

---

*文档来源：Agent Factory 经验教训库（07_lessons/LESSONS.md）*
*联系方式：通过 Telegram @factory_orchestrator 联系造物*
