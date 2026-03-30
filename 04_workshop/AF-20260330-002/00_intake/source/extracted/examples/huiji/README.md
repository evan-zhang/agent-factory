# AI 慧记 — 使用场景与触发条件

## 场景一：查询会议列表

- **触发**："帮我查一下最近的慧记"、"我的会议记录列表"、"最近有什么会议"
- **接口**：chatListByPage (4.1)
- **语义分流**：用户未提供会议号 → 走归属维度列表
- **示例**：
  ```bash
  python3 scripts/huiji/chat-list-by-page.py 0 10
  ```

## 场景二：按会议号查询

- **触发**："会议号 xxx 的纪要"、"这场会议的慧记"（用户提供了会议号）
- **接口**：listHuiJiIdsByMeetingNumber (4.11)
- **语义分流**：用户提供了会议号 → 走会议维度查询
- **示例**：
  ```bash
  python3 scripts/huiji/list-by-meeting-number.py MTG-20260327-001
  ```

## 场景三：获取会议原文

- **触发**："这个会议说了什么"、"会议内容"、"转写原文"
- **策略**：根据会议状态自动选择最优路径
  - **进行中**：有缓存则 4.10 增量拉取，无缓存则 4.4 全量
  - **已结束**：先 4.8 改写原文，失败则 4.4 兜底
- **示例**：
  ```bash
  # 全量拉取
  python3 scripts/huiji/split-record-list.py <meetingChatId>

  # 增量拉取
  python3 scripts/huiji/split-record-list-v2.py <meetingChatId> 120034

  # 检查改写原文
  python3 scripts/huiji/check-second-stt-v2.py <meetingChatId>
  ```

## 场景四：AI 分析（基于原文）

拿到原文后，AI 根据用户意图进行分析：

### 📝 会议总结
- **触发**："总结一下"、"会议纪要"、"概要"
- **能力**：生成结构化纪要（主题、要点、决策、遗留问题）

### ✅ 待办提取
- **触发**："有什么待办"、"谁负责什么"、"跟进事项"
- **能力**：从原文中提取待办事项、责任人、截止时间

### 🔍 专题分析
- **触发**："关于 xxx 讨论了什么"、"财务那块说了什么"
- **能力**：按主题定位相关讨论内容并提取

## 场景五：搜索会议

- **触发**："帮我找 xxx 的会议"、"搜索 xxx"
- **接口**：chatListByPage (4.1) + nameBlur
- **示例**：
  ```bash
  python3 scripts/huiji/chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"nameBlur":"周会"}'
  ```
