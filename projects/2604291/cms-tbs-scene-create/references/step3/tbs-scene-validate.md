### tbs-scene-validate.py — Step3 收集完整性校验

**步骤**：在进入 Step4 之前，调用脚本对当前已经收集到的 Step3 关键信息做一次“必填校验”。脚本只负责检查字段是否齐全，并通过 `missingFields` 返回缺失项；不负责落库、不负责持久化任何 JSON，只依赖上游临时拼装的入参。

```bash
python3 scripts/tbs-scene-validate.py --params-json "<当前收集到的 Step3 数据>" --mode step3


输出（统一 JSON）：
- **脚本运行成功**：stdout
  - `success=true`
  - `passed=true/false`
  - `missingFields`（blocking 缺失字段列表）
- **脚本运行失败**：stderr
  - `success=false`
  - `error`

Step3 必填校验（passed=false 时禁止继续进入 Step4 / 需回到 Step2 补全）：
- `时间地点`
- `医生担忧点`
- `代表目标`
- `医生画像`
- `最佳实践要点`

当 `passed=false`：
- 上游 Skill 不进入 Step4
- 根据 `missingFields` 引导用户回到 Step2 仅补全缺失项

当 `passed=true`（必须执行）：
1. 基于 Step3 已确认信息生成：
   - `title`（场景标题）
   - `sceneBackground`（场景背景）
2. `title` 生成规则：
   - 仅包含：`核心顾虑关键词 + 目标动作`
   - 不拼接其他信息（如医院/科室/产品等）
   - 长度 `<= 25` 字
3. `sceneBackground` 必须满足：
   - 覆盖：场景发生时机/地点、双方角色关系、关键顾虑点、代表本次希望达成的训练目标
   - 禁止第一/第二人称（如：你/我/你们/我们/咱们）
   - 禁止具体姓氏/姓名
   - 长度 `<= 180`
4. 生成后让用户确认“完整已确认清单 + 标题 + 场景背景”。
5. 若用户发生修改，按“变更影响回显”执行（必须）：
   - 仅修改 `title`：回显并确认 `完整已确认清单 + title`。
   - 修改 `sceneBackground`：回显并确认 `完整已确认清单 + title + sceneBackground`。
   - 修改 `医生核心顾虑` 或 `代表目标`（关键输入）：必须重新生成并回显确认
     - `title`
     - `sceneBackground`
     - 并标记“产品知识主题需重新生成”，随后进入产品知识主题重生与确认流程。
6. 仅当受影响字段全部重新确认无误后，才允许进入下一阶段（产品知识主题确认）。

