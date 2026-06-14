# 字段抽取规范（v0.10.0 半自动 → v0.10.1 全自动）

> 本文档定义 v0.10.0 半自动字段抽取流程和 v0.10.1 全自动升级路径。

## v0.10.0 半自动（当前版本）

**核心思想**：脚本只给提示词，实际抽取由 sub-agent 用 LLM 完成 + 人工确认。

### 流程

```
sub-agent 调 field_extractor.sh --gate gate-1-regulatory
    ↓
返回 markdown 提示词（含必抽字段 JSON schema）
    ↓
sub-agent 用 LLM 抽取（基于 web_fetch 抓取的文本）
    ↓
sub-agent 输出 JSON 草稿
    ↓
**人工确认关键字段**（approval_date / holder / indication）
    ↓
写入 references/{prefix}/{prefix}-XXX.md
```

### 6 个 Gate 的提示词

| Gate | 用途 | 最低字段数 |
|------|------|----------|
| gate-1-regulatory | 监管/批准 | 7 |
| gate-2-clinical | 临床证据 | 8 |
| gate-3-market | 市场/竞争 | 7 |
| gate-4-pricing | 准入/定价 | 7 |
| gate-5-cmc | CMC/工艺 | 6 |
| default | 兜底 | 灵活 |

### 防护机制（防 sub-agent 偷懒）

1. **必抽字段填 `null` 视为证据不足**——不是直接拒绝，但下游会被警告
2. **关键字段人工确认不可跳过**——preflight 校验章节含引用 `[{prefix}-XXX]`
3. **最低文件数门槛**——validate_gate_search.sh 强制 references/{prefix}/ 有 ≥2 个文件

## v0.10.1 全自动升级路径（占位）

### 触发条件

只有当 **v0.10.0 半自动的抽取准确率 >85%** 时才允许 v0.10.1 全自动上轨。

### 升级步骤

1. 准备 10 个 case 集
2. LLM 抽取 → 人工 ground truth 对比
3. 准确率 <85% → 停开 v0.10.1，维持 v0.10.0
4. 准确率 ≥85% → 升级 v0.10.1：field_extractor.sh 内部加 LLM 调用
5. 人工确认改为抽检（5% 随机抽 + 异常率告警）

### 风险

- v0.10.1 一旦上线，sub-agent 可能完全信任自动结果，**人工抽检一旦漏过就可能写入错误数据**
- 需保留 **每个字段的来源 URL + 原文片段** 才能复盘

## 当前 v0.10.0 不做的事

- ❌ LLM 自动调用（留 v0.10.1）
- ❌ 字段值交叉验证（如"持有人"和"批准文号"互相校验）
- ❌ 字段补全（缺字段不补，标 null）
- ❌ 字段标准化（如"医保乙类"统一为"Reimbursement: B"）
