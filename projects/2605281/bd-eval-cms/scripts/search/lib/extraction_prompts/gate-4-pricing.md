# Gate 4 准入/定价字段抽取提示词

**Gate 类型**：医保/招采/价格

**输入**：URL + 抓取文本（医保局公告/集采公告/省级招采）

**必抽字段**：

```json
{
  "reimbursement_status": "医保乙类 | 医保甲类 | 自费 | 集采中选 | 国谈中选",
  "reimbursement_year": YYYY,
  "nrdl_round": "国谈批次（如 2024 国谈）",
  "vbp_round": "集采批次（如第七批集采）",
  "reimbursement_ratio": 数字（报销比例 0-1）,
  "price_cny": 数字,
  "price_basis": "挂网价 | 中选价 | 医保支付价"
}
```

**抽取规则**：
- 国谈/集采需要明确批次和年份
- 价格以官方公告为准
- 找不到的字段填 `null`

**人工确认**：核对价格和医保状态后写入。
