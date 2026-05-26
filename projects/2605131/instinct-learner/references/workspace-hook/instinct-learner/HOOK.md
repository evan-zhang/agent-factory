---
name: instinct-learner
description: "持续学习闭环：注入 Top-K instincts、自动提取、严格解析 used_ids 并在用户反馈后更新置信度、低频 prune。"
homepage: https://docs.openclaw.ai/automation/hooks
metadata: {"openclaw":{"emoji":"🧠","events":["agent:bootstrap","message:received","message:sent","gateway:startup"],"requires":{"bins":["python3"],"config":["hooks.internal.entries.instinct-learner.enabled"]}}}
---

# Instinct Learner Workspace Hook

这是给 **skill 形态**配套的 workspace hook。

