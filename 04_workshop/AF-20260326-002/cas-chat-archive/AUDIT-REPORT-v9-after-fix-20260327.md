# AUDIT-REPORT-v9 (After Fix)

- 项目：AF-20260326-002 / cas-chat-archive
- 时间：2026-03-27 11:48~11:56 (Asia/Shanghai)
- 目标：修复 v8 审计的 P0 问题并复测

---

## 已修复项

### P0-1 时间戳 `Z` 兼容（已修）
- 文件：`scripts/cas_archive.py`
- 变更：`parse_ts()` 增加 RFC3339 `...Z -> +00:00` 归一化
- 结果：Python 3.10 下可正常处理 hook 生成的 ISO 时间

### P0-2 打包缺失 hooks（已修）
- 文件：`scripts/publish.py`
- 变更：
  - `ALLOWED_TOP_DIRS` 增加 `hooks`
  - 新增 `REQUIRED_ARCHIVE_ENTRIES` 强校验
  - 打包后校验关键文件必须存在
- 结果：`.skill` 包已包含 `hooks/cas-chat-archive-auto/{HOOK.md,handler.ts}`

### P0-3 测试覆盖错位（已修）
- 文件：`scripts/test_cas.py`
- 变更：新增 internal hook `handler.ts` 集成测试（通过 Node+TypeScript 动态转译执行）
  - agent scope 归档路径验证
  - 附件白名单阻断验证
- 结果：测试覆盖从 legacy hook 扩展到线上 internal hook 主链路

---

## 同步优化

- `hooks/.../handler.ts`：当事件无可归档文本但存在越界附件时，也会输出 blocked 告警（可观测性增强）。
- 文档对齐：
  - `config.example.yaml` 改为 internal hook 主路径（legacy 标记 deprecated）
  - `README.md` 增加运行要求（Python 3.10+）
  - `deploy-life.sh` 下一步提示改为 internal hook
  - `CHANGELOG.md` 新增 `1.1.0-test.1` 修复记录
  - `SKILL.md` 明确 Python 3.10+ 基线

---

## 复测结果

1) 语法检查：
- `python3 -m py_compile scripts/*.py` ✅

2) 全量回归：
- `python3 scripts/test_cas.py` ✅ 14/14
- `python3.10 scripts/test_cas.py` ✅ 14/14

3) 打包校验：
- `python3 scripts/publish.py --dry-run --version 1.1.0-test.2` ✅
- 包内关键文件校验：`missing []` ✅

4) 运行态同步：
- 已同步 hook 文件到 `life/ops/company/code` 的 gateway state hooks 目录 ✅

---

## 当前结论

- v8 报告中的 P0 三项已全部关闭。
- 代码已具备继续灰度验收条件。
- 下一步建议：继续完成四网关真实流量 E2E 验收（重点 ops/company/code），通过后再评估默认切换 `CAS_SCOPE_MODE=agent`。
