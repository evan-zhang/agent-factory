## 审查结论

**总体评级**：WARN
**置信度**：0.88
**审查对象**：M4c + M4d cron pilot gate 闸门 — `cron_readiness.py`、operator notification route contract、Gateway cron 设计稿、显式 manual-pilot override 流程
**审查时间**：2026-06-24
**审查模式**：M4c/M4d 闸门（quick 单轮 battle-mixed）
**使用模型**：MiniMax-M3 (subagent)

被审材料：
- `PLAN.md`
- `design/DESIGN.md`
- `design/reviews/M4c-cron-readiness-selfcheck-2026-06-24.md`
- `design/reviews/M4d-operator-calendar-selfcheck-2026-06-24.md`
- `src/references/gateway-cron.md`
- `src/scripts/cron_readiness.py`
- `src/scripts/operator_notification.py`
- `src/scripts/dry_run_orchestrator.py`
- `tests/test_m4a_validators.py`（共享）

跨轮次吸收参考：
- M3.5 闸门：3 项 schema 漂移 major（M001-M003）已在 M4a Week 1 通过 `validate_schema.py` 关闭（`evidence_id: ev_<ulid>` 正则、双轨 evidence quality 字段 `publisher_authority + ai_classified_quality` 保留、`claim.v1` 恢复 `claim_kind + polarity`），M4b B001（`promote_candidate` ↔ `verdict` 互斥）已在 `validate_schema._check_validation_event` 关闭并加负例测试。

