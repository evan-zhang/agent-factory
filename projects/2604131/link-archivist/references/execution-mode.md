# 执行模式

## 两种模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **sub-agent（推荐）** | 主 Agent 识别链接后 spawn sub-agent 执行，不阻塞主对话 | 日常使用 |
| **直接执行** | 主 Agent 自己按 Phase 1-5 执行 | 调试、快速测试 |

## sub-agent 模式流程

1. **识别**：主 Agent 收到链接，判断需要 Link Archivist 处理
2. **通知用户**：立即回复，告知已安排后台处理及预计时间
   - full 模式：3-5 分钟
   - short 模式：1-2 分钟
   - 含视频下载：额外 +1-2 分钟
3. **spawn worker**：`sessions_spawn` 创建 sub-agent，参数：
   - `task`：读取 `specs/agents/link-archivist-worker.md` 的内容作为任务指令
   - `cwd`：`~/.openclaw/skills/link-archivist/`
   - `mode`：`run`（一次性任务）
4. **等待完成**：sub-agent 完成后自动 announce
5. **汇报结果**：主 Agent 收到 announce，用正常对话语气向用户报告结果

## sub-agent spawn 模板

```
你是 Link Archivist Worker。请读取 specs/agents/link-archivist-worker.md 了解你的角色和规则。

任务：处理以下链接
- URL: {url}
- 模式提示: {mode_hint 或 "自动判断"}
- 补充上下文: {extra_context 或 "无"}

请按 references/workflow.md 的 Phase 1-5 执行。完成后输出 LINK_ARCHIVIST_RESULT 结构。
```

## 结果汇报模板

成功：
> ✅ 链接处理完成
> 模式：{full/short}
> 归档：{archive_path}
> 摘要：{summary}

部分成功：
> ✅ 链接处理完成（部分）
> 归档：{archive_path}
> ⚠️ {warnings}
> 摘要：{summary}

失败：
> ❌ 链接处理失败
> 原因：{失败原因}
> 建议：{用户可采取的行动}
