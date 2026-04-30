---
name: vault-writer
version: "1.0.1"
skillcode: vault-writer
github: https://github.com/evan-zhang/agent-factory
description: 当 Agent 需要将内容（报告、笔记、摘要等）写入 Obsidian vault 时触发。负责路径计算、文件写入、frontmatter 生成和 vault 内组织。
---

# Vault Writer

## 触发判断

```
收到写入请求
 ├─ 有 vault 配置    → 注入 frontmatter → 计算路径 → 写入
 ├─ 无 vault 配置    → 提示运行 --init 初始化
 └─ 路径不存在       → 报错终止（不自动创建 vault）
```

## 初始化配置

运行 `scripts/init_config.py --init` 进行配置。

**发现已有 Vault**：脚本读取 `~/Library/Application Support/obsidian/obsidian.json`，列出当前注册的所有 vault 供用户选择。

用户也可以手动输入一个已有目录的绝对路径作为目标。

⚠️ **不创建新 vault**：如需新建 vault，请先在 Obsidian app 中创建。

**配置文件**（按环境自动选择路径）：
- OpenClaw：`~/.openclaw/vault-writer-config.json`
- 其他：`~/.config/vault-writer-config.json`

**配置文件示例**：
```json
{
  "vault_path": "/Users/evan/Library/Mobile Documents/iCloud~md~obsidian/Documents/github分享",
  "default_folder": "AI调研",
  "default_tags": ["agent-output"]
}
```

- `vault_path`（必填）：目标 Obsidian vault 根目录
- `default_folder`（可选）：vault 内默认写入子目录，留空则写 vault 根目录
- `default_tags`（可选）：默认注入的 tags，默认 `["agent-output"]`

## 工作流（两步，极简）

### Step 1：配置检测 [MUST]

运行 `scripts/init_config.py` 检查配置状态。

门控：`vault_path` 已配置且目录可写 → 进入 Step 2。
未通过：提示运行 `--init`。

### Step 2：写入 [MUST]

运行 `scripts/write_note.py --file <md文件路径>` 完成同步。

脚本行为：
1. 读取源文件内容
2. 注入 YAML frontmatter（没有则添加，已有则只补充缺失字段）
3. 计算目标路径：`{vault_path}/{default_folder}/YYYY-MM-DD/{源文件名}`
4. 冲突时加序号，不覆盖
5. 写入文件

**路径规则**：
- 未指定 folder + 配置了 default_folder → `{vault_path}/{default_folder}/YYYY-MM-DD/`
- 指定了 folder → `{vault_path}/{folder}/YYYY-MM-DD/`
- 均未指定 → `{vault_path}/YYYY-MM-DD/`

**frontmatter 注入规则**：
- 源文件无 frontmatter → 添加 `created_at` + `tags`
- 源文件已有 frontmatter → 只补充缺失字段，不覆盖已有内容
- 时间来源：`datetime.now()`，禁止 LLM 推断

**完成提示**：`✅ 已写入 vault：<vault_relative_path>`

## 降级策略

- vault 目录不可写 → 报错，提示检查权限
- obsidian.json 不存在（非 macOS）→ 跳过自动发现，要求手动输入路径
- 源文件不存在 → 报错终止
- 文件名冲突且序号达到上限（100）→ 报错，建议手动处理

## 脚本

`scripts/init_config.py`：配置初始化、检测、路径验证
`scripts/write_note.py`：同步 md 文件到 vault

**关键用法**：

```bash
# 初始化配置（列出已有 vault 供选择）
python3 scripts/init_config.py --init

# 检查当前配置状态
python3 scripts/init_config.py
# {"ok": true, "vault_path": "/path/to/vault", "writable": true}

# 同步 md 文件到 vault
python3 scripts/write_note.py --file /path/to/report.md
# {"ok": true, "path": "/vault/AI调研/2026-04-30/report.md", ...}

# 指定子目录和标签
python3 scripts/write_note.py --file /path/to/report.md --folder "会议纪要" --tags "会议,决策"

# 不创建日期子目录
python3 scripts/write_note.py --file /path/to/report.md --no-date-subfolder
```

## 参考

`examples/`：使用示例（待补充）

## 工具映射（非 OpenClaw 环境）

| SKILL 工具 | 其他环境对应 | 说明 |
|------------|-------------|------|
| `exec(command)` | 终端执行 | 执行脚本 |
| `write(file, content)` | 脚本内文件写入 | 本 skill 通过脚本写入，Agent 不直接 write |

## 边界

**本 Skill 负责**：配置初始化（发现已有 vault）→ 注入 frontmatter → 写入文件到 Obsidian vault

**不负责**：
- 创建新 Obsidian vault
- 搜索/读取 vault 内已有笔记
- Obsidian 同步管理（由 Obsidian app 负责）
- 渠道发送（Agent 自行决定）
- 文件内容生成（Agent 负责生成，本 Skill 只管写入）

## 配置与授权

安装后运行 `scripts/init_config.py --init` 初始化。

**初始化流程**：
1. 脚本自动发现 macOS 上已注册的 Obsidian vault
2. 列出所有已有 vault 的名称和路径，供用户选择
3. 用户也可手动输入已有目录的绝对路径
4. 脚本验证所选目录存在且可写，写入配置文件

配置文件：`~/.openclaw/vault-writer-config.json`

- `vault_path`（必填）：目标 vault 根目录，从已有 vault 列表选择或手动输入
- `default_folder`（可选）：vault 内默认写入子目录
- `default_tags`（可选）：默认注入的 tags，默认 `["agent-output"]`

无需配置即可用：无（必须先初始化 vault_path）。

**限制**：只能写入已有的 Obsidian vault，不支持创建新 vault。

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new

**标题格式**：`[BUG] vault-writer: 简短描述` 或 `[FEATURE] vault-writer: 简短描述`

**建议包含**：
1. 重现步骤
2. 预期行为 vs 实际行为
3. 环境信息（OpenClaw 版本、操作系统、Obsidian 版本）
4. 相关日志或错误信息
