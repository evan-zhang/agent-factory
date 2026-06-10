1. 每个模块必须有 README

新模板文件：
.aodw-next/templates/module-readme-template.md

内容包括：
# <模块名称>

## 1. 职责（Responsibilities）
- 说明此模块的职责范围
- 它解决什么问题

## 2. 目录结构（Files）
- 列出关键文件
- 用 frontmatter mapping 连接文档与文件
---
module: orders
files:
  - apps/api/src/orders/**
  - apps/web/src/pages/orders/**
---

## 3. 不可破坏原则（Invariants）
- 必须遵守哪些行为
- 不能改变的数据结构
- API 契约

## 4. 依赖关系（Dependencies）
### 上游：
- users
- auth

### 下游：
- reporting

## 5. 常见流程说明（Workflows）
- 一个典型流程如何运作

## 6. 历史行为（History）
- 本模块的重大演化记录（RT 关联）


⸻

2. AI 必须维护模块的 mapping

每次修改以下内容时必须更新 module README 的 frontmatter：
	•	新增模块目录
	•	修改模块包路径
	•	新增关键文件
	•	移除关键文件
	•	API 行为修改
	•	数据结构修改

mapping 规范（写入 ai-knowledge-rules）：
related_files:
  - apps/api/src/orders/order_service.ts
  - apps/api/src/orders/order_model.ts

AI 必须同时在 RT 的 invariants.md 和 module README 里更新对应说明。

⸻

3. 模块总索引

新增文件：
.aodw-next/06-project/modules-index.yaml

格式：
version: 1

modules:
  - name: orders
    path: docs/modules/orders.md
    root: apps/api/src/orders
  - name: payments
    path: docs/modules/payments.md
    root: apps/api/src/payments


⸻

4. 模块知识的优先级

AI 必须：
	•	修改代码前先查模块 README
	•	决策 Spec-Full / Lite 时必须引用模块 invariants
	•	改动完成后必须更新模块 README 和 modules-index.yaml

⸻
