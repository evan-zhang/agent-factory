# TOOLS.md - Local Notes

## 发布 = push 到 GitHub master

版本号三处同步：`projects/{id}/VERSION` / SKILL.md frontmatter `version` / `version.json`。SemVer 格式。

## 安装方式

```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory && git sparse-checkout set projects/{id}/{skill-name}
```

ClawHub 发布：`clawhub publish ./projects/{id}/{skill} --slug ... --version ...`

## 推送后交付模板

push 后立即发到当前对话：

```
🔬 {Skill} v{x.y.z}

📦 安装：git sparse-checkout set projects/{id}/{skill-name}

本次更新：
1. ...

重点测试：
- ...
```

## Skill 规范

SKILL.md 必含「配置与授权」节（必填/可选配置项 + 获取方式）和「问题反馈」节（Issue 地址 + 格式要求）。

## 外部 API 文档

玄关开放平台：`https://github.com/xgjk/dev-guide/`，curl 直接获取。
