# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## Skill 发布流程

每次 Skill 发布必须按顺序执行：

1. **GitHub**：变更 commit 并 push
2. **ClawHub**：执行 `clawhub publish` 发布新版本
3. **发布说明**：写清楚更新内容、安装命令、反馈渠道，发给 Evan 以便通知其他 Agent

**注意**：三个步骤缺一不可。发布后必须立即写发布说明，不能遗漏。

---

### 外部平台文档（API 唯一来源）

提到"玄关"/"开放平台"/"CWork API"/"工作协同接口"/"AI慧记接口"时，从这里获取最新接口文档：

| 平台 | GitHub 地址 | 覆盖业务模块 |
|------|-------------|-------------|
| 玄关开放平台 | https://github.com/xgjk/dev-guide/ | CWork(工作协同) / AI慧记 / BP / 所有 CMS 业务模块 |

使用方式：`web_fetch` 抓取对应目录下的 API 文档，与本地 `references/api-endpoints.md` 对比差异。
