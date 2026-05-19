---
name: link-archivist
version: "1.11.0"
skillcode: link-archivist
github: https://github.com/evan-zhang/agent-factory
description: 当用户发送一个链接（YouTube/通用 URL）、文件或粘贴文本，需要抓取内容并生成调研报告时触发。
---

# Link Archivist

## 安装

### 方式一：手动安装（推荐）

```bash
# 1. 下载 skill 文件
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2604131/link-archivist

# 2. 复制到 OpenClaw 全局 skills 目录（所有 agent 均可使用）
cp -r projects/2604131/link-archivist ~/.openclaw/skills/

# 3. 初始化配置
cd ~/.openclaw/skills/link-archivist
python3 scripts/init_config.py --set archive_dir=/你的归档目录

# 4. 重启 gateway 使 skill 生效
openclaw gateway restart
```

### 方式二：ClawHub 安装（发布后可用）

```bash
openclaw skills install link-archivist
```

### 前置条件

- `agents.defaults.subagents.maxSpawnDepth: 2`（spawn sub-agent 深度需要 ≥2）

### 可选配置

```bash
# Web Search 交叉验证（显著提升报告质量）
python3 ~/.openclaw/skills/link-archivist/scripts/init_config.py --set tavily_api_key=你的key

# 视频归档（仅 full 模式 + YouTube/抖音来源时需要）
python3 ~/.openclaw/skills/link-archivist/scripts/init_config.py --set video_archive_dir=/视频归档目录
```

### 目录说明

Skill 应安装到 **OpenClaw 全局 skills 目录**（`~/.openclaw/skills/`），而非某个 Agent 的 workspace 目录下。全局安装后，所有 Agent 均可调用该 skill，无需重复安装。

## 执行模式（v1.8.0+）

本 Skill 支持两种执行模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **sub-agent（推荐）** | 主 Agent 识别链接后 spawn sub-agent 执行，不阻塞主对话 | 日常使用，用户可能同时有其他交互 |
| **直接执行** | 主 Agent 自己按 Phase 1-5 执行 | 调试、快速测试、sub-agent 不可用时 |

### sub-agent 模式流程

1. **识别**：主 Agent 收到链接，判断需要 Link Archivist 处理
2. **通知用户**：立即回复，告知已安排后台处理及预计时间
   - full 模式：3-5 分钟
   - short 模式：1-2 分钟
   - 含视频下载：额外 +1-2 分钟
3. **spawn worker**：`sessions_spawn` 创建 sub-agent，参数：
   - `task`：读取 `specs/agents/link-archivist-worker.md` 的内容作为任务指令
   - `cwd`：skill 根目录（`projects/2604131/link-archivist/`）
   - `mode`：`run`（一次性任务）
4. **等待完成**：sub-agent 完成后自动 announce
5. **汇报结果**：主 Agent 收到 announce，用正常对话语气向用户报告结果

### sub-agent spawn 模板

主 Agent spawn 时，task 参数示例：
```
你是 Link Archivist Worker。请读取 specs/agents/link-archivist-worker.md 了解你的角色和规则。

任务：处理以下链接
- URL: {url}
- 模式提示: {mode_hint 或 "自动判断"}
- 补充上下文: {extra_context 或 "无"}

请按 SKILL.md 的 Phase 1-5 执行。完成后输出 LINK_ARCHIVIST_RESULT 结构。
```

### 结果汇报模板

主 Agent 收到 sub-agent 结果后，按以下模板向用户汇报：

成功时：
> ✅ 链接处理完成
> 模式：{full/short}
> 归档：{archive_path}
> 摘要：{summary}

部分成功时（有 warning）：
> ✅ 链接处理完成（部分）
> 归档：{archive_path}
> ⚠️ {warnings}
> 摘要：{summary}

失败时：
> ❌ 链接处理失败
> 原因：{失败原因}
> 建议：{用户可采取的行动}

## 触发判断

