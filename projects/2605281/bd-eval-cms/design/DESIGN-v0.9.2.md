# DESIGN-v0.9.2 — 单一入口（run-opportunity.sh）

**版本**: v0.9.2 (DRAFT)
**日期**: 2026-06-13
**对应 REQ**: REQ-v0.9.2.md
**前置版本**: v0.9.1 质量护栏版
**状态**: 方案设计

---

## 1. 设计目标

提供一个"业务程序 / 流水线 / cron 任务"可调用的单一入口，传入最少必要信息（品种名 + 公司名 + 可选上下文），自动：

1. 生成唯一 caseCode
2. 创建 case 目录 + 初始化 state.json
3. 写一份 `00-opportunity.md` 留底原始输入
4. 调起 `orchestrator-resume.sh` 自驱 Phase 1 → 5.5
5. 把 case 路径 / caseCode / 当前状态输出到 stdout，程序可解析

---

## 2. 入口设计

### 2.1 脚本路径

`projects/2605281/bd-eval-cms/scripts/run-opportunity.sh`

### 2.2 调用语法

**Flag 形式（推荐，少量字段）**：

```bash
bash scripts/run-opportunity.sh \
  --product "TRTL-729" \
  --company "TestCo Pharma" \
  [--indication "非小细胞肺癌"] \
  [--region "中国"] \
  [--notes "靶向药引进评估"] \
  [--ext /path/to/material.pdf] \
  [--scheme B] \
  [--mode auto] \
  [--dry-run]
```

**JSON 形式（推荐，结构化）**：

```bash
bash scripts/run-opportunity.sh --json /path/to/opportunity.json
```

或 stdin：

```bash
echo '{"product":"TRTL-729","company":"TestCo"}' | bash scripts/run-opportunity.sh --json -
```

### 2.3 JSON Schema

```json
{
  "product": "TRTL-729",
  "company": "TestCo Pharma",
  "indication": "非小细胞肺癌",
  "region": "中国",
  "notes": "靶向药引进评估",
  "scheme": "B",
  "mode": "auto",
  "ext": ["/path/to/material.pdf"],
  "businessEntityHint": "深康"
}
```

字段缺省均允许；`product` 与 `company` 是仅有的必填项。

### 2.4 Stdout 输出契约（程序解析用）

脚本最后 4 行固定输出：

```
CASE_PATH=/Users/.../bd-eval-cms/260613-TRTL
CASE_CODE=260613-TRTL
PHASE_STATUS=phase-1:pending|orchestrator_handoff
OPPORTUNITY_ID=260613-TRTL::TestCo-Pharma::TRTL-729
```

程序可用 `grep '^CASE_'` 提取。

---

## 3. 内部实现

### 3.1 流程图

```
parse args / JSON
  ↓
validate: product / company 非空
  ↓
generate caseCode (date + 4字母缩写)
  ↓
opportunity_id = caseCode + "::" + product + "::" + company
  ↓
case dir = $SKILL_ROOT/$caseCode
  ↓
if case dir 不存在:
  mkdir + subdirs (02-gate-by-chapter, battle, references/P1, EXT, history)
  write state.json (12 gateStatus = pending, lastHeartbeat = now, all opportunity fields)
  write 00-opportunity.md
  write EXT-001.md (if ext provided)
  ↓
if case dir 已存在:
  校验 state.json 存在 + gateStatus 结构 + opportunity 字段与本次输入是否一致
  (若 opportunity_id 一致 → 续跑；若不一致 → 报错)
  ↓
if --dry-run: 打印将要执行的动作，exit 0
  ↓
调用 orchestrator-resume.sh --case-code=$caseCode --mode=$mode
```

### 3.2 caseCode 生成规则

- 日期：`date +%y%m%d` （YYMMDD）
- 4 字母缩写（按 product 推导）：
  - 英文 / 拉丁字符：去空格连字符，取前 4 个字母大写，不足 4 个用 X 补齐
  - 含中文字符：调 `pypinyin` 取每个汉字拼音首字母，最多 4 个，不足 4 个用 X 补齐
  - 混合：分别处理后取前 4 字符
- 冲突保护：同目录已存在但 product 字段不一致 → 追加 `-01 / -02` 后缀
- 长度上限：8 字符（与现有命名一致：JMKX, EPIO, TRTL, LNXB, WSTD）

### 3.3 state.json 初始化

最小字段：

