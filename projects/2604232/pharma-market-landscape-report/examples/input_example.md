# 输入示例

```yaml
product_name: Velphoro (sucroferric oxyhydroxide)
local_brand_name: Velphoro
therapy_area: 肾脏科 / CKD / 高磷血症
target_market: 台湾
language: 繁體中文
license_holder: Rxilient Medical Taiwan
assessment_mode: market-only
output_mode: full-report
special_notes:
  - 聚焦透析相关服务提供者渠道，区分 HD 与 PD
  - 优先使用 TFDA、NHI、台湾肾脏医学会与主要医学中心官网资料
  - 如涉及 ESRD 患者估算，需标注时间口径与来源差异
```

# 预期行为
- 建立 3 条调研轨道：市场全景、患者分布、渠道深挖。
- 先完成 15 章证据收集，再开始 HTML 报告撰写。
- 输出固定 15 章、3 部分的完整 HTML 报告。
- 对任何缺失事实统一标记为 `[未找到]`。
- 在 KOL、TFDA、NHI、CKD、ESRD、HD、PD 等专业术语上保留英文原文。
