# Issues #10 & #11 修复任务

## 问题描述

### #10: 会议结束判断逻辑错误
`pull_core.py` 的 `detect_runtime_status()` 调用 `checkSecondSttV2` API 获取 STT 转写状态，但这不是会议整体状态。会议结束后 AI 系统继续往文件写 PPT 内容，导致文件持续增大，被错误判断为"会议仍在进行"。

### #11: 违反用户明确指令
监控脚本在判定会议结束后，向用户发"要做纪要吗？"的消息，违反了用户"不用再和我确认"的指令。这是 SKILL.md / agent 行为层面的问题。

## 代码位置

主要文件：`scripts/huiji/pull_core.py`

### #10 修复方案

在 `pull_core.py` 中：

1. 新增 `detect_combine_state(meeting_chat_id)` 函数，调用 `chatListByPage` API 获取 `combineState` 字段：
   - `combineState=0` → 进行中
   - `combineState=1` → 处理中
   - `combineState=2` → 已完成
   - `combineState=3` → 失败

2. 修改 `run_pull_once()` 的结束判断逻辑：
   - **优先**检查 `combineState`：如果 `=2`（已完成）或 `=3`（失败），立即判定为结束
   - 仅当 `combineState` 无法获取时，fallback 到现有的 `runtime_status` + `consecutive_empty_polls` 判断

3. `chatListByPage` API 信息：
   - URL: `https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/chatListByPage`
   - Method: POST
   - Body: `{"meetingChatId": "xxx", "pageNum": 1, "pageSize": 1}`
   - Response: `result.data[0].combineState`
   - Auth: same as other APIs (appKey header from `XG_BIZ_API_KEY` env var)

4. 当 `combineState=2` 时，触发 `pull_completed()` 做全量拉取确认

### #11 修复方案

这不需要改 Python 代码。在 `pull_core.py` 的 `run_pull_once()` 返回结果中：
- 当会议结束时（`combineState=2`），返回结果中增加 `"meeting_ended": true` 标记
- 调用方（agent/SKILL.md 指令层面）根据此标记决定是否发确认消息
- 但这个需要改 SKILL.md 或 agent 指令，不在本次 Python 修复范围内

## 约束

- 只修改 `scripts/huiji/pull_core.py`
- 不修改其他文件
- 保持现有的 API 调用模式（`_call_api` + `build_headers`）
- 保持向后兼容：`detect_runtime_status()` 仍然存在，新增 `detect_combine_state()` 作为补充
- 不要修改 `poll-scheduler.py` 或其他文件
