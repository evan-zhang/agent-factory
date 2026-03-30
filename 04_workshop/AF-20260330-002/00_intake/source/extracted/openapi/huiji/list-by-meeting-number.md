# POST /ai-huiji/meetingChat/listHuiJiIdsByMeetingNumber

## 作用

按视频会议号查询当前用户在该场会议参与关系下可访问的慧记列表。即使会议由他人录制、慧记归属不在当前用户名下，只要当前用户参与了该会议，仍可通过此接口查到。

**与 4.1 的差异**：4.1 查的是「归属在当前用户名下」的慧记；本接口查的是「我参加了的那场视频会议」下的慧记。二者不可替代。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meetingNumber` | String | 是 | 视频会议号（与会议域一致） |
| `lastTs` | Long | 否 | 增量时间戳（毫秒）。不传或 ≤0：拉取最近一个月；>0：增量拉取 |

## 响应参数

`data` 类型为 `List<AiSummaryLastRecordItemVO>`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `chatId` | String | 慧记 ID（即 meetingChatId，可直接传给 4.4/4.8/4.10） |
| `isDoneRecordingFile` | Boolean | 录音文件是否已完成 |
| `open` | Boolean | 会议是否仍在进行中 |
| `startTime` | Long | 开始时间（毫秒） |
| `stopTime` | Long | 结束时间（毫秒），null 表示仍在进行中 |

## 会议状态判断

| 条件 | 状态 | 后续操作 |
|---|---|---|
| `open = true` | 进行中 | 用 4.4/4.10 获取实时转写 |
| `open = false` 且 `isDoneRecordingFile = true` | 已结束 | 先用 4.8 检查改写原文，fallback 到 4.4 |

## 请求示例

```bash
# 基本用法
python3 scripts/huiji/list-by-meeting-number.py MTG-20260327-001

# 增量拉取
python3 scripts/huiji/list-by-meeting-number.py --body '{"meetingNumber":"MTG-001","lastTs":1716345600000}'
```

## 脚本映射

- `../../scripts/huiji/list-by-meeting-number.py`
