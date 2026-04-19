# BP 统一工作平台

> 版本：v1.0.0  
> 最后更新：2026-04-12  
> 来源：外部交付包（bp-skill.tar.gz）

---

## 定位

BP 的管理、评估、审计三个能力统一入口。共享同一套数据接口（BP API + CWork API），按触发词路由到不同工作流。

---

## 三大核心流程

### 1. 审计流程（bp-auditor）
**触发词**：`BP审计` / `审计报告` / `诊断BP` / `审计G-1`

**输出**：深度诊断报告（问题描述+根因分析+多方案+建议方案+行动责任人）

### 2. 评估流程（bp-evaluator）
**触发词**：`BP评估` / `评分` / `评估G-1` / `给BP打分`

**输出**：结构化评分（P0/P1/P2 + 可实现性评级）

### 3. 管理流程（bp-manager）
**触发词**：`创建BP` / `更新KR` / `管理BP` / `查BP` / `查KR`

**输出**：数据操作结果

---

## 与其他 BP Skill 的关系

| Skill | 主要能力 | 状态 |
|-------|---------|------|
| **bp-unified** | 审计+评估+管理统一入口 | ✅ 本产品 |
| bp-auditor | 专注审计（两级联动） | 🔧 在建 |
| bp-manager | 专注管理（CRUD） | 🔧 在建 |
| bp-prototype | 模板制造（年报/半年报/季报/月报） | ✅ 已发布 |
| bp-reporting-templates | 报告生成（月报/季报/半年报/年报） | ✅ 已发布 |

**设计原则**：本产品不替代 bp-prototype 和 bp-reporting-templates，专注在"审计+评估+管理"三个流程的统一调度。

---

## 文件结构

```
bp-unified/
├── SKILL.md              # 统一入口定义
├── README.md             # 本文件
├── scripts/
│   ├── bp_client.py     # BP API 客户端
│   ├── cwork_client.py  # CWork API 客户端
│   ├── fetch.py          # 数据获取脚本
│   └── bp_evaluator.py  # 评估引擎（1454行）
├── references/
│   └── BP系统业务说明.md
├── grv-templates/
│   ├── v1-两层三层.md    # bp-evaluator 框架
│   └── v4-两级联动.md    # bp-auditor 框架
└── reports/             # 报告输出目录
```

---

## 依赖关系

- **BP API**：`scripts/bp_client.py`
- **CWork API**：`scripts/cwork_client.py`

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-04-12 | 初始版本，整合审计+评估+管理三大流程 |

---

_来源：外部交付包 bp-skill.tar.gz | 整合：Zaowu_
