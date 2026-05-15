# BD评估 Skill — 速查卡

## 触发词

- "BD评估" / "跑品种" / "评估新药" / "BD品种筛选" / "新批次"

## 一句话启动

> 给我评估以下品种：CG-0255、RHOFADE、门冬氨酸钙片

---

## 完整流水线

```
Phase 1: DISCOVERY        ~5分钟/品种
Phase 2: 模板Battle        ~10分钟/品种
Phase 3: GRV逐章节        ~30分钟/品种（最耗时）
Phase 4: GRV Battle       ~15分钟/品种
Phase 5: 报告合并+终检    ~5分钟/品种
HTML生成+上传+归档         ~10分钟/品种
─────────────────────────────────────────
合计                      ~75分钟/品种
```

## 单命令操作速查

### 跑完整流程
```
评估品种：{名称1}、{名称2}
```

### 只生成HTML（已完成报告）
```
生成HTML：CG-0255、RHOFADE
```

### 只上传归档（已有链接）
```
归档：CG-0255，报告链接: https://...，Battle链接: https://...
```

## 文件位置

```
~/.openclaw/skills/bd-eval/
├── SKILL.md                           ← 主入口
└── references/
    ├── SOP.md                         ← 完整流程规范
    ├── sub-agent-prompt-template.md   ← 子Agent prompt
    └── bd_report_templates_full.md    ← 7套模板

projects/bd-eval/{品种名}/
├── state.json                         ← 状态文件
├── links.md                           ← 在线报告链接（归档）
├── 01-discovery.md                    ← 发现文件
├── 02-grv-by-chapter/                ← 逐章节GRV
├── battle/                            ← Battle对抗文档
├── 03-battle-summary.md               ← Battle摘要
└── 04-final-report.md                 ← 最终报告
```

## 并行执行

最多5个并发，建议：
- 5个品种并行 → Phase1-2
- 完成后继续 Phase3-5
- 超过5个分两批

## 子Agent超时应对

Phase3 超时时，记录完成章节数，主会话补全或手工编译。

## 归档脚本

```bash
~/.openclaw/skills/bd-eval/scripts/archive-links.sh \
  CG-0255 \
  "https://doc.20100706.xyz/raw/xxx" \
  "https://doc.20100706.xyz/raw/yyy"
```

## 问题追踪

| # | 问题 | 状态 |
|---|------|------|
| 1 | Phase3 超时导致章节不完整 | 待改进 |
| 2 | Phase2 模板Battle 部分跳过 | 待改进 |
| 3 | HTML 风格不统一 | 待确认 |
