# DESIGN-v0.9.1 - bd-eval-cms 质量固化版方案设计

- 日期：2026-06-13
- 阶段：AF-SOP S3 方案设计
- 状态：DRAFT，待 Reviewer 评审与 Evan 确认
- 对应需求：design/REQ-v0.9.1.md
- 目标版本：v0.9.1

## 1. 设计目标

v0.9.1 不做大规模业务扩展，而是把 v0.9 已经跑通的 Style A1 通用模板内核固化为可持续演进的工程底座。

核心目标：

1. profile 可被 schema 校验
2. profile 覆盖状态可被 registry 统一管理
3. 上游 Markdown 与 renderer 之间有明确输出契约
4. renderer 不再静默吞掉关键结构缺失
5. 测试从“组件覆盖”升级到“契约 + 失败策略 + 真实案例 smoke”
6. 发布范围继续可控，避免历史脏工作区误入版本

## 2. 总体架构

v0.9.1 保持现有目录结构不大改，只在 `templates/style-a1/` 下补齐治理层文件与校验逻辑。

建议结构：

```text
templates/style-a1/
  render.py
  test_render.py
  skeleton.html
  styles.css
  design-token.md
  color-themes/
    mckinsey-navy.yml
  profiles/
    common.json
    A-1.json
    A-5.json
    A-7.json
    registry.json          # 新增：profile 注册表
    schema.json            # 新增：profile schema
  contracts/
    markdown-contract.md   # 新增：上游 Markdown 输出契约
  fixtures/
    sample-a-1.md
    sample-a-5.md
    sample-a-7.md
    expected/
      common.json
      by-skill/
        A-1.json
        A-5.json
        A-7.json
      negative/            # 新增：失败用例 expected
  smoke/
    README.md              # 新增：真实案例验收说明
    run_smoke.py 或 shell 入口 # 可选，若实现成本低则新增
```

说明：

- 不移动现有 profile 文件，避免破坏 v0.9 行为。
- 新增 schema / registry / contract，不引入复杂外部依赖。
- 测试优先使用 Python 标准库；如需 JSON Schema 校验，优先实现轻量校验函数，不强制引入 `jsonschema` 包。

## 3. Profile schema 设计

### 3.1 文件位置

`templates/style-a1/profiles/schema.json`

### 3.2 设计原则

schema 不追求覆盖完整业务规则，只约束 profile 的最小可用结构。

v0.9.1 的 schema 只解决三件事：

1. profile 文件是不是可识别
2. 必选字段有没有
3. required_components / coverage_requirements 是否可用于测试

### 3.3 必选字段

每个 skill profile 至少包含：

```json
{
  "version": "0.9.1",
  "profile_type": "skill",
  "skill_code": "A-1",
  "skill_name": "投前评估报告",
  "extends": "common",
  "business_context": {},
  "required_components": {},
  "coverage_requirements": {
    "minimum_coverage": 95,
    "critical_components": []
  },
  "fail_policy": {}
}
```

common profile 至少包含：

```json
{
  "version": "0.9.1",
  "profile_type": "common",
  "required_components": {},
  "coverage_requirements": {
    "minimum_coverage": 95,
    "critical_components": []
  }
}
```

### 3.4 fail_policy 字段

建议每个 skill profile 显式包含：

```json
"fail_policy": {
  "missing_profile": "fail",
  "invalid_profile_schema": "fail",
  "missing_required_component": "fail",
  "unreplaced_template_token": "fail",
  "missing_optional_component": "warn",
  "missing_reference_shell": "warn"
}
```

这样 renderer 和 test_render.py 可以共享同一失败策略。

## 3.5 字段命名与版本迁移决策（评审闭环）

本节用于闭环 S3 评审提出的 P0 条件项，作为 S4 开发前置约束。

### 3.5.1 字段命名决策

v0.9.1 采用零迁移优先策略：

- common profile 与 skill profile 统一沿用 `required_components`。
- 不在 v0.9.1 引入 `expected_components` 作为 profile 主字段。
- `fixtures/expected/` 目录中的 expected 文件继续作为测试期望定义，不与 profile 主字段混用。

原因：现有 `common.json`、`A-1.json`、`A-5.json`、`A-7.json`、`render.py` 与 `test_render.py` 已基于 `required_components` 跑通。v0.9.1 的目标是质量固化，不做字段语义迁移。

### 3.5.2 版本迁移决策

S4 第一步必须统一升级 4 个既有 profile 的版本字段：

- `profiles/common.json`：0.9.0 → 0.9.1
- `profiles/A-1.json`：0.9.0 → 0.9.1
- `profiles/A-5.json`：0.9.0 → 0.9.1
- `profiles/A-7.json`：0.9.0 → 0.9.1

版本升级是 v0.9.1 schema 校验的前置条件。

### 3.5.3 Profile fallback 决策

未知 profile 不允许自动 fallback 到 `default_profile`。

规则：

- 显式传入未知 profile：fail-fast。
- 自动检测到未知 profile：fail-fast，并输出候选 active profile。
- 自动检测不到 profile：fail-fast，要求调用方显式传 profile。
- `registry.default_profile` 只作为注册表元数据或人工提示，不用于自动套用。

