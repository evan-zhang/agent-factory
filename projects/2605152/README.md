# BD 品种评估流水线 Skill 包

> 一键安装后，任何 Agent 均可独立执行完整的 BD 投前评估流程。

---

## 安装

```bash
# 1. 解压
tar -xzf bd-eval-package.tar.gz
cd bd-eval-package

# 2. 安装
bash install.sh --target ~/.openclaw/skills

# 3. 验证
ls ~/.openclaw/skills/bd-eval/SKILL.md
ls ~/.openclaw/skills/doc-viewer/SKILL.md
ls ~/.openclaw/skills/multi-search/SKILL.md
```

---

## Skill 三层架构

本包包含 **3 个主 Skill + 1 个参考 Skill**，分层说明如下：

### 【主 Skill 1】bd-eval（核心，必须）

```
路径: ~/.openclaw/skills/bd-eval/
来源: 本包自带
用途: 主流水线，包含完整 Phase 1-5.5 执行逻辑
触发词: BD评估 / 跑品种 / 评估新药 / BD品种筛选 / 新批次
```

- SOP 流程规范（v5.2）
- 子 Agent Prompt 模板
- 7 套 BD 评估模板（bd_report_templates_full.md，139KB）
- 归档脚本（archive-links.sh）

### 【主 Skill 2】doc-viewer（核心，必须）

```
路径: ~/.openclaw/skills/doc-viewer/
来源: 本包自带
用途: 生成风格03 琥珀金整体报告 HTML（Phase 5.5 必须）
依赖文件:
  templates/style-03/reference-amber.html   ← 琥珀金参考范例
  templates/style-03/color-themes/amber.yml ← 琥珀金配色
  design-standards/*.md                      ← HTML/CSS/表格/打印规范
```

**为什么必须**: Phase 5.5 整体报告 HTML 只能通过 doc-viewer 生成，缺少此 Skill 则无法完成最终报告展示。

### 【主 Skill 3】multi-search（核心，必须）

```
路径: ~/.openclaw/skills/multi-search/
来源: 本包自带
用途: 多源搜索降级基础设施（Phase 1 和 Phase 3 的搜索能力依赖）
核心能力:
  - 环境能力探测（搜索/抓取/JS渲染）
  - 搜索降级链（web_search → fallback）
  - 三轮递进检索策略
```

**为什么必须**: Phase 1 DISCOVERY 和 Phase 3 GRV 逐章节都需要持续调用 web_search，multi-search 提供了搜索能力的标准化探测和降级逻辑。

### 【参考 Skill】tpr-framework（可选，建议安装）

```
路径: ~/.openclaw/skills/tpr-framework/
来源: 本包自带
用途: Phase 2 模板选择 Battle 和 Phase 4 GRV Battle 的规范参考
核心文件:
  references/battle-protocol.md   ← TPR Battle 规范
  references/grv-standard.md      ← GRV 质量标准
  references/orchestrator-ops.md   ← 子 Agent 编排模式
```

**建议安装**: 即使没有此 Skill，bd-eval 也能跑完流程，但 Phase 2/4 的 Battle 质量会降低。

---

## 完整依赖图

```
bd-eval Skill（主）
  │
  ├── ✅ doc-viewer         ← Phase 5.5 整体报告 HTML 生成
  │       └── templates/style-03/   ← 琥珀金风格模板
  │
  ├── ✅ multi-search      ← Phase 1/3 搜索能力
  │       └── references/         ← 降级策略
  │
  └── ✅ tpr-framework     ← Phase 2/4 Battle 规范（可选）
          └── references/battle-protocol.md
```

---

## 完整流程（Phase 1 → 5.5）

```
用户触发
  ↓
Phase 1: DISCOVERY
  → 宽度搜索（multi-search 探测 + web_search，≥5次）
  → 写入 01-discovery.md
  → 模板匹配（7套模板选1套）
  ↓
Phase 2: 模板选择 Battle
  → 参考 tpr-framework/battle-protocol.md
  → 审查层独立子Agent验证模板选择
  ↓
Phase 3: GRV 逐章节深度评估
  → 逐章 web_search 搜索（每章 ≥3次，multi-search 降级链）
  → 子Agent逐章撰写（参考 sub-agent-prompt-template.md）
  → 独立验证子Agent交叉检查
  → 参考来源含 URL（论文风格 [1][2]）
  ↓
Phase 4: GRV Battle 对抗
  → 参考 tpr-framework/battle-protocol.md
  → 审查层 vs 执行层，最多3轮对抗
  → 输出 03-battle-summary.md + 03-battle.md
  ↓
Phase 5: 报告合并 + 质量终检
  → 合并全部章节 + Battle摘要 → 04-final-report.md
  ↓
Phase 5.5: HTML 生成
  → 整体报告 → doc-viewer skill → 风格03 琥珀金 HTML
  → Battle报告 → bd-eval 自生成 → 蓝白对阵风 HTML
  → 上传 doc.20100706.xyz
  → 归档 links.md + state.json
```

---

## 安装后验证清单

```bash
# 1. 核心 Skill 存在
ls ~/.openclaw/skills/bd-eval/SKILL.md         # ✅ 主流水线
ls ~/.openclaw/skills/doc-viewer/SKILL.md    # ✅ HTML生成器
ls ~/.openclaw/skills/multi-search/SKILL.md  # ✅ 搜索基础设施

# 2. doc-viewer 模板完整
ls ~/.openclaw/skills/doc-viewer/templates/style-03/reference-amber.html
ls ~/.openclaw/skills/doc-viewer/templates/style-03/color-themes/amber.yml

# 3. bd-eval 模板完整
ls ~/.openclaw/skills/bd-eval/references/bd_report_templates_full.md  # 139KB

# 4. 可选 Skill
ls ~/.openclaw/skills/tpr-framework/references/battle-protocol.md   # 推荐安装
```

---

## 版本

| Skill | 版本 |
|-------|------|
| bd-eval | v1.1.0 |
| doc-viewer | 随包版本 |
| multi-search | 随包版本 |
| tpr-framework | 随包版本 |
| SOP | v5.2（含已知问题追踪）|
