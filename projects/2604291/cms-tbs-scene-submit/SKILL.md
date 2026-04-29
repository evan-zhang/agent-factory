---
name: cms-tbs-scene-submit
description: TBS场景创建 Step4.2：组装参数、查询/创建 persona、调用 API 落库创建场景。
skillcode: cms-tbs-scene-submit
version: 2.0.0
dependencies:
  - cms-auth-skills
---

# cms-tbs-scene-submit（落库提交）

## 核心定位
将已确认的场景数据组装为 API 请求，完成 persona 查建和场景落库。

## 输入（从 state.json 读取）
- `state.config.access_token`（必填）
- `state.config.baseUrl`（必填）
- `state.collect`（场景基础数据、医生画像、title、sceneBackground）
- `state.generate`（knowledgeIds、doctorOnlyContext、coachOnlyContext、repBriefing）

## 执行流程

### Phase 1：前置校验
```bash
python3 scripts/tbs-scene-validate.py --params-json "<组装后的完整参数>" --mode createScene
```
- `passed=false`：返回失败原因，不继续
- `passed=true`：进入 Phase 2

### Phase 2：Persona 查建
医生画像处理规则：
1. 调用 `GET /rolePersona/forResourceSelect`
2. 按「姓氏 + 职称 + 简介/人设相似度」匹配
3. 命中：取已有 personaId
4. 未命中：调用 `POST /rolePersona/createRolePersona` 新建

注意：`personaIds` 必须是 ID 数组，不能填文本。

### Phase 3：落库
```bash
python3 scripts/tbs-scene-create.py --params-json "<最终入参>" --access-token "$ACCESS_TOKEN"
```

入参结构：
```json
{
  "scene": {
    "title": "from state.collect.title",
    "departmentId": "from state.collect.departmentId",
    "drugId": "from state.collect.drugId",
    "businessDomainId": "from state.collect.businessDomainId",
    "location": "from state.collect.location",
    "doctorOnlyContext": "from state.generate.doctorOnlyContext",
    "coachOnlyContext": "from state.generate.coachOnlyContext",
    "repBriefing": "from state.generate.repBriefing",
    "personaIds": "from Phase 2",
    "knowledgeIds": "from state.generate.knowledgeIds"
  }
}
```

## 输出（写入 state.json）
- `state.submit.personaIds`：查建后的 persona ID 列表
- `state.submit.sceneDbId`：创建成功的场景 ID
- `state.submit.status`：success / failed
- `state.submit.error`：失败原因（如有）

## 成功判定
脚本 stdout 输出 `success: true` 且 `sceneDbId` 非空。

## 失败处理
- ID 解析失败：检查 state.collect 中的名称是否在 config 主数据中存在
- persona 创建失败：检查画像四要素是否完整
- createScene API 失败：记录 apiRaw 用于排查

## 配置与授权
- 必填：TBS access-token（从 state.json 读取）
- 可选：TBS_ENV / TBS_BASE_URL 环境变量

## 问题反馈
- Issue 地址：https://github.com/xgjk/xg-skills/issues
- 标题格式：`[cms-tbs-scene-submit] 简要描述问题`
- 建议包含：脚本完整输出、入参 JSON（脱敏）、state.submit 内容
