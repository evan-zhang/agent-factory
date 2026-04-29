### 4. tbs-scene-create.py — 落库

**步骤**：在 `tbs-scene-validate.py` passed=true 后，调用 `POST /scene/createScene` 创建对话场景，并返回 `sceneDbId`。脚本只依赖上游从“当前会话内容”临时拼装的入参，不要求把任何 JSON 持久化存储。

```bash
# 推荐：params-json（上游用当前会话内容临时拼装入参）
python3 scripts/tbs-scene-create.py --params-json "<当前会话拼装的入参>" --access-token "$ACCESS_TOKEN"

```
`params-json` 结构需满足（示意）：
```json
{
  "scene": {
    "title": "...",
    "departmentId": "...",
    "drugId": "...",
    "businessDomainId": "...",
    "location": "...",
    "doctorOnlyContext": "...",
    "coachOnlyContext": "...",
    "repBriefing": "...",
    "personaIds": [],
    "knowledgeIds": []
  }
}
```

ID 组装规则（必须）：
- `scene.departmentId` / `scene.drugId` / `scene.businessDomainId` 必须优先使用 Step1 上下文中的 `name -> id` 映射结果。
- 生成阶段如果只有名称（如“消化内科”“乐健素”“临床推广”），先在上下文数组中查对应项：
  - `state.departments[]`：按 `name` 查 `id`
  - `state.drugs[]`：按 `name` 查 `id`
  - `state.businessDomains[]`：按 `name` 查 `id`
- 查到后写入对应 `id` 再调用落库脚本；不要直接把名称填进 `*Id` 字段。
- 若上下文未命中，再走兜底解析（调用已有 name->id 解析能力）并回写上下文。

persona 组装规则（必须）：
- Step2/Step3 已收集的医生画像四要素（人设配置/简介描述/姓氏/职称）用于组装 `scene.personaIds`。
- 落库前先查现有画像：
  - 调用 `GET /rolePersona/forResourceSelect`
  - 按“姓氏 + 职称 + 人设配置/简介描述相似度”匹配（至少保证姓氏/职称一致）
- 命中：
  - 取已有 `personaId`，写入 `scene.personaIds`
- 未命中：
  - 调用 `POST /rolePersona/createRolePersona` 新建画像
  - 用返回的 `personaId` 写入 `scene.personaIds`
- 禁止把医生画像文本直接填进 `scene.personaIds`；该字段必须是 `personaId` 结构数组。

输出约定（统一 JSON）：
- 成功：stdout
  - `success=true`
  - `sceneDbId`（来自 API data）
  - `apiRaw`（API 原始响应，便于排查）
- 失败：stderr
  - `success=false`
  - `error`

