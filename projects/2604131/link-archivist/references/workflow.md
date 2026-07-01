# 工作流（Phase 1-5）

> **门控规则**：未完成 Phase N 禁止进入 Phase N+1。每阶段 MUST 按顺序执行。
> **进度提示**：每进入一个 Phase MUST 向用户发送进度消息。

## Phase 1：初始化与配置检测 [MUST]

**进度提示**：`⚙️ [1/5] 初始化配置中...`

**动作**：运行 `scripts/init_config.py` 检查配置状态。
**门控条件**：`archive_dir` 已配置且目录可写 → 进入 Phase 2。
**未通过**：引导用户配置 `archive_dir`，流程暂停。

## Phase 2：抓取内容 + 决定模式 [MUST]

**进度提示**：`📡 [2/5] 正在抓取内容...`

**动作**：
1. 抓取内容 → 判断 URL 类型：
   - **今日头条**（`m.toutiao.com` / `www.toutiao.com`）：`python3 scripts/toutiao_fetch.py "<url>"`
   - **抖音**（`v.douyin.com` / `douyin.com`）：`scripts/douyin_process.py`
   - **YouTube**：详见 `references/youtube-workflow.md`
   - **其他 URL**（默认 2026-07）：`python3 scripts/firecrawl_fetch.py "<url>"`
     - 输出标出模式 → 送进 decide_mode.py
     - 输出 JSON 模式 → 取 `data.markdown` + `data.metadata.title`
2. 抓取失败 / 输出 < 500 字 → 降级到 `crwl "<url>" -o markdown`（Crawl4AI）
3. 仍失败 → 降级到 `curl -sL https://r.jina.ai/<url>`
4. 运行 `scripts/decide_mode.py` 判断模式
   - **full**：GitHub/YouTube，或关键词命中 → 完整调研报告
   - **short**：新闻资讯类 → 2-3 句话摘要
   - **ask**：不确定 → 问用户

**视频归档**（可选，仅 full 模式 + 视频来源）：
- 运行 `scripts/video_archive.py --url "<url>" --platform youtube|douyin --mode full`
- 成功后返回 `temp_path`，必须在 Phase 5 传递给 archive_report

**门控条件**：内容已成功抓取 + 模式已确定 → 进入 Phase 3。
**未通过**：按 `references/degradation-rules.md` 降级处理。

## Phase 3：执行调研 + 生成报告 [MUST]

**进度提示**：`🔍 [3/5] 正在执行调研...`

**动作**：按 `references/survey-methodology.md` 执行调研并生成报告。
- full 模式：含 web_search 交叉验证、Claim 验证、GitHub 项目发现
- short 模式：2-3 句话摘要

**full 模式额外步骤**：
1. 使用 `session_search` 搜相关历史会话记录
2. 使用 `read_index` 搜本地知识库文件
3. 结合两者动态生成个性化洞察

**门控条件**：报告文件已生成 → 进入 Phase 4。

> **Phase 3 LLM 要求**：MUST 让 LLM 输出符合 frontmatter 格式的字段（summary、entities、tags、confidence），详见 `references/phase3-prompt-template.md`。

## Phase 4：报告验证 [MUST]

**进度提示**：`✅ [4/5] 验证报告完整性...`

**动作**：运行 `scripts/validate_report.py <报告文件> --mode <full|short>`
- 若 `missing` 非空 → MUST 补充缺失 section 后重新验证
- 循环直到 `ok: true`

**门控条件**：`validate_report.py` 返回 `ok: true` → 进入 Phase 5。

## Phase 5：归档 + 索引 [MUST]

> ⚠️ **强制纪律**：归档 **必须** 通过 `scripts/archive_report.py` 执行。**禁止** Agent 自行拼接 frontmatter 或绕过脚本直接写文件。脚本会强制用标准格式重写 frontmatter。

**进度提示**：`💾 [5/5] 归档并索引中...`

**动作**：
1. 运行 `scripts/archive_report.py`，参数：
   - `--file <报告文件>`
   - `--dir {archive_dir}`
   - `--title "<标题>"`
   - `--source-url "<原始URL>"`（外部链接必填）
   - `--summary "<摘要>"`
   - `--entities '<json数组>'`
   - `--tags '<json数组>'`
   - `--confidence <high|medium|low>`
2. 脚本自动：
   - 从服务器系统时间获取日期（禁止用 LLM 推断时间）
   - 生成标准 frontmatter（archive/source/source_type/created_at/entities/summary/tags/confidence）
   - 调用 `lib.kb_index.update_single` 增量索引
   - 触发 XGKB 同步（如果配置了 `.xgkb.json`）
3. 归档路径：`{archive_dir}/YYYY/MM/{K|M}-{YYMMDD}-{NNN}-{标题简称}.md`

**视频 rename**（可选）：
- 条件：Phase 2 下载了视频（有 temp_path）
- 运行 `scripts/video_archive.py --rename --temp "<temp_path>" --archive-id "<archive_id>"`
