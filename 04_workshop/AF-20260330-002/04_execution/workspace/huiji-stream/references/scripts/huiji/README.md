# AI 慧记 — 脚本清单

## 使用前准备

所有脚本只需 `appKey` 鉴权：

```bash
export XG_BIZ_API_KEY="<your-appKey>"
```

可选增强鉴权（非必须）：

```bash
export XG_USER_TOKEN="<your-access-token>"
```

## 脚本列表

| 脚本 | 用途 | 基本用法 |
|---|---|---|
| `chat-list-by-page.py` | 分页查询我的慧记列表 | `chat-list-by-page.py [--human] [pageNum pageSize]` |
| `list-by-meeting-number.py` | 按视频会议号查询慧记 | `list-by-meeting-number.py [--human] <meetingNumber>` |
| `split-record-list.py` | 全量查询分片转写原文 | `split-record-list.py <meetingChatId>` |
| `split-record-list-v2.py` | 增量查询分片转写原文 | `split-record-list-v2.py <meetingChatId> [lastStartTime]` |
| `check-second-stt-v2.py` | 查询改写原文状态 | `check-second-stt-v2.py <meetingChatId>` |

## 通用参数

**`--human`**：列表查询脚本支持此参数，自动将时间戳转换为可读格式（`2026-03-29 13:59:10`），会议状态加图标（🟢进行中 / ✅已完成），减少 AI 手动转换时间戳出错的风险。

**`--body '<json>'`**：所有脚本均支持传入完整请求体。

所有脚本均支持 `--body '<json>'` 方式传入完整请求体，适合需要使用高级参数的场景：

```bash
# 示例：带筛选条件的列表查询
python3 chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"chatType":7,"nameBlur":"周会"}'

# 示例：带增量时间戳的会议号查询
python3 list-by-meeting-number.py --body '{"meetingNumber":"MTG-001","lastTs":1716345600000}'
```

## 使用示例

```bash
# 查询我的慧记列表（第0页，每页10条）
python3 chat-list-by-page.py 0 10

# 📌 推荐：人类可读格式（时间戳自动转换）
python3 chat-list-by-page.py --human 0 10

# 搜索名称包含"周会"的慧记
python3 chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"nameBlur":"周会"}'

# 按会议号查询
python3 list-by-meeting-number.py MTG-20260327-001

# 全量获取转写原文
python3 split-record-list.py abc123

# 增量获取转写原文（只拉新分片）
python3 split-record-list-v2.py abc123 120034

# 检查改写原文状态
python3 check-second-stt-v2.py abc123
```