```json
{
  "caseCode": "260613-TRTL",
  "name": "TRTL-729",
  "displayName": "TRTL-729 (TestCo Pharma)",
  "scheme": "B",
  "businessEntity": "待确认",
  "routedSkill": "待路由",
  "routedChain": [],
  "phase": "opportunity_accepted",
  "opportunity": {
    "id": "260613-TRTL::TRTL-729::TestCo-Pharma",
    "product": "TRTL-729",
    "company": "TestCo Pharma",
    "indication": "非小细胞肺癌",
    "region": "中国",
    "notes": "靶向药引进评估",
    "extFiles": [],
    "submittedAt": "2026-06-13T19:55:00+08:00",
    "source": "scripts/run-opportunity.sh"
  },
  "gateStatus": {
    "phase-1": "pending",
    "phase-2": "pending",
    "one-pager": "pending",
    "gate-0": "pending",
    "gate-1": "pending",
    "gate-2": "pending",
    "gate-3": "pending",
    "gate-4": "pending",
    "gate-5": "pending",
    "phase-4-battle": "pending",
    "phase-5-merge": "pending",
    "phase-5-5-html": "pending"
  },
  "lastHeartbeat": "2026-06-13T19:55:00+08:00",
  "inProgressGate": null,
  "currentVersion": 1,
  "gateVersions": {
    "One-pager": 1, "Gate-0": 1, "Gate-1": 1, "Gate-2": 1,
    "Gate-3": 1, "Gate-4": 1, "Gate-5": 1
  },
  "financialThresholdType": "待判断",
  "routingDecision": null,
  "discovery": null,
  "updateHistory": []
}
```

### 3.4 00-opportunity.md 模板

```markdown
# 商机输入

- **caseCode**: 260613-TRTL
- **product**: TRTL-729
- **company**: TestCo Pharma
- **indication**: 非小细胞肺癌
- **region**: 中国
- **scheme**: B
- **notes**: 靶向药引进评估
- **submittedAt**: 2026-06-13T19:55:00+08:00
- **source**: scripts/run-opportunity.sh

## 原始输入

（echo 原始 JSON / flags 完整内容，便于追溯）

## 处置

由 `scripts/run-opportunity.sh` 接收后启动 Phase 1 DISCOVERY。
```

### 3.5 续跑幂等性

- 同日 + 同 product + 同 company → 同 opportunity_id
- 若 case dir 已存在且 opportunity_id 一致 → 视为续跑，调 `orchestrator-resume.sh` 自驱
- 若 case dir 已存在但 opportunity_id 不一致（同缩写冲突）：
  - 报 WARN，加 `-01 / -02` 后缀再创建
  - 或直接拒绝并提示调用方补充信息

### 3.6 与 v0.9.1 质量护栏的兼容

- 新 case 初始化时 `gateStatus.phase-5-5-html = pending` → 不触发 preflight
- Phase 5.5 触发时由 v0.9.1 preflight 接管，行为不变
- 不修改 `start-phase.sh` / `preflight-phase.sh` / `render_report.sh` / `sync-to-knowledge-base.sh`

---

## 4. 文档更新

### 4.1 SKILL.md

- frontmatter `description` 增加触发词：
  - "新商机入池"、"跑一个品种"、"自动跑全链路"、"从品种名自动开始"
- 新增小节：`## 入口与调用`

### 4.2 EXECUTION.md

- "快速开始" 段更新为先用 `run-opportunity.sh`
- 新增"单一入口 / 商机驱动"章节

### 4.3 references/opportunity.example.json

新增 JSON 输入模板。

---

## 5. 测试方案

| 测试 | 预期 |
|------|------|
| `bash -n scripts/run-opportunity.sh` | exit 0 |
| `--help` | 退出码 0 + 完整用法 |
| 缺 product | exit 1 + 明确报错 |
| 缺 company | exit 1 + 明确报错 |
| 英文 product | caseCode 4 字母缩写正确 |
| 中文 product | caseCode 用 pypinyin 首字母 |
| 混合 product | 截前 4 字母 |
| 重复调用同输入 | 幂等，state.json 不被覆盖 |
| 重复调用不同输入同日 | 报冲突 / 加后缀 |
| `--dry-run` | 零文件副作用，退出 0 |
| `--json` | 正常解析 + 启动 |
| `--json -` (stdin) | 正常解析 + 启动 |
| 真实跑一条 | 调起 orchestrator-resume.sh，state.json 正确初始化 |

---

## 6. 文件清单

**新增**：
- `scripts/run-opportunity.sh`
- `design/REQ-v0.9.2.md`
- `design/DESIGN-v0.9.2.md`
- `design/REVIEW-DESIGN-v0.9.2.md` (待 Reviewer)
- `references/opportunity.example.json`
- `scripts/test-run-opportunity.sh` (单元测试)

**修改**：
- `SKILL.md` (frontmatter description + 新增"入口与调用"小节)
- `EXECUTION.md` ("快速开始" + "单一入口" 章节)
- `version.json` (bump 0.9.1 → 0.9.2 + changelog)
- `VERSION` (0.9.1 → 0.9.2)
- `design/DISCUSSION-LOG.md` (追加 v0.9.2 工作条目)

**不修改**：
- run.sh / orchestrator-resume.sh / start-phase.sh / preflight-phase.sh / render_report.sh / sync-to-knowledge-base.sh
- 22 个 skill 文件
- 4 个 profile
- 既有 fixture
- 既有健康检查
