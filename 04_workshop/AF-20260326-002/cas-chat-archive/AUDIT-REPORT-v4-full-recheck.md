# CAS Chat Archive - 全面复核报告 v4

时间：2026-03-27 06:46
目标：对已发现问题做“全量复核”，确认是否遗漏，并给出更优解。

---

## 1) 复核范围与方法

- 代码静态复查：`cas_archive.py` / `cas_hook.py` / `publish.py` / `test_cas.py`
- 行为验证：
  - 长文本 Hook 回归
  - 发布脚本 dry-run 与产物内容检查
  - 并发写入压力复测
  - 安全探针（附件任意路径）

---

## 2) 复核结论（是否找全）

结论：**上一轮未找全，存在新增高优先级问题**。

新增确认的问题：

### F1（Critical）session-state 原子写并发冲突
- 现象：`save_state` 使用固定临时文件名 `session-state.json.tmp`。
- 并发下多个进程会互相覆盖/抢占，出现：
  - `FileNotFoundError: ... session-state.json.tmp -> session-state.json`
- 影响：部分写入报错，状态更新不稳定。

### F2（High）附件路径白名单仍缺失（已实测）
- 现象：hook 允许归档任意可读路径文件。
- 实测：可归档 `/etc/hosts` 到 assets。
- 影响：存在越权归档风险（数据外带面）。

### F3（Medium）Hook 多 subprocess 架构仍偏重
- 现状：稳定性已提升，但每条消息仍多次进程创建。
- 影响：吞吐上限受限，高并发场景延迟不优。

### F4（Low/Process）ClawHub 发布与本地打包策略不一致风险
- 现状：`publish.py` 本地打包已白名单；但 `clawhub publish <dir>` 仍可能按目录语义发布。
- 影响：若 ClawHub 侧未过滤，可能带入非必要文件。

---

## 3) 已确认解决的问题（复核通过）

- 目录逃逸（gateway 参数）✅
- 长消息 argv 崩溃 ✅
- 包内自包含递归 ✅
- internal 发布假阳性 ✅
- 锁超时参数失效 ✅
- 大文件缺少上限 ✅

验证：
- `test_cas.py`：8/8 通过
- `publish.py --dry-run --version 1.0.1`：通过
- 包内容检查：仅 `SKILL.md + scripts/*.py`

---

## 4) 更优解决方案（建议）

## 方案A（最稳，推荐）——“单锁 + 单事务 + 事件优先”

核心思想：
1. 用同一把 gateway/day 级锁保护 `log + state`（同临界区）。
2. state 不再用固定 `.tmp`，改 `mkstemp` 唯一临时文件再 `os.replace`。
3. 所有消息先写事件日志（append-only），session 可异步整理/重建。

优点：
- 彻底解决 F1 并发冲突。
- 宕机可恢复（事件日志可重放）。
- 可演进到批量写入。

代价：
- 实现复杂度中等。

## 方案B（快速止血）——“state 独立加锁 + 唯一 tmp”

1. 给 `session-state.json` 单独加锁文件。
2. 临时文件名改为 `session-state.<pid>.<tid>.tmp`。
3. 写 state 失败不影响消息日志落盘（降级策略）。

优点：
- 改动小，修复快。
- 48小时内可上线。

代价：
- 架构上仍是“双写分离”，长期仍建议转方案A。

## 方案C（性能优先）——Hook 进程内直调

1. 把 `cas_archive.py` 抽成可导入模块（`archive_core.py`）。
2. `cas_hook.py` 直接函数调用，去掉多数 subprocess。

优点：
- 延迟明显降低。
- 错误处理更统一。

代价：
- 需要重构结构并补回归测试。

## 附件路径安全（强制）

建议策略：
- 默认只允许：`~/.openclaw/gateways/<gateway>/uploads/` 下路径。
- 增加 `CAS_ALLOWED_ATTACHMENT_ROOTS` 白名单扩展。
- 非白名单路径：拒绝并记录安全告警。

---

## 5) 建议执行顺序

P0（今天）
1. 修 F1：state 并发冲突（至少上方案B）
2. 修 F2：附件路径白名单

P1（本周）
3. Hook 直调重构（方案C）
4. ClawHub 发布前加入“实际产物清单检查”

P2（下迭代）
5. 转方案A（事件优先 + 可重放）
6. 加磁盘阈值告警与运维面板

---

## 6) 结论

- 这次“全面复核”结果：**之前并未找全**，现在补齐了关键遗留（尤其 F1）。
- 当前代码可继续灰度，但若要“最高标准上线”，建议先完成 P0 两项。