原因：错误套用 A-1 比直接失败更危险。

### 3.5.4 Strict 策略决策

v0.9.1 采用 renderer 默认 strict，不新增 CLI `--strict` flag。

规则：

- `render.py` 默认执行 strict 校验。
- `render_report.sh` 只负责透传 profile 参数，不新增 strict 参数。
- 如后续确需宽松模式，必须另起版本设计，不在 v0.9.1 引入。

### 3.5.5 负向测试补齐决策

负向测试必须覆盖 §6.3 的全部 fail-fast 条件，不能只覆盖部分条件。详见 §7.2。

## 4. Profile registry 设计

### 4.1 文件位置

`templates/style-a1/profiles/registry.json`

### 4.2 设计目标

registry 是 profile 的统一索引，用来回答：

- 哪些 skill 已有 profile
- 哪些 skill 只是占位
- 默认 profile 是什么
- 每个 profile 文件在哪里
- 覆盖状态是什么

### 4.3 建议结构

```json
{
  "version": "0.9.1",
  "default_profile": "A-1",
  "default_profile_usage": "metadata_only_no_auto_fallback",
  "profiles": {
    "A-1": {
      "status": "active",
      "file": "A-1.json",
      "description": "海外已上市/中国未上市投前评估",
      "coverage_level": "validated"
    },
    "A-5": {
      "status": "active",
      "file": "A-5.json",
      "description": "中国已上市推广权/代理权接管",
      "coverage_level": "validated"
    },
    "A-7": {
      "status": "active",
      "file": "A-7.json",
      "description": "多标的横向筛选",
      "coverage_level": "validated"
    }
  },
  "planned_profiles": {
    "A-0": { "status": "planned" },
    "A-2": { "status": "planned" },
    "A-3": { "status": "planned" },
    "A-4": { "status": "planned" },
    "A-6": { "status": "planned" },
    "A-8": { "status": "planned" },
    "A-9": { "status": "planned" },
    "D-1": { "status": "planned" },
    "D-2": { "status": "planned" },
    "D-3": { "status": "planned" },
    "D-4": { "status": "planned" },
    "B-1": { "status": "planned" },
    "B-2": { "status": "planned" },
    "B-3": { "status": "planned" },
    "C-1": { "status": "planned" },
    "C-2": { "status": "planned" },
    "C-3": { "status": "planned" },
    "E-1": { "status": "planned" }
  }
}
```

### 4.4 关键约束

- active profile 必须有实际文件。
- planned profile 不要求有实际文件。
- renderer 只允许加载 active profile。
- 未注册 profile 默认 fail-fast，不再静默 fallback 到 A-1。

## 5. Markdown contract 设计

### 5.1 文件位置

`templates/style-a1/contracts/markdown-contract.md`

### 5.2 设计目标

contract 不是写作指南，而是上游报告生成端和 Style A1 renderer 之间的接口协议。

目标是让上游输出稳定结构，避免 renderer 依靠模糊文本猜测。

### 5.3 必选结构

所有 Style A1 profile 的 Markdown 至少应包含：

1. 报告标题，包含 skill code 或 state.json 中提供 skill_code
2. One-pager 或等价终局先立章节
3. 至少一个结论框：`::: conclusion-box`
4. 至少一个风险框：`::: risk-box`
5. 至少一个置信度标识：`[置信度:A]` / `[置信度:B]` / `[置信度:C]` / `[置信度:D]`
6. 至少一个阶段标签：`[阶段A]` / `[阶段B]` / `[阶段C]`
7. 术语表或 glossary table
8. 参考文献章节或 references shell

A-1 额外要求：

- `::: exclusion-box`
- Gate 1 / Gate 2 至少存在
- Battle 审查层与执行层结构

A-5 额外要求：

- 推广权 / 代理权接管相关结论结构
- 既有市场承接风险说明

A-7 额外要求：

- 多标的比较结构
- 筛选结论结构

### 5.4 信息不足表达

禁止上游因为信息不足而省略结构。

正确做法：保留结构，并写明：

- 信息不足
- 当前置信度
- 需要补充的数据
- 对结论的影响

## 6. Renderer 校验策略

### 6.1 当前问题

v0.9 的 renderer 在 profile 不存在时会 fallback 到通用配置或 A-1，这对开发友好，但对生产不安全。

### 6.2 v0.9.1 策略

新增严格模式，建议默认开启。

v0.9.1 不新增 CLI `--strict` flag，统一采用 render.py 默认 strict：

- 显式传 profile 时，profile 不存在即失败
- 未显式传 profile 时，允许从 Markdown / state.json 自动检测
- 自动检测失败、检测到未知 profile、或 profile 未注册时，一律 fail-fast，不自动套用 default_profile
- registry.default_profile 只作为人工提示信息，不参与自动渲染决策

### 6.3 fail-fast 条件

以下情况必须非 0 退出：

1. profile 未注册或非 active
2. active profile 文件不存在
3. profile schema 校验失败
4. required component 缺失
5. critical component 缺失
6. 模板变量残留
7. 输出 HTML 文件未生成

