# LEARNING-LOOP.md

## 改进记录

### 2026-04-05 — tools_provided 检查缺失

**问题**：D1-D5 评分维度均未检查 tools_provided 字段

**发现来源**：GitHub Issue #13

**修复内容**：
- D1 严重 -2：有 scripts/ 但未声明 tools_provided
- D1 轻微 -1：tools_provided 缺少 command 或 description

**教训**：工作流类 Skill 也需要声明可调用工具，确保 Agent 激活后知道执行什么

---

*最后更新：2026-04-05*
