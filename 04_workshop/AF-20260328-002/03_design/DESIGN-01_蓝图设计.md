# DESIGN-01 蓝图设计 — AF-20260328-002 cms-sop

- **项目 ID**：AF-20260328-002
- **阶段**：S3 DESIGN
- **文档状态**：DRAFT
- **版本**：v1.0
- **责任人**：设计总工
- **创建时间**：2026-03-29T09:23:00+08:00

---

## 一、整体架构

```
触发词 → SKILL.md（路由层，≤120行）
            ↓
       模式判断（硬规则）
      ↙              ↘
  Lite 路径         Full 路径
  read lite-guide   read full-guide
  直接执行          spawn 子 Agent
  写文件            子 Agent 写文件
                    主 Agent 读文件
```

---

## 二、SKILL.md 设计（路由层）

### 严格内容约束

```markdown
---
name: cms-sop
description: 统一SOP执行框架。触发词："新建SOP"/"创建任务"/"SOP"/"快速任务"/"完整SOP"。
  自动判断 Lite（轻量）或 Full（完整）模式。
---

## 【必读】加载规则

每次触发必须执行以下步骤，不得跳过：

1. 判断模式（见下方条件）
2. Lite → `read references/lite-guide.md`
   Full → `read references/full-guide.md`
3. 确认看到子文档第一行"# 已加载"标记后，才能继续
4. 每次触发重新加载，禁止复用缓存

## 模式判断（满足任一→Full，模糊默认Full）

- 预计耗时 > 20 分钟
- 涉及 ≥ 2 个系统
- 需要跨 gateway 协作
- 需要多轮人工确认
- 有发布/重启等高影响操作
- 需要完整审计链路

以上均不满足 → Lite

## 能力索引

| 操作 | 脚本 | 说明 |
|---|---|---|
| 创建实例 | `scripts/init_instance.py` | --mode lite\|full |
| 状态管理 | `scripts/update_state.py` | 状态流转 |
| 交接 | `scripts/handover.py` | 换人接手 |
| Lite→Full升级 | `scripts/upgrade.py` | 继承迁移 |

详细规则见：
- Lite：`references/lite-guide.md`
- Full：`references/full-guide.md`
- 共享：`references/shared/`
```

预估行数：约90行，在120行上限内。

---

## 三、子文档设计

### 3.1 references/lite-guide.md

```
# 已加载 lite-guide.md

## 五步执行流程
TARGET → PLAN → CHECKLIST → EXECUTE → ARCHIVE

## 四件套文件说明
（每个文件的填写规范和字段说明）

## 确认单门禁
（执行前确认单的标准格式）

## 升级触发条件
（何时调用 upgrade.py）

## 常见场景示例
（3个典型 Lite 任务示例）
```

约150行，单一职责：Lite 执行规则。

---

### 3.2 references/full-guide.md

```
# 已加载 full-guide.md

## 执行路径说明
（spawn 子 Agent 的触发时机和方式）

## 七件套文件说明
（每个文件的填写规范和字段说明）

## 子 Agent 注入规范
（注入哪些文件、结果如何写回）

## 多轮确认机制
（3轮上限、主编排介入逻辑）

## ARTIFACTS 自动收集规范
（LOG.md 打 [ARTIFACT] 标记的格式）
```

约200行，单一职责：Full 执行规则。

---

### 3.3 references/shared/state-machine.md

```
# 已加载 state-machine.md

## status 完整定义
（13个状态值及含义）

## stage 完整定义
（6个阶段值及含义）

## 合法状态转换表
（哪些转换是允许的，哪些是禁止的）

## mode 字段
（lite / full 含义）
```

约80行，Lite 和 Full 共用。

---

### 3.4 references/shared/confirm-protocol.md

```
# 已加载 confirm-protocol.md

## 确认单标准格式
- 背景
- 执行步骤
- 风险点
- 推荐方案（如有多选项）
- 推荐理由
- 需用户确认的问题

## 确认结果类型
APPROVED / REJECTED / CHANGE_REQUESTED / DEFERRED

## 多轮确认规则
- confirmCount 维护
- 3轮上限
- 主编排介入格式
```

约60行，Lite 和 Full 共用。

---