本地验证：
- `python3 -m unittest discover -s tests -v` → Ran 25 tests OK
- `python3 -m py_compile src/scripts/*.py` → OK
- `python3 src/scripts/cron_readiness.py --event-root /tmp/.../events --registry src/strategies/registry.yaml --custom-refs src/strategies/custom_refs.yaml` → 5/5 checks pass, exit 0
- `python3 src/scripts/operator_notification.py --route route.json --event-root ...` → 接受合法 route + 拒绝非 dry-run / 缺字段 route

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 可执行性 / 本地 dry-run 真能跑 | 5 | 25 测试全过；`cron_readiness.py` 直接以 `tmpdir` 跑通 discovery → validation 全链；operator notification 接受合法 route 并产出结构化 payload；`py_compile` 干净。 |
| 闸门覆盖度（M4c 自检声明的 7 项） | 4 | absolute event root ✅ / TAROC active+cron ✅ / Chokepoint 非 cron ✅ / CLI allowlist ✅ / discovery idempotency ✅ / confirm validation 双事件 ✅ / promote/verdict 互斥 ✅。但**没有**任何"production_calendar 必须拒"的 check。 |
| M4b B001 关闭落实 | 5 | `validate_schema._check_validation_event` 强加 `promote_candidate == (verdict=='confirm')`；`test_validation_event_rejects_promote_verdict_mismatch` 负例在；`cron_readiness.check_validation_gate` 独立端到端验证；orchestrator 也不再有 `promote = verdict == 'confirm'` 的"代码层对齐"作为唯一防御。 |
| operator notification 边界（不发送、不触网） | 5 | 模块无网络调用、无 file write（除 JSON dump 到 stdout）、`CHANNELS = {discord, telegram, email, local_log}` 是白名单字符串而**不是调用对象**；`build_failure_payload` 永远 `dry_run: True`，payload schema 标 `operator_notification_payload.v1`。 |
| calendar source 三态白名单 + 强制 override reason | 4 | argparse `choices` 锁死三态；`manual_pilot_override` 无 `--calendar-override-reason` 即拒绝（`calendar_override_reason_required`）；`run_context.context_warnings` 注入 `not_production_calendar` 与 `calendar_override_reason_present`。**但**：`production_calendar` 通过且无任何 warning（详见 M001）。 |
| 与 S3 DESIGN / M3.5 一致性 | 4 | cron 不在 skill 内（DESIGN §2 不做清单 + §3.2 模块边界）守住；execution guard / approval gate / migrate_legacy_csv 仍未触及（不在本闸门范围）；Chokepoint maturity_gate 在 registry 保留。DESIGN §5 Decision Log 2026-06-24 两条新决策（cron 闸门、manual_pilot_override）已落。 |
| 测试覆盖与可回归性 | 4 | 25 测试覆盖 schema 16 + registry 4 + execution guard 2 + event_store 3 + orchestrator 7 + cron_readiness 3 + operator_notification 3；新增 cron 闸门三件套独立可跑；缺：`production_calendar` 拒绝 / 重放 vs 重跑 UX / `severity_min` 实际过滤（详见 m001-m003）。 |
| 自我报告准确性 | 3 | M4c selfcheck 写 "Ran 20 tests OK"、M4d selfcheck 写 "Ran 25 tests OK"，实测均为 25 — M4c 数字已陈旧（M4d 之前合并的 5 个新测试未计入 M4c selfcheck 计数器）。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| M001 | major | 闸门缺口 / 设计违规 | `src/scripts/dry_run_orchestrator.py` L253 + L323 + `src/scripts/cron_readiness.py` 全文 | `production_calendar` 是 M4d 设计的"reserved"标签，DESIGN §5 与 `gateway-cron.md` L88 明确"Production cron must not be enabled until `run_context.v1.calendar_source=production_calendar` is backed by a real market-calendar source"。但 argparse 仅 `choices=[dry_run_fixture, manual_pilot_override, production_calendar]`，orchestrator 对 `production_calendar` 不做拒绝 / 不打 warning、不验证是否真有 `market-calendar` source；`cron_readiness` 五项 check 也未对此拦截。本地实测：`--calendar-source production_calendar` + `--caller cron` + `--strategy-id taroc` 跑出 `ok=true, dispatch=dispatch, 4 events written`，`run_context.context_warnings` 仅有 `calendar_source:production_calendar`，**没有** `not_production_calendar`。 | 实测复现；`build_run_context` L80-83 仅对 `{dry_run_fixture, manual_pilot_override}` 加 `not_production_calendar` warning，对 `production_calendar` 视为"已就位"。 | 在 `build_run_context` 加分支：`if calendar_source == "production_calendar" → context_warnings.append("production_calendar_label_requires_real_source")`；或更严格——`--calendar-source production_calendar` + 非 `caller=manual` 时直接 reject `code=production_calendar_requires_real_source`，并在 `cron_readiness` 加第 6 项 check `production_calendar_blocked_for_cron`。 |
| M002 | major | Gateway cron 安全 / 边界模糊 | `src/references/gateway-cron.md` L74-80 | CLI 允许清单列了所有 flag 的合法名，但**没有显式禁止** Gateway 把 user-controlled 字段（`strategy_id` / `custom_ref` / `caller`）透传给 orchestrator。M4b 闸门已记 M003（同一个 doc），但 M4c/M4d 闸门中 gateway-cron.md 仍未加"参数来源约束"或"Gateway 必须按 schema/registry 派生参数，禁止从 user message 转发"。当前 doc 只说"必须设 `--caller cron`"和"不得传 shell fragments / raw paths / 未知 flags"，未约束 `--strategy-id` 与 `--custom-ref` 的来源。 | gateway-cron.md 全文 grep 未出现"参数来源"/"do not forward user" 等约束；与 M4b 的 M003 同源。 | 在 gateway-cron.md §"Trigger Contract" 加一段："Gateway 必须从 cron schedule config 派生 `--strategy-id` / `--strategy-version` / `--universe-ref` / `--custom-ref`，禁止从 user message、notification payload、Discord thread history 转发这些字段。" |
| M003 | major | 一致性 / operator 通知契约 | `src/scripts/operator_notification.py` `build_failure_payload` + `gateway-cron.md` L104-118 | `severity_min` 字段被 `validate_route` 强校验（拒绝非 `info/warning/critical`），但 `build_failure_payload` **永远** 写 `severity: warning`，从不读 `severity_min` 也不按其过滤。`severity_min: critical` 的 route 也会收 `severity: warning` 的 payload，与"按严重度过滤"的常规契约语义不符。 | 实测：`severity_min: critical` + 跑 `build_failure_payload` → `payload.severity = "warning"`；代码 grep 未发现任何 `severity_min` 引用除 `validate_route` 的白名单校验。 | 决策二选一：(a) `build_failure_payload` 按 `severity_min` 决定是否生成 payload（critical route 收到 info/warning payload → 跳过），并在 payload schema 加 `filtered_out: true/false`；(b) `severity_min` 仅作为"文档化期望"，删除 validator 中 `invalid_severity` 强校验。倾向 (a)，与"分层降噪"惯例一致。 |
| m001 | minor | 测试覆盖 | `tests/test_m4a_validators.py` `CronReadinessTests` | 仅 3 项 cron_readiness 测试（happy / relative event_root / chokepoint cron），未覆盖：(a) `production_calendar` 被闸门拦截（M001 修复后需补）；(b) `event_root` 父目录不可写（如只读文件系统）；(c) `--calendar-source manual_pilot_override` 但缺 reason 在 readiness dry-run smoke 中失败；(d) `severity_min` 在 operator_notification 中实际过滤（M003 修复后需补）。 | `CronReadinessTests` 类 grep 仅 3 个 `def test_`；`OperatorNotificationTests` 仅 3 个测试。 | 至少补 3 个：`test_readiness_blocks_production_calendar_for_cron`、`test_route_severity_min_filters_payload`、`test_dry_run_smoke_rejects_manual_pilot_without_reason`。 |
| m002 | minor | 设计 / UX | `src/scripts/cron_readiness.py` `check_dry_run_smoke` | smoke 用 `tempfile.mkdtemp(prefix=".cron-readiness-smoke-", dir=event_root)` 在 event_root 下建临时目录并发事件，最终 `shutil.rmtree` 清理。这违反 `gateway-cron.md` L74 "Do not write canonical events under `src/`, `tests/`, or the installed skill directory" 的精神（小写：smoke 仍把临时目录塞在 event_root），且若 smoke 中途异常 + `ignore_errors=True` 清理失败，会留下脏文件污染下一次 readiness run。 | `cron_readiness.py` L131 + L171；无 `--keep-smoke` / `--smoke-root` 显式选项。 | smoke 用独立 `tempfile.mkdtemp()` 不嵌入 event_root；或在 `event_root/.cron-readiness-smoke-<ts>/` 子目录名前加 `.` 并在 README/selfcheck 写明"残留不污染业务事件路径"。 |
| m003 | minor | 一致性 | `src/references/gateway-cron.md` "Failure Handling" + `operator_notification.py` | gateway-cron.md "Failure Handling" 写"notify the configured operator route with `request_id`, `correlation_id`, `reject.code`, and event paths when available"，但 `operator_notification.build_failure_payload` 只接受 `run_result` dict（提供 `request_id` / `correlation_id` / `reject_code` / `event_root` / `run_mode` / `market` / `strategy_id`），**没有** event paths 字段（`atomic_request.v1.jsonl` 等路径）。Gateway 拿到 payload 后**仍无法**定位具体哪个 JSONL 写失败。 | `build_failure_payload` L67-83 仅 7 个 include_fields；gateway-cron.md 期望"event paths when available"。 | `operator_notification_payload.v1` 加可选字段 `event_paths: [str]`（来自 `run_result.written[].event_path`），并在 `REQUIRED_FIELDS` 不强制但文档化为 "when available"。 |
| m004 | minor | 一致性 / 文档 | `design/reviews/M4c-cron-readiness-selfcheck-2026-06-24.md` L29 | selfcheck 写 "Ran 20 tests OK"，实测 25，且 M4d selfcheck 也写 25。说明 M4c selfcheck 是在 M4d 测试合并前写就，未随 batch 更新。 | 实测 `unittest discover -s tests` → `Ran 25 tests in 0.037s`；两份 selfcheck 数字不一致。 | M4c selfcheck 数字改为 25（或拆成"M4c 阶段测试数 + 总测试数"两栏）；M3.5 selfcheck 也回顾 grep 一遍（之前报告也偶有"12 vs 13"漂移）。 |
| m005 | minor | 边界 / 可观察性 | `src/scripts/cron_readiness.py` L84-99 `check_cli_allowlist` | 用 `parser.parse_args(allowed)` 验证允许 flag，再用 `parse_args(allowed + ["--broker", "futu"])` 期望 `SystemExit` 来证明"未知 broker flag 被拒"。但 argparse 的行为是"未知 long-option → error + exit 2"，这等价于"任何 orchestrator 子命令之外的未知 flag 都被拒"，并未证明"已知子命令 flag 之外的 broker/action 调用面被拒"。若 orchestrator 将来给 discovery 加 `--broker` 选项（无 `--action`），本测试会假阳性。 | `check_cli_allowlist` 仅做一次 negative；未做"discovery 仍拒绝 --action / --buy / --sell 等"覆盖。 | 在测试中再追加一组 negative args（如 `["discovery", "--buy"]`、`["discovery", "--send-discord"]`），并断言 `SystemExit`；或读取 `orchestrator` 模块 docstring/源码 grep `sub.add_parser("broker")` 显式证明子命令集。 |
| m006 | minor | 设计 / 一致性 | `src/scripts/dry_run_orchestrator.py` `build_validation_events` L177-203 | `validation_event.v1.signal_date` 写 `_today()`（**今天**），不取 `--signal-date` 或 draft 原始 signal_date。意味着同一天对历史 draft 重跑 validation 时，`signal_date` 会变成"重跑当天"，破坏 audit 一致性（虽然 idempotency 由 `(draft_id, validation_run_id, calendar_checked_at, validation_session_key)` 保住，但 `signal_date` 仍是 misleading）。 | `build_validation_events` L190 直接 `_today()`；DESIGN §4.1 risks 明示"Validation idempotency breaks on rerun → use `calendar_checked_at` and `validation_run_id`; do not rely only on `signal_date`"。 | `signal_date` 取自 `draft.signal_date` 或 args 的 `--signal-date`（若 validation 加）；`_today()` 仅作 fallback 并打 `context_warnings.append("validation_signal_date_fallback_to_today")`。 |
| I001 | info | 文档 | `src/references/gateway-cron.md` L98-103 | 文档示例 route 用 `target: "/tmp/stock-picking-operator.log"`（绝对硬编码 `/tmp`），Gateway 在 macOS 上 `/tmp` 是 symlink-resolved per-user，跨用户路径不可用；Linux container 内 `/tmp` 又可能无写权限。 | gateway-cron.md 示例 JSON 第 4 行 `target: "/tmp/stock-picking-operator.log"`。 | 把示例 target 改为占位符 `${STOCK_PICKING_OPERATOR_LOG}` 或 `~/.stock-picking/operator.log`，并在 L7 注明"示例路径，生产 Gateway 必须改成可写位置"。 |
| I002 | info | 设计 / UX | `src/references/gateway-cron.md` "Idempotency" | 文档写"Retries should still be operator-visible, and intentional re-runs must use a new schedule window key"，但 `dry_run_orchestrator.run_discovery` 在 idempotent replay 时**不写** `run_context.v1`，仅返回 `{ok:true, idempotent_replay:true, written:[]}`。Gateway 看到 `written: []` + 没有新 event_path，**无法** 在 retry 时区分"已经写过" vs "orchestrator 抛了写入异常" vs "event_root 不可写"。 | `run_discovery` L243-249 仅返 `idempotent_replay: True`，未把"上次写的 event_path"传回 Gateway；gateway-cron.md 期望 retry 时"operator-visible"。 | idempotent replay 时附加 `last_written_paths: [str]`（来自 store 反查），并在 `operator_notification_payload.v1` 加可选字段；或至少 `run_discovery` 返回 `previous_event_path` 用于 operator 日志。 |
| I003 | info | 文档 | `design/DESIGN.md` §5 Decision Log | M4c / M4d 两条决策已记录，但 `dry_run_orchestrator.py` L323 把 `production_calendar` 列为合法 choice 的事实**未在 Decision Log** 注明"v1 暂不阻断 production_calendar，待 M4e 接入真实 calendar source 后改 reject"。 | DESIGN Decision Log 末条是 M4d；orchestrator 已接受 production_calendar。 | 加一条 Decision Log："2026-06-24: M4d 保留 `--calendar-source production_calendar` 为 argparse 合法值，仅作为未来 marker；orchestrator 当前不阻断，依赖 M4e 真实 calendar source + cron_readiness 新 check 拦截。" |

