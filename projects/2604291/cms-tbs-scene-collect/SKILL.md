---
name: cms-tbs-scene-collect
description: TBS场景创建 Step2-3：引导用户输入场景信息，多轮回显确认，校验通过后生成标题和场景背景。纯交互编排，无脚本调用。
skillcode: cms-tbs-scene-collect
version: 2.0.0
---

# cms-tbs-scene-collect（信息收集与校验）

## 核心定位
引导用户补齐场景创建所需的所有信息。多轮交互，每轮回显完整已确认清单，仅补问缺失项。校验通过后生成 title + sceneBackground。

## 输入（从 state.json 读取）
- `state.config.businessDomains`（展示给用户选择）
- `state.config.departments`（展示给用户选择）
- `state.config.drugs`（展示给用户选择）
- `state.collect`（已有数据，用于断点续接）

## 执行流程

### Phase 1：首次展示输入模板
当 collect section 为空时，展示默认输入模板：

```
开始创建场景。你可以选一种方式发给我：

- 业务领域选哪一类：临床推广 / 院外零售 / 学术合作 / 通用能力？
- 这次主要面对哪个科室/哪类医生？
- 要沟通的产品是什么？
- 场景发生在哪（门诊/病房/院外等）？
- 医生最关注或最担心的问题是什么？（建议 1-2 条）
- 这次代表希望达成什么目标？
- 是否有时间窗口、业务节点或其他背景？

💡 强烈建议顺手补一条：当时你是怎么和医生沟通成功的？
💡 可选补充：请用 2-3 句话描述这位医生。

你可以先简单写，信息不完整也没关系。我会自动提取并回显确认清单，再补问关键缺口。
```

### Phase 2：回显确认 + 补问
从用户回复中提取信息，每轮回显完整已确认清单（不丢字段），仅补问缺失项。

必须收集的字段：
- 业务领域 / 科室 / 品种（从 config 主数据匹配）
- 时间地点
- 医生担忧点（1-2 条）
- 代表目标
- 医生画像四要素（人设配置/简介描述/姓氏/职称）
- 最佳实践要点三项（开场话术/回应问题话术/推荐建议）

回显规则：
1. 每轮输出「完整已确认清单」，包含所有轮次已确认内容
2. 已确认字段不得丢失
3. 每轮最多补问 2 个缺失项

### Phase 3：校验
所有字段收集完毕后，执行校验：
```bash
python3 scripts/tbs-scene-validate.py --params-json "<state.collect>" --mode step3
```
- `passed=false`：回到 Phase 2，只补问 missingFields，不重新展示模板
- `passed=true`：进入 Phase 4

### Phase 4：生成标题与场景背景
基于已确认信息生成：
- `title`：核心顾虑关键词 + 目标动作，<=25 字
- `sceneBackground`：覆盖场景时机/地点、双方角色关系、关键顾虑、训练目标，<=180 字
  - 禁止第一/第二人称
  - 禁止具体姓氏/姓名

生成后让用户确认。用户修改时：
- 仅改 title：回显完整清单 + title
- 改 sceneBackground：回显完整清单 + title + sceneBackground
- 改核心顾虑或目标：重新生成 title + sceneBackground

## 输出（写入 state.json）
- `state.collect` 的所有字段（含 title、sceneBackground）
- 同时回填匹配到的 `businessDomainId`、`departmentId`、`drugId`

## 成功判定
`state.collect.title` 和 `state.collect.sceneBackground` 非空。

## 配置与授权
- 无需 access-token
- 无需额外配置

## 问题反馈
- Issue 地址：https://github.com/xgjk/xg-skills/issues
- 标题格式：`[cms-tbs-scene-collect] 简要描述问题`
- 建议包含：当前已确认清单、缺失字段、校验结果
