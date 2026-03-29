# CAS Chat Archive - 复核审计报告 v2

审计时间：2026-03-27 06:30
项目：AF-20260326-002
范围：`cas_archive.py` / `cas_hook.py` / `publish.py` / `test_cas.py`

---

## 一、对上一版审计的复核结论

### 已确认成立
1. Gateway 名称未校验，存在目录逃逸风险（`../`）。
2. Hook 通过多次 subprocess 调用，性能开销偏大。
3. 磁盘满、权限异常等运行时异常处理不足。
4. 附件路径未限制来源目录，存在越权归档风险。

### 需要修正（上一版表述不准确）
1. **文件锁行为**：`flock(LOCK_EX)` 是阻塞等待，不是“立即返回”；但 `timeout_seconds` 参数确实未生效，可能造成无限等待。
2. **附件复制失败后仍写日志**：当前代码是先 `copy2` 再写日志；复制失败会直接异常退出，不会写入成功日志。

---

## 二、新增发现（本轮复核新增）

### N1（Critical）Hook 在长消息下会直接崩溃
- 现象：`cas_hook.py` 把完整消息作为 `--text` 命令行参数传给子进程。
- 复现实验：inbound 文本约 2.5MB 时，触发 `OSError: [Errno 7] Argument list too long`。
- 影响：长消息归档失败，且 hook 进程异常退出。
- 建议：改为临时文件传递（`--text-file`）或 stdin 传输，不走 argv。

### N2（Critical）发布包把自己打进了自己（自包含递归）
- 现象：`publish.py` 在 `dist/` 目录生成 `.skill`，同时 `os.walk(SKILL_DIR)` 又把 `dist/` 打进去。
- 实测：包内出现 `dist/cas-chat-archive-1.0.1.skill`（即包文件本身）。
- 影响：包体膨胀、结构污染，存在校验失败风险。
- 建议：打包时显式排除 `dist/`、`*.skill`、审计/部署文档。

### N3（High）发布成功状态可能“假阳性”
- 现象：未设置 `CAS_INTERNAL_REGISTRY` 时，internal publish 返回 mock 成功。
- 影响：流程显示“发布成功”，但实际上未发布。
- 建议：默认应返回失败（或明确 `--allow-mock` 才可通过）。

### N4（High）Hook 异常捕获不完整
- 现象：只捕获 `CalledProcessError`，未捕获 `OSError`（如 N1 场景）。
- 影响：会直接抛 traceback，影响稳定性。
- 建议：补充 `except OSError` 和兜底异常，保证 hook 不炸主流程。

### N5（High）skill 包内容超范围
- 现象：当前打包包含 `README.md` / `CHANGELOG.md` / `AUDIT-REPORT.md` / `DEPLOYMENT.md` 等。
- 影响：与技能最小化原则冲突，可能影响分发规范与审核通过率。
- 建议：仅保留 `SKILL.md` + `scripts/` + 必需资源。

### N6（Medium）会话状态更新存在并发竞态窗口
- 现象：`load_state -> maybe_session_header -> append_locked -> save_state` 不是同一临界区。
- 影响：极端并发时可能出现 session 编号或状态覆盖不一致。
- 建议：对 state 与 log 采用同一把锁（事务化写入）。

---

## 三、风险优先级（复核后）

### P0（立刻修）
1. N1 长消息 argv 崩溃
2. N2 打包自包含递归
3. Gateway 名称校验（目录逃逸）

### P1（本周修）
4. N3 内部发布假阳性
5. N4 Hook 异常兜底
6. state/log 并发一致性

### P2（下个迭代）
7. 磁盘容量阈值与告警
8. 附件大小限制
9. 附件路径白名单

---

## 四、结论

本轮复核后，上一版问题清单总体方向正确，但有 2 条表述需要修正；同时新增 6 条问题，其中 2 条为立即阻塞级（长消息崩溃、发布包自包含）。

建议先打一个 **v1.0.1-hardening** 补丁版，完成 P0 与 P1 后再推进自动化部署与外部分发。
