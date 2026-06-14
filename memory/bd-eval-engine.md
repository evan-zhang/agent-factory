# Memory — bd-eval-engine 项目

## 2026-05-30 [决策] Battle 机制从全量一次性改为 Gate-Level 多轮收敛

- **决策**：废弃 P4 阶段全量 Battle（6个Gate跑完后一次性审查），改为每个 Gate 完成后立即触发 Gate-Level Battle + 自查 + 最多3轮收敛
- **前车之鉴**：原来一轮 Battle 容易变成形式主义（Executor 只需口头回应不需改文件）；Gate 之间的数据传导性意味着 Gate-1 的错误会传导到 Gate-6，必须尽早纠正
- **上下文**：参考 TPR 三省制的 Battle 协议（battle-protocol.md v2.2.0），引入自查先行、状态机驱动、3轮收敛机制
- **具体方案**：
  - 每个阶段分级：Discovery/One-pager/Reporter 只加自查；Router 加自查+轻量Battle(1轮)；Gate-1~6 加自查+完整Battle(最多3轮)
  - Battle 状态机：自查通过 → Auditor审查(APPROVE/REJECT/CONDITIONAL) → REJECT则Executor真改文件 → Auditor重审 → 最多3轮 → 未解决则标记争议继续
  - 成本估算：理想14次LLM(自查后1轮过) ~ 26次LLM(一般2轮)，耗时 25~40min（现19min）
- **代码改动**：新增 self-check.md prompt；改造 battle.py 加状态机；改造 engine.py Gate后立即Battle；改造 evaluator.py 自查触发

## 2026-05-30 [决策] README 作为方案唯一权威来源

- **决策**：所有讨论结论、架构决策都写入 README.md，README 即方案文档
- **上下文**：Evan 明确要求"README 里的东西就是我们讨论的东西，将来都要放到 README 里面"
