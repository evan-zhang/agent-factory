---
name: xgjk-skill-auditor
description: Audit and score Agent Factory skills across 5 dimensions before publishing. Use when reviewing a skill before ClawHub release, checking skill quality, running security scan, generating PASS/REVISE verdict, or auditing cms-cwork / cms-sop / bp-reporting-templates and other factory skills.
homepage: https://github.com/evan-zhang/agent-factory
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=xgjk-skill-auditor
metadata:
  requires:
    env: []
---

# xgjk-skill-auditor

工厂专属 Skill 质检工具。5 维度评分，给出 PASS/REVISE 判定 + 具体改进方向。

## When to Use

- 发布 Skill 到 ClawHub 之前做质检
- 修改现有 Skill 后验证是否符合标准
- 对某个 Skill 进行安全合规扫描
- 生成评分报告（附 file:line 问题定位）

## Do Not Use When

- 只是想快速读一个 Skill 的内容（直接用 read 工具）
- 想决定"要不要建 Skill"（用颗粒度决策树，见 SKILL-QUALITY-PRINCIPLES.md）

## Audit 流程

### Step 1 — 盘点 + 分类

`find /path/to/skill -type f | sort`，读取 SKILL.md 全文。
确定 Skill 类型（API集成/工作流/纯文档/混合），加载 `references/factory-weights.md` 获取权重。

### Step 2 — 安全扫描（优先）

加载 `references/security-patterns.md`，运行 C1-C5 CRITICAL 扫描。
任意命中 → D4 = 1，直接 REVISE，停止后续评分。
无 CRITICAL → 继续 S1-S3 严重 / M1-M2 轻微扫描。

### Step 3 — 逐维度评分

加载 `references/scoring-rubric.md`，按 D1→D5 顺序评分。
每个问题标注 `[file:line]`，不双重扣分。

### Step 4 — 判定

加权总分 = Σ(维度分 × 权重)
PASS：总分 ≥ 7.5 AND D4 ≥ 6；否则 REVISE

### Step 5 — 输出报告

用以下格式输出（Telegram 适配，先结论）：

```
【PASS / REVISE】skill-name v版本号
综合得分：X.X / 10（API集成类）

• D1 结构质量（15%）：X/10
• D2 触发质量（15%）：X/10
• D3 内容质量（20%）：X/10
• D4 安全合规（35%）：X/10
• D5 发布合规（15%）：X/10

问题清单：
- [D1] SKILL.md 超过 80 行（当前 120 行）→ 推细节入 references/
- [D4] setup.md 缺失，有外部 API 调用 → 新建 setup.md 声明 endpoints

改进方向：
- 优先修复 D4（门控维度）
- 其次处理 D1 超长问题
```

## Core Rules

1. **D4 是门控维度**：CRITICAL 安全问题一票否决，不论其他维度分数。
2. **白名单优先**：`env_credential_access` 是已知误报，不扣分，报告中注明。
3. **问题定位到行**：每个问题必须标注 `[file:line]`，不写模糊描述。
4. **不做修复**：本工具只审计，不修改文件。发现问题 → 列清单 → 等人工处理。

## References

- `references/maintenance.md` — 维护信息（版本/GitHub/Issue 入口）
- `references/factory-weights.md` — Skill 类型分类 + 5 维度权重矩阵
- `references/scoring-rubric.md` — D1-D5 详细 checklist + 评分规则
- `references/security-patterns.md` — CRITICAL/严重/轻微 grep pattern + 误报白名单
