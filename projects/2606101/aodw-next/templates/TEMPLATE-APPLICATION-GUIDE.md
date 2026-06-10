# 模板应用指南 (Template Application Guide)

## 1. 模板机制概述

AODW Next 使用**统一模板机制**来生成各个平台的适配器文件，确保所有平台的内容保持一致。

### 1.1 模板位置

**源模板**：`.aodw-next/templates/aodw-kernel-loader-template.md`

这个模板包含所有平台的通用内容，使用占位符标记平台差异：
- `{{REF_PREFIX}}` - 引用前缀（Cursor: `@`，其他: 空）

### 1.2 适配器文件位置

**生成的适配器文件**（在源仓库中）：
- `templates/AODW_Adapters/antigravity/.agent/rules/aodw-next.md`
- `templates/AODW_Adapters/cursor/.cursor/rules/aodw-next.mdc`
- `templates/AODW_Adapters/claude/CLAUDE.md`
- `templates/AODW_Adapters/gemini/.agent/rules/aodw-next.md`
- `templates/AODW_Adapters/general/AGENTS.md`

**注意**：适配器文件在用户项目中安装到对应位置。

---

## 2. 模板处理流程

### 2.1 安装阶段（用户项目）

1. **CLI 检测模板**：检查 `.aodw-next/templates/aodw-kernel-loader-template.md` 是否存在
2. **使用 Processor**：根据平台选择对应的 Processor
3. **生成适配器文件**：在用户项目中生成适配器文件

**Processor 处理**：
- **AntigravityProcessor**：替换 `{{REF_PREFIX}}` 为空，注入 `trigger: always_on`
- **CursorProcessor**：替换 `{{REF_PREFIX}}` 为 `@`，注入 frontmatter（globs, alwaysApply 等）
- **ClaudeProcessor**：替换 `{{REF_PREFIX}}` 为空
- **GeminiProcessor**：替换 `{{REF_PREFIX}}` 为空
- **GeneralProcessor**：替换 `{{REF_PREFIX}}` 为空

---

## 3. Processor 说明

### 3.1 AntigravityProcessor

**处理**：
- 替换 `{{REF_PREFIX}}` 为空字符串
- 注入 `trigger: always_on` frontmatter（仅对 kernel loader）

**输出**：
- 文件：`templates/AODW_Adapters/antigravity/.agent/rules/aodw-next.md`
- 格式：Markdown with frontmatter

### 3.2 CursorProcessor

**处理**：
- 替换 `{{REF_PREFIX}}` 为 `@`
- 注入 frontmatter：`globs: *`, `alwaysApply: true`, `description`, `tags`
- 文件扩展名改为 `.mdc`

**输出**：
- 文件：`templates/AODW_Adapters/cursor/.cursor/rules/aodw-next.mdc`
- 格式：Markdown with Cursor-specific frontmatter

### 3.3 ClaudeProcessor

**处理**：
- 替换 `{{REF_PREFIX}}` 为空字符串
- 不注入 frontmatter

**输出**：
- 文件：`templates/AODW_Adapters/claude/CLAUDE.md`
- 格式：标准 Markdown

### 3.4 GeminiProcessor

**处理**：
- 替换 `{{REF_PREFIX}}` 为空字符串
- 不注入 frontmatter

**输出**：
- 文件：`templates/AODW_Adapters/gemini/.agent/rules/aodw-next.md`
- 格式：标准 Markdown

### 3.5 GeneralProcessor

**处理**：
- 替换 `{{REF_PREFIX}}` 为空字符串
- 不注入 frontmatter

**输出**：
- 文件：`templates/AODW_Adapters/general/AGENTS.md`
- 格式：标准 Markdown

---

## 4. 相关文件

- **模板文件**：`.aodw-next/templates/aodw-kernel-loader-template.md`
- **Processor 实现**：`cli/bin/processors/index.js`
- **CLI 安装脚本**：`cli/bin/aodw.js`
- **适配器文件**：`templates/AODW_Adapters/`

---

## 5. 版本历史

- **v4.0.0**：AODW Next，统一使用 `.aodw-next` 目录
