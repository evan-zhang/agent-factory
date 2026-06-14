# Gate 2 临床字段抽取提示词

**Gate 类型**：临床证据

**输入**：URL + 抓取文本（试验登记页面优先 ClinicalTrials.gov）

**必抽字段**：

```json
{
  "trial_id": "NCT ID 或 ChiCTR ID",
  "phase": "I / II / III / IV",
  "status": "recruiting / active-not-recruiting / completed / terminated",
  "enrollment": 数字,
  "primary_endpoint": "主要终点",
  "primary_completion": "主要终点完成日 YYYY-MM",
  "results_available": true | false,
  "sponsor": "申办方"
}
```

**抽取规则**：
- ClinicalTrials.gov 用 NCT 编号
- 中国试验用 ChiCTR 编号
- 找不到的字段填 `null`
- 数字 enrollment 必须为整数

**人工确认**：核对 phase / status / enrollment 后再写入。
