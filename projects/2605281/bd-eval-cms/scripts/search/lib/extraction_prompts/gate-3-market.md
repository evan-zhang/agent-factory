# Gate 3 商业/市场字段抽取提示词

**Gate 类型**：市场/竞争/准入

**输入**：URL + 抓取文本（市场报告/医保公告/竞品分析）

**必抽字段**：

```json
{
  "market_size_cny": 数字（人民币元）,
  "market_growth_yoy": 数字（年同比 %）,
  "competitors": ["竞品1", "竞品2"],
  "price_corridor_cny": [最低, 最高],
  "reimbursement_status": "医保乙类 | 医保甲类 | 自费 | 集采中选 | 国谈中选",
  "reimbursement_year": YYYY,
  "channel_accessibility": "高 | 中 | 低"
}
```

**抽取规则**：
- 市场数据以最新公开数据为准（标注年份）
- 价格区间用中国市场价格（人民币）
- 找不到的字段填 `null`

**人工确认**：核对市场规模/医保状态后写入。
