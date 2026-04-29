## Step1：Fetch training context（进入 Agent 即执行）

**触发**：Agent 一进入创建链路，先执行 Step1。

### 执行脚本（获取业务领域/科室/品种 + 产品知识主数据）
进入 Agent 创建链路后立即执行：
```bash
python3 scripts/tbs-scene-fetch-config.py --access-token "$ACCESS_TOKEN"
```

### 写入上下文（state）
- `state.businessDomains = [{ id, name }]`
- `state.departments = [{ id, name }]`
- `state.drugs = [{ id, name }]`
- `state.productKnowledges = [{ knowledgeId, drugId, category, title }]`

### 写入规则
脚本执行成功后，将结果按数组形式存入上下文：
- `state.businessDomains = [{ id: resolved.businessDomainId, name: <业务领域名称> }]`
- `state.departments = [{ id: resolved.departmentId, name: <科室名称> }]`
- `state.drugs = [{ id: resolved.drugId, name: <品种名称> }]`
- `state.productKnowledges = masterData.knowledgeList`
  - 每项至少包含：`knowledgeId`、`drugId`、`category`、`title`