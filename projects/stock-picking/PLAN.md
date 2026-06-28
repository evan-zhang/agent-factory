# PLAN.md — stock-picking

## 当前状态

**S6 release gate 已通过（factory-reviewer conditional_go，2026-06-25）**，stock-picking pilot 正式进入 **S7：生产 cron 启用 + 4 周观测**。S5a-S5f 最小生产链路、pilot 评估底座、cron contract、positive evidence gate、pytest.ini、cron-manifest 快照全部就绪；67/67 测试通过。下一步：实跑 3 档 cron 一次验证 Discord 投递，然后开始 4 周 PASS/WATCH 比例追踪决定是否扩 universe。

## 已完成

- [x] 收集 stock-picking-v2 原始结构与问题
- [x] 收集 serenity/chokepoint 方法论资料
- [x] 记录原始需求讨论到 `DISCUSSION-LOG.md`
- [x] 保存完整情报摘要到 `intelligence-brief.md`
- [x] 重写 `REQ-01.md`：从单体交易系统改为模块化 SOP 编排层
- [x] 在 `REQ-01.md` 中补充全流程图与逐节点评审稿

## 进行中

- [x] 节点 0：外部触发入口评审会
- [x] 节点 1：交易日与运行上下文检查评审会
- [x] 节点 2：策略选择器评审会
- [x] 节点 3：TAROC Strategy 评审会
- [x] 节点 4：Chokepoint Strategy 评审会
- [x] 节点 5-8：候选生命周期评审会（WARN 已补契约）
- [x] 节点 9-12：行动与风险层评审会（已核对 quant 台账）
- [x] 节点 13：Research Evidence Store 评审会
- [x] S2 总体基线收敛与冲突清理
- [x] 起草 `design/GRV.md`
- [x] GRV Battle 一轮审查（WARN）
- [x] 修订 `design/GRV.md`，吸收 B001 + M001-M005
- [x] GRV Battle 二轮复审（WARN，无 blocker / major）
- [x] 创建 S3 `design/DESIGN.md`
- [x] 创建 registry baseline 与 registry selector 设计
- [x] 将 `src/references/data-schema.md` 升级为 P0 schema baseline
- [x] 创建 execution guard skeleton plan
- [x] M3.5 reviewer 闸门审查（WARN，0 blocker，3 major）
- [x] 修订 `data-schema.md`，补 `## Schema Changelog` 并回贴 REQ-01 evidence/claim 基线
- [x] 补齐 migration / registry / custom_refs / execution-guard 的 M3.5 minor 缺口

## 下一步

