# TPR ↔ Ralph Loop 桥接规范

> 本文档定义 TPR 四阶段与 Ralph Loop 持续执行的无缝衔接。
> 适用场景：TPR Phase 3 Battle 通过后，GRV 方案直接交由 Ralph Loop 执行。

---

## 一、衔接设计原理

### 1.1 两个框架的职责边界

| 阶段 | TPR 负责 | Ralph Loop 负责 |
|------|---------|----------------|
| 需求澄清 | ✅ DISCOVERY.md | — |
| 方案制定 | ✅ GRV.md（目标+KR+举措） | — |
| 方案对抗 | ✅ Battle（门下省 vs 尚书省） | — |
| 持续执行 | — | ✅ Implementation 全程 |

**核心逻辑**：TPR 前 3 步解决"做什么、怎么做"，Ralph Loop 接手第 4 步"持续做到"。

### 1.2 衔接触发条件

满足以下全部条件时，触发 TPR → Ralph Loop 桥接：
1. TPR Battle 已完成（门下省给出 APPROVE 或 CONDITIONAL PASS）
2. GRV.md 已定稿（版本锁定）
3. 对应项目目录下有 `GRV.md` 和 `DISCOVERY.md`
4. 用户明确说"开始执行"或"交由 Ralph 执行"

---

## 二、GRV → Ralph state.json 转换

### 2.1 字段级映射规则

| GRV 字段 | Ralph state.json 字段 | 说明 |
|---------|----------------------|------|
| `task` | `task` | GRV 项目名称 + DISCOVERY 目标摘要 |
| `goal` | `goal` | GRV 第 1 节"目标拆解"的总体描述 |
| `meta.projectId` | `meta.projectId` | P001 格式 |
| `meta.grvVersion` | `meta.grvVersion` | 如 v1.2 |
| `meta.grvPath` | `meta.grvPath` | GRV.md 的绝对路径 |
| 每个 KR | `checklist` 条目 | 格式：`<KR编号> <KR描述>` |
| 每个举措 | `route` 条目 | 仅 autonomous 模式 |
| 关键决策 | `decisions` 条目 | Battle 中的结论 |

### 2.2 checklist 生成规则（执行者模式）

每个 KR 拆解为若干 checklist 条目，每条必须包含三要素：

```
范围：<KR 编号> <涉及的文件/模块/目录>
证据：<验收命令或文件 diff>
测试：<exit 0 或输出符合预期>
```

**示例**：GRV 中有一条 KR：
```
KR 编号：P001-G001-R002
KR 描述：API 接口文档覆盖率 100%
验收方式：所有 endpoint 有 docstring + openapi.yaml 同步
```

转换为 checklist 条目：
```
P001-G001-R002-01：所有 API endpoint 添加 docstring（范围：src/api/*.py）
P001-G001-R002-02：docstring 与 openapi.yaml 字段一致（证据：openapi-validate 脚本通过）
P001-G001-R002-03：pytest tests/api/ 全部通过（测试：exit 0）
```

### 2.3 route 生成规则（自主者模式）

每个举措编号直接作为 route 的一条步骤：

| 举措编号 | 举措描述 | 转为 route 条目 |
|---------|---------|----------------|
| P001-G001-R001-A001 | 初始化项目结构 | `P001-G001-R001-A001：初始化项目结构` |
| P001-G001-R001-A002 | 接入数据库 | `P001-G001-R001-A002：接入数据库` |
| P001-G001-R002-A001 | 实现认证模块 | `P001-G001-R002-A001：实现认证模块` |

---

## 三、桥接 SOP（Step by Step）

### Step 1：确认衔接条件

执行者（TPR Orchestrator 或人）确认：
- [ ] Battle 记录已归档（`battle/BATTLE-R{n}-*.md`）
- [ ] GRV.md 版本号已锁定
- [ ] 门下省最终 verdict 为 APPROVE 或 CONDITIONAL PASS
- [ ] 用户下达"开始执行"指令

### Step 2：生成桥接元数据

读取 GRV，提取以下信息写入桥接文件：

```
projects/{PROJECT-ID}/bridge-metadata.json
```

```json
{
  "projectId": "P001",
  "grvVersion": "v1.2",
  "grvPath": "/absolute/path/to/GRV.md",
  "discoveryPath": "/absolute/path/to/DISCOVERY.md",
  "battleRounds": 2,
  "finalVerdict": "APPROVE",
  "checklistSource": "GRV KR table",
  "totalKRs": 5,
  "totalActions": 12,
  "bridgedAt": "2026-05-21T00:00:00Z",
  "mode": "executor",
  "ralphStatePath": "./ralph-state.json"
}
```

### Step 3：初始化 Ralph state.json

```bash
# 方式一：手动创建
cp ralph/references/state-example-executor.json projects/{id}/ralph-state.json

# 方式二：脚本初始化（推荐）
bash ralph/scripts/init-state.sh \
  projects/{id}/ralph-state.json \
  --task "$(cat GRV.md | head -1 | tr -d '#')" \
  --goal "$(cat GRV.md | sed -n '/目标拆解/,/^##/p' | head -20)" \
  --mode executor \
  --checklist "P001-G001-R001-01: ..." "P001-G001-R001-02: ..."
```

### Step 4：注入 GRV 上下文到 PROMPT.md

创建 `projects/{id}/ralph-prompt.md`，格式：

