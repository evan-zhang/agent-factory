---
name: cms-sop
description: 统一SOP执行框架。触发词："新建SOP"/"创建任务"/"SOP"/"快速任务"/"完整SOP"/"SOP Lite"/"SOP Full"。自动判断 Lite（轻量）或 Full（完整）模式。
---

## 【必读】加载规则（Critical — 不得跳过）

每次触发必须严格执行以下步骤：

1. 判断模式（见下方条件）
2. **必须先读对应 guide 文件，再执行任何操作：**
   - Lite → `read references/lite-guide.md`
   - Full → `read references/full-guide.md`
3. 确认看到子文档**第一行**"# 已加载"标记，**才能继续**
4. **每次触发重新加载，禁止复用历史缓存**
5. **禁止在未读取 guide 的情况下直接调用 scripts/ 下的任何脚本**
6. 若脚本报错，必须按报错提示修正，**禁止忽略错误继续执行**

## 模式判断（满足任一→Full，模糊默认Full）

1. 预计耗时 > 20 分钟
2. 涉及 ≥ 2 个系统
3. 需要跨 gateway 协作
4. 需要多轮人工确认
5. 有发布/重启等高影响操作
6. 需要完整审计链路

以上均不满足 → **Lite**

## 硬性门禁（脚本内置，不可绕过）

| 门禁 | 条件 | 说明 |
|---|---|---|
| 进入 RUNNING | `checklistConfirmed=true` | 未完成确认单脚本直接拒绝 |
| 高风险操作 | 必须加 `--confirm` | DONE/ARCHIVED/UPGRADED 需显式确认 |
| upgrade.py | 只允许 Lite 实例 | Full 或已完成实例脚本直接拒绝 |
| increment-confirm | 第3次触发介入提示 | 超3轮自动输出 INTERVENTION_REQUIRED |

## 能力索引

| 操作 | 脚本 | 说明 |
|---|---|---|
| 创建实例 | `scripts/init_instance.py --mode lite\|full` | --title --owner --root |
| 状态管理 | `scripts/update_state.py` | --status --stage --action |
| 交接 | `scripts/handover.py` | --from-owner --to-owner --reason --next-steps |
| Lite→Full升级 | `scripts/upgrade.py` | --reason（仅限Lite实例）|

详细规则：
- Lite → `references/lite-guide.md`（guide-token 见文件第二行，写入 LOG.md 作审计）
- Full → `references/full-guide.md`（guide-token 见文件第二行，写入 LOG.md 作审计）
- 共用 → `references/shared/state-machine.md` / `confirm-protocol.md` / `upgrade-rules.md`

> **说明**：guide-token 用于版本追溯和可审计性，不用于安全门控。
> 真正的技术门控由脚本业务逻辑（上方硬性门禁）提供。
