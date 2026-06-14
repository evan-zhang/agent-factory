# Gate 5 CMC/供应链字段抽取提示词

**Gate 类型**：CMC/工艺/质控

**输入**：URL + 抓取文本（DMF 公开信息/原料药厂商/CDE 审评报告）

**必抽字段**：

```json
{
  "api_source": "原料药来源厂商",
  "api_dmf_status": "DMF 状态",
  "manufacturing_site": "生产场地",
  "process_route": "工艺路线概述",
  "capa_status": "现场检查/CAPA 状态",
  "excipient_supplier": "关键辅料供应商"
}
```

**抽取规则**：
- 找不到的字段填 `null`
- 生产场地要具体到国家+城市

**人工确认**：核对原料药来源和工艺路线后写入。
