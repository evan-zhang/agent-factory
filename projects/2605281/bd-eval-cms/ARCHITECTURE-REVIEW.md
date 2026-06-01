# bd-eval-engine 架构方案审核文档

> 创建时间：2026-05-29
> 状态：待审核
> 背景：基于 Agent SDK 全景研究报告（https://doc.20100706.xyz/view/42ccc531222e），将现有 OpenClaw Skill `bd-eval-cms` 封装为独立 API 应用。

---

## 一、项目背景

### 1.1 现状

我们有一个运行在 OpenClaw 内的 Skill：`bd-eval-cms`（CMS 康哲药业投前评估体系）。

- 位置：`projects/2605281/bd-eval-cms/`
- 功能：基于 19 个技能 + 6-Gate 门控的完整 BD 评估流水线
- 已有案例：利奈昔巴特（完整跑通 Phase 1-5.5）
- 执行方式：用户在 Telegram 说"CMS投前评估：{品种名}"，OpenClaw 的 Agent 按技能定义执行
- 耗时：60-80 分钟/品种

### 1.2 目标

将 bd-eval-cms 封装为一个**完全独立的应用/API**：

- **黑盒**：用户提供品种信息 → API 自动执行 Phase 1-5.5 → 输出文件到指定位置
- **独立**：不依赖 OpenClaw，任何环境都能部署运行
- **模型无关**：后端可接任意 LLM（glm-5.1 / GPT-4o / Claude / DeepSeek）
- **可嵌入**：既能作为独立 API 服务运行，也能作为 Python 包嵌入其他系统

### 1.3 约束

- 不影响现有 Skill 的持续运行
- 技能定义保持 Markdown 格式，业务人员可修改评估规则不动代码
- 将来是独立 BD 管理系统的后端引擎

---

## 二、技术选型

### 2.1 Agent SDK 选型：OpenAI Agents SDK

理由：
- 轻量，纯库引入，无平台依赖
- 不锁厂商：通过 `set_default_openai_client()` 可接任何兼容 OpenAI API 的模型
- 已验证 glm-5.1 兼容
- 原生支持 MCP（Model Context Protocol）
- 内置 Agent Loop（多步推理 + 工具调用循环）
- 适合"智能调度"场景

不选其他 SDK 的理由：
- Google ADK：GCP 绑定太重
- LangGraph：框架重，学习曲线高，当前场景不需要图引擎
- Claude Agent SDK：绑定 Claude 模型
- CrewAI：抽象层级太高，精细控制不足

### 2.2 搜索能力：Tavily（通过 MCP 接入）

理由：
- 专为 AI Agent 设计，返回结构化结果
- 有官方 MCP server，与 Agent SDK 无缝集成
- 免费额度 1000 次/月
- 搜索质量口碑好

备选：MiniMax Search API（直接 REST 调用）

### 2.3 API 框架：FastAPI

理由：轻量、异步支持好、自动生成文档

### 2.4 状态管理：文件系统 + state.json

理由：
- 跟现有 Skill 的目录结构一致
- 简单可靠，不引入数据库依赖
- 支持断点续跑

---

## 三、系统架构

### 3.1 三层分离

```
┌─────────────────────────────────┐
│  API Layer (FastAPI)            │
│  POST /evaluate                 │  ← 接口层：HTTP 端点
│  GET /status/{case_id}          │
│  POST /update/{case_id}         │
│  GET /report/{case_id}          │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Pipeline Layer (Python 状态机)  │
│  Phase 1 → 2 → 3 → 4 → 5 → 5.5 │  ← 编排层：流程控制
│  状态持久化 / 并行调度 / 断点续跑 │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Intelligence Layer (Agent SDK) │
│  LLM 调用 / 工具注册 / 路由决策  │  ← 智能层：AI 推理
│  Gate 评估 / Battle 审查         │
│  模型可替换（glm/gpt/claude/…）  │
└─────────────────────────────────┘
```

### 3.2 为什么编排不交给 Agent SDK

bd-eval-cms 的流程是**确定性的**：
- Phase 1 必须在 Phase 2 前完成
- Gate 6 必须等 Gate 1-5
- Battle 是固定两轮
- One-pager 必须先跑

这些不需要 LLM 判断，用 Python 状态机写死更可靠、更可调试。

Agent SDK 只负责需要"智能"的部分：
- Phase 1：Discovery 搜索策略（LLM 决定搜什么）
- Phase 2：D-0 路由决策（LLM 判断产品类型匹配哪个技能）
- Phase 3：Gate 内容撰写（LLM 读技能定义 + 搜索结果写评估章节）
- Phase 4：Battle 对抗审查（LLM 审查 + LLM 回应）
- Phase 5：质量终检（LLM 检查 8 项标准）

### 3.3 并行执行

