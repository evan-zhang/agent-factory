# bd-eval-cms v0.1.0 测试后改进清单

## 来源：利奈昔巴特首次端到端测试（2026-05-28）

---

### 改进项 1：参考文献体系（重大）

**问题**：报告中数据来源标注模糊（"外网核查""分析推断"），没有具体URL、抓取时间和原文内容。无法追溯任何数据点到原始出处。多个子 Agent 并行写入同一个 REFERENCES.md 时编号冲突（REF-013 出现两次等）。

**需求**：
1. 每次搜索/抓取的资料，原始内容（或摘要）必须单独存储为参考文献
2. 参考文献格式：编号、标题、原始URL、抓取时间、内容摘要/原文摘录
3. **改造方案：动态前缀 + 独立递增 + 按前缀拆分存储 + Phase 5 合并**
   - 每个子 Agent 由 Orchestrator 在 spawn 时分配唯一前缀，内部从 001 开始独立递增
   - 固定前缀：P1-（Phase 1）、BT-（Battle）
   - 动态前缀：G1-G6（标准 6-Gate）、G7（A-3 的额外 Gate）、OP-（One-pager）、L1-L5（A-0 的5层扫描）、S1-S3（A-7 的3个 Stage）等
   - 存储方式：按前缀拆分为独立文件（P1-references.md、G1-references.md 等）
   - Phase 5 合并时读取所有前缀文件生成 REFERENCES.md 总索引
4. 报告正文中引用数据时，用参考文献编号标注（类似学术论文 [1][2] 方式）
5. 最终报告末尾附完整参考文献表（按前缀分组，含原始URL）

**影响范围**：
- **Phase 1 DISCOVERY**：每次 web_search + web_fetch 的结果都要抓取内容、存入 P1-references.md
- **Phase 3 Gate 子Agent**：每个 Gate 的搜索结果也要存入各自前缀的参考文献文件
  - Gate 1 前提门：≥3次搜索（Alfasigma资质、5.1类注册、CMS管线）
  - Gate 2 定调门：≥3次搜索（IBAT竞品、PBC瘙痒竞品、Alfasigma中国权利）
  - Gate 3 证据门：≥3次搜索（GLISTEN数据、安全性、KOL观点）
  - Gate 4 支付门：≥4次搜索（PBC流行病学、NRDL定价、Ocaliva状态）
  - Gate 5 成本门：≥3次搜索（合成路线、License-in对价、推广成本）
  - Gate 6 可做门：无额外搜索（综合前面）
- **所有 Skill 定义的搜索要求**：每个技能定义文件中的搜索步骤都要抓取+存储
- **最终报告**：每段数据/事实必须标注参考文献编号，末尾附完整引用表

**修改文件**：
- `SKILL.md`：Phase 1、Phase 3 的搜索指令增加"抓取+存储参考文献"步骤，改为动态前缀体系
- `references/SOP.md`：搜索流程增加参考文献采集规范，增加"参考文献前缀分配表"
- `references/sub-agent-prompt-template.md`：Gate writer prompt 增加参考文献要求，改为动态前缀体系
- 所有 Gate 子Agent 的 task 指令模板（spawn 时注入前缀）

---

### 改进项 2：Phase 1 完成输出包含路由决策单

**问题**：Phase 1 完成时 state.json 和 discovery 文件缺少路由决策信息。

**需求**：
- Phase 1 完成时，state.json 和 01-discovery.md 必须包含：
  - 推荐主技能（如 A-1）
  - 串接链路（如 D-1 → D-2 → A-1 → A-6 → D-3）
  - 财务门槛类型（如 创新药）
  - 路由依据说明

**修改文件**：
- `SKILL.md`：Phase 1 输出规范增加路由决策单
- `references/SOP.md`：Phase 1 完成检查清单增加路由项

---

### 改进项 3：增量更新与外部资料注入（v0.2 新增）

**需求**：
1. 支持三种执行模式：全量评估（标准）、全量评估 + 外部资料注入、增量更新（只重跑指定 Gate）
2. 外部资料统一管理：用户提供的补充资料（文件/URL/文本）统一提取关键信息，存入 EXT-references.md，使用固定前缀 EXT-
3. Gate 文件版本管理：增量更新时备份当前版本到 history/ 目录，支持版本对比和回滚
4. 增量更新流程：只重跑指定 Gate + Gate 6 依赖检查 + Battle 审查只审变更 + 更新最终报告
5. 子 Agent prompt 模板改造：增加外部资料优先规则（搜索前先读 EXT-references.md，已覆盖维度减少搜索）
6. 验证子 Agent 模板改造：增加版本一致性检查和外部资料引用检查

**影响范围**：
- **SKILL.md**：Phase 1 之前增加外部资料处理步骤，Phase 3 增量更新模式说明
- **references/sub-agent-prompt-template.md**：Gate/One-pager 子 Agent 模板增加外部资料优先规则，验证子 Agent 模板增加版本检查
- **references/SOP.md**：新增"执行模式"章节（三种模式说明），新增"增量更新 SOP"章节（10步流程），参考文献前缀分配表增加 EXT- 前缀
- **state.json**：增加版本字段（currentVersion、lastUpdatedAt、updatedGates、updateReason、externalReferences）

