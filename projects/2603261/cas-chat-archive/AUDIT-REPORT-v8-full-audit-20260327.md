# AUDIT-REPORT-v8 (Full Audit)

- 项目：AF-20260326-002 / cas-chat-archive
- 审计时间：2026-03-27 11:40~11:50 (Asia/Shanghai)
- 审计目标：对当前代码做“完整体检”：功能正确性 / 安全性 / 兼容性 / 可发布性 / 可运维性

---

## 1) 审计范围

代码与脚本：
- `scripts/cas_archive.py`
- `scripts/cas_inspect.py`
- `scripts/cas_review.py`
- `scripts/cas_hook.py`
- `scripts/publish.py`
- `scripts/test_cas.py`
- `hooks/cas-chat-archive-auto/handler.ts`

文档与部署：
- `README.md`
- `DEPLOYMENT.md`
- `config.example.yaml`
- `deploy-life.sh`

---

## 2) 执行证据（命令级）

1. 语法检查：
- `python3 -m py_compile scripts/*.py` ✅ 通过

2. 回归测试（默认 python3）：
- `python3 scripts/test_cas.py` ✅ 11/11 通过

3. 兼容性测试（python3.10）：
- `python3.10 scripts/test_cas.py` ✅ 11/11 通过
- 额外用例（Z 时区时间戳）：
  - `record-bundle` 输入 `timestamp=...Z` ❌ 失败（ValueError: Invalid isoformat string）

4. 打包检查：
- `python3 scripts/publish.py --dry-run --version 1.1.0-test.1 ...` ✅ 成功打包
- 检查包内容：仅 `SKILL.md + scripts/*`，**不含 `hooks/`**

5. 生产 hook 一致性：
- 四网关 hook 文件与仓库一致：`life/ops/company/code` ✅ 同步

---

## 3) 结论总览

- 总体结论：**核心功能可用，但存在 3 个高优先级风险，需在“测试->正式”前修复。**
- 严重度统计：
  - Critical: 1
  - High: 2
  - Medium: 2
  - Low: 2

---

## 4) 详细发现

### F-01 (Critical) Python 3.10 下 `Z` 时间戳解析失败（会导致归档失败）
- 位置：`scripts/cas_archive.py` `parse_ts()`
- 现象：`datetime.fromisoformat("...Z")` 在 py3.10 抛错。
- 影响：当前 TS hook 使用 `toISOString()`（带 `Z`），在 python3.10 环境可能全量归档失败（fail-soft 下主流程不挂，但数据会漏）。
- 复现：已复现（命令见证据第3条）。
- 建议：在 `parse_ts` 中统一兼容：`ts = ts.replace("Z", "+00:00")` 后再解析；并补充单测覆盖 `Z` 格式。

### F-02 (High) 打包产物不含 `hooks/`，自动归档能力无法随 Skill 分发
- 位置：`scripts/publish.py` (`ALLOWED_TOP_DIRS = {"scripts", "references", "assets"}`)
- 现象：`.skill` 包不含 `hooks/cas-chat-archive-auto/*`。
- 影响：通过市场安装后缺少 internal hook 代码，自动归档能力无法开箱即用。
- 建议：将 `hooks` 纳入白名单，并在打包后做“必要文件存在性”校验。

### F-03 (High) 测试覆盖偏差：测试的是 legacy `cas_hook.py`，不是线上启用的 internal hook `handler.ts`
- 位置：`scripts/test_cas.py`（当前仅调用 `cas_hook.py`）
- 影响：测试绿灯不等于线上链路绿灯，可能漏检 `handler.ts` 回归问题。
- 建议：新增针对 `handler.ts` 的集成测试（事件样本：`message:preprocessed` / `message:sent` / blocked attachment / scope-mode=agent）。

### F-04 (Medium) 文档与运行架构存在漂移
- 位置：`config.example.yaml`, `deploy-life.sh`
- 现象：仍以 `postResponse + cas_hook.py` 为主，未对齐 internal hook 方案。
- 影响：新部署者按旧文档会走错路径，增加运维噪音。
- 建议：保留 legacy 说明但明确“deprecated”，默认文档切到 internal hook。

### F-05 (Medium) 兼容性口径不一致
- 位置：`CHANGELOG.md`（历史写法提到 Python 3.8+）
- 现象：当前代码使用 `X | Y` 注解语法，最低需 py3.10。
- 影响：对外兼容承诺与实际不一致。
- 建议：统一改为“Python 3.10+”或回退类型写法到 `typing.Optional`。

### F-06 (Low) blocked 附件在“无文本且无可归档附件”场景下无告警输出
- 位置：`hooks/.../handler.ts`
- 现象：早退条件会跳过 blocked 列表日志。
- 影响：安全审计可观测性降低（仅极少场景）。
- 建议：将 blocked 检查前置，至少输出一次警告。

### F-07 (Low) 分享台账写入未做并发去重保护
- 位置：`scripts/cas_review.py` `mark-shared`
- 现象：并发写可能重复记录（逻辑上允许，但不够严格）。
- 影响：统计噪音。
- 建议：增加可选 `--idempotency-key` 或写前查重。

---

## 5) 建议修复优先级（按上线风险）

P0（必须先修）
1. F-01 `Z` 时间戳兼容
2. F-02 打包包含 `hooks/`
3. F-03 为 `handler.ts` 增加覆盖测试

P1（本轮建议修）
4. F-04 文档统一到 internal hook
5. F-05 兼容版本口径修正

P2（可随后）
6. F-06 blocked 可观测性增强
7. F-07 share-log 幂等增强

---

## 6) 审计结论

- 当前代码可继续灰度，但离“正式发布可回归可复制”还差一步：
  - **先补 P0 三项**，再做一次全量回归和四网关真实流量验收。
- 建议下一版本标记：`v1.1.0-rc1`（修复 P0 后）。