```markdown
# 执行者 PROMPT — 项目 {ID} Implementation

## 任务
{task from GRV 目标拆解}

## 最终目标
{GRV goal 原文}

## GRV 方案路径（已通过 Battle）
来自 `GRV.md` v{version}，Battle round {n}，{verdict}

### 目标与关键成果
{从 GRV 目标拆解表格复制}

### 举措清单
{从 GRV 举措表格复制}

## 完成条件 checklist（三要素格式）
{每条 KR 转换为 checklist 条目}

## 约束
- 只修改 GRV 范围内涉及的文件
- 每次迭代完成后必须运行验证命令
- 发现 GRV 未覆盖的场景 → 记录到 blockers，不自行决策

## GRV 参考路径
- GRV：{grvPath}
- DISCOVERY：{discoveryPath}

## 验证命令参考
{从 GRV 提取所有验收方式对应的命令}
```

### Step 5：启动 Ralph Loop

```bash
# 执行者模式
bash ralph/scripts/ralph-loop.sh \
  --prompt projects/{id}/ralph-prompt.md \
  --state projects/{id}/ralph-state.json \
  --max-iterations 20

# 或自主者模式（GRV 举措已足够清晰时）
bash ralph/scripts/ralph-loop.sh \
  --prompt projects/{id}/ralph-prompt.md \
  --state projects/{id}/ralph-state.json \
  --mode autonomous \
  --max-iterations 20
```

### Step 6：执行中定期同步

| 触发时机 | 操作 |
|---------|------|
| 每次迭代结束 | Ralph 更新 `ralph-state.json`，审查门下省验收意见 |
| 每 5 次迭代 | 向 TPR Orchestrator 报告进度（完成率+blockers） |
| 发现 GRV 缺陷 | 记录到 `decisions`，触发 TPR 重新 Battle |

---

## 四、模式选择决策树

```
Battle 通过后，选择 Ralph 运行模式：

GRV 的 KR 是否足够具体、可直接转化为 checklist？
  ├─ 是（每个 KR 都有明确验收标准）→ 执行者模式
  │   理由：完成条件已清晰，AI 按清单执行即可
  │
  └─ 否（KR 粒度粗、需要 AI 自主探索）→ 自主者模式
      理由：AI 需要自行拆解、验证、记录

GRV 的举措是否完整覆盖所有工作？
  ├─ 是（Battle 已充分讨论）→ 执行者模式
  └─ 否（仍需 AI 自主规划部分路径）→ 自主者模式

用户偏好？
  用户说"按 GRV 逐条执行" → 执行者模式
  用户说"AI 自主推进、以终为始" → 自主者模式
```

**默认推荐**：执行者模式（风险更低，更符合"GRV 已是最终方案"的预设）。

---

## 五、TPR 角色在桥接后的变化

| 角色 | Battle 后职责 | Ralph 循环中职责 |
|------|------------|----------------|
| 编排 Agent（Orchestrator） | 调度 Battle，确认 GRV 定稿 | 监控 Ralph 进度，处理 blockers 升级 |
| 中书省 | 起草 GRV | 归档 GRV，提供方案查询 |
| 门下省 | Battle 审查 | 定期验收（每 5 次迭代） |
| 尚书省 | 应答 Battle | 实际执行角色由 Ralph coding agent 替代 |

**尚书省角色的替代说明**：
- TPR Battle 阶段，尚书省负责应答和防御
- 进入 Ralph Loop 后，执行由 coding agent（Claude Code / Codex）完成
- 尚书省在 Ralph 期间不消失，但其职责转变为"方案守护者"——确保 Ralph 不偏离 GRV 范围

---

## 六、blocker 处理与回退机制

### 6.1 Ralph 遇到 GRV 未覆盖的场景

```
Ralph 发现：GRV 没有覆盖这个技术选型
  ↓
记录到 ralph-state.json > blockers
  ↓
通知 TPR Orchestrator
  ↓
Orchestrator 判断：
  ├─ 触发 TPR 重新 Battle（范围变更）→ 新增 GRV 条款
  └─ 属于细节实现，AI 可自行决策 → 记录到 decisions，继续
```

### 6.2 checklist 无法通过（验证反复失败 > 2 次）

```
Ralph 验证失败 > 2 次
  ↓
检查 GRV 的验收标准是否有误
  ↓
  ├─ GRV 标准本身错误 → 触发 TPR 重新 Battle
  └─ Ralph 执行有误 → 回退本次修改，换方式重做
```

---

## 七、文件归档结构（桥接后）

```
projects/{PROJECT-ID}/
├── DISCOVERY.md           ← TPR Phase 1
├── GRV.md                 ← TPR Phase 2（版本锁定）
├── GRV.md.sig             ← GRV 签名（防篡改）
├── battle/
│   ├── BATTLE-R1-MENXI.md
│   ├── BATTLE-R1-SHANGSHU.md
│   └── BATTLE-SUMMARY.md  ← 最终 verdict
├── bridge-metadata.json    ← 【新增】桥接元数据
├── ralph-state.json        ← 【新增】Ralph 状态
├── ralph-prompt.md         ← 【新增】Ralph 执行 prompt
└── ralph-journal.md        ← 【新增】Ralph 执行日志（每轮迭代汇总）
```

---

## 八、注意事项

1. **GRV 版本锁定后再桥接**。Battle 期间 GRV 可能有多轮修订，桥接前必须确认最终版本。
2. **checklist 不要照搬 KR 原文**。KR 是给人看的验收描述，checklist 是给 AI 看的执行指令，必须翻译为三要素格式。
3. **Ralph Loop 不做 Battle**。如果 Ralph 执行中发现方案有重大缺陷，先停下来，不继续执行，等 TPR 重新 Battle。
4. **coding agent 的模型选择**：Ralph 默认用 Claude Code，可用 `--executor codex` 切换。参考 TPR 模型策略，编码任务不需要最强模型。
