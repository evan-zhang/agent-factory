---
name: file2voice
description: "文件转口播语音。读取文件内容，AI 改写为口播稿，调用 MiniMax Speech 2.8 TTS 生成音频文件。触发词：转口播、生成口播、文件转语音、朗读、转音频"
version: "1.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605151/file2voice/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=file2voice
---

# File2Voice — 文件转口播语音

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605151`
> 工厂主页：https://github.com/evan-zhang/agent-factory

读取文件内容，AI 智能改写为口播稿，调用 MiniMax Speech 2.8 TTS 生成音频文件。

## 触发判断

```
收到消息
 ├─ 用户发送文件 + 说「转口播」/「生成口播」/「转语音」/「朗读」/「转音频」
 │   → 触发
 │
 ├─ 用户说：file2voice <文件路径>
 │   → 触发
 │
 └─ 其他 → 不触发
```

## 支持的输入文件类型

`.txt`、`.md`、`.markdown`、`.html`、`.pdf`、`.doc`、`.docx`（Word）

## 核心流程

```
文件输入 → 文本提取 → AI 改写口播稿 → 用户确认 → TTS 合成 → 音频输出
```

### Step 1: 文本提取

- `.txt` / `.md` / `.markdown`：直接读取
- `.html`：提取正文，去除标签
- `.pdf`：调用 `pdftotext` 或内置 `pdf` 工具提取文本
- `.doc` / `.docx`：调用 `python-docx` 或 `textutil`（macOS）提取文本
- 提取后统计字数，用于判断口播时长

### Step 2: AI 改写口播稿

将原始文本发给大模型，按以下规则改写：

**时长控制**（按 250 字/分钟估算，优先控制在 5 分钟内）：
- 原文 ≤ 1000 字 → 3 分钟口播（约 750 字）
- 原文 ≤ 2500 字 → 5 分钟口播（约 1250 字）— 默认目标
- 原文 > 2500 字 → 提炼核心，仍控制在 5 分钟内
- 用户明确要求时才生成 10 分钟口播（约 2500 字）

**风格智能判断**：
根据文件内容自动推断口播风格：

| 内容类型 | 推荐风格 | 说明 |
|----------|----------|------|
| 技术文档 | 讲解风 | 结构清晰、术语准确、节奏平缓 |
| 新闻资讯 | 播报风 | 简洁有力、信息密度高 |
| 故事/小说 | 叙事风 | 有情感起伏、节奏变化 |
| 商务报告 | 专业风 | 正式、数据驱动、逻辑清晰 |
| 日常分享 | 轻松风 | 口语化、亲和力强 |

用户也可指定风格覆盖自动判断。将来支持用户自定义风格模板。

**口播稿改写 Prompt 模板**：

```
你是一位专业口播稿撰稿人。请将以下内容改写为一篇适合语音播报的口播稿。

要求：
1. 时长目标：{target_minutes} 分钟（约 {target_chars} 字）
2. 风格：{style}
3. 口播稿要求：
   - 开头有吸引人的引入（3-5 句）
   - 中间内容分段清晰，每段有自然过渡
   - 结尾有总结或引导
   - 避免书面化表达，适合口语朗读
   - 数字、专有名词要读出来自然

原始内容：
---
{original_text}
---

请直接输出改写后的口播稿，不要输出分析过程。
```

### Step 3: 用户确认

向用户展示：
- 检测到 XX 类型内容，建议「XX 风格」
- 目标时长：X 分钟
- 口播稿预览

用户可以：
- 回复「确认」→ 继续 Step 4
- 提出修改意见 → 重新改写
- 指定不同风格/时长 → 调整后重新改写
- 回复「--auto」→ 跳过确认直接生成

### Step 4: TTS 合成

调用 MiniMax Speech 2.8 API：

**API 信息**（已验证 2026-05-15）：
- Endpoint: `POST https://api.minimax.io/v1/t2a_v2`
- 认证: `Authorization: Bearer <MINIMAX_API_KEY>`
- 模型: `speech-2.8-hd`（Max-Highspeed 套餐，19,000字/天 HD 额度）
- 响应: JSON 格式，音频在 `data.audio` 字段，hex 编码
- 响应: JSON 格式，音频在 `data.audio` 字段，hex 编码

**文本分段**：
- API 单次最长 10,000 字符
- 口播稿按自然段落分段，每段不超 2,000 字符（保证合成质量）
- 每段单独调用 TTS
- 多段音频用 `ffmpeg` 拼接为完整文件
- **响应是 JSON（非二进制）**，需从 `data.audio` 提取 hex 编码音频并解码

**默认参数**：
- `voice_id`: `Chinese (Mandarin)_Male_Announcer`
- `speed`: 1
- `format`: mp3
- `sample_rate`: 32000
- `output_format`: hex
- `model`: speech-02-turbo

**风格→音色映射**：

| 风格 | 默认音色 | Voice ID |
|------|----------|----------|
| 讲解风 | 男声-播音员 | Chinese (Mandarin)_Male_Announcer |
| 播报风 | 男声-新闻主播 | Chinese (Mandarin)_News_Anchor |
| 叙事风 | 女声-温暖少女 | Chinese (Mandarin)_Warm_Girl |
| 专业风 | 男声-可靠主管 | Chinese (Mandarin)_Reliable_Executive |
| 轻松风 | 女声-甜美女声 | Chinese (Mandarin)_Sweet_Lady |

### Step 5: 音频输出

- 输出格式：MP3（默认）/ WAV（可指定）
- 多段音频用 `ffmpeg` 拼接
- 返回音频文件给用户

## CLI 接口（可选）

```bash
file2voice <input_file> [options]

选项：
  -o, --output <path>     输出文件路径（默认：与输入同目录）
  -s, --style <style>     口播风格（讲解风/播报风/叙事风/专业风/轻松风）
  -d, --duration <min>    目标时长（3/5/10，默认自动）
  -v, --voice <id>        音色 ID（覆盖自动匹配）
  --auto                  跳过确认直接生成
  --format <fmt>          输出格式（mp3/wav，默认 mp3）
```

## 配置与授权

### 必填配置项

- `MINIMAX_API_KEY`：MiniMax 国际版 API Key
  - 获取方式：https://platform.minimax.io/dashboard
  - 配置方式：环境变量 `MINIMAX_API_KEY` 或在 config.json 中设置

### 可选配置项

- `DEFAULT_VOICE`：默认音色 ID（默认：male-yunbo）
- `DEFAULT_FORMAT`：默认输出格式（默认：mp3）
- `DEFAULT_SAMPLE_RATE`：默认采样率（默认：32000）

### 依赖

- `ffmpeg`：音频拼接（必须）
- `curl`：API 调用（系统自带）
- `python-docx` 或 `textutil`：Word 文件文本提取（可选）
- `pdftotext`：PDF 文本提取（可选，也可用内置 pdf 工具）

### 无需配置即可用

- 文本提取
- 口播稿改写（使用当前 Agent 的大模型）

## 问题反馈

- Issue 地址：https://github.com/evan-zhang/agent-factory/issues/new?labels=file2voice
- 标题格式：`[file2voice] 简要描述`
- 请包含：重现步骤、输入文件类型和大小、错误日志
