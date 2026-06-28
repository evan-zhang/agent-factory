# LEARNING LOOP - Link Archivist

## Daily

### 2026-06-19（v2.0 合并 + C 类评审日）
- **Problem → Rule**：archive_report.py 缺 --tags 参数，导致 Phase 3 模板要求的 tags 永不落盘 → 脚本参数与 prompt 模板必须对齐，C 类评审必查"端到端数据流"
- **Problem → Rule**：parse_frontmatter 无法解析 relationships 嵌套结构 → 改用 PyYAML safe_load，并对历史坏数据做防御
- **Mismatch → Preference**：OKF 对齐初步想承诺 full compliance → 评审后收敛为 OKF-style（保守不承诺），更符合实际定位
- **Pattern**：配置迁移用户担心丢数据 → 改为 .bak 备份不删除，给用户回退窗口

### 2026-06-22（D 类评审日）
- **Problem → Rule**：源码已更新到 2.6.1 但安装态仍停留在 2.5.0 → 发布流程必须包含"同步安装路径"步骤，不能只改源码
- **Problem → Rule**：设计档案（DESIGN.md/LEARNING-LOOP.md/SHARE-LOG.jsonl）长期缺失但功能正常 → 说明档案是"评审合规"需求而非"运行时"需求，但缺档会导致 D 类评审 BLOCK
- **Pattern**：references/ 14 个文件 + SKILL.md 568 行（旧版）→ v2.6.1 已精简到 103 行 + 核心内容移入 references，三层披露落地

**改进行动**：
1. 发布流程加一步：rsync 源码 → 安装路径
2. 每次评审后立即补设计档案，不拖到下次
3. 过程文档及时归档到 docs/archive/

## Weekly

### 2026-W25（06-16 ~ 06-22）
- **重复问题 Top3**：
  1. 版本号不同步（出现 ≥2 次）
  2. 设计档案缺失（每次 D 类评审都中招）
  3. frontmatter 非标准字段积累（skillcode/github）
- **生效规则**：archive_report.py 强制 frontmatter、禁止 LLM 推断时间、不造轮子（v3 wiki 不做）
- **下周计划**：监控 v2.6.1 运行稳定性；考虑 frontmatter 非标准字段的自动化检测

## Monthly

### 2026-06
- **系统性问题**：发布纪律执行不到位（源码改了→制品没同步→版本不同步→档案没补），根因是"发布 checklist"未自动化
- **改进路线图**：
  1. 短期：手动发布 checklist（本次已修复）
  2. 中期：S6 发布步骤脚本化（zip + sync + verify）
  3. 长期：CI 自动校验版本一致性 + 档案完整性