Phase 3 的 Gate 并行执行策略：
```
One-pager（先跑完）
    ↓
Gate 1 + Gate 2 + Gate 3（asyncio 并行）
    ↓
Gate 4 + Gate 5（asyncio 并行）
    ↓
Gate 6（串行，依赖 Gate 1-5 结论）
```

Phase 4 Battle 对抗：
```
审查层 Agent → 输出异议清单
    ↓
执行层 Agent → 逐条回应
    ↓
审查层重审（最多 3 轮）
```

---

## 四、目录结构

```
bd-eval-engine/                    # 独立 Git repo
├── pyproject.toml
├── config.yaml                    # 所有配置集中管理
├── skills/                        # 从工厂复制的 Markdown 技能定义（只读）
│   ├── SOP.md
│   ├── 00_CMS-投前评估技能体系总规则.md
│   ├── 00_体系总规则增补条款_v1.1.md
│   ├── D-0_bd-evaluation-router.md
│   ├── A-1_bd-cn-overseas-unlisted.md
│   ├── A-2_bd-cn-agency-rights.md
│   ├── A-3_bd-cn-self-rd-pipeline.md
│   ├── A-4_bd-cn-biosimilar.md
│   ├── A-5_bd-cn-marketed-product-rights.md
│   ├── A-6_bd-cn-rx-to-otc.md
│   ├── A-7_bd-multi-target-screening.md
│   ├── A-8_bd-cn-generic-advanced.md
│   ├── B-1_medical-aesthetics-product-evaluator.md
│   ├── B-2_medical-aesthetics-portfolio-audit.md
│   ├── B-3_bd-cn-otc-consumer-health.md
│   ├── C-1_bd-intl-single-market.md
│   ├── C-2_bd-intl-multi-market.md
│   ├── C-3_bd-intl-portfolio-strategy.md
│   ├── D-1_pharma-bd-due-diligence.md
│   ├── D-2_pharma-market-landscape-report.md
│   ├── D-3_bd-project-one-pager.md
│   ├── E-1_bd-equity-biotech-due-diligence.md
│   └── sub-agent-prompt-template.md
├── bd_eval/
│   ├── __init__.py
│   ├── config.py                  # 读取 config.yaml
│   ├── api/                       # FastAPI 薄壳
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI app 创建
│   │   └── routes.py              # 路由定义
│   ├── pipeline/                  # 状态机 + Phase 编排
│   │   ├── __init__.py
│   │   ├── engine.py              # 主引擎：Phase 流转
│   │   ├── state.py               # state.json 读写 + 断点续跑
│   │   └── scheduler.py           # asyncio 并行调度
│   ├── agent/                     # Agent SDK 智能层
│   │   ├── __init__.py
│   │   ├── tools.py               # @function_tool 注册
│   │   ├── discovery.py           # Phase 1：Discovery Agent
│   │   ├── router.py              # Phase 2：D-0 路由 Agent
│   │   ├── evaluator.py           # Phase 3：Gate 评估 Agent
│   │   ├── battle.py              # Phase 4：Battle 对抗 Agent
│   │   ├── reporter.py            # Phase 5：报告合并 + 质量检查 Agent
│   │   └── model.py               # 模型配置
│   ├── output/                    # 文件输出
│   │   ├── __init__.py
│   │   ├── writer.py              # 按技能规范写文件
│   │   ├── html.py                # 麦肯锡深蓝 HTML 生成
│   │   └── sync.py                # 知识库同步（可选模块）
│   └── mcp/                       # MCP 集成
│       ├── __init__.py
│       └── search.py              # Tavily MCP 或直接 API 封装
├── cases/                         # 运行时品种目录（output_root，gitignore）
│   └── .gitkeep
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   └── test_api.py
├── docker/
│   └── Dockerfile
└── README.md
```

---

## 五、配置设计

### config.yaml

```yaml
model:
  provider: openai_compatible      # openai / openai_compatible
  base_url: https://xxx/v1         # 模型 API 地址
  api_key: ${MODEL_API_KEY}        # 从环境变量读
  name: glm-5.1

search:
  provider: tavily                 # tavily / minimax / serpapi
  api_key: ${TAVILY_API_KEY}

output:
  root: ./cases                    # 品种目录根路径

knowledge_base:                    # 可选：知识库同步
  enabled: false
  api_url: ""
  app_key: ""
  project_id: ""

html_upload:                       # 可选：HTML 上传
  enabled: false
  endpoint: ""
```

---

## 六、API 设计

### 6.1 POST /evaluate — 发起全量评估

请求：
```json
{
  "product_name": "利奈昔巴特",
  "generic_name": "linaxibat",
  "partner": "XXX Pharma",
  "indication": "胆汁酸腹泻",
  "business_entity": "深康",
  "external_files": []            // 可选：外部资料路径
}
```

