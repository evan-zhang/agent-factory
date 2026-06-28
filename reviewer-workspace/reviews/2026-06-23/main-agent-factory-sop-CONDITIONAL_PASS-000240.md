## 审查结论

**总体评级**：CONDITIONAL_PASS  
**置信度**：0.82  
**审查对象**：A 类业务评审 — agent-factory-sop v1.1.0 五项改进方案  
**审查时间**：2026-06-23 00:02 CST  
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 必要性 | 4 | 5 项大多对应 ECC 调研指出的真实缺口；但第 3 项“强制 version”与 ECC 原始观察存在口径差异，需要解释 OpenClaw 为什么比 ECC 更强约束。 |
| 充分性 | 3 | 方向正确，但缺少落地模板、检查口径、例外规则与与现有 S5 预算检查的合并方案。 |
| 一致性 | 4 | S2 定位声明、S4 转发句式、S5 体积审计能形成链路；主要重叠在 version/description 已部分存在于 v1.0.0。 |
| 风险评估 | 3 | “推荐四段式”和“只标注不拦截”冲击较小；强制 version 与转发目标可能制造机械填充、错误依赖和维护负担。 |
| 优先级 | 4 | 建议顺序应为 S2 定位 → S4 description/frontmatter/结构 → S5 审计；如果实施清单未显式排序，容易先改格式后补定位。 |
| 遗漏 | 3 | 缺少基线审计、迁移策略、示例模板、版本 bump 规则、related_skills 校验和重复/重叠检测。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 充分性 | 改动 3 | “frontmatter 强制 version”方向可采纳，但方案没有说明版本字段与现有发布流程、VERSION 文件、semver bump 的关系，容易产生“字段存在但不可信”。 | 现有 SOP v1.0.0 的 SKILL.md 已有 `version: 1.0.0`；S5 自动检查已包含“frontmatter 有 name、description、version”（`SKILL.md:127-129`）。ECC 调研也指出 ECC 中 `version` 只在确实需要版本化时才有（`01-skill-design-patterns.md:46-48`），但落地建议又把 OpenClaw 全量 version 作为 P0（`01-skill-design-patterns.md:200-208`）。 | 保留“OpenClaw Skill 必填 version”，但补充：初始版本默认 `0.1.0` 或发布版 `1.0.0`；任何 S6 发布必须同步 bump frontmatter 与 VERSION；S5 校验 semver 且检查两处一致。 |
| F002 | major | 半截子方案 | 改动 2 | “排除项 + 转发目标”必要，但没有规定转发目标不存在、未安装、名称变化、多个候选时如何写，可能导致虚假的 forward-pointer 网络。 | 现有 description 要求仅含“动词开头、3-5 触发词、排除项”（`SKILL.md:109-113`）；ECC 证据是 `Use frontend-patterns...` 这类明确 forward-pointer（`01-skill-design-patterns.md:70-78`），调研指出 OpenClaw 现状“skill 之间无转发”（`01-skill-design-patterns.md:188-190`）。 | 要求转发目标必须是已存在 Skill 名或标注 `(待建)`；S5 增加 related/forward target 存在性检查；无明确目标时“按需自行处理”只能作为临时占位，并在 S8 迭代候选中记录。 |
| F003 | major | 可执行性 | 改动 5 | 体积审计只给“总量 >50、平均 >150 行”两个阈值，不能定位问题来源，也未说明统计层级，可能只能产生噪音。 | ECC context-budget 给的是分桶审计：Agents、Skills、Rules、MCP、CLAUDE.md 等不同阈值（`01-skill-design-patterns.md:124-140`）；现有 S5 已有单个 SKILL.md 行数预算（`SKILL.md:127`），新增“当前层级总数和平均行数”若不定义层级会与现有预算脱节。 | 定义统计范围为“当前发布层级/目标安装层级”；输出至少包含总数、平均、中位数、Top 5 最大 Skill、超过单体预算清单；总量/平均只做黄色提示，单体预算仍按现有 S5 执行。 |
| F004 | minor | 必要性 | 改动 1 | 四段式结构必要且低风险，但“推荐”可能导致复杂 Skill 继续结构漂移；同时缺少中文标题约定。 | ECC 调研明确总结共同四段式：“When to Use → How to Use → Examples → Best Practices”（`01-skill-design-patterns.md:68`）；现有 SOP 只有写法规范和最小结构，没有 SKILL.md 内部章节规范（`SKILL.md:115-120`）。 | 维持“推荐非强制”，但在 S4 提供模板：`何时触发 / 执行流程 / 示例 / 最佳实践`；若偏离四段式，必须在 CODE-01 摘要说明原因。 |
| F005 | minor | 重叠 | 改动 4 | S2 新增“Skill 定位声明”与 S1 已有排除边界、S3 粒度判断存在重叠；若不整合，会增加重复填写。 | 现有 S1 已要求用户画像、触发词、不做什么、排除边界（`SKILL.md:44-59`）；S2 当前输出 REQ-01 包含用户画像、核心功能、触发词、不做什么、约束、验收（`SKILL.md:61-64`）；S3 已包含拆分/合并的粒度判断（`SKILL.md:83-89`）。 | 把“类型、前置、后置、重叠 Skill”作为 REQ-01 的“路由定位”小节，复用 S1 排除边界，避免重复；S3 只负责验证拆分/合并是否与定位一致。 |
| F006 | minor | 遗漏 | 全案 | 缺少迁移/兼容策略：v1.1.0 对新 Skill 生效没问题，但旧 Skill 如何补 version、origin、description 转发句式未定义。 | ECC 落地建议明确要写 `scripts/skill-audit.js` 扫所有 SKILL.md，缺 origin/version 默认填值（`01-skill-design-patterns.md:200-205`）；README 也把 frontmatter 改造列为 P0（`README.md:14-17`）。 | 增加“v1.1.0 只约束新增/修改 Skill；旧 Skill 通过单独 audit 任务批量治理，不阻塞本 SOP 升级”的说明，并给出迁移脚本需求而非立即纳入 SOP 主流程。 |
| F007 | info | 取舍合理性 | 不采纳项 | 不采纳四象限物理分区、instinct 自动进化、PreToolUse Hook 门控总体合理，符合 SOP 边界；但应保留“语义字段”而非完全丢弃。 | ECC README 认为 Hook 门控与记忆分层是结构性缺失（`README.md:16-19`），但这些属于平台/目录治理；当前 SOP 是 Skill 生产流程，不宜承接平台级改造。 | 在 SOP 中只加入 `metadata.origin`、`metadata.related_skills` 与定位声明；四象限物理迁移、Hook 门控、自动进化另立平台项目。 |

