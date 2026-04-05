---
name: bp-auditor
description: 基于两级联动审计框架的 BP 审计 skill。触发词：BP审计 / 审计报告 / 诊断BP / 审计 G-1。输入 BP 编码，输出两级联动审计报告。
homepage: https://github.com/evan-zhang/agent-factory
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=bp-auditor
version: "1.0.0"
tools_provided:
  - name: fetch
    category: exec
    risk_level: medium
    permission: exec
    description: 通过 BP API 获取 BP 数据，支持 goal-code 和 bp-id 两种方式
    status: active
  - name: audit
    category: exec
    risk_level: low
    permission: exec
    description: 基于两级联动框架执行 BP 审计分析
    status: active
metadata:
  requires:
    env:
      - BP_APP_KEY
---

# bp-auditor

## 定位

BP 审计 skill，基于**两级联动审计**理念：
- **第一级**：根 BP 自身 Goal + KR + 举措 是否拆解清晰、充分
- **第二级**：根 BP 的每个 KR/举措，承接方（下级 BP）是否精准承接、有效落地

递归深度：**只到直接下级 BP，不继续往下追**

## 核心原则

### 编排者角色（Orchestrator）

编排者是调度者，**不是执行者**。原则：**Brain Only, No Hands**。

- 只调度：spawn sub-agent、协调、汇报
- 不执行：不直接读 API、不直接写报告、不自己跑 fetch.py

**正确流程**：编排者收到指令 → spawn 执行者 → 执行者完成 → 编排者汇报

### 触发词

- `BP审计`
- `审计报告`
- `诊断BP`
- `审计 G-1`
- `帮我做 BP 审计`

---

## 执行流程

### Step 1：Spawn 执行者获取数据

**执行者（Shangshu）** 负责数据获取：

```bash
python3 skills/bp-auditor/fetch.py --goal-code G-1 -o /tmp/bp-{CODE}.json
python3 skills/bp-auditor/fetch.py --bp-id {DOWNSTREAM_BP_ID}
```

### Step 2：Spawn 执行者按 GRV 框架分析

**执行者** 读取 `grv-template.md`，按框架逐层评估。

### Step 3：汇总报告，发给 Evan

---

## Sub-Agent 调度规范

### 调度前检查（必须执行）

**每次 spawn 前必须读取**：

1. `memory/self-improving/corrections.md`（最近3条）
2. `memory/self-improving/patterns.md`（相关成功模式）

格式：
```
读取 memory/self-improving/corrections.md
读取 memory/self-improving/patterns.md
```

### Spawn 标签格式

```
[bp-auditor] {阶段} - {任务描述}
```

示例：
```
[bp-auditor] DISCOVERY - 获取G-1数据
[bp-auditor] ANALYSIS - 评估下游BP
[bp-auditor] REPORT - 生成诊断报告
```

### Spawn 后必须执行

1. **立即 notify**：发送 "Started: {任务名}，Sub-Agent={类型}。可用 subagents list 查看状态。"
2. **立即 yield**：调用 sessions_yield，不同步等待

### 结果交付

Sub-agent 完成后：
- 自动 announce 结果
- 编排者用正常语气向 Evan 汇报：做了什么、结果在哪、发给 Evan

### 错误恢复

| 错误 | 处理方式 |
|------|---------|
| 429 模型超限 | 换模型重试，不自己执行 |
| sub-agent 失败 | 重 spawn，不自己接手 |
| 文件写入失败 | 检查是否用错了工具（edit vs write） |

### 文件预创建

如果 sub-agent 会写文件：
1. 先用 `write` 创建占位符文件
2. 在 task 里注明："文件已预创建，可用 edit 修改"

---

## 两级联动审计流程

```
Step 1: spawn 数据获取执行者 → fetch.py 获取根 BP 数据
Step 2: spawn 分析执行者 → 对根 BP 执行 Level 1 评估（Goal + KR + 举措）
Step 3: 识别下游 BP 列表
Step 4: for each downstream BP（分批 spawn）→ 对每个下游 BP 执行 Level 2 评估（Goal + KR + 举措）
        - 每批最多 3 个下游 BP
        - 每批完成后汇报进度
        - 避免单次 spawn 处理过多下游 BP 导致超时
Step 5: 汇总所有 P0/P1/P2 问题
Step 6: 生成报告 → 发给 Evan
```

### 下游 BP 处理原则

**问题**：下游 BP 数量多时，单次 spawn 会超时。

**解决方案**：分批处理，每批最多 3 个下游 BP。

```
# 伪代码
downstream_list = [BP1, BP2, BP3, BP4, BP5, BP6]
for batch in chunks(downstream_list, 3):
    for bp in batch:
        spawn audit_downstream(bp)
    wait_for_batch_completion()
    report_progress(len(completed), len(total))
```

---

## BP 节点评估标准

### 目标层

- 清晰性：description 非空
- 对齐性：有上游 KR/举措 承接
- 完整性：业务方向覆盖完整
- **注意：目标无 measureStandard，不检查**

### KR 层

- 充分性：KR 覆盖 BP 所有目标方向
- 独立性：KR 之间边界清晰
- SMART-S：measureStandard 定义业务边界（如"AI产品"需有定义）
- SMART-M：measureStandard 含数字（null = P0）
- 匹配性：责任人能力与 KR 方向匹配
- 支撑性：有举措或下游承接

### 举措层

- 完整性：举措覆盖 KR 方向
- 科学性：举措设计合理
- 标准性：有明确交付物
- 可执行性：有人/时间/资源
- 有效性：能支撑 KR 实现
- 延期风险：截止日期是否过期（>30天 = P0）

---

## 问题分级

| 级别 | 判定原则 |
|------|---------|
| **P0** | KR measureStandard 为 null / 举措过期 >30天 / 目标设计失效 / 承接口径断裂 |
| **P1** | 局部缺陷 / 举措标准模糊 / 无因果链 / 责任人匹配存疑 |
| **P2** | 优化建议 |

---

## 诊断深度要求

每个问题必须包含：
1. **问题描述**：具体是什么
2. **根因分析**：为什么发生
3. **多方案**：至少2个解决路径
4. **建议方案**：明确推荐哪个
5. **行动责任人**：谁来做

---

## 文件说明

| 文件 | 作用 |
|------|------|
| `fetch.py` | 数据获取脚本（调用 BP API） |
| `grv-template.md` | 两级联动审计框架（含评估维度和诊断深度要求） |
| `report-template.md` | 最终报告格式规范 |
| `skills/bp-manager/scripts/bp_client.py` | BP API 客户端（fetch.py 依赖） |
| `skills/cms-cwork/scripts/cwork-search-emp.py` | 员工查询（用于核实责任人身份） |

---

## 特殊约束

- **顶级目标（如 G 层）**：跳过"对齐性"检查（无上游，不需要对齐）
- **目标层**：不检查 measureStandard（目标本来就没有）
- **KR 层**：重点检查 measureStandard 是否为 null
- **举措层**：检查延期天数，>30天 = P0