响应：
```json
{
  "case_id": "利奈昔巴特",
  "status": "running",
  "estimated_minutes": 70
}
```

后台异步执行 Phase 1 → 2 → 3 → 4 → 5 → 5.5

### 6.2 GET /status/{case_id} — 查询进度

响应：
```json
{
  "case_id": "利奈昔巴特",
  "phase": "report_finalized",
  "current_version": 1,
  "conclusion": "推进",
  "started_at": "2026-05-29T21:00:00+08:00",
  "completed_at": "2026-05-29T22:10:00+08:00",
  "report_url": "/report/利奈昔巴特",
  "quality_check": {
    "gateCards": "PASS",
    "financialThreshold": "PASS",
    "vetoCheck": "PASS"
  }
}
```

### 6.3 POST /update/{case_id} — 增量更新

请求：
```json
{
  "gates": [2, 6],
  "external_files": []
}
```

### 6.4 GET /report/{case_id} — 获取报告

返回最终报告内容或下载链接。

---

## 七、核心流程映射

### Phase 1: DISCOVERY
- Pipeline 层：创建品种目录 + 初始化 state.json
- Agent 层：Discovery Agent 执行宽度搜索（web_search ≥5 次）+ web_fetch 抓取参考文献
- 输出：01-discovery.md + references/P1/*.md + state.json

### Phase 2: D-0 路由
- Pipeline 层：读取 discovery 结果
- Agent 层：Router Agent 读取 D-0 路由决策树 + 技能定义，匹配产品类型
- Agent 层：Battle Agent 独立审查路由决策
- 输出：battle/ROUTE-SELECTION-AUDITOR.md + state.json 更新

### Phase 3: 逐 Gate 评估
- Pipeline 层：scheduler.py 按 One-pager → Gate 1-3 并行 → Gate 4-5 并行 → Gate 6 串行 调度
- Agent 层：每个 Gate 由独立 Evaluator Agent 执行，读取对应技能 Markdown + 搜索
- 输出：02-gate-by-chapter/*.md + references/{G1,G2,...}/*.md

### Phase 4: Battle 对抗
- Pipeline 层：串行调度 审查 → 回应 → 重审（最多 3 轮）
- Agent 层：审查层 Agent + 执行层 Agent 对抗
- 输出：battle/BATTLE-R1-AUDITOR.md + battle/BATTLE-R1-EXECUTOR.md + 03-battle-summary.md

### Phase 5: 报告合并 + 质量终检
- Pipeline 层：合并文件 + 调用质量检查
- Agent 层：Reporter Agent 执行 8 项质量终检
- 输出：04-final-report.md + references/REFERENCES.md

### Phase 5.5: HTML 生成 + 上传
- Pipeline 层：读取报告 + 调用 HTML 生成 + 可选上传
- 输出：REPORT.html + 可选上传 + 可选知识库同步

---

## 八、项目管理

### 8.1 在 Agent Factory 注册

在工厂 projects 目录下创建 `projects/2605291/` 管理元信息：
```
projects/2605291/
├── METADATA.json          # 指向 GitHub repo
├── VERSION                # 跟踪版本
├── state.json             # 项目状态
└── README.md              # 项目说明
```

### 8.2 独立 Git 仓库

代码在独立 repo 管理：`github.com/evan-zhang/bd-eval-engine`

### 8.3 技能定义同步

skills/ 目录从工厂 `projects/2605281/bd-eval-cms/references/` 复制。工厂更新技能定义后，重新复制即可。

---

## 九、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 长任务中断（60-80 分钟） | 评估半途中断 | state.json 记录进度，支持断点续跑 |
| LLM 输出不稳定 | Gate 内容质量波动 | 质量终检 8 项门控 + Battle 对抗审查 |
| 搜索 API 限流 | Phase 1 搜索受阻 | 请求间隔 + 重试 + 多 provider fallback |
| 模型 API 超时 | 单步执行失败 | 每步超时重试（最多 2 次）|
| 技能定义变更 | 已运行任务结果过时 | 版本锁定，运行中的任务不受影响 |

---

## 十、待审核问题

请重点审核以下方面：

1. **架构合理性**：三层分离是否合理？Pipeline 层用 Python 状态机而非框架图引擎是否足够？
2. **Agent SDK 选型**：OpenAI Agents SDK 是否适合这个场景？是否遗漏了更好的选择？
3. **并行策略**：asyncio 并行 Gate 评估是否有潜在问题？
4. **搜索方案**：Tavily 是否合适？MCP 集成方式是否正确？
5. **状态管理**：文件系统 + state.json 的方案是否可靠？
6. **技能 Markdown 运行时读取**：性能影响？是否有更好的方式？
7. **API 设计**：端点设计是否合理？遗漏了什么？
8. **整体可行性**：这个方案能否跑通？有没有致命缺陷？
