# UI Workflow Rules

**适用场景**：UI/界面相关工作

---

## 0. 概述

> **关键规则**：所有 UI 相关任务**必须**在 RT 目录中创建 HTML 版本的界面原型，并**必须**获得用户确认后才能进入实现阶段。

---

## 1. 强制要求

⚠️ **绝对禁止**：
- ❌ 在 HTML 原型未获用户确认前生成实现代码
- ❌ 跳过 UI 原型或界面设计阶段
- ❌ 未经过用户确认直接进入实现阶段

---

## 2. 流程步骤

### Step 0: 任务类型判断

**触发条件**（任一满足即视为 UI 任务）：
- 涉及页面、界面、布局、组件、表单、Dashboard
- 涉及前端 UI、样式、视觉呈现
- 涉及用户操作流程、交互体验、可视化
- 用户明确提到"界面"、"UI"、"设计"、"原型"

---

### Step 1: HTML 原型（强制）

**AI 必须**：
1. 生成静态 HTML 原型
2. 保存位置：`RT/RT-XXX/docs/ui-prototype.html`
3. 使用 Tailwind CSS 实现统一审美（如项目使用）

**原型内容**：
- 页面结构
- 核心组件
- 关键交互流程
- 表单布局
- **无真实逻辑代码**

**用户确认**：
- 原型必须通过用户审查（A/B/C）
- 确认后才能进入实现阶段

---

### Step 2: 实现阶段（可选）

**仅在以下情况进入**：
- HTML 原型已获用户确认
- 明确告知"现在开始实现"

---

## 3. 配置模板位置

**HTML 原型模板**：
- 位置：`.aodw-next/templates/ui-prototype.template.html`

**前端工具配置**：
- ESLint 配置模板：`.aodw-next/templates/tools-config/frontend/eslint.config.template.json`
- TypeScript 配置模板：`.aodw-next/templates/tools-config/frontend/tsconfig.paths.template.json`

---

## 4. 检查清单

| 项目 | 检查项 | 状态 |
|-------|---------|------|
| HTML 原型 | `docs/ui-prototype.html` 已创建并确认 | |
| 技术栈 | React/TypeScript / Vue 已配置 | |
| 工具链 | ESLint / Prettier 已安装 | |

---

## 5. 审计选项

**AI 识别到 UI 任务时，必须提供以下审计选项**：

1. **UI 设计流程**（推荐）：按 AODW UI 规范设计原型，等待确认
2. **UI 审计流程**：按 AODW UI 规范审计现有界面，提供改进建议
3. **UI 找问题流程**：按 AODW UI 规范找出界面问题，提供修复建议

---

## 6. 禁止行为

⚠️ **严禁以下行为**：
- ❌ 生成实现代码（HTML 原型仅包含结构和布局）
- ❌ 跳过 HTML 原型阶段
- ❌ 未经确认进入实现阶段
- ❌ 不遵循项目 UI 设计系统（如有）
