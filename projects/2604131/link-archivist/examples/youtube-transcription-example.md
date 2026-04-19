# Example 3: Full + Transcription — YouTube 视频

## 输入
用户发送：`https://www.youtube.com/watch?v=example789`

## 决策过程
1. 来源判断：youtube.com → **直接 full**（来源规则）
2. yt-dlp 获取信息：标题"AI Agent架构深度解析"，时长 22 分钟，频道"某技术博主"

## 执行过程
1. yt-dlp 提取标题、时长、频道名
2. 时长 >15 分钟 → 需要 whisper 转录
3. yt-dlp -x 下载音频 → whisper 转录为文本
4. 基于转录文本生成报告（补充 web_search 验证关键信息）
5. 搜索本地索引 → 发现与 K-260408-001（Agent框架对比）高度相关
6. 生成完整报告
7. 清理临时文件（rm 音频+转录文件）
8. 归档到 `{archive_dir}/2026-04-13/K-260413-003-AIAgent架构解析.md`

## 输出（报告节选）

```
# AI Agent 架构深度解析：视频调研报告

> 来源：YouTube（某技术博主）
> 链接：https://www.youtube.com/watch?v=example789
> 调研日期：2026-04-13
> 视频时长：22分钟

## 核心观点
1. Agent 架构正从单体向模块化演进
2. Memory 层是当前最大的差异化因素
...

## 与已有调研关联
与 K-260408-001（Agent框架对比）互补：视频侧重架构设计思路，之前的调研侧重功能对比...
```
