## 审查结论

**总体评级**：WARN
**置信度**：0.85
**审查对象**：M4b 业务模块闸门评审 — discovery / validation dry-run orchestrator、event store、legacy projection、execution guard 串接、Gateway cron 设计
**审查时间**：2026-06-24
**使用模型**：MiniMax-M3 (subagent)

被审材料：
- `PLAN.md`
- `design/DESIGN.md`
- `design/reviews/M4b-selfcheck-2026-06-24.md`
- `src/SKILL.md`
- `src/scripts/dry_run_orchestrator.py`
- `src/scripts/event_store.py`
- `src/scripts/migrate_legacy_csv.py`
- `src/scripts/validate_schema.py`
- `src/scripts/validate_registry.py`
- `src/scripts/execution_guard.py`
- `tests/test_m4a_validators.py`
- `src/references/gateway-cron.md`

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| S3/M4a 边界遵守 | 4 | 编排器不触网、不调 broker、CSV 仅作 projection；但 cron 设计未排除 Gateway 通过 shell 注入 `custom_ref` 等参数的可能。 |
| Orchestrator 真实串接 | 4 | discovery→validation 经 event store 串通，validation→candidate promotion 通过 schema 串通；`--draft-file` 路径未走 schema 校验。 |
| 测试覆盖 | 3 | 13 个测试覆盖 happy path 与 6+ 拒绝分支；但缺 `validation_event.promote_candidate` 与 `verdict` 一致性、idempotency、跨 schema 失败、registry snapshot 漂移等关键路径。 |
| Gateway cron 安全 | 3 | 边界与拒绝条件写齐；但触发契约完全依赖 Gateway 正确传 CLI 参数、缺 idempotency 去重、operator 通知路径未强制。 |
| 内部一致性 | 4 | design / SKILL / scripts / tests 总体一致；`validation_event.promote_candidate` 与 `verdict` 缺 schema 级互斥规则是个小漏洞。 |
| 可审计性 | 4 | 全部事件经 `validate_schema` 落 JSONL；`--dry-run` 固定为 `true`；`approval.v1` 与 `execution_guard_decision.v1` 拒绝路径在测试中验证。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| B001 | blocker | 一致性 / 安全 | `src/scripts/validate_schema.py` `_check_validation_event` | `validation_event.v1` 没有强制 `promote_candidate` 与 `verdict` 的一致性：手工构造 `{verdict=reject, promote_candidate=True}` 仍可通过 schema 校验；只有 `dry_run_orchestrator` 的 `build_validation_events` 在代码层做了 `promote = verdict == 'confirm'` 的对齐。绕过 orchestrator 直接写事件即可伪造 promoted candidate。 | `validate_schema._check_validation_event` 仅检查 UUID 字段，未对 `promote_candidate` 与 `verdict` 强加互斥；本地复现确认 `{verdict:'reject', promote_candidate:True}` 返回 `ok=True`。 | 在 `_check_validation_event` 中加规则：`if verdict == 'confirm' → promote_candidate == True`；其他 verdict 必须 `promote_candidate == False`。 |
| M001 | major | 测试覆盖 | `tests/test_m4a_validators.py` | 没有针对 B001 的负例（`verdict=reject + promote_candidate=True` 应被 schema 拒绝）。 | `SchemaValidatorTests` 中所有 validation_event fixture 都是 `verdict=confirm / promote=True`；未断言一致性规则。 | 加 `assert_invalid({verdict:'reject', promote_candidate:True}, 'promote_verdict_mismatch')`。 |
| M002 | major | 测试覆盖 | `tests/test_m4a_validators.py` | 缺少 idempotency 重复执行与 cross-event 部分失败回归测试。`--event-root` 同目录重复跑 discovery 会产生第二条 atomic_request；orchestrator 没有任何去重保护。 | selfcheck 明示 "idempotency key is recorded but not enforced"；测试集无重复执行用例。 | 加测试：同一 `idempotency_key` 第二次跑应被拒绝或返回 0 写入；同时验证 `append_many` 中途失败时的部分写入行为。 |
| M003 | major | Gateway cron 安全 | `src/references/gateway-cron.md` | 触发契约依赖 Gateway 调用者正确传 `--strategy-version=1.0.0` 等参数；如果 Gateway 把 cron metadata 拼成 `idempotency_key`，未来注入 `strategy_id=chokepoint` 即可绕过 manual-only 限制（registry 层仍会拒绝，但 cron 设计上没显式禁止）。 | gateway-cron.md 仅说"不能 infer fallback"，未说 Gateway 任何字段不可被覆盖、未给出参数白名单。 | 在 cron 文档加 "Gateway 必须白名单传入参数；不得转发 user 控制的 strategy_id / caller / custom_ref"。 |
| M004 | major | 边界 / 可审计 | `src/scripts/dry_run_orchestrator.py` `_load_draft_records` | `--draft-file` 路径直接 `json.loads` 后传入 `build_validation_events`，绕过了 `event_store.append` 的 schema 校验；空 candidates 静默返回无事件。 | `dry_run_orchestrator._load_draft_records` 无 `validate_record` 调用；自检仅说 "produced JSONL files for ... validation event, and candidate record"，但没有 fixture 覆盖空 draft。 | 在 `run_validation` 入口对 `drafts[-1]` 调 `validate_schema.validate_record`，对空 candidates 返回 `candidate_not_found` 拒绝码。 |
| m001 | minor | 设计一致性 | `src/references/gateway-cron.md` 56-65 行 | "Do not write canonical events under `src/`, `tests/`, or the installed skill directory" 但 `dry_run_orchestrator.py` 默认 `--registry`/`--custom-refs` 路径是 `src/strategies/*.yaml`（仓库内）；这与 cron 文档语义不冲突，但易让人误以为"绝对不能写仓库内文件"。 | gateway-cron.md 限定 event root；scripts 默认 registry 路径在仓库内是正常的（registry 是配置）。 | 文档补充一句：cron 写 event root，但不写 registry 路径；registry 是包内只读资源。 |
| m002 | minor | 测试覆盖 | `tests/test_m4a_validators.py` `RegistryTests` | `test_required_rejects` 把所有拒绝路径压成一个测试；当某条拒绝码被静默改写时，回归不易暴露。 | 单测试 `test_required_rejects` 包含 7 个 `assertEqual`。 | 拆成 7 个独立 `test_reject_<code>` 方法。 |
| m003 | minor | 性能 / 可靠性 | `src/scripts/dry_run_orchestrator.py` `run_validation` | `store.read_schema("draft_candidates.v1")` 每次重读整个 JSONL；N 次验证会 O(N²) 增长。M4b 体量下不构成性能问题，但 S5 / 长期 cron 调度是负担。 | `JsonlEventStore.read_schema` 无缓存；orchestrator 每次 validation 都重读。 | v1 可接受；记入 S5 backlog：event store 加 `last_index_per_schema` 缓存。 |
| m004 | minor | 一致性 | `src/SKILL.md` "执行流程" 与 `flows/validation.md` | `SKILL.md` 提到 "verdict 来自 validation flow"，`flows/validation.md` 描述了"复选"流程；但 M4b 仅 `build_validation_events` 实现 verdict 注入，没在 SKILL 写 verdict 来源（人工输入？monitor 触发？）。 | SKILL.md "5. 候选生命周期" 未提及 verdict 来源；design/DESIGN.md 也未定义。 | 在 SKILL.md 加一句"validation verdict 在 v1 是 caller 输入；S5 接入 evidence store 后改为自动评估"。 |
| m005 | minor | 可维护性 | `src/scripts/dry_run_orchestrator.py` `build_parser` | `discovery` 与 `validation` 子命令共用 `--event-root` / `--registry` / `--custom-refs` 是正确的，但 validation 没有 `--caller`，导致无法在 cron 路径下生成 validation 事件。 | `validation` 子命令的 argparse 没有 `--caller` 选项。 | 给 validation 加上 `--caller` 以支持未来 operator 触发的对账。 |
| m006 | minor | 设计 | `src/references/gateway-cron.md` "Failure Handling" | "do not retry strategy execution automatically" 没有明确 max retry budget；触发投递失败 vs 业务失败被混在一起。 | gateway-cron.md "Failure Handling" 段落未分两类失败。 | 拆为 "Trigger delivery failure"（重试 3 次，指数退避）和 "Business failure"（不重试，仅通知）。 |
| I001 | info | 文档 | `design/reviews/M4b-selfcheck-2026-06-24.md` | "Ran 12 tests" 与实际 `Ran 13 tests` 不符。 | 实跑 `unittest discover -s tests` 输出 `Ran 13 tests in 0.019s`；selfcheck 写 12。 | 更新 selfcheck 数字，或合并为 "13 tests pass"。 |
| I002 | info | 设计 | `src/SKILL.md` | M4b 把 `stock-picking` 描述成 SOP 编排层，但仍 alias 为 `sp2`；与原 `stock-picking-v2` 名字关系不清。 | SKILL.md frontmatter `aliases: [sp2, stock-picking, stock-picking-v2]`。 | 在 Decision Log 写一行"保留 v2 alias 为兼容期"并设删除日期。 |

