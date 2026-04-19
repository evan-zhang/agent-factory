# TPR-20260329-002 交付说明

**项目名称**：慧集会议语义流处理器
**交付日期**：2026-03-30
**交付对象**：Skill 工厂（造物）
**来源**：三省工作台（编排 Agent）

---

## 一、项目背景

为 AI慧记（Huiji）平台新增**会中实时语义流处理**能力。现有 Skill（v1.10.0）只支持会后模式，本次升级使其能够在会议进行中实时增量消费 transcript，提供实时速记、滚动摘要、行动项抽取等能力。

**核心定位**："会中优先、会后兼容"的会议语义流处理器。

## 二、交付包结构

```
TPR-20260329-002-delivery.zip
├── DISCOVERY.md                    ← 需求规格说明书
├── GRV.md                          ← 技术契约（架构+验收标准+约束）
├── DELIVERY_NOTE.md                ← 本文件
└── source/
    └── extracted/
        ├── SKILL.md                ← 现有 Skill 完整规范（v1.10.0，必须在其基础上扩展）
        ├── openapi/huiji/
        │   ├── api-index.md        ← API 索引（5个接口）
        │   ├── chat-list-by-page.md
        │   ├── list-by-meeting-number.md
        │   ├── split-record-list.md
        │   ├── split-record-list-v2.md
        │   └── check-second-stt-v2.md
        ├── scripts/huiji/
        │   ├── README.md
        │   ├── get-transcript.py   ← 现有统一入口脚本
        │   ├── chat-list-by-page.py
        │   ├── list-by-meeting-number.py
        │   ├── split-record-list.py
        │   ├── split-record-list-v2.py
        │   └── check-second-stt-v2.py
        └── examples/huiji/
            └── README.md           ← 使用场景与触发条件
```

## 三、关键文件说明

| 文件 | 作用 | 注意事项 |
|------|------|----------|
| `DISCOVERY.md` | 需求规格，定义了做什么、为什么做、验收指标 | 会中实时是核心，会后兼容是底线 |
| `GRV.md` | 技术契约，定义架构设计、数据结构、验收标准 | 内含 SQLite 表结构、事件模型、轮询策略 |
| `source/extracted/SKILL.md` | 现有 v1.10.0 完整规范 | **必须在此基础上新增章节，不修改现有内容** |
| `source/extracted/openapi/` | 5 个 API 的详细文档 | 核心是 splitRecordListV2（增量）和 checkSecondSttV2（二次转写） |
| `source/extracted/scripts/` | 现有 Python 示例脚本 | 可直接运行，用于理解 API 行为 |

## 四、核心设计决策（已确认）

1. **拉模式增量同步**：平台无 webhook/stream，用短轮询 + 游标
2. **同步语义层**：APPEND/REPLACE/DELETE 事件模型，保证幂等和顺序
3. **自适应轮询**：活跃 2s / 静默 8s，断连指数退避
4. **本地 SQLite**：存储 checkpoint + 事件日志 + 滚动摘要
5. **体验分层**：T+3s 速记 / T+30s 滚动卡片 / 二次转写静默修正

## 五、验收硬指标

| 指标 | 目标值 |
|------|--------|
| 端到端延迟 P95 | ≤ 8s |
| 重复事件率 | ≤ 0.5% |
| 丢片段率 | ≤ 0.1% |
| 二次转写替换成功率 | ≥ 99% |
| 断连恢复追平时间 | ≤ 60s |

## 六、实施路线

| Phase | 周期 | 内容 |
|-------|------|------|
| A | 第1周 | 增量拉取 + checkpoint + 流展示 |
| B | 第2周 | 二次转写替换 + 幂等/去重 + 滚动摘要 |
| C | 第3周 | 行动项抽取 + 会后一键纪要导出 |

## 七、注意事项

1. **不修改现有 Skill 内容**，只在 SKILL.md 末尾新增"会中实时模式"章节
2. **鉴权方式不变**：appKey (XG_BIZ_API_KEY)
3. **防幻觉原则**沿用现有约束
4. **生产域名**：`sg-al-ai-voice-assistant.mediportal.com.cn/api`
5. 建议同时监控的会议上限 ≤ 3 场
