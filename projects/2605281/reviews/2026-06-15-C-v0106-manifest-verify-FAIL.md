## 评审结论

**总体评级**：FAIL

**评审对象**：C 类代码改动 — fe30fd5 / bd-eval-cms v0.10.6 manifest + verify-manifest
**评审时间**：2026-06-15

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---|---|
| 正确性 | 1 | verify-manifest 的核心 required_files 校验在管道 while 子 Shell 中执行，结果计数与失败数组未回传，导致缺零件也可通过；preflight 还要求 phase-5-5-html 在渲染前已 completed，流程自相矛盾。 |
| 安全性 | 3 | 未见凭证泄露；路径多数加引号，但 JSON 拼接用 shell 变量直接嵌入 Python 字符串，遇特殊字符存在输出破坏/注入风险。 |
| 健壮性 | 2 | JSON 解析失败、缺 state 可处理，但空目录/缺文件关键路径被子 Shell bug 吞掉；sync 无参数在 set -u 下会非友好退出。 |
| 可维护性 | 3 | 引入 manifest 作为单一真相源方向正确，但 shell 内多段内联 Python + 管道状态副作用较难维护，preflight 职责迁移遗漏了旧校验。 |
| 测试覆盖 | 2 | 材料声称有 render-sample 与 --json 验证，但未覆盖“空目录/缺 required_files 应失败”这一最关键路径，也未覆盖 preflight 渲染前状态。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] `verify-manifest.sh` 用 `echo "$MANIFEST_ITEMS" | while ...; do check_file ...; done` 执行 required_files 校验，Bash 中管道右侧在子 Shell 运行，`FAIL_ITEMS/WARN_ITEMS/PASS_COUNT/TOTAL_COUNT/JSON_RESULTS` 的修改不会回到主 Shell；实测只含 completed `state.json`、缺全部零件的目录仍输出“通过: 2 / 2”并 exit 0 → 修复建议：改为 here-string / process substitution（如 `while ...; do ...; done <<< "$MANIFEST_ITEMS"`），或用临时文件/纯 Python 完成全量校验，并新增空目录缺文件回归测试。
2. [严重度：高] `preflight-phase.sh` 委托 manifest 后继承了 `state_gates_must_be_completed` 中的 `phase-5-5-html`，但 preflight 是 Phase 5.5 HTML 生成前检查；渲染前要求 `phase-5-5-html=completed` 会阻断正常首次渲染 → 修复建议：manifest 区分“渲染前 required gates”和“归档后 required gates”，或 verify-manifest 增加 mode（preflight/sync），preflight 不应要求自身完成。
3. [严重度：中] v0.10.0 旧 preflight 中的搜索证据校验 `scripts/search/validate_gate_search.sh` 被 193→71 行重构移除，而 manifest notes 又明确 evidence 目录暂不纳入；这不是等价保留，可能放过无证据/引用不足的 Gate → 修复建议：将搜索证据作为 manifest 的独立校验段或在 preflight 委托 verify-manifest 后继续执行 `validate_gate_search.sh`。
4. [严重度：中] `verify-manifest.sh --json` 通过多段 `python3 -c` 将 `$item_label/$description/${file_reasons[*]}` 直接嵌入 Python 单引号字符串；路径或描述含 `'`、换行、反斜杠时会破坏 JSON 输出甚至执行异常 → 修复建议：用环境变量/argv 传参给 Python，或一次性由 Python 读取 manifest 并生成 JSON，避免 shell 字符串插值。
5. [严重度：低] `sync-to-knowledge-base.sh` 在 `set -u` 下直接 `CASE_DIR="$1"`，无参数时会触发 unbound variable 而非可操作错误；且 `MISSING_WARNINGS` 命名已不准确（实际是 fail 计数） → 修复建议：改为 `CASE_DIR="${1:-}"` 并显式报用法；重命名计数变量为 `MISSING_FAILS`。

---

**最重要的一条建议**

先修复 `verify-manifest.sh` 的管道子 Shell 状态丢失，并用“仅有 state.json、缺全部 required_files 必须 exit 1”的测试锁死，否则 fail-closed 校验体系当前实际上是 fail-open。