---

**最重要的一条建议**

把 B001（`validation_event.promote_candidate` 与 `verdict` 的 schema 级一致性）补上，并加一条对应的负例测试 — 这一点在 cron pilot 之前是事件链可信度的最低防线；缺了它，外部任何写入路径都能伪造 promoted candidate。

---

**附加说明（不在 M4b 范围但顺手指出）**

- `src/scripts/position-monitor.py` 用 `subprocess.run(cmd, shell=True)` 拼 `source .env && longbridge quote ...`：当 env 文件不可信时存在命令注入面。已确认 `position-monitor.py` 不在本次 M4b 改动文件列表，且 module 边界文档说 M4b 仅负责新 orchestrator；建议在 S5 risk-monitor flow 落地时一并把 `position-monitor.py` 替换为 `risk-monitor.md` flow + 走 `execution_guard` 的 quote 路径。
- `src/scripts/validate_schema.py` 的 `validate_record` 接受 list/dict 中的任意 `confidence.level` 字符串，未在 schema enum 限制；属 minor，建议把 `confidence.level` 加到 enum。
- `migrate_legacy_csv.py` 当前不写文件（只 stdout），跟 design "CSV 只读兼容" 一致；OK。

---

**总体评价**

M4b 完成了 S3 → M4b 业务模块的第一段可执行切面：