- [x] 自检 S3 文件一致性
- [x] 调用 factory-reviewer 做 M3.5 闸门审查
- [x] 根据 M3.5 结果修订 S3 baseline
- [x] M4a Week 1：实现 `src/scripts/validate_schema.py`，用正/反例 fixtures executable close M001-M003
- [x] M4a Week 1：实现 `src/scripts/validate_registry.py`，覆盖 registry snapshot / custom_ref / Chokepoint 拒绝用例
- [x] M4a Week 1：实现 execution-guard decorator/proxy skeleton 与 7 条拒绝测试
- [x] 决定各模块是独立 skill、子 skill 目录，还是先以 references/ 子模块落地：S4/S5 前保持单 skill package + 分离 flows/references/scripts
- [x] M4b：重写旧 `src/SKILL.md`，移除 CSV 单体和自动交易叙述
- [x] M4b：补齐 `target-pool` / `approval` / `reconcile` / `risk-monitor` flow skeleton
- [x] M4b：收敛 discovery / validation / weekly-review 到事件 schema 输出
- [x] 设计统一数据契约，重点补 `strategy_id`、`source_evidence`、`confidence`、`next_step`
- [x] M4b：实现 append-only event store 与 legacy CSV projection skeleton
- [x] M4b：实现最小 discovery dry-run orchestrator
- [x] M4b：实现最小 validation dry-run orchestrator
- [x] 设计 Gateway cron 外部调度方案（S4 后部署侧文档）
- [x] M4b WARN 修订：validation promote/verdict 一致性、discovery 幂等、cron 参数白名单、draft-file schema 校验
- [x] 设计 execution guard 最小骨架和拒绝用例
- [x] M4c：实现 `src/scripts/cron_readiness.py`，把 Gateway cron pilot design gate 变成可执行检查
- [x] M4c：补 readiness tests，覆盖 absolute event root、Chokepoint 禁 cron、CLI allowlist、discovery 幂等与 validation gate
- [x] M4d：定义 operator notification route contract
- [x] M4d：封装 dry-run calendar fixture，强制显式 manual-pilot override reason
- [x] M4d：请求 factory-reviewer 做 cron pilot gate 复审（WARN，3 major）
- [x] M4d WARN 修订：`production_calendar` hard reject、Gateway 参数来源约束、operator `severity_min` 阈值过滤
- [x] M4e：接入 production-backed market calendar source（pandas-market-calendars v5.4.0）
- [x] M4e：实现 `src/scripts/market_calendar.py`，覆盖 CN/HK/US 三市场交易日/休市日/半日市判断
- [x] M4e：改 `dry_run_orchestrator.py`，移除 `production_calendar` hard reject，替换为真实日历查询
- [x] M4e：更新 `cron_readiness.py`，将 guard 检查改为 integration 检查
- [x] M4e：编写 16 项测试，全部通过
- [x] M4e：更新 `gateway-cron.md` 文档
- [x] M4e：factory-reviewer 复审（reviewer 超时降级为自检，0 blocker/0 major/2 minor，结论 PASS）
- [x] Operator notification route 配置（Discord #stock-picking，production mode）
- [x] Gateway cron 定时任务创建（CN/HK/US 三市场，周一至五）
- [x] 全链路手动验证（CN discovery 成功写入 4 个事件）

**S4 全部完成。S5a-S5f 最小生产链路与 pilot 评估底座已落地：config universe → Longbridge 只读行情 → web_search 研究协议 → research/claim adapter → 频道报告 wrapper → pilot analyzer。下一步等待首轮 cron 实跑，并按 analyzer 输出调 universe。**

## S5 进度

- [x] S5a：新增 `src/scripts/market_data.py`，支持 Longbridge quote 只读行情、CLI JSON 前缀解析、quote evidence 生成
- [x] S5a：`dry_run_orchestrator.py` 新增 `--market-data-source longbridge_quote`，真实 quote 写入 `evidence_ref.v1` + `draft_candidates.v1`
- [x] S5a：补 `tests/test_s5_market_data.py`，全量 47 tests 通过
- [x] S5a：真实 Longbridge smoke 成功（US quote 写入 atomic/context/dispatch/evidence/draft 事件链）
- [x] S5a：三市场 Gateway cron payload 切换为 `longbridge_quote` 模式，仍保持 dry_run、禁止交易
- [x] S5b：新增 `src/scripts/research_data.py`，支持 research JSON → `evidence_ref.v1` + `claim.v1`
- [x] S5b：`dry_run_orchestrator.py` 支持 `--research-file`，把 positive / negative evidence 回填到 draft
- [x] S5b：真实 Longbridge quote + research fixture smoke 成功
- [x] S5c：新增 `src/scripts/discovery_report.py`，生成频道可读 TAROC discovery 摘要
- [x] S5c：新增 `src/scripts/discovery_job.py`，只在本次写入 draft 时渲染报告，休市日输出 HEARTBEAT_OK
- [x] S5c：三市场 Gateway cron payload 切换到 `discovery_job.py`
- [x] S5d：新增 `src/scripts/research_protocol.py`，生成正/负面搜索计划并校验 research JSON
- [x] S5d：三市场 Gateway cron payload 接入 web_search 研究协议，强制 negative_query 执行和 validate gate
- [x] S5e：新增 `src/config/universe.yaml`，CN/HK/US 默认 universe 从 smoke symbols 扩到高流动性候选池
- [x] S5e：`market_data.py` / `research_protocol.py` / `dry_run_orchestrator.py` 支持 `--universe-file` + `--universe-ref`
- [x] S5e：三市场 Gateway cron payload 改为读取 universe config；HK 从 09:00 错峰到 09:08，降低 Longbridge rate limit 风险
- [x] S5f：新增 `src/scripts/pilot_analyzer.py`，自动检查 candidate/universe 覆盖、quote evidence、正面研究、负面搜索、claim 覆盖
- [x] S5f：三市场 Gateway cron payload 接入 pilot analyzer；非 HEARTBEAT_OK 输出会附带 PASS/WATCH 分析

