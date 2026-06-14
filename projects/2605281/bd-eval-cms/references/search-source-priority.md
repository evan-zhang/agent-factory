# 来源优先级（v0.10.0）

> 本文档定义 `core_search.sh` + `source_ranker.sh` 用的来源分级规则。

## 四级体系

| Tier | 类型 | 信用分 | 例子 |
|------|------|-------|------|
| **T1** | 政府/监管 | 0.95 | NMPA / CDE / FDA / EMA / PMDA / NHSA / NHC / WHO-IRC / USPTO |
| **T2** | 临床/学术 | 0.85 | ClinicalTrials.gov / PubMed / Cochrane / WHO / MedRxiv |
| **T3** | 行业数据库 | 0.70 | IQVIA / EvaluatePharma / Drugs.com / Pharmacodia / Menet / 弗若斯特沙利文 |
| **T4** | 企业/媒体 | 0.50 | 公司官网 / 药智网 / 行业自媒体 / 36 氪 / 药融云 |

## 排序规则

1. 同一查询结果按 T1→T4 排序
2. 同 tier 内按相关性（web_search 自带 score）
3. 配额吃紧时优先返回 T1+T2
4. T4 标注"需用户核实"才能写入 references/

## 配置位置

`scripts/search/lib/source_priority.json`（核心配置）

## 后续维护

- 添加新域：编辑 json 后无需重启，sub-agent 调脚本时即生效
- 域冲突：若 nmpa.gov.cn 在 T1 也在 T3，**取高 tier**
- 删域：直接删除数组元素

## 不在表内

- 内部百度/Google 搜索结果：按 T4 处理
- 微信公众号转载：按 T4 处理
- 自媒体头条：按 T4 处理
