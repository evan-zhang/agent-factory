# State 读写约定 — TBS 场景创建流程

## state.json 结构

编排 Skill (`cms-tbs-scene-create`) 负责创建和持久化 state 文件。
所有原子 Skill 通过 state.json 传递数据。

```json
{
  "projectId": "2604291",
  "flow": "scene-create",
  "currentStep": "config|collect|generate|submit",
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "config": {
    "access_token": "xxx",
    "baseUrl": "https://...",
    "businessDomains": [],
    "departments": [],
    "drugs": [],
    "productKnowledges": []
  },
  "collect": {
    "businessDomainName": "",
    "businessDomainId": "",
    "departmentName": "",
    "departmentId": "",
    "drugName": "",
    "drugId": "",
    "location": "",
    "doctorConcerns": "",
    "repGoal": "",
    "doctorPersona": {
      "personaConfig": "",
      "introDescription": "",
      "surname": "",
      "title": ""
    },
    "bestPracticePoints": {
      "openingScript": "",
      "questionResponseScript": "",
      "recommendation": ""
    },
    "title": "",
    "sceneBackground": ""
  },
  "generate": {
    "productKnowledgeNeeds": [],
    "knowledgeIds": [],
    "missingKnowledgeTopics": [],
    "doctorOnlyContext": "",
    "coachOnlyContext": "",
    "repBriefing": ""
  },
  "submit": {
    "personaIds": [],
    "sceneDbId": "",
    "status": "",
    "error": ""
  }
}
```

## 各 Skill 读写矩阵

| Skill | 读 | 写 | 触发条件 |
|-------|----|----|----------|
| config | state.config.access_token | state.config.* | 进入创建链路 |
| collect | state.config (展示选项) | state.collect.* | config 完成 |
| generate | state.collect + state.config.productKnowledges | state.generate.* | collect.title/sceneBackground 已确认 |
| submit | state.collect + state.generate + state.config | state.submit.* | generate 完成 + 用户确认提交 |

## 约定

1. 每个 Skill 只读自己需要的 section，只写自己的 section
2. 编排 Skill 负责检查前置条件、推进 currentStep
3. state.json 是唯一的数据传递介质，不依赖对话上下文传结构化数据
4. access_token 写入 state.config，所有需要鉴权的 Skill 从这里读取
