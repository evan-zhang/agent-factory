---
name: metaphor-builder
version: "0.1.0"
skillcode: metaphor-builder
github: https://github.com/evan-zhang/agent-factory
description: 将抽象概念转化为隐喻故事的 Skill。用户指定概念时直接生成；未指定时基于 Obsessions 笔记或 Agent 对用户的理解给出 3 个推荐选项，再生成故事与 HTML 页面。
---

# Metaphor Builder — 隐喻构建器

## 核心定位
将任意抽象概念通过隐喻故事呈现，让概念"自己浮现"而非直接解释。生成完整 HTML 页面，可直接分享。
目标：5 分钟让读者理解一个概念。

## 触发条件
用户说：给我讲讲 XXX / 用隐喻解释一下 / 这个概念什么意思 / 能帮我把 XXX 变得好理解吗 / 给我生成一个隐喻 / 什么道理 / 帮我理解一下

两种模式：
- 直接模式：用户指定了具体概念 → 立即生成隐喻故事 + HTML 页面
- 推荐模式：用户未指定具体概念 → 基于 Obsessions 或 Agent 上下文推荐 3 个选项 → 用户选 → 生成

## 直接模式
1. 读取 references/concept-template.md，结构化概念
2. 调用 references/story-template.md，生成约 1500-2500 字故事
3. 读取 templates/metaphor-page/ 设计规范，生成 HTML，上传至 doc.20100706.xyz，返回链接

## 推荐模式
1. 读取 config.json 的 vault_path（方式 A：Obsessions 笔记），或用 Agent 上下文（方式 B）
2. 选出 3 个最有隐喻潜力的概念呈现给用户
3. 用户选择后进入直接模式

## 核心提示词（注入生成过程）
请选择一个【研究生以上难度】的概念。不要直接解释它。先构造一个完整世界观，再通过角色冲突、规则限制、资源交换或系统演化，把这个概念隐藏在故事结构里。要求：1. 不要提前暴露概念名 2. 读者应能逐渐感受到某种规律存在 3. 在结尾处才揭晓真正概念 4. 最后详细解释：概念本身/隐喻映射/哪些机制对应现实理论 5. 不要写成童话，要像高质量科幻/黑镜/哲学寓言 6. 故事本身必须成立，即使不知道概念也能读

## 配置与授权
- 必填：vault_path（Obsessions 笔记路径），用户运行 python3 scripts/init_config.py --init 初始化，未配置则降级为方式 B
- 可选：html_style（默认 style-11）
- 无需配置：直接模式、推荐模式（Agent 上下文）

## 依赖关系
- doc-viewer：HTML 生成与上传

## 问题反馈
Issue：https://github.com/evan-zhang/agent-factory/issues/new?labels=metaphor-builder
