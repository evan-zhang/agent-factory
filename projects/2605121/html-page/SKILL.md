---
name: html-page
description: "通用型内容展示页生成器。根据用户提供的内容和素材，生成风格化的 HTML 单页面，自动上传并返回预览链接。触发词：生成页面、HTML页面、内容展示、宣传页、报告页面"
version: "1.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605121/html-page/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=html-page
---

# html-page — 通用型内容展示页生成器

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`2605121`
> 工厂主页：https://github.com/evan-zhang/agent-factory

## 概述

根据用户提供的内容（文字、数据、观点）和素材（图片），生成风格化的 HTML 单页面。页面用于文章、报告、观点、内容的展示和宣传。

## 触发判断

```
收到消息
 ├─ "生成页面" / "做一个页面" / "HTML页面" / "宣传页" / "展示页" / "报告页面"
 │   └─ 进入素材收集流程
 └─ 非页面生成意图 → 不触发
```

## 执行流程

### Step 1：风格选择

向用户展示可用风格模板列表，用户选择一个。

当前可用模板：

**风格 01 — Data & AI Report（企业数据智能白皮书）**
综合风格，适合完整报告页面。定义文件：`templates/style-01-data-ai-report.md`

**风格 02 — Google Cloud / IDC 企业报告视觉系统（6 套变体）**
同一视觉体系下的 6 种页面变体，适合按需选择：

| 编号 | 变体名称 | 适用场景 |
|------|----------|----------|
| 02-A | 四色拼贴封面风 | 报告首页/入口页 |
| 02-B | 大图 Hero 章节封面风 | 章节页/观点页 |
| 02-C | 白底咨询报告内容页 | 正文页/分析页 |
| 02-D | 彩色模块矩阵风 | 方法论/模块清单 |
| 02-E | 数据洞察大数字风 | 指标页/数据页 |
| 02-F | 案例/行业卡片风 | 场景页/案例页 |

定义文件：`templates/style-02-google-cloud-idc.md`

### Step 2：素材收集

通过对话逐项收集以下信息（用户可能一次给齐，也可能分多次）：

**必填项：**
- 页面标题（主标题）
- 页面内容（正文/观点/数据，用户口述即可，Agent 负责结构化）

**可选项（用户不提供则用模板默认值）：**
- 副标题
- 数据点（如 "73% 的企业已采用 AI"）
- 图片（用户发送附件，或 Agent 从素材库选择占位图）
- 作者/来源信息
- 页脚信息

### Step 3：页面生成

1. 读取所选风格模板的规范文件（`templates/style-XX.md`）
2. 根据内容结构和模板规范，生成完整 HTML 文件
3. HTML 规范：
   - 单文件，内联 CSS
   - 使用 TailwindCSS CDN（`<script src="https://cdn.tailwindcss.com">`）
   - 轻量动效：fade-in、slide-up、counter（数字跳动）
   - 响应式设计（移动端适配）
   - 图片使用用户提供的 URL 或占位图

### Step 4：上传与交付

1. 将 HTML 文件上传到 Doc Viewer 服务：
```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@output.html;filename=<标题>.html"
```

2. 返回预览链接给用户：`http://doc.20100706.xyz/view/<doc_id>`

### Step 5：迭代（可选）

用户查看后可要求修改：
- 调整内容/文案
- 更换图片
- 微调配色
- 调整布局

使用 Doc Viewer 更新接口（链接不变）：
```bash
curl -X PUT http://doc.20100706.xyz/api/{doc_id} \
  -F "file=@updated.html;filename=<标题>.html"
```

## 风格模板规范

每个模板是一个 Markdown 文件（`templates/style-XX.md`），包含：
- 配色体系（主色、辅色、中性色的具体色值）
- 字体规范（字族、大小、粗细）
- 布局结构（Hero、内容区、数据区、结尾区的排列方式）
- 卡片/组件风格
- 动效规范
- AI 生成 Prompt 模板

模板只管风格层（配色、字体、质感），布局根据内容动态生成。

## 技术约束

- 输出：单个 HTML 文件，无外部依赖（除 TailwindCSS CDN）
- 文件大小：< 1MB（不含图片，图片使用外链）
- 浏览器兼容：现代浏览器（Chrome/Safari/Firefox 最新版）
- 不使用 JavaScript 框架，纯 HTML + CSS + 原生 JS（动效）
- 移动端响应式：使用 TailwindCSS 的响应式断点

## 失败处理

| 场景 | 处理 |
|------|------|
| 用户素材不足 | 提示缺少哪些必填项，不强行生成 |
| 生成失败 | 重试一次，仍失败则报告错误 |
| Doc Viewer 上传失败 | 将 HTML 文件直接发送给用户作为附件 |
| 文件超过 10MB | 提示用户减少图片数量或使用压缩图片 |

## 安装方法

**方式一（推荐）：git sparse-checkout**
```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605121/html-page
```

**方式二（备选）：svn export**
```bash
svn checkout https://github.com/evan-zhang/agent-factory/trunk/projects/2605121/html-page
```

Skill 目录：`projects/2605121/html-page/`

## 配置与授权

无需额外配置即可使用。

依赖服务：
- **Doc Viewer**（`http://doc.20100706.xyz`）：用于页面托管和预览，无需认证
- **TailwindCSS CDN**：用于样式渲染，公开服务

## 问题反馈

使用中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new?labels=html-page

**标题格式**：`[BUG] html-page: 简短描述` 或 `[FEATURE] html-page: 简短描述`

**建议包含**：
1. 重现步骤
2. 预期行为 vs 实际行为
3. 环境信息（OpenClaw 版本、浏览器）
4. 相关日志或错误信息
