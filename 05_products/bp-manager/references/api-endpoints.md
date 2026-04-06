# BP API 端点参考

> ⚠️ **重要提示**：本文档仅供参考，**不是权威来源**。
>
> **唯一权威来源**：https://github.com/xgjk/dev-guide/tree/main/02.产品业务AI文档/BP
>
> 本文档是官方文档的本地缓存，可能过时或不完整。如需获取最新的 API 规范，请直接访问官方文档。

**数据源**: 玄关开放平台 - BP系统API说明.md

**最后更新**: 2026-04-06

---

## 接口清单

### 周期管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| listPeriods | GET | /bp/period/list | 查询周期列表 |
| getPeriodDetail | GET | /bp/period/{periodId}/detail | 获取周期详情 |

### 分组管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| listGroups | GET | /bp/group/list | 获取分组树 |
| getPersonalGroupIds | POST | /bp/group/getPersonalGroupIds | 批量查询员工个人类型分组ID |
| searchGroups | GET | /bp/group/searchByName | 按名称搜索分组 |
| getGroupMarkdown | GET | /bp/group/markdown | 获取分组完整BP的Markdown |
| batchGetKeyPositionMarkdown | POST | /bp/group/batchGetKeyPositionMarkdown | 批量获取关键岗位详情Markdown |
| getKeyPositionDetail | GET | /bp/group/getKeyPositionDetail | 获取关键岗位详情（已废弃） |


### 目标管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| getGoalTree | GET | /bp/goal/tree | 获取目标树（含目标、KR、举措） |
| getGoalDetail | GET | /bp/goal/{goalId}/detail | 获取目标详情 |
| createGoal | POST | /bp/goal/create | 新增目标 |
| updateGoal | POST | /bp/goal/update | 更新目标 |
| deleteGoal | POST | /bp/goal/delete | 删除目标 |

### 关键成果（KR）管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| getKrDetail | GET | /bp/kr/{krId}/detail | 获取KR详情 |
| createKr | POST | /bp/kr/create | 新增KR |
| updateKr | POST | /bp/kr/update | 更新KR |
| deleteKr | POST | /bp/kr/delete | 删除KR |

### 关键举措（举措）管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| getActionDetail | GET | /bp/action/{actionId}/detail | 获取举措详情 |
| createAction | POST | /bp/action/create | 新增举措 |
| updateAction | POST | /bp/action/update | 更新举措 |
| deleteAction | POST | /bp/action/delete | 删除举措 |

### 汇报管理

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| getReports | POST | /bp/report/list | 获取汇报列表 |
| getReportDetail | GET | /bp/report/{reportId}/detail | 获取汇报详情 |

---

## 使用说明

本文档是 BP API 的本地缓存，仅供参考。如果发现与官方文档不一致，以官方文档为准。

**如何获取最新官方文档**：
```bash
curl -sL "https://github.com/xgjk/dev-guide/tree/main/02.产品业务AI文档/BP"
```
