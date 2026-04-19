# 贡献指南

## 项目结构

本仓库是 Agent Factory——Skill 产品生产线。

所有 Skill 源码位于 `projects/` 目录，编号规则为 `YYMMDDN`（7 位）。

## 快速索引

| Skill 名称 | 项目编号 | 目录 |
|---|---|---|
| cas-chat-archive | 2603261 | `projects/2603261/cas-chat-archive/` |
| bp-reporting-templates | 2603271 | `projects/2603271/`（多个 Skill） |
| cms-meeting-materials | 2603301 | `projects/2603301/` |
| xgjk-skill-auditor | 2603311 | `projects/2603311/xgjk-skill-auditor/` |
| tpr-framework | 2604011 | `projects/2604011/tpr-framework/` |
| bp-manager | 2604012 | `projects/2604012/bp-manager/` |
| bp-prototype | 2604013 | `projects/2604013/bp-prototype/` |
| create-xgjk-skill | 2604014 | `projects/2604014/create-xgjk-skill/` |
| openclaw-model-rankings | 2604031 | `projects/2604031/openclaw-model-rankings/` |
| bp-auditor | 2604051 | `projects/2604051/bp-auditor/` |
| cms-meeting-monitor | 2604052 | `projects/2604052/cms-meeting-monitor/` |
| skill-tool-registry | 2604053 | `projects/2604053/` |
| bp-unified | 2604121 | `projects/2604121/bp-unified/` |
| link-archivist | 2604131 | `projects/2604131/link-archivist/` |
| douyin-video-analysis | 2604171 | `projects/2604171/douyin-video-analysis/` |

> 最新完整索引：`projects/` 目录下每个子目录对应一个项目编号。

---

## 提交 Issue

**必须包含以下信息**，否则将被关闭：

1. **所属 Skill 名称**（必填）
2. **所属项目编号**（如 2604131）
3. **问题描述**（清晰描述症状）
4. **复现步骤**（如果可以复现）

**禁止**：
- 不写明是哪个 Skill 的 Issue
- 同时报告多个 Skill 的问题（拆成多个 Issue）
- 报告与 Skill 无关的功能请求

---

## 提交 PR

**PR 必须符合以下条件**：

1. **只改一个项目**：每个 PR 对应一个项目编号（2604XXX），不改多个项目
2. **包含 VERSION 更新**：版本号已升
3. **包含测试说明**：说明你做了什么测试

**禁止**：
- 在一个 PR 里同时改 `projects/2604131/` 和 `projects/2604171/`
- 修改 `specs/` 目录（规范层只读）
- 修改其他项目的目录

---

## 目录隔离规则

```
specs/         ← 只读，禁止修改
projects/      ← 每个项目只改自己的目录
```

如果你需要改动 `specs/`，请先提 Issue 说明原因，由仓库维护者评估。