```
收到消息
 ├─ URL/链接
 │   ├─ sub-agent 模式（推荐）
 │   │   ├─ 通知用户：已安排后台处理，预计 X 分钟
 │   │   ├─ spawn link-archivist-worker sub-agent
 │   │   ├─ 等待 sub-agent 完成（announce）
 │   │   └─ 向用户汇报结果
 │   └─ 直接执行模式
 │       └─ 进入下方 Phase 1-5
 ├─ 文件
 │   └─ 同上（sub-agent 或直接执行）
 ├─ 粘贴文本
 │   └─ 直接判断模式，进入 Phase 1-5
 └─ 未初始化
     └─ 引导配置 archive_dir
```

## 初始化配置

运行 `scripts/init_config.py` 检查配置状态。

配置文件（按环境自动选择路径）：
- OpenClaw：`~/.openclaw/link-archivist-config.json`
- Hermes：`~/.hermes/link-archivist-config.json`
- 其他：`~/.config/link-archivist-config.json`

**配置文件示例**：
```json
{
  "archive_dir": "/path/to/knowledge-base",
  "xgjk_app_key": "your-app-key-here",
  "tavily_api_key": "your-tavily-api-key",
  "video_archive_dir": "/path/to/video-archive"
}
```

- `archive_dir`：本地归档主目录（**必填**）
- `video_archive_dir`：视频归档目录（可选，未配置则不保存视频文件。仅 full 模式生效）
- **Obsidian 同步**：本 Skill 不负责。归档文件写入 `archive_dir` 后，由外部 Observer 机制（如 fsnotify、cron 脚本）同步到 Obsidian

配置 tavily_api_key 可显著提升报告质量（Web Search 交叉验证）。获取：https://tavily.com

## 工作流（阻塞式，禁止跳步）

> **门控规则**：未完成 Phase N 禁止进入 Phase N+1。每阶段 MUST 按顺序执行。
> **进度提示**：每进入一个 Phase MUST 向用户发送进度消息，用户可据此监督和干预。

### Phase 1：初始化与配置检测 [MUST]

**进度提示**：`⚙️ [1/5] 初始化配置中...`

**动作**：运行 `scripts/init_config.py` 检查配置状态。
**门控条件**：`archive_dir` 已配置且目录可写 → 进入 Phase 2。
**未通过**：引导用户配置 `archive_dir`，流程暂停。
**用户可干预**：用户提供 archive_dir 路径，或补充其他配置项。

### Phase 2：抓取内容 + 决定模式 [MUST]

**进度提示**：`📡 [2/5] 正在抓取内容...`

**动作**：
1. 抓取内容 → 判断 URL 类型，分别处理：
   - **今日头条文章**（`m.toutiao.com` 或 `www.toutiao.com`）：调用 `python3 scripts/toutiao_fetch.py "<url>"`
   - **抖音视频**（`v.douyin.com` / `douyin.com`）：调用 `scripts/douyin_process.py`
   - **YouTube 视频**：详见 `references/youtube-workflow.md`
   - **其他通用 URL**：`curl -sL https://r.jina.ai/{url}`
2. 运行 `scripts/decide_mode.py` 判断模式
   - **full**：GitHub/YouTube，或关键词命中（开源/框架/论文等）→ 完整调研报告
   - **short**：新闻资讯类 → 2-3 句话摘要
   - **ask**：不确定 → 问用户

**进度提示**（模式确定后）：`📡 [2/5] 内容已抓取，模式：<full|short|ask>，来源：<类型>`

**视频归档**（可选，仅 full 模式 + 视频来源）：
- 条件：`mode == "full"` 且配置了 `video_archive_dir` 且 URL 是 YouTube / 抖音
- 运行 `scripts/video_archive.py --url "<url>" --platform youtube|douyin --mode full`
- 成功后返回 `temp_path`（临时文件路径），**必须在 Phase 5 传递给 archive_report 或手动 rename**
- 抖音下载失败不阻塞流程，YouTube 失败则报告错误
- 进度提示：`📡 [2/5] 视频保存中...`

**门控条件**：内容已成功抓取 + 模式已确定 → 进入 Phase 3。
**未通过**：按 `references/degradation-rules.md` 降级处理，或报告错误后终止。
**用户可干预**：抓取失败时，用户可手动提供内容文本；mode=ask 时用户决定模式。

