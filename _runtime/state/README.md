# _runtime/state/

Rule-W26-01 要求 Orchestrator 在收到 gateway 重启 system prompt 时，先读本目录下 state.json 校验真实进度。

## 目录结构

```
_runtime/state/
├── README.md           # 本文件
├── factory.json        # 工厂全局状态（运行中、重启中、维护中等）
└── projects/           # 各项目 state.json（按项目编号组织）
    └── {project-id}/
        └── state.json
```

## 当前状态

- factory.json：尚未创建
- projects/：尚未创建

## 创建规则

当 Orchestrator 启动新项目时，必须在 `projects/{project-id}/state.json` 写入初始状态。
