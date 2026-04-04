# Issue #9 诊断上下文

## 症状
cas-chat-archive 不记录对话、不生成日报、不发送日报。4个 gateway (life/ops/company/code) 均受影响。

## 已确认的事实

1. **Hook 未注册**：4个 gateway 的 `openclaw.json` 中 `hooks.internal.entries["cas-chat-archive-auto"]` 均为 `null`
2. **无近期日志**：`~/.openclaw/chat-archive/{life,ops,company,code}/logs/` 下无今天或昨天的日志文件
3. **Skill 文件完整**：`skills/cas-chat-archive/` 下 hook handler.ts、cas_hook.py、cas_archive.py 均存在
4. **Hook 机制**：`hooks/cas-chat-archive-auto/handler.ts` 是 internal hook，需要在 gateway config 中注册才能触发
5. **DEPLOYMENT.md** 声称已"同步并启用"4个 gateway，但实际配置为空

## 需要分析师回答

1. 根因确认：hook 是从未成功注册，还是注册后被某个操作（如 gateway restart / config apply）清除了？
2. 修复方案：如何正确注册 internal hook 到 4 个 gateway？是否需要修改每个 gateway 的 openclaw.json？
3. 防复发：是否有 auto-hook 机制可以在 gateway 启动时自动注册？

## 参考文件
- Hook handler: `skills/cas-chat-archive/hooks/cas-chat-archive-auto/handler.ts`
- Hook 说明: `skills/cas-chat-archive/hooks/cas-chat-archive-auto/HOOK.md`
- Python hook: `skills/cas-chat-archive/scripts/cas_hook.py`
- 部署文档: `skills/cas-chat-archive/DEPLOYMENT.md`
- Gateway 配置: `~/.openclaw/gateways/{life,ops,company,code}/openclaw.json`