### Phase 3：执行调研 + 生成报告 [MUST]

**进度提示**：`🔍 [3/5] 正在执行调研...`

**动作**：按 `references/survey-methodology.md` checklist 逐步执行调研并生成报告。
- full 模式：含 web_search 交叉验证、Claim 验证、GitHub 项目发现
- short 模式：生成 2-3 句话摘要

**full 模式子步骤进度**：
- `🔍 [3/5] 调研：内容分析中...`
- `🔍 [3/5] 调研：GitHub 项目发现中...`
- `🔍 [3/5] 调研：Web Search 交叉验证中...`
- `🔍 [3/5] 调研：Claim 验证中...`
- `🔍 [3/5] 调研：生成个性化洞察中...`

**full 模式额外步骤**：
1. 使用 `session_search` 搜相关历史会话记录
2. 使用 `read_index` 搜本地知识库文件
3. 结合两者动态生成个性化洞察

**门控条件**：报告文件已生成（full 模式须包含 Claim 验证表）→ 进入 Phase 4。
**未通过**：补充缺失内容，重新生成。
**用户可干预**：调研过程中用户可补充信息、指定重点关注方向、纠正错误数据。

### Phase 4：报告验证 [MUST]

**进度提示**：`✅ [4/5] 验证报告完整性...`

**动作**：运行 `scripts/validate_report.py <报告文件> --mode <full|short>`
- 若 `missing` 非空 → MUST 补充缺失 section 后重新验证
- 循环直到 `ok: true`

**进度提示**（验证结果）：
- 通过：`✅ [4/5] 报告验证通过`
- 未通过：`⚠️ [4/5] 报告缺少：<缺失项>，正在补充...`

**门控条件**：`validate_report.py` 返回 `ok: true` → 进入 Phase 5。
**未通过**：按 `missing` 列表补充内容，不得跳过。
**用户可干预**：用户可查看报告草稿，提出修改意见后再归档。

### Phase 5：归档 [MUST]

**进度提示**：`💾 [5/5] 归档中...`

**动作**：MUST 运行 `scripts/archive_report.py` 完成归档，禁止 Agent 直接用 write 工具写文件。
- 脚本自动从服务器系统时间获取日期（`datetime.now()`），禁止使用 LLM 生成的时间
- 本地归档 → `{archive_dir}/YYYY/MM/K-{YYMMDD}-{NNN}-{标题简称}.md`
- YAML 元信息头由脚本自动生成（archive、source、source_type、created_at、tags）

**注意**：本 Skill 单一职责——只负责归档到 `archive_dir`。Obsidian 同步由外部 Observer 机制处理（不在本 Skill 范围内）。

**进度提示**（完成后）：`✅ [5/5] 归档完成：<归档路径>`

**视频 rename**（可选，在归档完成后）：
- 条件：Phase 2 下载了视频（有 temp_path）且归档生成了 archive_id
- 运行 `scripts/video_archive.py --rename --temp "<temp_path>" --archive-id "<archive_id>"`
- 最终路径：`{video_archive_dir}/YYYY/MM/{archive_id}.mp4`
- 进度提示：`💾 视频已归档：<视频路径>`

**完成**：归档路径确认，流程结束。
**用户可干预**：用户可指定归档目录、修改文件名。

> ⚠️ **时间来源要求**：归档日期、编号、YAML created_at 字段 MUST 从服务器系统时间获取（`datetime.now()`），不得使用 LLM 推断的时间。如需校准，优先用 NTP 或世界时 API。

## 降级策略

详见 `references/degradation-rules.md`（YouTube 字幕 / Web Search / 音频转录三种场景）

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/init_config.py` | 检测/创建配置文件 |
| `scripts/decide_mode.py` | 判断 short/full/ask |
| `scripts/youtube_subtitle.py` | YouTube 字幕提取 |
| `scripts/tavily_search.py` | Tavily Web Search |
| `scripts/douyin_process.py` | 抖音视频：mcporter 解析 → curl 下载 → ffmpeg 提取音频 → 报告生成 |
| `scripts/video_archive.py` | 视频归档：YouTube/抖音视频下载到归档目录（可选） |
| `scripts/archive_report.py` | 归档报告到本地目录 |
| `scripts/validate_report.py` | 归档前验证报告完整性（JSON 输出） |

**关键用法**：
```bash
# 判断模式
python3 scripts/decide_mode.py "<URL>" --content "<抓取到的内容>"

