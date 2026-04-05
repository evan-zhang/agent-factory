# 评分规则（D1-D5）

## 总体规则

- 每个维度满分 10 分，从 10 开始扣分，下限 1
- 严重问题 -2，轻微问题 -1，不双重扣分（同一问题只扣一次）
- **D4 安全门控**：任意 CRITICAL 安全问题 → 强制 REVISE，不论总分
- 判定规则：总分 ≥ 7.5 AND D4 ≥ 6 → **PASS**；否则 → **REVISE**
- 加权总分 = Σ(维度分 × 对应类型权重)，见 factory-weights.md

---

## D1 — 结构质量

### 扣分项

**严重 -2：**
- SKILL.md 正文超过 80 行（每超 20 行额外 -1，上限扣到 1）
- frontmatter 缺少 name 或 description 字段
- references/ 文件超过 3 个且无法说明各自独立用途
- 有 README.md / CHANGELOG.md / CONTRIBUTING.md 等人类文档
- **有 scripts/ 或 executables，但 SKILL.md 未声明 tools_provided**

**轻微 -1：**
- name 不是 kebab-case 或超过 64 字符
- SKILL.md 有目录但无实际内容的占位章节
- SKILL.md 和 references/ 之间存在重复内容
- assets/ 或 scripts/ 存在但无法说明必要性
- **tools_provided 已声明但缺少 command 字段**
- **tools_provided 缺少 description**

### 加分场景（不超过原始分）
无加分，只扣分。

---

## D2 — 触发质量

### 扣分项

**严重 -2：**
- description 不是动词开头（以 "Use when" / "A skill" / "This skill" 开头）
- description 无任何具体触发词，只有抽象描述
- 与工厂其他已有 Skill 存在明显功能重叠（>50%）

**轻微 -1：**
- description 触发词 < 3 个
- 未覆盖口语化/中文表达（工厂 Skill 中英文混用场景多）
- 有 "Use when..." 章节但内容 < 3 条
- description 超过 30 词（英文）/ 60 字（中文）

---

## D3 — 内容质量

### 扣分项

**严重 -2：**
- 关键步骤无法操作（只说"做什么"，不说"怎么做"）
- 存在 ALWAYS/NEVER/CRITICAL 大写强调，且未附原因解释
- 示例代码有语法错误或引用不存在的函数/变量
- references/ 文件路径在 SKILL.md 中被引用但实际不存在

**轻微 -1：**
- 被动语态为主（"文件应该被读取" 而非 "读取文件"）
- 关键步骤未解释"为什么"，只有指令
- 示例使用 foo/bar/baz 等占位值，不够真实
- 有 ## When to Use 章节但 < 3 条

---

## D4 — 安全合规（门控维度）

### CRITICAL（任意一条 → 强制 REVISE）

- 硬编码凭证（API Key / Token / Password 明文出现在任何文件）
- 使用 `process.env.WRITE` 或直接写入 process.env
- 调用外部 URL 但未在 setup.md 的 External Endpoints 章节声明
- 脚本中有 `eval()`、`exec()` 动态执行未知代码

### 严重 -2：

- 有外部 API 调用但 frontmatter 未声明 `metadata.requires.env`
- setup.md 不存在但 Skill 需要初始化凭证
- 含 "silently" / "secretly" / "automatically monitor" 等敏感词（可能触发扫描器）

### 轻微 -1：

- 字段名用 `appKey` 而非 `apiKey`（易被扫描器关联）
- LLM 凭证由 Skill 内部存储而非调用方注入
- suspicious 标记存在但未在文档中说明是否为误报

### 已知工厂误报白名单（不扣分）

- `env_credential_access`：因 API Key 必须随请求发送，结构性误报，记录即可

---

## D5 — 发布合规

### 扣分项

**严重 -2：**
- ClawHub slug 与 SKILL.md name 字段不一致
- 版本号不符合语义化版本（major.minor.patch）
- 发布后 suspicious 标记为 BLOCKED（非 medium confidence）

**轻微 -1：**
- `05_products/index.md` 未同步最新版本号
- 缺少 `05_products/{skill-name}/design/` 档案目录
- DESIGN.md / DISCUSSION-LOG.md / SHARE-LOG.jsonl 任一缺失
- changelog 描述过于简略（"bug fix" / "update" 不可接受）

---

## D6 — Orchestrator & Multi-Agent 管理

适用类型：工作流类 / 混合类 Skill，尤其是声称支持 Orchestrator 角色的 Skill

### 扣分项

**严重 -2：**
- 声称是 orchestrator 类 Skill，但没有定义任何 sub-agent spawn 规则
- 没有任务状态定义（pending / in_progress / completed / blocked）
- 没有依赖关系管理
- 允许 orchestrator 做执行工作（写代码/写文档）但没有限制说明

**轻微 -1：**
- 缺少 read-only first 原则（复杂任务未分阶段）
- 缺少上下文加载规范（直接塞长文本而不是用文件路径）
- 没有自我改进文档（corrections.md / patterns.md / task-tracker.md）
- 缺少并发限制说明（max concurrent sub-agent 数量）
- 没有文件锁机制说明（防止多 agent 写同一文件）

### 加分场景（不超过原始分 +2）
- 明确区分 Orchestrator 和 Sub-Agent 的职责边界
- 定义了完整的任务追踪和依赖管理机制
- 包含自我反省和经验沉淀的具体触发条件
- 有 read-only first + write/execute 两阶段分离
