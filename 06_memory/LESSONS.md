# 经验教训库（Lessons Learned）

> 全局经验分享项目，记录所有 Agent 在生产环境中遇到的真实问题、根因分析和防护措施。
> 不按项目分文件，按时间倒序累积在同一文件中。
> 每次 sub-agent spawn 时，Orchestrator 应把最近的教训注入 task。

---

## [2026-04-03] GLM-5.1 推理循环失控事件

**严重程度**：P0（用户信任受损）
**涉及模型**：zai/glm-5.1（通过 openai-completions API）
**涉及 Agent**：factory-orchestrator

### 事件经过

在讨论"把玄关开放平台地址存在哪个文件"时，GLM-5.1 的内部推理（thinking）陷入死循环——同一段关于 memory_search 和 TOOLS.md 的分析被重复了数百遍。循环内容全部是英文，溢出到用户可见的回复中，导致用户收到几十条英文垃圾消息。

### 根因分析

1. **模型层**：GLM-5.1 在处理复杂多步推理时，thinking 循环没有正确终止，陷入了同一段分析的无限重复
2. **平台层**：OpenClaw 的 `tools.loopDetection` 默认关闭，没有自动刹车机制
3. **规则层**：没有"必须用中文回复"的硬性规则，导致循环内容以英文输出

### 防护措施

| 层级 | 措施 | 状态 |
|------|------|------|
| 平台层 | 启用 `tools.loopDetection`（8/15/25 三层保护） | ✅ 已生效 |
| 规则层 | RULES.md 第0条：必须用中文回复 | ✅ 已写入 |
| 规则层 | 回复结尾禁止反问，直接给行动建议 | ✅ 已在 RULES.md |

### 具体配置

```json
tools: {
  loopDetection: {
    enabled: true,
    warningThreshold: 8,      // 连续8次无进展 → 警告
    criticalThreshold: 15,     // 连续15次无进展 → 阻断循环
    globalCircuitBreakerThreshold: 25,  // 连续25次 → 强制终止会话
    detectors: {
      genericRepeat: true,     // 同工具同参数重复
      knownPollNoProgress: true, // poll类工具无进展
      pingPong: true,          // 两工具来回切换
    },
  },
}
```

### 经验教训

1. **不能靠用户盯着**：如果 Evan 不在手机旁边，循环会一直跑到 token 上限。平台必须有自动保护
2. **规则和配置双保险**：RULES.md 写行为规则（用中文），loopDetection 写硬保护（自动刹车）。两层都不可缺少
3. **GLM-5.1 的风险特征**：通过 openai-completions API 调用时，thinking 可能不正确终止。在复杂推理任务中需要特别注意
4. **配置默认值不够安全**：OpenClaw 的 loopDetection 默认关闭。建议所有生产环境都启用

### 复现场景

- 模型：zai/glm-5.1
- 任务类型：复杂多步推理（对比多个存储位置、权衡优缺点）
- 触发条件：thinking 在分析"TOOLS.md vs memory/*.md vs references/"时无法收敛
- 持续时间：约 2 分钟（用户手动中断）

---

<!-- 模板：后续经验用以下格式追加 -->

<!-- ## [日期] 标题
**严重程度**：P0/P1/P2
**涉及模型**：
**涉及 Agent**：

### 事件经过
（简述发生了什么）

### 根因分析
（为什么会发生）

### 防护措施
（做了什么来防止复发）

### 经验教训
（提炼出的可复用知识） -->