- 编排器 `dry_run_orchestrator.py` 与 `event_store.py` / `validate_schema.py` / `validate_registry.py` / `execution_guard.py` 串得通，dry-run 默认开启，`--draft-file` 之外的主路径都走 `validate_record`。
- 13 个单测覆盖 happy path、registry 6+ 拒绝码、execution guard 6 个拒绝码、event store / migration / dry-run orchestrator 三类集成路径。
- Gateway cron 设计在职责切分、event root、retry 边界上写清楚，符合 S3 DESIGN §3.7 / §4.1。
- 主要缺口是 B001（schema 缺 verdict/promote 一致性）和 M002（idempotency 未实现且无测试）— 这两条在 cron pilot 之前必须闭合。

**verdict 决策依据**：无 blocker 安全/事实错误；但 B001 是 schema 层的 invariant 漏洞，cron pilot 之前必须闭合；故整体 verdict 暂为 **WARN**，修订后无需重新走 M3.5 审查流程，可直接进 cron pilot 设计 gate。

---

**JSON 报告**

```json
{
  "review_id": "stock-picking-m4b-gate-2026-06-24",
  "caller": "agent:chat-main-agent:discord:channel:1518968470233022464",
  "domain": "stock-picking",
  "mode": "battle",
  "reviewer": "factory-reviewer",
  "model": "newapi-openai/MiniMax-M3",
  "reviewed_at": "2026-06-24",
  "verdict": "warn",
  "confidence": 0.85,
  "findings": [
    {"id": "B001", "severity": "blocker", "category": "consistency", "location": "src/scripts/validate_schema.py:_check_validation_event", "fix": "add cross-field rule: verdict==confirm iff promote_candidate==True"},
    {"id": "M001", "severity": "major", "category": "test_coverage", "location": "tests/test_m4a_validators.py:SchemaValidatorTests", "fix": "add negative test for verdict/promote mismatch"},
    {"id": "M002", "severity": "major", "category": "test_coverage", "location": "tests/test_m4a_validators.py + dry_run_orchestrator.py", "fix": "implement idempotency dedup and add regression test"},
    {"id": "M003", "severity": "major", "category": "cron_safety", "location": "src/references/gateway-cron.md", "fix": "explicit Gateway parameter whitelist"},
    {"id": "M004", "severity": "major", "category": "boundary", "location": "src/scripts/dry_run_orchestrator.py:_load_draft_records", "fix": "validate draft via validate_record before build_validation_events"},
    {"id": "m001", "severity": "minor", "category": "doc_consistency", "location": "src/references/gateway-cron.md:56", "fix": "clarify that registry stays package-internal"},
    {"id": "m002", "severity": "minor", "category": "test_maintainability", "location": "tests/test_m4a_validators.py:RegistryTests.test_required_rejects", "fix": "split into per-code tests"},
    {"id": "m003", "severity": "minor", "category": "performance", "location": "src/scripts/dry_run_orchestrator.py:run_validation", "fix": "add per-schema index cache in S5"},
    {"id": "m004", "severity": "minor", "category": "consistency", "location": "src/SKILL.md:5", "fix": "document verdict source as caller input in v1"},
    {"id": "m005", "severity": "minor", "category": "cli_design", "location": "src/scripts/dry_run_orchestrator.py:build_parser", "fix": "add --caller to validation subcommand"},
    {"id": "m006", "severity": "minor", "category": "doc", "location": "src/references/gateway-cron.md:Failure Handling", "fix": "split trigger delivery vs business failure"},
    {"id": "I001", "severity": "info", "category": "doc", "location": "design/reviews/M4b-selfcheck-2026-06-24.md", "fix": "update test count to 13"},
    {"id": "I002", "severity": "info", "category": "design", "location": "src/SKILL.md:frontmatter", "fix": "log v2 alias retention/deprecation"}
  ],
  "tests_run": {"total": 13, "passed": 13, "failed": 0},
  "out_of_scope_flags": [
    "src/scripts/position-monitor.py uses shell=True with .env interpolation — pre-M4b legacy, log for S5 risk-monitor flow rewrite"
  ],
  "ready_for_next_gate": false,
  "gate_decision": "WARN — close B001 and M002 before cron pilot; M001/M003/M004 also recommended"
}
```
