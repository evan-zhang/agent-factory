# Gate 1 监管字段抽取提示词

**Gate 类型**：监管/批准

**输入**：
- URL（来源页）
- 抓取文本（已用 web_fetch 抓取）

**必抽字段**（以 JSON 输出）：

```json
{
  "approval_date": "YYYY-MM-DD",
  "approval_status": "approved | pending | rejected | conditional",
  "holder": "持有人/MAH",
  "indication": "适应症（中文）",
  "regulatory_pathway": "路径（如 NDA / BLA / 优先审评 / 附条件批准）",
  "data_protection": "数据保护期截止日 YYYY-MM-DD 或 N/A",
  "patent_expiry": "核心专利到期日 YYYY-MM-DD 或 N/A"
}
```

**抽取规则**：
- 找不到的字段填 `null`，不要编造
- 日期必须 YYYY-MM-DD 格式，否则填 `null`
- 持有人用官方名称（不要简称）
- 一条来源产出一个 JSON，多来源合并

**人工确认**：抽取完成后请用户核对关键字段（approval_date / holder / indication），确认后再写入 `references/{prefix}/{prefix}-XXX.md`。
