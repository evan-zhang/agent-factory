# REQ-01 需求确认草案 — AF-20260328-002 cms-sop

- **项目 ID**：AF-20260328-002
- **阶段**：S2 REQUIREMENTS
- **文档状态**：APPROVED
- **版本**：v1.0
- **责任人**：工厂调度员（造物）
- **创建时间**：2026-03-29T09:20:00+08:00
- **用户确认**：Evan（2026-03-29）

---

## 一、产品定位

**产品名称**：`cms-sop`
**定位**：统一 SOP 执行框架，合并 Lite 和 Full 两个模式为一个 Skill，按任务复杂度自动路由。

| 维度 | Lite 模式 | Full 模式 |
|---|---|---|
| 适用场景 | 20分钟内/单系统/单次确认 | 超出 Lite 范围的复杂任务 |
| 文件套件 | 四件套 | 七件套 |
| 执行路径 | 读 guide → 直接执行 | 读 guide → spawn 子 Agent |
| 触发方式 | 主动创建 | 主动创建 或 从 Lite 升级 |

---

## 二、功能需求（已确认）

### F01：模式判断（硬规则）

满足任一条件 → Full 模式（模糊时默认 Full）：
- 预计耗时 > 20 分钟
- 涉及 ≥ 2 个系统
- 需要跨 gateway 协作
- 需要多轮人工确认
- 有发布/重启等高影响操作
- 需要完整审计链路

以上均不满足 → Lite 模式

### F02：文件套件

**Lite 四件套**（继承 cms-soplite v1.0.6）：
- `TASK.md`：任务书 + 执行计划 + 决策记录
- `LOG.md`：执行日志 + 阶段摘要 + 阻塞记录
- `RESULT.md`：结果留痕 + 交付物索引 + 用户确认
- `HANDOVER.md`：交接记录

**Full 七件套**（Lite 四件套 + 三个独立文件）：
- `PLAN.md`：执行计划（步骤/时间/风险预案/里程碑），必填/可选分级
- `DECISIONS.md`：决策记录，每次用户确认后自动写入（空确认只写一行摘要）
- `ARTIFACTS.md`：交付物索引，LOG.md 打 `[ARTIFACT]` 标记自动汇总，归档时提示手动补充

### F03：多轮确认机制

- 每次用户确认写入 `DECISIONS.md`，`state.json` 维护 `confirmCount` 字段
- **上限3轮**：第3轮仍未通过，主编排 Agent 强制介入分析
- 介入后输出：分歧点分析 + 两个选项（再给三轮 / 带缺陷往下走）
- 用户拍板，选择记入 `DECISIONS.md`
- "带缺陷往下走"时，缺陷清单必须写入 `RESULT.md` 遗留问题区

### F04：Lite → Full 升级

- 触发：执行中发现超出 Lite 范围
- 动作：
  1. Lite 实例 `status = "UPGRADED"`，记录升级原因
  2. 调用 `scripts/upgrade.py` 执行迁移：
     - TASK.md 顶部插入继承声明区
     - LOG.md 内容复制并打 `[继承自Lite]` 标记
     - 补齐 Full 三个缺失文件（PLAN/DECISIONS/ARTIFACTS）
     - 更新 state.json：`mode: "full"`，`upgradedFrom: "<lite-id>"`，`confirmCount: 0`

### F05：渐进式加载架构（新原则落地）

- `SKILL.md` ≤120行，只做路由
- 执行规则放 `references/` 子文档，按需读取
- 共享规则放 `references/shared/`
- Full 路径通过 spawn 子 Agent 隔离执行
- 子 Agent 结果通过文件传递，不通过自由文本

---

## 三、state.json 字段规范（Full 扩展）

```json
{
  "id": "SOP-YYYYMMDD-NNN",
  "title": "任务标题",
  "mode": "lite | full",
  "owner": "factory-orchestrator",
  "status": "DISCUSSING | READY | RUNNING | REVIEWING | WAITING_USER | BLOCKED | PAUSED | ON_HOLD | CANCELLED | DONE | ARCHIVED | HANDOVER_PENDING | UPGRADED",
  "stage": "TARGET | PLAN | CHECKLIST | EXECUTE | ARCHIVE | DONE",
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601",
  "deadline": "",
  "reason": "",
  "checklistConfirmed": false,
  "confirmCount": 0,
  "upgradedFrom": "",
  "resume": {
    "lastCompleted": "",
    "currentBlocked": "",
    "waitingFor": "",
    "nextAction": ""
  }
}
```

---

## 四、脚本清单

| 脚本 | 功能 | 参数 |
|---|---|---|
| `init_instance.py` | 创建实例 | `--mode lite\|full --title --owner --root` |
| `update_state.py` | 状态管理 | `--instance-path --status --stage --action` |
| `handover.py` | 交接记录 | `--instance-path --from --to --reason --next-steps` |
| `upgrade.py` | Lite→Full 迁移 | `--instance-path --reason` |

---

## 五、目录结构

```
cms-sop/
├── SKILL.md                          # ≤120行，路由层
├── references/
│   ├── lite-guide.md                 # Lite 完整执行规则
│   ├── full-guide.md                 # Full 完整执行规则
│   └── shared/
│       ├── state-machine.md          # 状态机定义（共用）
│       ├── upgrade-rules.md          # 升级规则（共用）
│       └── confirm-protocol.md       # 用户确认协议（共用）
│   └── templates/
│       ├── lite/                     # 四件套模板
│       │   ├── TASK-template.md
│       │   ├── LOG-template.md
│       │   ├── RESULT-template.md
│       │   └── HANDOVER-template.md
│       └── full/                     # 七件套模板（继承 lite/ 四件套）
│           ├── PLAN-template.md
│           ├── DECISIONS-template.md
│           └── ARTIFACTS-template.md
└── scripts/
    ├── init_instance.py
    ├── update_state.py
    ├── handover.py
    └── upgrade.py
```

---

## 六、与 cms-soplite 的关系

- `cms-soplite` 继续存在，不删除，标记为 `deprecated`
- `cms-sop` 发布后，SKILL.md 里加引导："建议迁移到 cms-sop"
- 现有 soplite 实例无需迁移，继续有效

---

## 七、验收标准

- [ ] SKILL.md ≤120行，通过渐进加载架构审核
- [ ] Lite 路径：创建实例 → 读 lite-guide → 执行 → 归档全流程通过
- [ ] Full 路径：创建实例 → 读 full-guide → spawn 子 Agent → 结果写文件 → 主 Agent 读取全流程通过
- [ ] Lite→Full 升级：upgrade.py 执行后四件套完整继承，state.json 字段正确
- [ ] 多轮确认：3轮后主编排介入机制触发
- [ ] clawhub 安装验证：所有模板和子文档完整打包

---

*S2 REQ-01 完成 | 2026-03-29T09:20:00+08:00*
