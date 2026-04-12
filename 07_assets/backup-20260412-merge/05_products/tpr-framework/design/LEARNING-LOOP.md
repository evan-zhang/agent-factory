# tpr-framework 学习复盘

## 2026-04-01

### Problem → Rule
**问题**：Critical Rules 用 NEVER/ALWAYS/Critical 大写，但未解释原因，AI 遵守规则的可靠性低于理解原因。
**规则**：每条强制规则必须附带"为什么"，让 AI 理解背后的逻辑，而非只能记忆死规则。

### Problem → Rule
**问题**：操作手册类内容（Bindings/Spawning）混入框架规则 SKILL.md，导致文件臃肿，触发时加载大量无关内容。
**规则**：SKILL.md 只放框架规则和角色边界。操作手册推入 references/，按需加载。