---

**逐项结论**

1. **改动 1：S4 四段式结构规范 — 建议采纳（P1，低风险）**  
   必要。现有 SOP 缺少 SKILL.md 内部结构模板，ECC 证据充分。建议作为“默认模板 + 可解释偏离”，不要强制所有简单工具凑齐四节。

2. **改动 2：S4 description 转发句式 — 建议采纳但需补校验（P0，低-中风险）**  
   很必要。它直接解决 OpenClaw skill 自包含、无 forward-pointer 的路由问题。但“按需自行处理”不能成为常态，否则会稀释转发要求。建议与 `metadata.related_skills` 联动，并在 S5 校验目标存在。

3. **改动 3：S4 frontmatter 强制 version — 条件采纳（P0，中风险）**  
   OpenClaw 工厂化生产需要强制版本化，且现有 SOP 已把 version 写入 S5 检查，因此这不是全新改动，而是把隐性要求前移到 S4。必须补 semver、bump 规则、VERSION 一致性，否则只是格式主义。`metadata.origin` 建议也从“可选”提高到“新增/外部迁入时必填”。

4. **改动 4：S2 Skill 定位声明 — 建议优先采纳（P0，低风险）**  
   这是五项里最能防止后续返工的一项。它把 forward-pointer 和边界判断前置到需求阶段，能支撑改动 2 和 3。注意不要与 S1 排除边界重复，应作为 REQ-01 的“路由定位”小节。

5. **改动 5：S5 Skill 体积审计 — 建议采纳但扩展输出（P1，低风险）**  
   “只标注不拦截”合理，避免因全局包袱阻塞单个 Skill 发布。但阈值和统计维度过粗，应增加 Top N、单体预算、层级定义和基线记录。

---

**建议实施顺序**

1. **先改 S2**：REQ-01 增加“Skill 定位声明/路由定位”。
2. **再改 S4 description/frontmatter**：将定位声明转化为 description 排除项、转发句式、related_skills、version/origin。
3. **再改 S4 SKILL.md 正文模板**：四段式作为推荐模板。
4. **最后改 S5 自动检查**：检查 semver、转发目标、related_skills、行数预算与层级体积审计。
5. **另立迁移任务**：对旧 Skill 做 audit 与批量修复，不阻塞 v1.1.0 SOP 发布。

---

**最重要的一条建议**

把五项改动串成一条闭环：**S2 先声明 Skill 在网络中的位置，S4 把位置写进 description/frontmatter/SKILL.md，S5 再用自动检查验证这些指针和体积是否可信**；不要只追加格式要求。
