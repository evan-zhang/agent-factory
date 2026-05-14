# File2Voice 使用手册

> 产品介绍页：https://doc.20100706.xyz/raw/cd90970cb901
> GitHub 仓库：https://github.com/evan-zhang/agent-factory/tree/master/projects/2605151/file2voice/

## 概述

File2Voice 将文件内容转为口播语音。不是简单地朗读文字，而是先由 AI 改写成口语化的口播稿，再调用 MiniMax Speech TTS 生成音频。

## 核心流程

```
文件 → 文本提取 → AI 改写口播稿 → 用户确认 → TTS 合成 → 音频输出
```

## 命令行用法

```bash
bash scripts/file2voice.sh <输入文件> [选项]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<输入文件>` | 要转换的文件路径 | 必填 |
| `-o, --output <路径>` | 输出音频文件路径 | 与输入同目录 |
| `-s, --style <风格>` | 口播风格 | AI 自动判断 |
| `-d, --duration <分钟>` | 目标时长（3/5/10） | 自动（优先5分钟） |
| `-v, --voice <音色>` | 音色 ID | 根据风格自动匹配 |
| `--auto` | 跳过确认直接生成 | 需确认 |
| `--format <格式>` | 输出格式（mp3/wav） | mp3 |
| `-h, --help` | 显示帮助 | — |

### 使用示例

**基本用法（自动判断风格，需确认）**：
```bash
bash scripts/file2voice.sh report.pdf
```

**指定风格，跳过确认**：
```bash
bash scripts/file2voice.sh article.md -s 播报风 --auto
```

**指定时长和输出路径**：
```bash
bash scripts/file2voice.sh notes.txt -d 3 -o ~/Desktop/output.mp3
```

**指定音色**：
```bash
bash scripts/file2voice.sh doc.docx -v "Chinese (Mandarin)_Radio_Host" --auto
```

## 支持的文件类型

- `.txt` — 纯文本
- `.md` / `.markdown` — Markdown
- `.html` / `.htm` — HTML（自动提取正文）
- `.pdf` — PDF（需安装 pdftotext 或 PyPDF2）
- `.doc` / `.docx` — Word（macOS 自带支持，Linux 需 python-docx）

## 口播风格

File2Voice 支持 5 种预置风格，AI 会根据内容自动选择最合适的：

| 风格 | 适用场景 | 自动匹配关键词 |
|------|----------|----------------|
| 讲解风 | 技术文档、教程、操作指南 | 教程、原理、技术、API、代码 |
| 播报风 | 新闻资讯、行业动态、公告 | 新闻、快讯、报道、发布、更新 |
| 叙事风 | 故事、案例、经历分享 | 故事、小说、经历、旅途 |
| 专业风 | 商务报告、数据分析、战略规划 | 报告、分析、数据、市场、营收 |
| 轻松风 | 生活分享、推荐、日常随笔 | 分享、推荐、好物、生活、旅行 |

你也可以手动指定风格覆盖自动判断。

## 音色列表（常用）

| Voice ID | 说明 |
|----------|------|
| `Chinese (Mandarin)_Male_Announcer` | 男声-播音员（默认） |
| `Chinese (Mandarin)_News_Anchor` | 男声-新闻主播 |
| `Chinese (Mandarin)_Reliable_Executive` | 男声-可靠主管 |
| `Chinese (Mandarin)_Gentleman` | 男声-绅士 |
| `Chinese (Mandarin)_Radio_Host` | 男声-电台主持人 |
| `Chinese (Mandarin)_Warm_Girl` | 女声-温暖少女 |
| `Chinese (Mandarin)_Sweet_Lady` | 女声-甜美女声 |
| `Chinese (Mandarin)_Mature_Woman` | 女声-成熟女性 |
| `Chinese (Mandarin)_Crisp_Girl` | 女声-清脆少女 |

完整列表：https://platform.minimax.io/docs/faq/system-voice-id

## TTS 引擎

File2Voice 支持双通道 TTS：

1. **mmx-cli（优先）**：MiniMax 官方 CLI 工具，自动检测认证和区域
2. **直接 API（降级）**：mmx-cli 不可用时自动降级，直接调用 MiniMax REST API

两者生成的音频质量相同，无需手动切换。

## 额度说明

MiniMax Token Plan Speech HD 按天配额：

| 套餐 | 每日额度 |
|------|----------|
| Plus | 4,000 字 |
| Max | 11,000 字 |
| Plus-Highspeed | 9,000 字 |
| Max-Highspeed | 19,000 字 |

额度每日 UTC 零点（北京时间 08:00）重置。

查询剩余额度：
```bash
mmx quota
```

## 单独使用各脚本

File2Voice 的脚本也可独立调用：

**只提取文本**：
```bash
bash scripts/extract_text.sh input.pdf output.txt
```

**只做文本预处理（风格检测、字数统计）**：
```bash
python3 scripts/rewrite.py input.txt output.txt 5 1250 auto
```

**只做 TTS 合成**：
```bash
bash scripts/tts.sh draft.txt output.mp3 "Chinese (Mandarin)_Male_Announcer" mp3 32000 1
```

## 常见问题

**Q: 提示 "usage limit exceeded"**
A: 当天 Speech HD 额度用完了，等待北京时间 08:00 重置。

**Q: PDF 提取文本为空**
A: 安装 pdftotext：`brew install poppler`，或确认 PDF 不是纯扫描件。

**Q: Word 文件提取失败（Linux）**
A: 安装 python-docx：`pip3 install python-docx`。

**Q: 音频拼接失败**
A: 确认 ffmpeg 已安装：`ffmpeg -version`。
