---
name: bp-reporting-templates
description: Generate BP monthly/quarterly/half-year/year report filling templates from BP data (API first, file fallback) with strict reviewer checks for code anchors, numeric traceability, and alert rules. Use when asked to 生成BP报告/填写BP模板/月报/季报/半年报/年报, or when generating performance report templates.
metadata:
  requires:
    env: [BP_APP_KEY]
  homepage: https://github.com/evan-zhang/agent-factory/issues
  version: v1.0.1
tools_provided:
  - name: main
    category: exec
    risk_level: medium
    permission: exec
    description: BP报告模板生成主入口，支持列出周期、模板类型、执行生成
    status: active
  - name: api_client
    category: exec
    risk_level: medium
    permission: read
    description: BP系统API客户端，获取实时数据
    status: active
  - name: filler
    category: exec
    risk_level: medium
    permission: write
    description: 模板填充器，将数据填入模板
    status: active
  - name: parser
    category: exec
    risk_level: low
    permission: read
    description: 解析器和数据预处理器
    status: active
  - name: reviewer
    category: exec
    risk_level: medium
    permission: read
    description: 审核器，校验锚点、数据追溯、告警规则
    status: active
  - name: template_manager
    category: exec
    risk_level: medium
    permission: write
    description: 模板管理器，处理模板存储和读取
    status: active
---

## API 文档

> ⚠️ **重要提示**：本 Skill 调用玄关开放平台 BP API，权威文档是玄关开放平台官方文档。
>
> **官方文档链接**：https://github.com/xgjk/dev-guide/tree/main/02.产品业务AI文档/BP
>
> 本 Skill 的代码实现与官方文档完全一致。如需查看完整的 BP API 规范，请直接访问上述官方文档。

---

# bp-reporting-templates

## Mandatory pre-check (before generation)
When this skill is used, **always do two selections first**:
1. List and select BP period
2. List and select template types (月报/季报/半年报/年报/四套)

Do not generate until both are confirmed.

## Script entry
- `scripts/main.py`

## Useful commands
```bash
# 1) 列出可选周期（供用户选择）
python3 scripts/main.py --list-periods --app-key "$BP_APP_KEY"

# 2) 列出可选生成类型（供用户选择）
python3 scripts/main.py --list-template-types

# 3) 执行生成（示例：季报+年报）
python3 scripts/main.py "为产品中心生成" \
  --app-key "$BP_APP_KEY" \
  --period-id "<period_id>" \
  --template-types "季报,年报" \
  --output ./output

# 4) 输入中未识别组织时可显式指定
python3 scripts/main.py "生成季报" \
  --app-key "$BP_APP_KEY" \
  --period-id "<period_id>" \
  --org-name "产品中心" \
  --template-types "季报"
```

## Runtime rules
- `app_key` must come from env/arg (`BP_APP_KEY` or `COMPANY_APP_KEY`), not hardcoded in code.
- Team default: use the validated standard company key via env injection (prefer `BP_APP_KEY`).
- If period is missing and multiple periods exist, ask user to choose.
- If template types are missing, ask user to choose.
- Keep output markdown traceable to BP source content.