---

**闸门结论**

- **M4c cron_readiness.py 本地 dry-run pilot gate**：**PASS**（仅 dry-run fixture 范围）
- **M4d operator_notification.py 路由契约**：**PASS**（dry-run-only 边界守住）
- **M4d 显式 manual-pilot override**：**PASS**（reason 强制 + warnings 注入）
- **production cron 部署闸门**：**BLOCK**（待 M001 修复 + M4e 真实 calendar 接入）

---

**进栈判断：是否允许进入下一阶段？**

**条件性允许进入 production-backed market calendar / cron pilot deployment design 阶段（M4e 设计），附带 3 项必须修订项**。

理由：
- M4c/M4d 在 dry-run 范围内实现完整、测试覆盖良好、boundary 守住（无网络 / 无 broker / 无消息发送）；
- 25 个测试全过，本地 cron_readiness 五项 check 全过，operator_notification 接受合法 route + 拒绝非 dry-run；
- B001（M4b blocker）已在 schema 层补上，与 cron 闸门联动正确；
- **但** M001（production_calendar 未拦截）+ M002（参数来源未约束）+ M003（severity_min 死代码）是必须修订的边界问题，不修即进 M4e 会导致"先污染后清理"。

修订后可直接进 M4e 设计，不需要再走一次 M4c/M4d 闸门。

