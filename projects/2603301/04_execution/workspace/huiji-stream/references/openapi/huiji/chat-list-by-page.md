# POST /ai-huiji/meetingChat/chatListByPage

## 作用

分页查询归属当前用户名下的慧记列表（「我的」慧记），支持筛选和搜索。通常作为获取 meetingChatId 的入口接口。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `pageNum` | Integer | 是 | 页码，从 0 开始 |
| `pageSize` | Integer | 是 | 每页数量 |
| `chatType` | Integer | 否 | 类型筛选：0=玄关会议, 1=上传音频, 2=提交文字, 3=上传文本文件, 4=文件列表, 5=录音, 7=AI慧记, 8=上传音频V2 |
| `chatTypeList` | List\<Integer\> | 否 | 类型列表，传入后忽略 chatType |
| `nameBlur` | String | 否 | 名称模糊搜索 |
| `sortKey` | String | 否 | 排序字段，默认 updateTime |
| `clean` | Boolean | 否 | 是否精简返回，默认 false |
| `sttOkOnly` | Boolean | 否 | 只返回转写成功的记录 |
| `minTs` | Long | 否 | 最小时间戳（毫秒） |
| `maxTs` | Long | 否 | 最大时间戳（毫秒） |

## 响应参数

`data` 类型为 `MeetingChatPageVO`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `total` | Long | 总记录数 |
| `pageContent` | List\<FindChatVO\> | 分页内容列表 |

`FindChatVO` 关键字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `_id` | String | 慧记 ID（用作 meetingChatId，注意后缀处理） |
| `originChatId` | String | 源头 ID（_id 有 `__数字` 后缀时用此字段作为 meetingChatId） |
| `name` | String | 会议名称 |
| `chatType` | Integer | 类型（见上方 chatType 说明） |
| `meetingBegin` | Long | 会议开始时间（毫秒时间戳） |
| `meetingLength` | Long | 会议时长（毫秒） |
| `combineState` | Integer | 状态：0=进行中, 1=处理中, 2=已完成, 3=失败 |
| `summaryState` | Integer | 总结状态：0=未开始, 1=进行中, 2=成功, 3=失败 |
| `simpleSummary` | String | 摘要 |
| `createTime` | Long | 创建时间（毫秒时间戳） |
| `updateTime` | Long | 更新时间（毫秒时间戳） |

## ⚠️ _id 后缀处理

`_id` 可能有 `__数字` 后缀（如 `abc123__45678`），不能直接用作 `meetingChatId`：

- **处理方式一**：截取双下划线前的部分 → `abc123`
- **处理方式二**：使用 `originChatId` 字段

## 请求示例

```bash
# 基本分页（第0页，每页10条）
python3 scripts/huiji/chat-list-by-page.py 0 10

# 筛选 AI 慧记类型 + 名称搜索
python3 scripts/huiji/chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"chatType":7,"nameBlur":"周会"}'

# 按时间范围查询
python3 scripts/huiji/chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"minTs":1716345600000,"maxTs":1716432000000}'
```

## 脚本映射

- `../../scripts/huiji/chat-list-by-page.py`
