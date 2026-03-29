# DESIGN-02 — CAS 零感知初始化方案

**项目编号**：AF-20260329-002
**设计版本**：v1.0
**设计日期**：2026-03-29
**设计者**：factory-orchestrator（与张成鹏确认）

---

## 一、问题

用户安装 cas-chat-archive 后，三个复盘 cron 不会自动创建，导致"日日有汇报/周周有总结/月月有复盘"形同虚设。

---

## 二、三层递进方案

### 第一层：SKILL.md 快速开始置顶（兜底）

在 SKILL.md 最顶部（frontmatter 之后、正文之前）加：

```markdown
## ⚡ 快速开始（安装后必做）

安装完成后，发送以下指令完成初始化：

> 帮我初始化 CAS 成长体系

AI 将自动创建三个复盘 cron（日报/周复盘/月复盘），无需手工配置。
```

### 第二层：`cas_setup.py` 一键初始化脚本

新建 `scripts/cas_setup.py`，功能：
1. 检查 `.cas_initialized` 标志文件是否存在
2. 检查三个 cron 是否已存在（通过 `openclaw cron list` 输出判断）
3. 不存在则通过 `subprocess` 调 `openclaw cron add` 创建三个 cron：
   - 日报：`0 19 * * *` Asia/Shanghai
   - 周复盘：`0 10 * * 6` Asia/Shanghai
   - 月复盘：`0 18 * * 5` Asia/Shanghai
4. 写入 `.cas_initialized` 标志文件
5. 输出初始化结果供 AI 汇报给用户

AI 收到"帮我初始化 CAS"后调用此脚本，幂等安全（重复运行不会重复创建）。

### 第三层：handler.ts 首次运行自动检测（真正无感）

在 `handler.ts` 的 `runCasRecordBundle` 返回后，增加初始化检测逻辑：

1. 检查 `{archiveRoot}/.cas_initialized` 是否存在
2. 不存在 → 调用 `cas_setup.py --auto`（静默模式，不需要用户确认）
3. `cas_setup.py --auto` 自动创建 cron + 写标志文件
4. handler.ts 在 console 输出 `[cas-chat-archive] 首次运行，已自动初始化复盘体系`

**效果**：用户发第一条消息触发 hook，后台静默完成所有初始化，用户完全无感。

---

## 三、幂等保障

- 标志文件：`{archiveRoot}/.cas_initialized`（存在即跳过）
- cron 名称去重：创建前先 `openclaw cron list`，按名称匹配，已存在则跳过
- 重复安装/重复触发均安全

---

## 四、文件变更清单

| 文件 | 操作 |
|------|------|
| `SKILL.md` | 顶部加"快速开始"章节 |
| `scripts/cas_setup.py` | 新建，一键初始化脚本 |
| `hooks/cas-chat-archive-auto/handler.ts` | 加首次运行检测逻辑 |

---

*设计确认：张成鹏 @ 2026-03-29*