**必须修订（3 项）**：
1. **M001** — `--calendar-source production_calendar` 在 cron caller 下必须显式 reject 或至少打 `not_production_calendar` warning；`cron_readiness` 加 check。
2. **M002** — `gateway-cron.md` §Trigger Contract 加一段"参数来源约束"：Gateway 必须从 cron schedule config 派生 `--strategy-id` / `--strategy-version` / `--custom-ref` / `--universe-ref`，禁止从 user message / notification payload / thread history 转发。
3. **M003** — `operator_notification.build_failure_payload` 实现 `severity_min` 实际过滤（或将其降为"文档化期望"）。

**建议修订（不阻塞）**：m001-m003 测试补全；m004 selfcheck 数字校正；m005 cli_allowlist 增加 negative coverage；m006 validation signal_date 来源修正；I001-I003 文档清理。

**禁止事项（即便修订完成也不允许）**：
- 在 production_calendar 真实接入 + cron_readiness 加对应 check 之前，禁止 Gateway 真正 enable cron schedule（仅允许 manual pilot + dry_run fixture）。
- 在 M002 修复前，禁止 Gateway 接收 user-supplied strategy_id / custom_ref 透传（即便仅 manual 路径）。

---

**最重要的一条建议**

**M001 必须修**——`production_calendar` argparse 合法 + orchestrator 不阻断 + cron_readiness 不检查 = 三层防御全部形同虚设。Gateway 误传 `--calendar-source production_calendar`（看似合理，因为 argparse 允许）就能跳过整个 M4d 设计意图。补一处 `--calendar-source production_calendar` 显式 reject + cron_readiness 加一项 check，整条链路恢复"production_calendar 仅作未来 marker"的语义。这条比 B001 更隐蔽——B001 是 schema 内不一致，写事件时立刻可见；M001 是"看着像合规但实际绕过 M4d 设计"。

---

## 归档元数据

- 审查对象类型：D 类（脚本 / 工具）+ 部分 B 类（gateway-cron 设计）+ 部分 C 类（operator_notification route contract）
- 审查模式：M4c/M4d 闸门（quick 单轮 + battle 局部）
- 上轮结论：M3.5 闸门 WARN（3 major M001-M003 schema 漂移，已在 M4a 关闭）；M4b 闸门 WARN（B001 promote/verdict 互斥，已在 M4a 关闭）
- 本轮结论：WARN（0 blocker / 3 major / 6 minor / 3 info）
- 进入下阶段：条件性通过 → M4e production-backed market calendar / cron pilot deployment design（M001-M003 修订完即可进；production cron 真实 enable 仍 BLOCK）
- 不可降级为 PASS 的原因：M001 + M002 + M003 任一项都会让 cron pilot 在真实 Gateway 启用时静默越界；属"边界未守"型问题，不是事实错误或逻辑跳跃

## 模型信息
- 使用模型：newapi-openai/MiniMax-M3
- 审查 subagent：factory-reviewer / M4c-M4d 闸门