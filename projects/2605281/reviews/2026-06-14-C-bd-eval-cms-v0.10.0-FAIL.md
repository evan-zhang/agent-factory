## 评审结论

**总体评级**：FAIL

**评审对象**：C 类代码改动 — bd-eval-cms v0.10.0（搜索能力内化）
**评审时间**：2026-06-14

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---:|---|
| 正确性 | 2 | 搜索证据门控的主路径存在运行时崩溃，orchestrator 的校验接口也未实际接入完成态写入。 |
| 安全性 | 2 | 配额锁与计数逻辑不可依赖，搜索调用可被并发绕过；证据校验可用空文件和伪引用轻易绕过。 |
| 健壮性 | 2 | 多处失败被静默降级或跳过，macOS/BSD date 兼容性仍有遗漏，核心脚本未覆盖真实调用路径。 |
| 可维护性 | 3 | 5 脚本职责拆分基本清楚，但 gate 配置硬编码、路径推导重复且已有错位，后续扩展容易继续出错。 |
| 测试覆盖 | 2 | bash -n、health-check、test-run-opportunity 均通过，但没有覆盖 v0.10.0 最关键的 preflight 搜索门控、配额并发、core_search 真实调用。 |

---

**关键问题**（最多 5 个）

1. [严重度：高] `scripts/preflight-phase.sh:155` 在 `set -u` 下引用未定义变量 `$PROJECT_DIR`，只要所有前置 gate 为 completed 并进入 v0.10.0 搜索证据校验就会直接崩溃；我用临时完整 case 复现为 `PROJECT_DIR: unbound variable` → 修复建议：改为传入已校验的 `CASE_DIR`，并为该分支补一个最小完整 case 的回归测试。
2. [严重度：高] `scripts/orchestrator-resume.sh:86-115` 声称“标记 completed 前先校验搜索证据”，但 `mark_gate()`（80-83）从未调用 `verify_search_evidence()`；同时 `verify_search_evidence()` 将 `STATE_FILE` 的 dirname 再取父目录（99-101），在当前 `STATE_FILE=$PROJECT_DIR/state.json` 结构下会错推到 skill root，导致校验被跳过或跑错目录 → 修复建议：在 `mark_gate gate completed` 前强制调用校验，并用 `PROJECT_DIR`/`dirname "$STATE_FILE"` 作为唯一 case_dir，不要再取父目录。
3. [严重度：高] `scripts/search/core_search.sh:35-62` 的配额管理不可用：`mkdir -p "$QUOTA_LOCK.dir"` 对已存在锁也返回成功，无法形成互斥；`window_start` 过期后未重置，`count` 在过期窗口后长期为 0；并发写 `quota.json.tmp` 也可能互相覆盖 → 修复建议：使用 `mkdir "$lockdir"` 原子抢锁 + `trap` 清锁；过期时重置 `window_start` 和 `calls`；计数使用当前窗口内 calls；对并发场景加测试。
4. [严重度：高] `scripts/search/validate_gate_search.sh:54-76` 的 UX 防偷懒门控强度不足且存在路径错配：`one-pager` 配置为 `One-pager.md`（29），实际产物在 `02-gate-by-chapter/One-pager.md`；章节文件不存在时只 warning 仍可能通过；文件数只统计 `*.md`，正文只 grep 任意 `[Gx-数字]`，空 reference 文件 + 伪引用即可过关 → 修复建议：章节缺失必须失败；校验引用编号对应真实 reference 文件；reference 文件至少校验 URL/抓取时间/关键数据点；修正 one-pager 路径。
5. [严重度：中] macOS bash/工具链兼容性仍未完全闭环：`orchestrator-resume.sh` 仍使用 `date -Iseconds`（BSD/macOS date 默认不支持），而 v0.10.0 声明“macOS bash 3.2 兼容性全部补齐”不成立 → 修复建议：统一改为 `date +%Y-%m-%dT%H:%M:%S%z` 或 python 生成 ISO 时间，并纳入 macOS 实机回归。

---

**可优化点**

- `core_search.sh:75-79` 定义了 `do_fetch()`，但主流程完全未调用；与“web_search/web_fetch + 输出 fetch_status”的设计/注释不一致。
- `projects/2605281/METADATA.json:29-33` 仍把 `multi-search` 标记为 required，与 v0.10.0 “无外部搜索 Skill 硬依赖”的说明冲突。
- `source_ranker.sh` 用 URL 子串匹配域名，可能把 `evil-nmpa.gov.cn.example.com` 判为 T1；建议解析 hostname 后做后缀域匹配。
- `keyword_templates.json` 对部分技能只有 2 个模板，低于文档宣称的 3-5 个；默认分支策略需要在模板里明确。

---

**正面观察**

- 版本号在 `VERSION`、`METADATA.json`、`bd-eval-cms/version.json`、`SKILL.md` frontmatter 四处均为 `0.10.0`。
- `bash -n` 覆盖 5 个搜索脚本及 3 个集成脚本无语法错误。
- `bd-eval-cms-health-check.sh` 当前通过：17 ✅ / 1 ⚠️ / 0 ❌。
- `scripts/test-run-opportunity.sh` 当前通过：19/19。
- 搜索子系统的职责拆分方向合理，source/keyword/field 三个轻脚本的基础单测可运行。

---

**可发版确认**

当前不可发版。必须至少完成以下修复后重新评审：

1. 修复 `preflight-phase.sh` 的 `$PROJECT_DIR` 崩溃，并新增真实 completed case 的 preflight 搜索门控测试。
2. 将 `verify_search_evidence()` 接入 completed 状态写入路径，修正 case_dir 推导。
3. 重写 `core_search.sh` 配额锁、窗口计数和并发写逻辑，并补并发/过期窗口测试。
4. 加固 `validate_gate_search.sh`：章节缺失失败、引用与 reference 文件一一对应、reference 内容结构校验、修正 one-pager 路径。
5. 修正 macOS `date -Iseconds` 兼容性，并用 macOS bash 3.2 实跑关键路径。

---

**最重要的一条建议**

先把“搜索证据门控”做成真实可执行、不可绕过的闭环；目前 v0.10.0 的核心卖点在主路径上会崩溃或被绕过，因此必须 FAIL。