# CAS 发布收口 SOP（v1.1.0-rc1）

适用范围：`life / ops / company`  
不纳入本期：`code`（deferred，经用户确认）

## 1) 发布前门槛（Go/No-Go）

必须全部满足：
1. 回归通过：`scripts/test_cas.py` = 14/14（py3.14 + py3.10）
2. 打包通过：`publish.py --dry-run --version 1.1.0-rc1`
3. 包内关键文件存在：
   - `SKILL.md`
   - `scripts/cas_archive.py`
   - `hooks/cas-chat-archive-auto/{HOOK.md,handler.ts}`
4. 目标网关 hook 启用：life/ops/company 的 `hooks.internal.entries.cas-chat-archive-auto.enabled=true`
5. 目标网关有真实落盘证据：life/ops/company 今日 in/out > 0

---

## 2) 发布流程（双通道）

### Step A：ClawHub
```bash
cd 04_workshop/AF-20260326-002/cas-chat-archive
python3 scripts/publish.py --channel clawhub --version 1.1.0-rc1 --changelog "RC release for life/ops/company"
```

### Step B：Internal
```bash
export CAS_INTERNAL_REGISTRY=<internal-registry-path>
cd 04_workshop/AF-20260326-002/cas-chat-archive
python3 scripts/publish.py --channel internal --version 1.1.0-rc1 --changelog "RC release for life/ops/company"
```

### Step C：记录台账
- 更新 `CHANGELOG.md`
- 更新 `P20260326-002-IDX-*`
- 更新 `03_governance/factory-registry.md`

### Step D：发布后页面核验（Internal）
- 引导 Evan 打开企业 Skill 市场主页：`https://skills.mediportal.com.cn/`
- 在页面上检查 `cas-chat-archive` 是否可见且信息一致（name/code/version/内部标记）。

---

## 3) 回滚策略（必须可执行）

触发条件（任一命中即回滚）：
- 归档显著漏记（连续采样 in/out 异常）
- hook 导致用户可见主流程异常
- 异常日志持续爆发且无法 30 分钟内止血

回滚动作：
1. 恢复上一稳定版本 `.skill`（建议 v1.0.3）
2. 保持 `CAS_STRICT_MODE=false`（避免阻断主链路）
3. 必要时临时 `hooks.internal.entries.cas-chat-archive-auto.enabled=false`
4. 回滚后立即执行 `cas_inspect.py report` 验证落盘恢复

---

## 4) 运行策略（当前阶段）

- 当前默认：`CAS_SCOPE_MODE=gateway`
- 切换到 `agent` 的门槛：
  1) 连续 3 天稳定（life/ops/company）
  2) 每日 report 无异常缺口
  3) 手动复盘链路运行稳定（share-log 去重可追溯）

---

## 5) 手动复盘操作规范（按用户确认）

默认模式：**手动触发 + 去重分享 + 可强制重发**

常用命令：
```bash
# 生成日报/周报/月报
python3 scripts/cas_review.py daily --scope-mode agent --gateway all --agent all --out-dir ./design/reviews
python3 scripts/cas_review.py weekly --week 2026-W13 --out-dir ./design/reviews
python3 scripts/cas_review.py monthly --month 2026-03 --out-dir ./design/reviews

# 分享去重
python3 scripts/cas_review.py share-status --period daily --key 2026-03-27 --share-log ./design/SHARE-LOG.jsonl
python3 scripts/cas_review.py mark-shared --period daily --key 2026-03-27 --share-log ./design/SHARE-LOG.jsonl
```
