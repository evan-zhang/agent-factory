# Agent Factory Workspace Index (Zaowu)

Welcome to the **Agent Factory** v2.0.

---

## 📂 Directory Structure

```
agent-factory/
├── specs/              规范层（只读）
│   ├── workflows/      SOP 工作流规范
│   ├── templates/      项目模板
│   ├── agents/         Sub-Agent 角色定义
│   ├── governance/     治理规范文档
│   └── quality/        质量标准
│
├── projects/           项目层
│   └── {YYMMDDN}/      按 YYMMDD+序号 编号
│
├── _runtime/           运行时数据（不入 git）
│   ├── logs/           工厂运行日志
│   ├── experience/     跨项目经验沉淀
│   └── governance/     治理台账实际数据
│
└── 根文件              SOUL.md, AGENTS.md, IDENTITY.md, USER.md, TOOLS.md, HEARTBEAT.md
```

## 🔒 Isolation Rules

- **specs/** — 只读，项目执行时不可修改或新增文件
- **projects/{id}/** — 每个项目只修改自己的目录
- **_runtime/** — Orchestrator 维护，不入 git

## 📜 Key Documents

- `SOUL.md` — Orchestrator 行为定义
- `IDENTITY.md` — 工厂身份（造物）
- `AGENTS.md` — Sub-Agent 调度规则
- `CLAWFILE.md` — 入口配置

---

*Agent Factory v2.0 | Restructured 2026-04-19*
