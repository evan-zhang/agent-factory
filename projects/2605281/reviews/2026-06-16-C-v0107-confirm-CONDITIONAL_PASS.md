## 评审结论

**总体评级**：CONDITIONAL_PASS

**评审对象**：C 类代码改动确认 — bd-eval-cms v0.10.7 / commit ef5771c
**评审时间**：2026-06-16

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 正确性 | 4 | v0.10.6 的关键 fail-open 校验、preflight 自循环、搜索证据调用、sync 参数处理均已修复；v0.10.7 的 SOP、placeholder、caseCode 修复基本到位。 |
| 安全性 | 4 | 未见凭证入仓，AppKey 改为 `.secrets/kb_appkey`，手动 caseCode 已拒绝空白、路径分隔符和引号；剩余 JSON 输出插值风险主要限本地自动化输出。 |
| 健壮性 | 4 | data=null 已降级为 `uploaded_no_preview` 且不再用假 fileId 调 preview，失败态更可解释；但 `uploaded_no_preview` 未回写到 state 的显式状态仍可改进。 |
| 可维护性 | 4 | manifest 分层 gate、SOP 与脚本凭证读取方式趋于一致，修复方向清晰；但 `start-phase.sh` 的占位说明与前置实际副作用仍容易误读。 |
| 测试覆盖 | 3 | 从代码可确认修复点存在，但未看到本次提交附带针对空目录 manifest、data=null、非法 caseCode 的自动回归测试。 |

---

**10 个问题修复状态确认**

| # | 问题 | 状态 | 确认依据 |
|---|---|---|---|
| 1 | P0 管道子Shell bug → here-string 修复 | 已修 | `verify-manifest.sh` 使用 `done <<< "$(echo "$MANIFEST_ITEMS")"`，`FAIL_ITEMS/PASS_COUNT/TOTAL_COUNT/JSON_RESULTS` 可回到主 shell。 |
| 2 | preflight 循环依赖 phase-5-5-html → `--mode render` | 已修 | `preflight-phase.sh` 调用 `verify-manifest.sh "$CASE_DIR" --mode render`；manifest 的 `state_gates_required_for_render` 不含 `phase-5-5-html`。 |
| 3 | `validate_gate_search` 误删 → preflight 恢复调用 | 已修 | `preflight-phase.sh` L72-L82 恢复 `scripts/search/validate_gate_search.sh`，按警告不阻断处理。 |
| 4 | JSON 输出注入（TODO）→ 确认风险可接受 | 可接受但未修 | `verify-manifest.sh --json` 仍有 shell 变量嵌入 Python 字符串；但 manifest/文件名为受控本地输入，非外部 API 暴露面，本轮可作为已知中风险 TODO 放行。 |
| 5 | sync 无参数报错 → `CASE_DIR="${1:-}"` + 友好报错 | 已修 | `sync-to-knowledge-base.sh` L23-L29 使用默认空值并输出用法示例，避免 `set -u` unbound variable。 |
| 6 | SOP 与脚本不一致 → python3 + `.secrets/kb_appkey` | 已修 | SOP Phase 5.5 L781-L794 明确脚本用 `python3 -c` 解析 config、AppKey 从 `.secrets/kb_appkey`；config.yaml L65-L68 同步说明。 |
| 7 | `saveFileByPath data=null` placeholder 不可靠 → `uploaded_no_preview` 降级 | 已修 | `sync-to-knowledge-base.sh` L385-L392 将 data=null 标为 `REPORT_STATUS="uploaded_no_preview"`，明确不尝试 preview ticket。 |
| 8 | sync 手动 caseCode 没 sanitize → 加 sanitize 校验 | 已修 | `sync-to-knowledge-base.sh` L30-L38 对第二参数拒绝空白、`/`、反斜杠和引号。 |
| 9 | “Phase 5.5 流程断裂” | 部分误报 / 仍需澄清 | L111-L114 确有“当前为占位实现”说明，支持“实际由 orchestrator/AI 调 render_report.sh + sync”的解释；但同一脚本 L43-L93 对 `phase-5-5-html` 仍会实际改 state、跑 preflight、直接 sync，且不调用 render。若该入口仍可被调用，原问题不是完全误报。 |
| 10 | “uploadContent 100002” | 误报倾向 | 当前 `API_BASE="https://sg-al-cwork-web.mediportal.com.cn/open-api"`，普通文件上传实际请求 `${API_BASE}/document-database/file/uploadContent`，代码层面已带 `/open-api` 前缀；未在本次只读评审中复现 100002。 |

---

**关键问题**（最多 5 个）

1. [严重度：中] `start-phase.sh` 对 `phase-5-5-html` 不是纯占位：L43-L93 有实际 preflight/sync/state 修改逻辑，但 L111-L114 又声明“当前为占位实现”，容易让评审和执行方对主链路产生相反理解 → 修复建议：二选一收敛：要么删除/禁用该分支的实际副作用，仅保留任务提示；要么把它补齐为 `preflight(render) → render_report.sh → sync` 的真实入口。
2. [严重度：低] `uploaded_no_preview` 降级不会在 state.json 中写入专门状态；当前回写逻辑只处理 `success` 和 `failed`，可能导致上层无法程序化识别“已上传但无预览” → 修复建议：在回写段增加 `uploaded_no_preview` 分支，记录 `reportHtmlStorage='kb-uploaded-no-preview'`、resourceId、kbPath 和人工查找提示。
3. [严重度：低] `verify-manifest.sh --json` 的 Python 字符串插值风险仍未消除 → 修复建议：后续用环境变量/argv 或纯 Python 重写 JSON 聚合，避免路径/描述中的引号破坏输出。

---

**最重要的一条建议**

把 Phase 5.5 的唯一入口彻底收敛：若 `start-phase.sh` 是占位，就不要执行 sync；若它是入口，就必须显式串起 `preflight(render) → render_report.sh → sync`，避免“占位说明”和“实际副作用”并存。
