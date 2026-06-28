## 评审结论

**总体评级**：CONDITIONAL_PASS

**评审对象**：C 类代码改动 — bd-eval-cms v0.10.0 修复后版本（搜索能力内化）
**评审时间**：2026-06-14

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 正确性 | 4 | 上轮 5 个阻断点主体均已修复并经实测通过，但 core_search 配额计数仍有 off-by-one。 |
| 安全性 | 4 | 未发现凭证泄露或注入新增风险；路径/状态校验整体增强。 |
| 健壮性 | 4 | preflight、orchestrator、validate 的关键失败路径已补强；配额耗尽分支错误信息仍不准确。 |
| 可维护性 | 4 | 修复集中、命名清晰；validate 单测表达可再收紧，避免“预期失败”场景误报通过。 |
| 测试覆盖 | 4 | 健康检查、19 单测、validate 5 场景、真实 preflight、锁与 date 残留均已实际验证；配额边界测试暴露小缺口。 |

---

**关键问题**（最多 5 个）

1. [严重度：中] `core_search.sh` 当前窗口计数使用 `c_dt.timestamp() > ws_dt.timestamp()`，窗口第一笔调用时间等于 `window_start` 时不被计入，实测 60 秒窗口内可通过 101 次调用而非 100 次 → 修复建议：改为 `>=`，或在初始化窗口时不把首笔调用放入 `calls`，二选一并新增 100/101 边界单测。
2. [严重度：中] `core_search.sh` 的 `if ! acquire_quota; then local rc=$?` 会拿到取反后的状态码，导致配额耗尽时误报“抢不到配额锁” → 修复建议：改为先调用 `acquire_quota; rc=$?; if [ $rc -ne 0 ]; then ...`，确保 rc=1/2 分支准确。
3. [严重度：低] `validate_gate_search.sh --test` 对 T2-T5 使用 `validate ... || echo "(预期失败)"`，若这些用例意外成功，脚本仍会继续并打印“全部通过” → 修复建议：为预期失败用例显式断言失败，例如 `if validate ...; then exit 1; else echo "预期失败"; fi`。

---

**5 个修复点核对结果**

| 修复点 | 核对结果 | 结论 |
|---|---|---|
| 修复 1：preflight `$PROJECT_DIR` 未定义 | 已改为 `$(dirname "$STATE_FILE")`；我用 `/tmp` 最小完整 case 实跑，完整 case 通过，缺失 gate 状态时正确失败且不崩。 | 通过 |
| 修复 2：orchestrator 校验接入 + case_dir 推导 | `case_dir=$(dirname "$STATE_FILE")` 正确；`mark_gate` 仅在 `status=completed` 时调用 `verify_search_evidence`，其他状态不触发校验。 | 通过 |
| 修复 3：core_search 配额锁 | `mkdir` 不带 `-p`，macOS BSD 第二次 mkdir 实测正确拒绝；过期窗口/锁释放方向正确。但计数仍有 100→101 的边界误差，且配额耗尽错误信息误报锁失败。 | 条件通过，需小修 |
| 修复 4：validate_gate_search 加固 | one-pager 路径已修正；章节不存在必失败；引用与 reference 文件对应；reference 结构校验覆盖 URL/抓取时间/关键数据点；实测 T1 通过、T2-T5 均失败。 | 通过，测试断言可优化 |
| 修复 5：macOS `date -Iseconds` | `grep -rn "date -Iseconds" projects/2605281/bd-eval-cms/scripts/` 零残留；`iso_now()` 已接入 orchestrator/run/start/core。 | 通过 |

---

**实际验证记录**

- `bash projects/2605281/bd-eval-cms/scripts/bd-eval-cms-health-check.sh`：17✅ 1⚠️ 0❌，通过。
- `bash projects/2605281/bd-eval-cms/scripts/test-run-opportunity.sh`：19/19 通过。
- `bash projects/2605281/bd-eval-cms/scripts/search/validate_gate_search.sh --test`：T1 通过，T2-T5 输出预期失败，脚本退出 0。
- macOS `mkdir` 原子锁测试：第二次 mkdir 正确拒绝。
- preflight `/tmp` 最小完整真实 case：完整 case 通过；将 gate-5 改为 pending 后正确失败，无 `$PROJECT_DIR` 崩溃。
- `grep -rn "date -Iseconds" projects/2605281/bd-eval-cms/scripts/`：0 残留。
- 额外配额边界测试：stub `web_search` 后连续 101 次调用均成功，第 102 次失败；说明仍有 off-by-one。

---

**可优化点**

1. 给 `core_search.sh` 增加独立单测：窗口初始化、窗口过期、100/101 边界、锁占用、坏 JSON quota 文件。
2. `validate_gate_search.sh --test` 应显式区分“测试通过”和“验证器返回失败但这是预期”的断言逻辑。
3. 配额错误信息建议输出明确分支：quota exhausted / lock contention / quota file parse reset，便于现场排障。

---

**正面观察**

- 上轮高风险问题基本都被定点修复，没有只做表面替换。
- preflight 与 orchestrator 都已把搜索证据校验纳入主链路，避免“有脚本但没接入”的空转。
- validate 的防护强度显著提升，已能挡住空 reference、伪引用、缺章节、缺结构字段等关键绕过。
- `date -Iseconds` 清理彻底，macOS 兼容性风险已消除。

---

**可发版确认**

当前为 **CONDITIONAL_PASS**：方向正确，上一轮 5 个阻断问题已基本解除，但建议发版前完成以下 2 个小修，不需要重评：

1. 修复 `core_search.sh` 计数 off-by-one，确保 60 秒窗口严格最多 100 次。
2. 修复 `acquire_quota` 返回码捕获，确保配额耗尽与锁竞争错误信息准确。

---

**最重要的一条建议**

发版前先把 `core_search.sh` 的 100/101 配额边界和返回码误报修掉，这是本轮唯一仍影响运行语义的遗留点。