### 6.4 warning 条件

以下情况允许生成，但必须记录 warning：

1. optional component 缺失
2. references-shell 暂未出现
3. profile 自动检测缺失但在失败前输出候选 profile 提示
4. 非关键封面字段缺失，使用默认值

### 6.5 校验报告

建议 renderer 或 test_render.py 输出结构化校验报告：

```json
{
  "profile": "A-1",
  "status": "pass",
  "coverage": 100,
  "errors": [],
  "warnings": []
}
```

## 7. 测试矩阵

### 7.1 正向测试

必须继续通过：

- A-1 fixture：100%
- A-5 fixture：100%
- A-7 fixture：100%
- 模板变量残留：0

### 7.2 负向测试

新增失败用例，与 §6.3 七类 fail-fast 一一对应：

1. `negative/profile-not-registered`：profile 未注册或非 active，必须失败
2. `negative/profile-file-missing`：active profile 文件不存在，必须失败
3. `negative/profile-schema-invalid`：profile schema 校验失败，必须失败
4. `negative/required-component-missing`：required component 缺失，必须失败
5. `negative/critical-component-missing`：critical component 缺失，必须失败
6. `negative/template-token-unreplaced`：模板变量残留，必须失败
7. `negative/output-html-missing`：输出 HTML 文件未生成，必须失败

### 7.3 真实案例 smoke

新增一个真实案例验收入口。

建议不直接修历史案例数据，优先选择一个较干净的新案例或 fixture 派生案例。

验收目标：

- 能运行完整 render_report.sh
- 能生成 HTML
- 能输出校验报告
- 不要求覆盖所有历史案例

## 8. 代码改动范围

v0.9.1 预计修改：

- `templates/style-a1/profiles/schema.json` 新增
- `templates/style-a1/profiles/registry.json` 新增
- `templates/style-a1/contracts/markdown-contract.md` 新增
- `templates/style-a1/render.py` 修改：加载 registry、校验 profile、失败策略
- `templates/style-a1/test_render.py` 修改：增加 schema / registry / negative tests
- `templates/style-a1/fixtures/expected/*` 视需要小幅更新
- `scripts/render_report.sh` 视需要透传 strict 或 profile 参数
- `SKILL.md` / `VERSION` / `version.json` 发版时更新为 0.9.1
- `design/` 文档更新

不应修改：

- `templates/style-12/` 行为
- `templates/style-13/` 行为
- 历史案例目录
- `dependencies/doc-viewer/`
- memory 文件

## 9. 发布白名单

v0.9.1 发布时建议只允许 staging：

- `projects/2605281/bd-eval-cms/SKILL.md`
- `projects/2605281/bd-eval-cms/VERSION`
- `projects/2605281/bd-eval-cms/version.json`
- `projects/2605281/bd-eval-cms/scripts/render_report.sh`（如有改动）
- `projects/2605281/bd-eval-cms/templates/style-a1/`
- `projects/2605281/bd-eval-cms/design/`
- `projects/2605281/bd-eval-cms/references/SOP.md`（如确需同步）

明确排除：

- `memory/`
- `projects/2605281/dependencies/doc-viewer/`
- 历史案例目录
- 老脚本改动，除非本次设计明确纳入
- `projects/2605281/VERSION`，除非项目级版本另行确认

## 10. 风险与控制

### 10.1 过度设计

风险：v0.9.1 变成规则引擎重构。

控制：只做 schema / registry / contract / 校验，不做自动业务判定。

### 10.2 兼容性破坏

风险：严格模式影响已有 A-1/A-5/A-7 fixture。

控制：先保持三 profile 正向测试 100%，再加负向测试。

### 10.3 历史脏改动误提交

风险：本地工作区存在大量历史改动。

控制：发布前用白名单 staging，并在 commit 前执行 `git diff --cached --name-status`。

## 11. 实施顺序

建议 S4 开发按以下顺序执行：

1. 统一 4 个既有 profile version 到 0.9.1，并新增 registry.json 与 schema.json
2. 新增 markdown-contract.md
3. test_render.py 增加 schema / registry 正向测试
4. render.py 接入 registry 与 profile schema 轻量校验
5. 增加负向测试
6. 增加真实案例 smoke 入口
7. 更新文档与版本号
8. 跑完整测试
9. Validator + Reviewer 质量门控
10. 发布 v0.9.1

## 12. S3 评审关注点

建议 Reviewer 重点评审：

1. schema 是否足够小，是否有过度设计
2. registry 是否能支撑后续 20 profile 扩展
3. Markdown contract 是否能真正约束上游输出
4. fail-fast / fail-soft 边界是否合理
5. 测试矩阵是否覆盖生产风险
6. 发布白名单是否能隔离历史脏工作区

## 13. 方案结论

本方案建议将 v0.9.1 定义为“质量固化版”，不扩业务宽度，而是补齐 profile-driven 体系的工程治理层。

如果本方案通过评审，则进入 S4 小步开发；如果评审认为 schema / registry / contract 边界仍不清晰，则回到 S3 修改设计，不进入代码。