### 3.5 references/shared/upgrade-rules.md

```
# 已加载 upgrade-rules.md

## 触发条件
（执行中发现超出 Lite 范围的判断依据）

## upgrade.py 执行步骤
（文件继承/state 迁移的完整流程）

## 继承声明区格式
（TASK.md 顶部插入的标准格式）

## 注意事项
（升级后不删除 Lite 实例）
```

约50行。

---

## 四、模板设计

### 4.1 Lite 四件套（继承 cms-soplite v1.0.6，微调）

**TASK-template.md 新增字段：**
- 元数据头加 `mode: lite`
- 继承声明区（升级时填写，正常创建留空）

**其余三件套**：直接复用 cms-soplite v1.0.6 的模板，仅加 `mode: lite` 字段。

---

### 4.2 Full 三个独立模板

**PLAN-template.md**

```markdown
# PLAN.md - {{id}}

---
- mode: full
- 文档状态：DRAFT
- 版本：v1.0
- 创建时间：{{createdAt}}
---

## 执行步骤（必填）

| 步骤 | 操作 | 负责方 | 预计耗时 | 依赖 |
|------|------|--------|----------|------|
| 1 | | | | |

## 里程碑（可选）

| 里程碑 | 目标时间 | 验收方式 |
|--------|----------|----------|
| | | |

## 资源需求（可选）

- 人员：
- 工具/权限：
- 外部依赖：

## 风险预案（必填）

| 风险 | 概率 | 影响 | 预案 |
|------|------|------|------|
| | | | |

## 回滚方案（必填）

> 如果执行失败，如何恢复到执行前状态
```

**DECISIONS-template.md**

```markdown
# DECISIONS.md - {{id}}

---
- mode: full
- 文档状态：DRAFT
- 版本：v1.0
- 创建时间：{{createdAt}}
---

## 决策记录

> 每次用户确认后自动追加。空确认（纯APPROVED无意见）只写一行摘要。

| 轮次 | 时间 | 决策主题 | 用户结论 | 用户意见 | 后续动作 |
|------|------|----------|----------|----------|----------|
| 1 | {{createdAt}} | | | | |

## 主编排介入记录

> 3轮未达成一致时填写

| 时间 | 分歧点 | 选项A | 选项B | 用户选择 | 缺陷清单 |
|------|--------|-------|-------|----------|----------|
| | | 再给三轮 | 带缺陷往下走 | | |
```

**ARTIFACTS-template.md**

```markdown
# ARTIFACTS.md - {{id}}

---
- mode: full
- 文档状态：DRAFT
- 版本：v1.0
- 创建时间：{{createdAt}}
---

## 自动收集产物

> 从 LOG.md 中 [ARTIFACT] 标记自动汇总。归档时生成。

| 产物名称 | 路径/位置 | 类型 | 版本 | 产生时间 |
|----------|-----------|------|------|----------|
| | | | | |

## 手动补充产物

> 请在此补充自动收集遗漏的产物

| 产物名称 | 路径/位置 | 类型 | 版本 | 备注 |
|----------|-----------|------|------|------|
| | | | | |

## 交付确认

- **交付对象**：
- **交付时间**：
- **接收确认**：
```

---

## 五、脚本设计

### 5.1 init_instance.py（扩展）

新增 `--mode lite|full` 参数：
- Lite：创建四件套（复用现有逻辑）
- Full：创建七件套（四件套 + PLAN/DECISIONS/ARTIFACTS）
- state.json 增加 `mode`、`confirmCount`、`upgradedFrom` 字段

### 5.2 update_state.py（扩展）

新增状态：`REVIEWING`、`WAITING_USER`、`ON_HOLD`、`CANCELLED`
新增操作：
- `--action wait-user`：设置 WAITING_USER，同时更新 `resume.waitingFor`
- `--action reviewed`：从 REVIEWING 回到 RUNNING
- `--action increment-confirm`：confirmCount +1，超过3自动标记需要介入

### 5.3 upgrade.py（新增）

