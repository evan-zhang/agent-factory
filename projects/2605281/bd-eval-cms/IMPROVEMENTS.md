# bd-eval-cms v0.1.0 测试后改进清单

## 来源：利奈昔巴特首次端到端测试（2026-05-28）

---

### 改进项 1：参考文献体系（重大）

**问题**：报告中数据来源标注模糊（"外网核查""分析推断"），没有具体URL、抓取时间和原文内容。无法追溯任何数据点到原始出处。

**需求**：
1. 每次搜索/抓取的资料，原始内容（或摘要）必须单独存储为参考文献
2. 参考文献格式：编号、标题、原始URL、抓取时间、内容摘要/原文摘录
3. 存储位置：`{品种目录}/references/REFERENCES.md`（统一一个文件，编号索引）
4. 报告正文中引用数据时，用参考文献编号标注（类似学术论文 [1][2] 方式）
5. 最终报告末尾附完整参考文献表（含原始URL）

**影响范围**：
- **Phase 1 DISCOVERY**：每次 web_search + web_fetch 的结果都要抓取内容、存入参考文献
- **Phase 3 Gate 子Agent**：每个 Gate 的搜索结果也要存入参考文献
  - Gate 1 前提门：≥3次搜索（Alfasigma资质、5.1类注册、CMS管线）
  - Gate 2 定调门：≥3次搜索（IBAT竞品、PBC瘙痒竞品、Alfasigma中国权利）
  - Gate 3 证据门：≥3次搜索（GLISTEN数据、安全性、KOL观点）
  - Gate 4 支付门：≥4次搜索（PBC流行病学、NRDL定价、Ocaliva状态）
  - Gate 5 成本门：≥3次搜索（合成路线、License-in对价、推广成本）
  - Gate 6 可做门：无额外搜索（综合前面）
- **所有 Skill 定义的搜索要求**：每个技能定义文件中的搜索步骤都要抓取+存储
- **最终报告**：每段数据/事实必须标注参考文献编号，末尾附完整引用表

**修改文件**：
- `SKILL.md`：Phase 1、Phase 3 的搜索指令增加"抓取+存储参考文献"步骤
- `references/SOP.md`：搜索流程增加参考文献采集规范
- `references/sub-agent-prompt-template.md`：Gate writer prompt 增加参考文献要求
- 所有 Gate 子Agent 的 task 指令模板

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

### 修改优先级

| 优先级 | 改进项 | 影响面 | 工作量 |
|--------|--------|--------|--------|
| P0 | 参考文献体系 | 全流程 | 大（SKILL.md + SOP + prompt模板 + Gate指令） |
| P1 | Phase 1 路由决策单 | Phase 1 | 小（SKILL.md + SOP） |

---

### 状态
- [ ] 待统一修改
- 测试报告归档：`利奈昔巴特/FINAL-REPORT.md` + `利奈昔巴特/REPORT.html`
