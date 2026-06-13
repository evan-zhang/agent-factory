# Source Manifest

> **Evan 落地配置（2026-06-13）**
> - `PROJECT_ROOT = /Users/evan/Documents/BP`
> - 集团 BP 体系基础材料位于 `PROJECT_ROOT/` 根目录（`BP体系完整说明稿（初版）.md` 等）
> - 集团及中心 BP 业务材料（`集团及中心BP/` 子目录）当前**缺失待补**，本 skill 落地时不随附
> - 报告母版位于 `/Users/evan/Documents/BP报告母版/`，作为另一组源材料

## 1. Source Discipline

Classify every source before using it:

| Status | Meaning | Can Support Final Claims |
|---|---|---|
| 已完整读取 | Main body or relevant full section read | Yes |
| 已读取关键部分 | Relevant part read, not full source | Scoped claims only |
| 只读到片段 | Search result, excerpt, preview, or partial text | Limited background only |
| 已定位但未打开 | Found but not opened | No |
| 附件/评论未读 | Attachment, embedded content, or comment not read | No |
| 缺失待补 | Expected source unavailable | No |

Do not cite unread sources as evidence.

## 2. Project Root Configuration

Before reading or writing any project file, confirm the project root with the user.

```
PROJECT_ROOT = <user-confirmed path>
```

How to determine PROJECT_ROOT by platform:

| Platform | How to set |
|---|---|
| Claude Code (local) | Infer from open files, or ask the user once at session start |
| OpenClaw | Ask the user in the first message if not already stated |
| Hermes (API) | Expect the user to provide it in the first message; ask if not provided |
| No file access | Set to N/A; ask the user to paste source content directly into the chat |

If PROJECT_ROOT cannot be determined, mark all file-based sources as 缺失待补 and proceed with user-provided content only.

## 3. Default Project Files (relative to PROJECT_ROOT)

The skill may use these files when accessible and relevant. Always verify the current path and read status.

| Type | Relative Path |
|---|---|
| BP rulebook | `集团BP生成要求规划书_v0.2.md` |
| Latest group BP docx | `集团及中心BP/【BP系统版】康哲集团2026年度业务计划BP.docx` |
| Group SP docx | `集团及中心BP/康哲集团五年战略规划（2026-2030年）纲要版-v1-20260107.docx` |
| Original group BP markdown | `集团及中心BP/集团_1781261080316.md` |
| Product center BP | `集团及中心BP/产品中心_1781261853002.md` |
| Finance center BP | `集团及中心BP/财经中心_1781261895868.md` |
| Operation management center BP | `集团及中心BP/经营管理中心_1781261866751.md` |
| HR center BP | `集团及中心BP/人力资源中心_1781261876801.md` |
| Supply chain center BP | `集团及中心BP/供应链中心_1781261885501.md` |
| Outside-hospital center BP | `集团及中心BP/院外业务中心_1781261992818.md` |
| 深西康 BP | `集团及中心BP/深西康_1781261964954.md` |
| 德镁医药 BP | `集团及中心BP/德镁医药_1781262042283.md` |
| 康哲维盛 BP | `集团及中心BP/康哲维盛_1781261975969.md` |
| 林刚 personal BP | `集团及中心BP/林刚_1781261814218.md` |
| 陈燕玲 personal BP | `集团及中心BP/陈燕玲_1781261831103.md` |

## 4. Reading Policy

1. Prefer existing Markdown files when available.
2. For DOCX sources, use this降级 priority:
   - First: use the corresponding `.md` file in the same directory if it exists.
   - Second: if the platform has a conversion tool (e.g. pandoc), run `pandoc --to markdown <file.docx>` to extract text.
   - Third: if no conversion tool is available, ask the user to paste the relevant sections as text into the chat.
3. Do not upload BP, financial, personal, or strategy files to external services.
4. If a source is outside the writable workspace, read only unless the user explicitly authorizes writing or conversion output.
5. Use source priority:
   - current user-confirmed rule;
   - official current BP/SP source;
   - center or lower-level BP source;
   - prior discussion memory;
   - AI inference marked待确认.

## 4. High-Risk Metric Pairs

Define before using:

| Pair | Control |
|---|---|
| 收入 / GMV / 终端销售额 / 报表收入 | State口径, unit, tax basis, report vs management |
| 含税 / 不含税 | State which one is used and whether both need columns |
| 目标 / 保底 / 基线 / 挑战 | State target tier |
| 集团直传 / 中心放大 | State upstream minimum and downstream amplification |
| 成果验收物 / 过程证据 | Keep final acceptance separate from monthly evidence |

## 5. Evan 本地可用源（额外补充）

`PROJECT_ROOT = /Users/evan/Documents/BP/` 下当前实际存在的文件：

| 用途 | 实际路径 | 当前状态 |
|---|---|---|
| BP 体系完整说明稿（初版） | `/Users/evan/Documents/BP/BP体系完整说明稿（初版）.md` | 已完整读取（smoke test 验证） |
| BP 体系完整说明视频版 | `/Users/evan/Documents/BP/BP体系完整说明视频版.md` | 已定位但未打开 |
| BP 体系说明稿——前言 | `/Users/evan/Documents/BP/BP体系说明稿——前言.md` | 已定位但未打开 |
| BP 体系说明稿（简洁版） | `/Users/evan/Documents/BP/BP体系说明稿（简洁版）.md` | 已定位但未打开 |
| BP 创建助手要求 | `/Users/evan/Documents/BP/BP创建助手要求.md` | 已定位但未打开 |
| BP 目标成果举措角色定义与使用说明 | `/Users/evan/Documents/BP/BP目标成果举措角色定义与使用说明.md` | 已定位但未打开 |
| BP 系统 API 说明 | `/Users/evan/Documents/BP/BP系统API说明.md` | 已定位但未打开；本 skill 当前不涉及系统对接 |

报告母版位于 `/Users/evan/Documents/BP报告母版/`，含半年报/季报/月报/年报/BP 预埋底图 5 份模板，按需引入。

> **判定规则**：本 skill 的语义层、流程层、模板层**不依赖**康哲集团具体业务材料，仅在用户明确要求审计/生成/审阅康哲集团某一具体 BP 对象时才询问是否补 `集团及中心BP/` 下文件。

