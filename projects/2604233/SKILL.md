---
name: seven-policy-collector
description: 七大政策采集 Skill Pack。按城市串行采集异地就医、异地生育报销、公积金异地购房贷款、购房资格、车牌摇号、子女上学、落户（本科学历）7 项政策的官方来源、辅助来源和缺口信息。输出标准化三表（指标汇总表/来源明细表/缺口与待补充）。依赖 multi-search Skill 的搜索基础设施。
skillcode: seven-policy-collector
github: https://github.com/evan-zhang/agent-factory
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604233
version: "1.3.0"
dependencies:
  - multi-search
---

# seven-policy-collector

## 核心定位

七大政策采集 Skill Pack 的**总控入口**。负责按城市串行调度 7 个政策采集模块，每个模块独立输出标准化的三表文件。

不单独执行采集，由 EXECUTION-PROMPT.md 驱动整体流程。

## 当前版本

**`1.2.2`**（见 `VERSION`）

## 包含的 7 个采集模块

| 顺序 | 模块名 | 采集主题 | Skill 目录 |
|------|--------|----------|-----------|
| 1 | out-of-town-medical-collector | 异地就医 | `01-out-of-town-medical-collector/` |
| 2 | out-of-town-maternity-collector | 异地生育报销 | `02-out-of-town-maternity-collector/` |
| 3 | cross-city-housing-fund-loan-collector | 公积金异地购房贷款 | `03-cross-city-housing-fund-loan-collector/` |
| 4 | home-purchase-eligibility-collector | 购房资格 | `04-home-purchase-eligibility-collector/` |
| 5 | vehicle-plate-lottery-collector | 车牌摇号 | `05-vehicle-plate-lottery-collector/` |
| 6 | children-school-admission-collector | 子女上学 | `06-children-school-admission-collector/` |
| 7 | hukou-settlement-collector | 落户（本科学历） | `07-hukou-settlement-collector/` |

## 执行流程

1. **Phase 0**：环境初始化与能力探测（`scripts/setup-minimax.sh`）
2. **Phase 1**：串行执行 7 个模块（由 `EXECUTION-PROMPT.md` 驱动）

## 统一输出格式

每个模块输出 3 个 Markdown 文件：

| 文件 | 内容 |
|------|------|
| `01-指标汇总表.md` | 按固定指标逐行汇总采集结果 |
| `02-来源明细表.md` | 每行 = 一个来源支撑一个指标，含完整 URL 和来源验证 |
| `03-缺口与待补充.md` | 缺口指标 + 缺口原因 + 已检索渠道 + 建议方向 |

## 依赖

- **multi-search**（项目 2604251）：搜索/抓取降级链、环境探测、检索策略
- **MiniMax web_search**：主力搜索引擎（需 MCP 配置）
- **Tavily / Exa**：可选搜索回退和增强

## 路由与加载规则

| 用户意图 | 模块 | 入口文件 |
|----------|------|----------|
| 执行完整采集 | 全部 7 个模块 | `EXECUTION-PROMPT.md` |
| 环境初始化 | setup | `scripts/setup-minimax.sh` |
| 配置指南 | docs | `docs/MiniMax-WebSearch-配置指南.md` |
| 单个模块采集 | 对应模块 | `0X-module-name/SKILL.md` |

## 宪章

- **不**并行执行（必须串行）
- **不**合并不同模块的输出
- **不**跨模块读取或修改其他模块目录
- **不**做政策裁决
- 每个模块只写入自己的固定输出目录

## 配置与授权

见 `docs/MiniMax-WebSearch-配置指南.md`。

## 问题反馈

- Issue 地址：https://github.com/evan-zhang/agent-factory/issues
- 标题格式：`[seven-policy-collector] 简要描述`
- 建议包含：重现步骤、环境信息（OpenClaw/Hermes）、相关日志

## 目录结构

```text
2604233/
├── SKILL.md                    ← 本文件（总控入口）
├── EXECUTION-PROMPT.md         ← 执行提示词（驱动 7 个模块）
├── VERSION                     ← Pack 版本号
├── scripts/
│   └── setup-minimax.sh        ← 环境初始化脚本
├── docs/
│   └── MiniMax-WebSearch-配置指南.md
├── 01-out-of-town-medical-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/01-异地就医.md
├── 02-out-of-town-maternity-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/02-异地生育报销.md
├── 03-cross-city-housing-fund-loan-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/03-公积金异地购房贷款.md
├── 04-home-purchase-eligibility-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/04-购房资格.md
├── 05-vehicle-plate-lottery-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/05-车牌摇号.md
├── 06-children-school-admission-collector/
│   ├── SKILL.md
│   ├── version.json
│   └── references/06-子女上学.md
└── 07-hukou-settlement-collector/
    ├── SKILL.md
    ├── version.json
    └── references/07-落户-本科学历.md
```
