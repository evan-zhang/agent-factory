---
name: bp
description: 玄关 BP 统一工作平台。触发词：
- BP审计 / 审计报告 / 诊断BP / 审计G-1 → 深度诊断（根因+方案+行动）
- BP评估 / 评分 / 评估G-1 → 结构化评分（P0/P1/P2）
- 创建BP / 更新KR / 管理BP → 数据操作（CRUD）
---

# BP 统一工作平台

## 定位

BP 的管理、评估、审计三个能力统一入口。共享同一套数据接口（BP API + CWork API），按触发词路由到不同工作流。

## 触发词路由

### → 审计流程（bp-auditor）

触发词：`BP审计` / `审计报告` / `诊断BP` / `审计G-1` / `帮我做BP审计`

输出：深度诊断报告（问题描述+根因分析+多方案+建议方案+行动责任人）

### → 评估流程（bp-evaluator）

触发词：`BP评估` / `评分` / `评估G-1` / `给BP打分`

输出：结构化评分（P0/P1/P2 + 可实现性评级）

### → 管理流程（bp-manager）

触发词：`创建BP` / `更新KR` / `管理BP` / `查BP` / `查KR`

输出：数据操作结果

---

## 共享数据接口

所有流程共享：

**BP API**：`scripts/bp_client.py`
- `BPClient.get_goal_detail(id)` — BP Goal
- `BPClient.get_key_result_detail(id)` — KR（必须用这个，get_goal_detail 拿不到 measureStandard）
- `BPClient.get_action_detail(id)` — 举措
- `BPClient.list_actions(kr_id)` — KR 下的举措列表
- `BPClient.get_task_children(bp_id)` — BP 下的子节点

**CWork API**：`scripts/cwork_client.py`
- `search_emp(name)` — 查询员工信息

---

## 审计流程（bp-auditor v4.0）

### 诊断深度五要素

每个问题必须包含：
1. 问题描述
2. 根因分析
3. 多方案（≥2）
4. 建议方案
5. 行动责任人

### BP 节点评估标准

**目标层**：
- 清晰性：description 非空
- 对齐性：有上游承接
- 完整性：业务方向覆盖完整
- 注意：目标无 measureStandard，不检查

**KR 层**：
- 充分性：KR 覆盖 BP 所有目标方向
- 独立性：KR 之间边界清晰
- SMART-S：measureStandard 定义业务边界
- SMART-M：measureStandard 含数字（null = P0）
- 匹配性：责任人能力与 KR 方向匹配
- 支撑性：有举措或下游承接

**举措层**：
- 完整性：举措覆盖 KR 方向
- 科学性：举措设计合理
- 标准性：有明确交付物
- 可执行性：有人/时间/资源
- 有效性：能支撑 KR 实现
- 延期风险：截止日期过期 >30 天 = P0

### 问题分级

| 级别 | 判定原则 |
|------|---------|
| P0 | KR measureStandard 为 null / 举措过期 >30天 / 目标设计失效 / 承接口径断裂 |
| P1 | 局部缺陷 / 举措标准模糊 / 无因果链 / 责任人匹配存疑 |
| P2 | 优化建议 |

### 两级联动审计流程

```
Step 1: fetch.py 获取根 BP 数据
Step 2: 对根 BP 执行 Level 1 评估（Goal + KR + 举措）
Step 3: 识别下游 BP 列表
Step 4: 对每个下游 BP 执行 Level 2 评估
Step 5: 汇总 P0/P1/P2 问题
Step 6: 生成诊断报告
```

### 特殊约束

- **顶级目标（如 G 层）**：跳过对齐性检查
- **目标层**：不检查 measureStandard
- **KR 层**：重点检查 measureStandard 是否为 null
- **举措层**：检查延期天数，>30天 = P0

---

## 评估流程（bp-evaluator）

### 两层×三层框架

**第一层**：BP 自身
- 目标层：清晰性、可衡量性、对齐性、完整性
- KR 层：充分性、独立性、SMART性、匹配性、支撑性
- 举措层：完整性、科学性、标准性、可执行性、有效性、延期风险

**第二层**：下游承接 BP（重复第一层）

---

## 管理流程（bp-manager）

### 常用操作

- `bp_client.create_goal(...)` — 创建 BP
- `bp_client.update_goal(id, ...)` — 更新 BP
- `bp_client.get_goal_detail(id)` — 读取 BP 详情
- `bp_client.search_tasks(keyword)` — 搜索 BP

---

## 文件结构

```
bp/
├── SKILL.md              # 本文件（统一入口）
├── scripts/
│   ├── bp_client.py     # BP API 客户端（来自 bp-manager）
│   ├── cwork_client.py  # CWork API 客户端（来自 cms-cwork）
│   └── fetch.py          # 数据获取脚本
├── references/
│   └── BP系统业务说明.md
├── grv-templates/
│   ├── v1-两层三层.md    # bp-evaluator 框架
│   └── v4-两级联动.md    # bp-auditor 框架
└── reports/             # 报告输出目录
```

---

## 编排者规范

- 编排者（我）只调度，不直接执行数据操作
- 大于 5 分钟的任务 spawn sub-agent
- sub-agent 按标签格式：`[bp] {流程} - {任务}`
- spawn 前读 `memory/self-improving/corrections.md`（最近3条）
- 文件合并用 `exec cat`，不用 sub-agent
