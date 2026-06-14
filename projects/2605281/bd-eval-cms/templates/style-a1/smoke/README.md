# Style A1 真实案例 Smoke 测试

## 概述

这个目录用于存放 Style A1 模板的真实案例 smoke 测试。Smoke 测试的目的是验证整个渲染链路在真实案例上能够正常工作。

## 使用方法

### 方法1：使用真实案例目录

如果你有真实的案例目录（如 `MB-001-Mage-Biologics`），可以直接运行：

```bash
# 从案例目录运行
python3 templates/style-a1/render.py \
  /path/to/your/case-directory \
  mckinsey-navy \
  /tmp/smoke-test-output.html \
  A-1
```

### 方法2：使用 Fixture 派生

如果真实案例数据不完整，可以从 fixture 派生：

```bash
# 使用 fixture 作为测试数据
python3 templates/style-a1/render.py \
  templates/style-a1/fixtures \
  mckinsey-navy \
  /tmp/smoke-test-output.html \
  A-1
```

### 方法3：创建最小测试案例

创建一个最小化的测试案例目录：

```bash
# 创建临时测试目录
mkdir -p /tmp/smoke-test-case
cd /tmp/smoke-test-case

# 创建必要的文件
# 1. 创建 04-final-report.md（包含完整的 A-1 报告结构）
# 2. 创建 state.json（包含元数据）
```

## 预期结果

成功的 smoke 测试应该：

1. ✅ 渲染器执行成功（退出码 0）
2. ✅ 生成完整的 HTML 文件
3. ✅ 所有模板变量被替换
4. ✅ 必选组件全部存在
5. ✅ 关键组件全部存在
6. ✅ 无校验错误

## 失败情况

如果 smoke 测试失败，可能的原因：

1. **Profile 未注册**：检查使用的 profile 是否在 `profiles/registry.json` 中注册
2. **必选组件缺失**：检查 Markdown 是否包含所有必选结构（结论框、风险框等）
3. **模板变量残留**：检查是否有未替换的 `{{TOKEN}}` 变量
4. **文件格式错误**：检查 Markdown 和 state.json 格式是否正确

## 真实案例要求

真实案例的 Markdown 文件应满足：

### 通用必选结构

- 报告标题（包含 skill_code）
- One-pager 或等价终局先立章节
- 至少 1 个 `conclusion-box`
- 至少 1 个 `risk-box`
- 置信度标识 `[置信度:A/B/C/D]`
- 阶段标签 `[阶段A/B/C]`
- 术语表或 glossary table
- 参考文献章节或 `references-shell`

### A-1 特定要求

- `exclusion-box`（业务主体互斥规则约束框）
- Gate 1 和 Gate 2 结论
- Battle 审查层与执行层结构

详细的契约要求见 `contracts/markdown-contract.md`。

## 示例：最小 A-1 报告结构

```markdown
# A-1 MB-001 投前评估报告

**评估品种**：MB-001
**评估日期**：2026-06-13
**业务单元**：深康

## One-pager 终局先立

**核心结论**：[置信度:A] 建议推进投前尽职调查。

**主要风险**：市场准入风险较高。

## 结论

::: conclusion-box
基于现有分析，建议推进该项目进入下一阶段评估。
:::

## 风险

::: risk-box
主要风险包括市场准入不确定性、供应链稳定性等。
:::

## 业务主体互斥规则约束

::: exclusion-box
本项目不涉及业务主体互斥限制。
:::

## Gate 1 结论卡

**结论**：[阶段A] 条件通过

## Gate 2 结论卡

**结论**：[阶段A] 通过

## 术语与缩写表

| 术语 | 解释 |
|------|------|
| CMS | 合同制造组织 |

## 参考文献

[1] 测试参考文献
```

## 调试技巧

如果 smoke 测试失败：

1. **查看渲染器输出**：渲染器会输出详细的错误信息
2. **检查校验报告**：渲染器会生成 JSON 格式的校验报告
3. **查看生成的 HTML**：检查 HTML 文件是否正确生成
4. **检查 profile 配置**：确认 profile 文件格式正确

## 自动化脚本（可选）

如果需要频繁运行 smoke 测试，可以创建自动化脚本：

```bash
#!/bin/bash
# smoke_test.sh

CASE_DIR="/path/to/your/case"
PROFILE="A-1"
OUTPUT="/tmp/smoke-test-$(date +%s).html"

python3 templates/style-a1/render.py \
  "$CASE_DIR" \
  mckinsey-navy \
  "$OUTPUT" \
  "$PROFILE"

if [ $? -eq 0 ]; then
  echo "✅ Smoke 测试通过"
  echo "输出文件: $OUTPUT"
else
  echo "❌ Smoke 测试失败"
  exit 1
fi
```

## 集成到 CI/CD（可选）

Smoke 测试可以集成到 CI/CD 流程中：

```yaml
# .github/workflows/smoke-test.yml
name: Smoke Test
on: [push, pull_request]

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install beautifulsoup4
      - name: Run smoke test
        run: |
          python3 templates/style-a1/test_render.py
```

## 联系方式

如果遇到问题，请：

1. 查看 `contracts/markdown-contract.md` 了解契约要求
2. 查看 `design/DESIGN-v0.9.1.md` 了解设计细节
3. 检查渲染器输出的详细错误信息
