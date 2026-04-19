# CAS Chat Archive - 部署配置指南（测试阶段）

项目：AF-20260326-002  
当前阶段：TESTING（灰度验证中）

## 1) 当前启用范围

已同步并启用 `cas-chat-archive-auto` internal hook：
- life
- ops
- company
- code

说明：
- 当前默认 `CAS_SCOPE_MODE=gateway`（稳妥测试模式）
- Agent 隔离能力已实现，待灰度确认后切换 `CAS_SCOPE_MODE=agent`

---

## 2) 核心环境变量

- `CAS_ARCHIVE_ROOT`（默认 `~/.openclaw/chat-archive`）
- `CAS_SCOPE_MODE`（`gateway` | `agent`）
- `CAS_DISK_WARN_MB`（默认 500）
- `CAS_DISK_MIN_MB`（默认 200）
- `CAS_MAX_ASSET_MB`（默认 100）
- `CAS_ALLOWED_ATTACHMENT_ROOTS`（可选扩展白名单）
- `CAS_STRICT_MODE`（默认 false，fail-soft）

---

## 3) 快速验收命令

```bash
# 1) 看 hook 是否启用
for g in life ops company code; do
  echo "=== $g ==="
  jq '.hooks.internal.enabled, .hooks.internal.entries["cas-chat-archive-auto"]' ~/.openclaw/gateways/$g/openclaw.json
done

# 2) 看今日日志是否落盘
today=$(date +%F)
for g in life ops company code; do
  echo "=== $g ==="
  ls ~/.openclaw/chat-archive/$g/logs/$today.md 2>/dev/null || echo "(no log today)"
done

# 3) 运营汇总（gateway视角）
python3 scripts/cas_inspect.py report --gateway all --scope-mode gateway

# 4) 运营汇总（agent视角，测试）
python3 scripts/cas_inspect.py report --gateway all --scope-mode agent --agent all
```

---

## 4) 手动复盘与分享去重

```bash
# 生成今日复盘（手动触发）
python3 scripts/cas_review.py daily --scope-mode agent --gateway all --agent all --out-dir ./design/reviews

# 查看某日是否已分享
python3 scripts/cas_review.py share-status --period daily --key 2026-03-27 --share-log ./design/SHARE-LOG.jsonl

# 标记已分享
python3 scripts/cas_review.py mark-shared --period daily --key 2026-03-27 --channel telegram:group:xxx --message-id 12345 --share-log ./design/SHARE-LOG.jsonl
```

规则：
- 默认不重复分享（以 SHARE-LOG 去重）
- 只有用户明确“强制分享”时允许重发

---

## 5) 测试阶段判定标准

通过标准（建议连续3天满足）：
1. 不影响正常聊天（无用户可感知阻断）
2. 归档日志稳定写入
3. 无严重错误信号
4. 容量增长可控

满足后建议切换：
- 从 `CAS_SCOPE_MODE=gateway` -> `CAS_SCOPE_MODE=agent`