# YouTube 字幕提取
python3 scripts/youtube_subtitle.py "<YouTube URL>"
# {"ok": true, "text": "字幕全文", "source": "manual"}

# Tavily 搜索
python3 scripts/tavily_search.py "<关键词>" [max_results]

# 视频归档下载（Phase 2）
python3 scripts/video_archive.py --url "<url>" --platform youtube|douyin --mode full
# {"ok": true, "temp_path": "/path/_temp_143022.mp4", ...}

# 视频归档 rename（Phase 5）
python3 scripts/video_archive.py --rename --temp "<temp_path>" --archive-id "K-260429-003"
# {"ok": true, "path": "/path/K-260429-003.mp4"}

# 检查视频归档是否可用
python3 scripts/video_archive.py --check

# 报告验证
python3 scripts/validate_report.py "<报告文件>" --mode full|short
# {"ok": true, "missing": [], "warnings": [...]}
```

## 参考

| 文件 | 内容 |
|------|------|
| `references/report-template.md` | 报告模板（full + short） |
| `references/archive-template.md` | 归档目录结构、编号规则 |
| `references/decision-rules.md` | 模式判断规则说明 |
| `references/youtube-workflow.md` | YouTube 详细处理流程 |
| `references/survey-methodology.md` | 调研方法论（执行调研完整说明）|
| `references/degradation-rules.md` | 完整降级策略 |
| `examples/` | 4 个完整示例 |

## 工具映射（非 OpenClaw 环境）

| SKILL 工具 | 其他环境对应 | 说明 |
|------------|-------------|------|
| `web_fetch(url)` | `curl -sL {url}` | 网页抓取 |
| `web_search(query)` | OpenClaw 内置 web_search，或 tavily_search.py | 网络搜索 |
| `session_search(query)` | Agent 内置 session_search | 搜历史会话和记忆 |
| `read_index(target)` | `search_files(target="files")` | 搜本地知识库文件 |
| `exec(command)` | 终端执行 | 执行命令 |
| `write(file, content)` | 文件写入 | 写文件 |
| `message(channel, text)` | 无需对应 | Skill 不负责发送 |

## 边界

**本 Skill 负责**：抓取 → 判断 → 调研 → 生成报告 → 归档本地

**不负责**：Obsidian 同步（外部 Observer 处理）、渠道发送（Agent 自行决定）、文件解析（PDF/Word/PPT/图片）、知识索引管理

## 配置与授权

安装后运行 `scripts/init_config.py` 初始化。配置文件：`~/.openclaw/link-archivist-config.json`

| 配置项 | 必填 | 说明 | 获取方式 |
|--------|------|------|----------|
| `archive_dir` | ✅ | 本地归档目录 | 自行指定路径 |
| `xgjk_app_key` | ❌ | 玄关 appKey（AI 慧记转写） | 联系玄关管理员 |
| `tavily_api_key` | ❌ | Tavily API key（Web Search 交叉验证） | https://tavily.com |
| `video_archive_dir` | ❌ | 视频归档目录（未配置则不保存视频，仅 full 模式生效） | 自行指定路径 |

**Obsidian 同步**：本 Skill 不负责同步到 Obsidian。归档文件后，由外部 Observer 机制（如 fsnotify、cron 脚本）处理。

无需配置即可用的能力：r.jina.ai 网页抓取、YouTube 字幕提取、抖音视频 ASR（Token 内置）、GitHub 项目发现。

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new

**标题格式**：`[BUG] link-archivist: 简短描述` 或 `[FEATURE] link-archivist: 简短描述`

**建议包含**：
1. 重现步骤
2. 预期行为 vs 实际行为
3. 环境信息（OpenClaw 版本、操作系统）
4. 相关日志或错误信息