**修改文件**：
- `SKILL.md`：Phase 1、Phase 3 增加外部资料和增量更新相关指令
- `references/sub-agent-prompt-template.md`：增加外部资料优先规则和版本一致性检查
- `references/SOP.md`：新增执行模式章节和增量更新 SOP 章节

---

### 改进项 4：案件代号体系 + 知识库自动同步（v0.2 新增）

**需求**：
1. 每个品种分配唯一案件代号（格式：YYMM-DDNN），用于知识库目录脱敏
2. Phase 5.5 完成后自动同步所有文件到玄关知识库（产品引进空间）
3. 同步脚本：scripts/sync-to-knowledge-base.sh
4. 增量更新后也触发全量同步

**代号格式**：`{YYMM}-{DDNN}`
- `YYMM` — 立项年月（如 2605 = 2026年5月）
- `DD` — 立项日期（如 29 = 29号）
- `NN` — 当天序号（01-99，从01开始）
- 示例：`2605-2901` = 2026年5月29日第1个案件

**分配时机**：Phase 1 DISCOVERY 创建品种目录时由 Orchestrator 分配

**分配逻辑**：
1. 取当前日期生成 `YYMM` 和 `DD`
2. 检查 `projects/2605281/bd-eval-cms/` 下当月目录中已有多少同日编号
3. 取 max(同日NN) + 1
4. 存入 state.json

**本地目录命名**：
- 本地品种目录仍用品种名（如 `利奈昔巴特`），方便阅读
- 知识库目录用代号（如 `2605-2901`），脱敏
- 映射关系在 state.json 中维护

**知识库配置**：
- API 基础地址：`https://sg-al-cwork-web.mediportal.com.cn/open-api/`
- appKey：`mN6bVc2Xz9Lk4Jh7Gt5Rf3Wp1Yq8As0D`
- 项目空间名称：产品引进知识库
- projectId：`2060176831872499713`

**核心接口**：`uploadContent`（AI 纯文本高速通道）
- 地址：`POST /document-database/file/uploadContent`
- 用途：上传 md/html/json 等纯文本文件
- 关键参数：
  - `projectId`：2060176831872499713
  - `content`：文件内容
  - `fileName`：文件名（不含路径分隔符）
  - `fileSuffix`：文件后缀（md/html/json）
  - `folderName`：目录路径（支持多级，如 `2605/2605-2901/02-gate-by-chapter`）
  - `nameConflictStrategy`：1（覆盖，新增版本）

**同步时机**：Phase 5.5 HTML 生成完成后自动执行

**同步范围**：品种目录下所有文件，包括：
- 根目录：state.json、01-discovery.md、03-battle-summary.md、04-final-report.md、links.md、execution-log.md、REPORT.html
- 02-gate-by-chapter/：所有 .md 文件（含 history/ 下的历史版本）
- battle/：所有 .md 文件
- references/：所有 .md 文件

**知识库目录结构**：
```
产品引进知识库/
└── {YYMM}/                           ← 月份目录（如 2605）
    └── {案件代号}/                    ← 代号目录（如 2605-2901）
        ├── state.json
        ├── 01-discovery.md
        ├── 03-battle-summary.md
        ├── 04-final-report.md
        ├── links.md
        ├── execution-log.md
        ├── REPORT.html
        ├── 02-gate-by-chapter/
        │   ├── One-pager.md
        │   ├── Gate-1-premise.md
        │   ├── ...
        │   └── history/
        │       └── Gate-2-positioning.v1.md
        ├── battle/
        │   ├── ROUTE-SELECTION-AUDITOR.md
        │   ├── BATTLE-R1-AUDITOR.md
        │   └── BATTLE-R1-EXECUTOR.md
        └── references/
            ├── P1-references.md
            ├── G1-references.md
            ├── ...
            ├── EXT-references.md
            └── REFERENCES.md
```

**调用脚本方式**：`bash scripts/sync-to-knowledge-base.sh "{品种目录}" "{案件代号}"`

**修改文件**：
- SKILL.md：Phase 1 增加代号分配、Phase 5.5 增加知识库同步
- references/SOP.md：新增知识库同步说明
- scripts/sync-to-knowledge-base.sh：新增同步脚本
- IMPROVEMENTS.md：本记录

**状态**：
- [x] 已改造（2026-05-29）

---

### 修改优先级

| 优先级 | 改进项 | 影响面 | 工作量 |
|--------|--------|--------|--------|
| P0 | 参考文献体系 | 全流程 | 大（SKILL.md + SOP + prompt模板 + Gate指令） |
| P1 | Phase 1 路由决策单 | Phase 1 | 小（SKILL.md + SOP） |
| P1 | 增量更新与外部资料注入 | 全流程 | 中（SKILL.md + SOP + prompt模板） |
| P1 | 案件代号体系 + 知识库自动同步 | Phase 1 + Phase 5.5 | 中（SKILL.md + SOP + 脚本） |

---

### 状态
- [x] 已改造（2026-05-29）
- 改造方案：动态前缀 + 独立递增 + 按前缀拆分存储 + Phase 5 合并 + 外部资料统一管理 + 增量更新流程 + 案件代号体系 + 知识库自动同步
- 测试报告归档：`利奈昔巴特/FINAL-REPORT.md` + `利奈昔巴特/REPORT.html`
