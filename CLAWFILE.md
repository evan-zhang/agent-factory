# CLAWFILE.md — Agent Factory 入口配置

## 工厂入口

本文件是 Agent Factory 的启动入口配置文件，供 OpenClaw 加载工厂主 Orchestrator。

### 配置

- **类型**: factory
- **版本**: v2.0
- **入口 SOUL**: `./SOUL.md`
- **角色定义**: `./AGENTS.md`
- **主工作区**: `./projects`

### 目录结构（v2.0）

```
agent-factory/
├── specs/              ← 规范层（只读）
│   ├── workflows/      SOP 工作流
│   ├── templates/      项目模板
│   ├── agents/         Sub-Agent 定义
│   ├── governance/     治理规范
│   └── quality/        质量标准
├── projects/           ← 项目层（每个项目独立目录）
│   └── {YYMMDDN}/      项目编号，如 2604191
│       ├── {skill}/    Skill 源码
│       ├── builds/     测试包
│       ├── releases/   正式发布包
│       └── VERSION     当前版本号
├── _runtime/           ← 运行时数据（不入 git）
│   ├── logs/           日志
│   ├── experience/     跨项目经验沉淀
│   └── governance/     治理台账实际数据
└── (根文件)            SOUL.md, AGENTS.md, IDENTITY.md 等
```

### Sub-Agent 定义

| 角色 | 路径 |
|------|------|
| interview | specs/agents/interview.md |
| analyst | specs/agents/analyst.md |
| generator | specs/agents/generator.md |
| validator | specs/agents/validator.md |
| assembler | specs/agents/assembler.md |
| reviewer | specs/agents/reviewer.md |
| governance-officer | specs/agents/governance-officer.md |

### 隔离规则

- **specs/** 是只读规范层，项目执行时不可修改
- **projects/{id}/** 是每个项目的独立空间，只修改自己的目录
- **_runtime/** 是运行时数据，由 Orchestrator 维护，不入 git

---

*Agent Factory v2.0*
