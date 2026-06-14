# REVIEW-DESIGN-v0.9.2 — 单一入口方案评审

**评审对象**: design/DESIGN-v0.9.2.md
**评审者**: 工厂 Orchestrator（自评审，无独立 Reviewer agent 接入）
**日期**: 2026-06-13
**结论**: PASS

---

## 1. 评审维度

### 1.1 入口单一性 ✅

- 业务程序只需一次调用 `run-opportunity.sh`
- 必填仅 `(product, company)`，其余可选
- 不需要业务侧预创建 case 目录、预写 state.json
- 不需要业务侧理解 12 个 gateStatus

### 1.2 唯一性 / 幂等性 ✅

- `caseCode = YYMMDD-XXXX`，4 字母缩写生成规则明确（英文 4 大写 / 中文 pypinyin FIRST_LETTER / 不足 X 补齐）
- `opportunity_id = caseCode::product::company`，是幂等键
- 同日同 product+company 重复调用：复用现有 case dir，不覆盖 state.json
- 冲突（同日同 4 字母但不同 product/company）：自动加 `-1 / -2` 后缀，超 99 报错

### 1.3 可观测性 ✅

- 4 个结构化 stdout prefix：`CASE_PATH=` / `CASE_CODE=` / `PHASE_STATUS=` / `OPPORTUNITY_ID=`
- 程序可用 `grep '^CASE_' | cut -d= -f2-` 解析
- `--dry-run` 提供零副作用预演

### 1.4 与 v0.9.1 质量护栏兼容 ✅

- 新 case 初始化时所有 gateStatus=pending → preflight 不触发（仅 Phase 5.5 时触发）
- Phase 5.5 触发时由既有 preflight 接管，行为不变
- 不修改 run.sh / orchestrator-resume.sh / start-phase.sh / preflight-phase.sh / render_report.sh / sync-to-knowledge-base.sh
- 不修改 22 个 skill 文件 / 4 个 profile / 既有 fixture

### 1.5 安全性 ✅

- `set -euo pipefail`：所有失败立即退出
- 数组空保护：`${#EXT_PATHS[@]} -gt 0` 守卫
- 参数解析 `${1:-}`：未传参兜底空串
- JSON 解析有 jq 校验
- 外部文件复制只接受 --ext 显式传入的路径

### 1.6 可测试性 ✅

- 17 用例覆盖：缺参、无效参数、英文/中文/混合缩写、真实创建、子目录、state.json、00-opportunity.md、幂等、4 prefix、JSON 文件、JSON stdin、冲突后缀、dry-run
- 全部 17/17 通过
- 既有 v0.9.1 验证门全部兼容：preflight 8/8、style-a1、smoke、health-check 9/9

### 1.7 文档同步 ✅

- SKILL.md frontmatter description 增加 7 个单一入口触发词
- SKILL.md 新增 Step 1.5 调用小节
- EXECUTION.md 替换"快速开始"为程序调用示例
- EXECUTION.md 新增"单一入口脚本"章节
- design/REQ-v0.9.2.md + DESIGN-v0.9.2.md + REVIEW-DESIGN-v0.9.2.md
- design/DISCUSSION-LOG.md 追加工作条目
- version.json changelog 补 0.9.1->0.9.2 条目

---

## 2. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 业务程序误传特殊字符 | `normalize_id` 过滤非 `A-Za-z0-9_-`，中文 company 名降级为空字段 |
| 大量同日同缩写 | 自动加 -1/-2 后缀；超 99 报错 |
| 中文拼音多音字 | pypinyin 默认行为，业务可接受；后续可加 manual 映射表 |
| 外部 ext 文件超大 | 不限制大小，由业务侧自控 |
| 半自动模式误用 | `--mode semi` 明确提示下一步手工命令 |

## 3. 决策

**PASS**：单一入口 v0.9.2 设计满足所有验收标准，可纳入下一轮发版。

**下一步**：
1. 真实全链路测试：等用户提供一个真实品种
2. 通过后与 v0.9.1 质量护栏联合打包为 v0.9.2 发布
3. 发布前必须按白名单提交（不 `git add -A`）

---

## 4. 签核

- 评审者：Factory Orchestrator（自评）
- 日期：2026-06-13
- 状态：PASS
