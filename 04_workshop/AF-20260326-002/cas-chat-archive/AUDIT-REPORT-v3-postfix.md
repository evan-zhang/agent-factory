# CAS Chat Archive - 复核审计报告 v3（修复后）

时间：2026-03-27 06:41
范围：v1.0.1-hardening 改动后复核

## 已修复项（本轮确认）

1. **目录逃逸**（已修）
- 现状：gateway 名称增加正则校验，仅允许 `[A-Za-z0-9._-]`。
- 结果：`--gateway ../escape` 现已拒绝。

2. **长消息 argv 崩溃**（已修）
- 现状：hook 改为 `--text-file` 临时文件传递，不再把长文本塞进命令行参数。
- 结果：长文本回归测试通过。

3. **发布包自包含递归**（已修）
- 现状：打包改为白名单（仅 `SKILL.md` + `scripts/` + 可选 `references/assets`），排除 `dist/` 和 `__pycache__`。
- 结果：产物不再包含自身 `.skill` 文件。

4. **内部发布假阳性**（已修）
- 现状：默认缺少 `CAS_INTERNAL_REGISTRY` 会失败；仅在 `--allow-mock-internal` 下允许 mock 成功。

5. **锁超时参数无效**（已修）
- 现状：文件锁改为非阻塞轮询 + timeout（默认 5s）。

6. **大文件缺少限制**（已修）
- 现状：`record-asset` 增加 `--max-asset-mb`（默认 100MB）。

## 仍建议继续优化（未阻塞）

1. **state 与 log 事务一致性**
- 目前消息写入与 session-state 写入仍不是同一原子事务。

2. **hook 进程开销**
- 仍采用 subprocess 调 cas_archive（已修稳定性，但未做函数内调用级优化）。

3. **附件路径白名单**
- 仍建议限制到 Gateway upload 目录，避免误归档任意路径文件。

4. **磁盘空间预检/告警**
- 仍建议加入剩余空间阈值预警。

## 验证结果

- `python -m py_compile`：通过
- `test_cas.py`：8/8 通过
- `publish.py --dry-run --version 1.0.1`：通过
- 打包内容检查：仅包含 `SKILL.md` + `scripts/*.py`

## 当前结论

v1.0.1-hardening 已达到“可灰度测试”标准，可继续在 life/factory/ops 进行观察；
建议并行排期 v1.0.2 做事务一致性与路径白名单强化。
