# Gateway Bindings 管理规范

## 核心问题

`config.patch` 在顶层做合并。如果只传新的 `bindings` 数组，会**替换掉整个现有 bindings 数组**，导致所有已有的 agent-channel 路由失效。

## 正确操作步骤

1. 先读当前配置：`gateway config.get` → 查看完整 bindings 数组
2. 复制完整现有数组
3. 在数组末尾追加新 binding
4. 用 `config.patch` 提交**合并后的完整数组**

```json
// ✅ 正确：包含所有现有 binding + 新 binding
{
  "bindings": [
    { ...EXISTING_BINDING_1... },
    { ...EXISTING_BINDING_2... },
    { ...NEW_BINDING... }
  ]
}

// ❌ 错误：只传新 binding，会抹掉其他所有路由
{
  "bindings": [{ ...NEW_BINDING... }]
}
```

## 当前 Bindings 清单

| Agent | Channel | Account |
|---|---|---|
| chat-main-agent | Discord | — |
| tpr-orchestrator | Telegram | default |
| quant-orchestrator | Telegram | quant |
| factory-orchestrator | Telegram | factory |

添加新 binding 前先对照此表，有冲突先上报，不自行处理。