## S6 进度（release gate · 2026-06-25 通过）

factory-reviewer 出具 `conditional_go`（claude-sonnet-4-6, 4 项 findings），全部已闭环：

- [x] F001 major：移除 `gateway-cron.md` validate 命令中误用的 `--candidate-limit`
- [x] F002 major：`validate_research_file` 强制 `positive_search_min_results=1`，positive=[] 直接 reject
- [x] F003 minor：新增 `pytest.ini`，`.venv` 内 `pytest -q` 无需手动 PYTHONPATH 即可 67/67 通过
- [x] F004 minor：归档 `design/cron-manifest-2026-06-25.json`，CN/HK/US 三档完整 schedule + isolated session + dry-run prompt + Discord 投递目标全部可独立审查
- [x] 复跑全测：67 passed, 4 warnings
- [x] 评审报告：`design/reviews/S6-release-review-2026-06-25.json`

## S7 进度（生产 cron 启用 + 4 周观测）

- [ ] S7a：实跑 3 档 cron 一次（最近交易日），确认 Discord #stock-picking 频道收报无误、报告语言/格式符合预期
- [ ] S7b：建立 4 周观测窗口（2026-06-25 起），按周记录 PASS/WATCH 比例与噪音事件
- [ ] S7c：根据 pilot_analyzer 输出与频道反馈，按市场调 universe（噪音高的剔除、流动性差的替换）
- [ ] S7d：观察 Longbridge quote 与 web_search 在三市场的耗时与失败率，必要时调 cron timeout / 错峰窗口
- [ ] S7e：4 周观测期满后，factory-reviewer 出 pilot retrospective，决定是否进入 S8（扩 universe / 加 Chokepoint manual flow / 接 my-positions 对账）

### Cron 任务清单

- cn-discovery: 09:00 周一至五 | A股 | Job ID: 8ea1b3ea
- hk-discovery: 09:08 周一至五 | 港股 | Job ID: bdc05e89
- us-discovery: 21:30 周一至五 | 美股 | Job ID: c115530a

## 关键决策

- cron 不属于 skill 内部职责，由 Gateway 外部调度
- 选股策略必须可替换，TAROC 与 Chokepoint 平级
- 复选、追踪、持仓监控、移动止损都应能独立复用
- `stock-picking` 是 SOP 编排层，不是大而全单体 skill
- Ralph Loop 前必须先通过 S3 设计与 M3.5 审查
- S4 拆为 M4a 安全/验证底座与 M4b 业务模块，避免并行上下文爆炸
- execution guard 是 P0，不是后补修复清单；真实 buy 无 approval 必须 hard error
- data-schema 的 evidence/claim 字段以 REQ-01 Node 13 为基线：`ev_<ulid>`、`cl_<ulid>`、`claim_kind + polarity`、双轨 evidence quality
- cron readiness 批准本地 dry-run pilot gate 及 production calendar（M4e 已接入 pandas-market-calendars）；Chokepoint 仍禁 cron
- production schedule 需 operator notification route 配置；calendar source 已由 M4e 提供真实数据

## 关键文件

- `REQ-01.md`
- `DISCUSSION-LOG.md`
- `intelligence-brief.md`
- `design/GRV.md`
- `design/DESIGN.md`
- `src/references/data-schema.md`
- `src/references/registry-design.md`
- `src/references/execution-guard.md`
- `src/references/gateway-cron.md`
- `src/scripts/cron_readiness.py`
- `src/scripts/pilot_analyzer.py`
- `src/scripts/operator_notification.py`
- `src/strategies/registry.yaml`
- `src/SKILL.md`（M4b 已重写为 SOP orchestration entrypoint）
