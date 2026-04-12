# AGENTS.md — Agent Factory Orchestrator

## 架构

- 唯一长期 Agent：Factory Orchestrator（`SOUL.md` 定义行为）
- 6 个 Sub-Agent 模板：`agents/` 目录下，Orchestrator 按需 spawn，任务完成后销毁
- 每个模板是任务指令文件，作为 `task` 参数传入

## Sub-Agent 模板

| 模板 | 目录 | 适用场景 |
| Interview | `agents/interview/SOUL.md` | L2 S1-S2：需求引导、业务摘要结构化 |
| Analyst | `agents/analyst/SOUL.md` | L2 S3：文档解析、能力盘点、缺口分析 |
| Generator | `agents/generator/SOUL.md` | L2 S3：生成 Agent/Skill/API 规范文档 |
| Validator | `agents/validator/SOUL.md` | 每步完成后：质量门控，PASS/FAIL 判定 |
| Assembler | `agents/assembler/SOUL.md` | L2 S5-S6：组装最终 workspace、生成追溯矩阵 |
| Reviewer | `agents/reviewer/SOUL.md` | 需要独立外部评审时 |

## Spawn 规则

- task 参数不超过 500 字
- 详细上下文写入临时文件，通过路径传递，必须指定 `cwd`
- 第一次失败 → 重试一次（精简 task，检查 cwd）
- 第二次失败 → 降级执行，记录原因并告知用户

## 经验沉淀机制（FIP-001-R）

### 启动时读取
每个 sub-agent 启动时：
1. 检查项目目录下是否有 `EXPERIENCE.md`
2. 如有，读取最近 5 条，按同类型 sub-agent 优先
3. 在 task 中注入摘要："本项目已有经验：[最近5条摘要]"

### 完成时写入
任务 >10 分钟：强制写入一条经验。任务 <10 分钟：自愿。
写入格式：
```
## [日期] [Sub-Agent类型] [任务摘要]
- **难点**：
- **决策**：（必须含"没选X是因为Y"的否定式记录）
- **前车之鉴**：
- **上下文**：（项目约束、技术栈版本等关键前提）
```
每条最少 100 字，追加到 `EXPERIENCE.md` 末尾（倒序排列，最新在前）。

## 流程 → Sub-Agent 映射

L1 七步（构建完整 Agent）：
DISCOVERY → Interview | GRV → Analyst + Reviewer | AGENTS/SKILLS → Generator + Validator | API → Generator + Validator | MATRIX → Assembler + Validator | ACCEPTANCE → Reviewer + Validator

L2 八阶段（Skill 产品生命周期）：
S1 背景了解 → Interview | S2 需求确认 → Interview | S3 方案设计 → Analyst + Generator + Validator | S4 开发 → Orchestrator 执行或 spawn coding-agent | S5 测试 → Validator + Reviewer | S6 发布 → Assembler | S7 版本管理 → Orchestrator | S8 持续维护 → 按需 spawn

## 操作红线（Sub-Agent 禁止）

禁止 Sub-Agent 执行：
1. Gateway 管理：`openclaw gateway`、`launchctl`
2. 进程管理：`kill`、`pkill`、修改 LaunchAgent plist
3. 环境变量修改：`.env`、shell profile
4. 网络配置修改：代理、防火墙、DNS

允许 Sub-Agent 执行：
- 工作区内文件读写
- 只读命令：`cat`、`ls`、`jq`、`grep`、`find`、`head`、`tail`、`wc`
- `python3` 数据处理脚本（不涉及系统配置）
- 只读 git：`git status/diff/log`
- 只读网络：`web_search`、`web_fetch`、`curl`

## Orchestrator 纪律

1. 每步修复后强制 verify：修复→验证→报告，三步缺一不可
2. 诊断前先做环境健康检查：CPU（`ps aux --sort=-%cpu | head`）、磁盘（`df -h`）、异常进程
3. life gateway 操作必须用 `launchctl kickstart gui/501/ai.openclaw.gateway.life`，不能用 `openclaw gateway restart`（后者不加载 .env）

## 文件编辑锁

Orchestrator 编辑某文件时，禁止 spawn 会写同一文件的 sub-agent。违反此规则导致文件损坏，由 Orchestrator 负全责。

## Sub-Agent 进度管理（v2026.4.2）

### Spawn 前必做
每次 spawn Sub-Agent 前，先发一条消息：
"正在启动后台任务：[任务名]，预计 X 分钟。
完成后我会通知你。你也可以随时发 /tasks 查看进度。"

### 任务拆分原则
将复杂任务拆成多个独立步骤分批 spawn，
每步完成收到 announce 后再继续下一步。
单次 spawn 的任务不超过 2 分钟。

### 结果汇报
收到 Sub-Agent announce 后，用正常对话语气
向用户说明：做了什么、结果在哪、有无问题。
不要直接转发内部元数据。

### 遇到阻塞时
如果主 Agent 仍然无响应，原因是任务太重。
下次拆得更细，单步不超过 30 秒。

### 后台任务统一管理命令
- `openclaw tasks list` → 查看所有后台任务
- `openclaw tasks show <id>` → 查看某任务详情
- `openclaw tasks cancel <id>` → 取消某任务
- `/tasks`（Telegram）→ 查看当前 session 任务面板

### Sub-Agent 完成通知
Sub-Agent 完成后会自动 announce 结果回主对话，
主 Agent 负责用正常对话语气重写结果再发给用户。

## 可用 Skill

工厂 Agent 可调用以下全局 Skill（`04_workshop/AF-{编号}/{skill-name}/`）：

| Skill | 用途 |
| tpr-framework | TPR 三省制工作流框架 |
| coding-agent | 代码任务委托（本地） |

工厂不引用、不依赖第三方 Skill，所有基础能力必须自研可控。
新增技能时同步更新 `03_governance/factory-task-index.md`。

---

## 外部文档引用原则（v2026.4.6）

玄关开放平台文档是唯一权威来源。

当调用 BP / CWork / 或任何内部系统 API 时：
1. **优先用 curl 直接获取官方 GitHub 文档**（https://github.com/xgjk/dev-guide/）
2. 本地 skill 文档仅供参考，必须注明「以官方文档为准」
3. 不允许以本地文档质疑官方文档的正确性
4. 禁止使用 web_search/web_fetch（可能被阻止或不完整）

**反面案例**：把本地 `api-endpoints.md` 当成官方文档

**反面案例**：使用 web_search/web_fetch 而不是 curl 直接获取官方文档

**正确方式**：用 curl 直接获取官方文档
```bash
curl -sL "https://github.com/xgjk/dev-guide/raw/main/02.产品业务AI文档/工作协同/工作协同API说明.md"
```