```python
# 执行步骤：
# 1. 读取 Lite 实例 state.json，验证 mode=lite 且 status 非 DONE/ARCHIVED
# 2. 读取 TASK.md，在顶部插入继承声明区
# 3. 读取 LOG.md，所有行前加 [继承自Lite] 标记，追加分隔线
# 4. 创建 PLAN.md / DECISIONS.md / ARTIFACTS.md（从 full/ 模板）
# 5. 更新 state.json：
#    mode: "full"
#    status: "DISCUSSING"（重置，让用户重新规划）
#    upgradedFrom: "<原lite实例id>"
#    confirmCount: 0
#    resume.nextAction: "补充 PLAN.md 执行计划"
# 6. 原 Lite 实例 state.json 的 status 设为 "UPGRADED"
```

### 5.4 handover.py（不变）

继承 cms-soplite 现有实现，无需修改。

---

## 六、Full 路径子 Agent 注入规范

### 注入内容

```python
task = f"""
你是 SOP Full 模式的执行子 Agent。

【必读文件】（按顺序读取）：
1. read {instance_path}/state.json
2. read {instance_path}/TASK.md
3. read {skill_dir}/references/full-guide.md
4. read {skill_dir}/references/shared/state-machine.md
5. read {skill_dir}/references/shared/confirm-protocol.md

【当前任务】：{task_description}
【实例路径】：{instance_path}

【执行规则】：
- 所有操作结果必须写入对应文件（LOG.md/RESULT.md等）
- 不通过自由文本向主 Agent 传递结果
- 每次状态变更调用 update_state.py
- 需要用户确认时写入 DECISIONS.md 并停止执行，等待主 Agent 轮询

【禁止】：
- 直接输出最终结论（必须写文件）
- 修改 SKILL.md 或 references/ 下的文件
- spawn 二级子 Agent
"""
```

### 主 Agent 结果读取

子 Agent 执行后，主 Agent 只读两个文件：
1. `state.json`：判断当前状态
2. `RESULT.md` 或 `DECISIONS.md`：获取结论或待确认内容

---

## 七、LOG.md ARTIFACT 标记规范

在 LOG.md 记录操作时，产生交付物的行加 `[ARTIFACT]` 标记：

```markdown
| 2026-03-29 10:00 | EXECUTE | 发布 cms-sop v1.0.0 到 ClawHub [ARTIFACT] | OK | slug=cms-sop, 发布标识=xxx |
| 2026-03-29 10:05 | EXECUTE | 生成 DESIGN-01.md [ARTIFACT] | OK | 路径=04_workshop/.../DESIGN-01.md |
```

归档时，`upgrade.py` 或归档脚本扫描 LOG.md，提取所有含 `[ARTIFACT]` 的行，写入 ARTIFACTS.md。

---

## 八、关键设计决策

| 编号 | 决策 | 理由 |
|---|---|---|
| DD01 | Lite 四件套模板直接继承 cms-soplite v1.0.6 | 避免重复设计，保持一致性 |
| DD02 | Full 路径结果通过文件传递 | 消除自由文本解析不可靠问题 |
| DD03 | upgrade.py 把原 Lite status 设为 UPGRADED | 保留原实例，不删除，可审计 |
| DD04 | 子 Agent 禁止 spawn 二级子 Agent | 防止递归膨胀失控 |
| DD05 | ARTIFACTS 自动收集 + 手动补充双轨 | 自动为主降低负担，手动兜底防遗漏 |
| DD06 | confirm-protocol.md 作为共享文件 | Lite/Full 确认单格式统一，改一处全生效 |

---

## 九、验收标准

- [ ] SKILL.md 行数 ≤120，内容只含路由层内容
- [ ] lite-guide.md 第一行为 `# 已加载 lite-guide.md`
- [ ] full-guide.md 第一行为 `# 已加载 full-guide.md`
- [ ] init_instance.py 支持 `--mode lite|full`，Full 模式生成七件套
- [ ] upgrade.py 执行后：Lite 实例 status=UPGRADED，Full 实例 TASK/LOG 包含继承内容
- [ ] update_state.py 支持 `increment-confirm`，超3次返回介入提示
- [ ] Full 路径：子 Agent 注入规范文件，执行后主 Agent 只读文件获取结果
- [ ] clawhub 安装后，所有模板和子文档完整存在

---

*S3 DESIGN-01 完成 | 2026-03-29T09:23:00+08:00*
