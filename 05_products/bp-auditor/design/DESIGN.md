# bp-auditor 设计档案

## 核心定位

基于两级联动审计框架的 BP 审计 Skill。对 BP 进行递归审计，输出诊断报告。

## 功能范围

- BP 数据获取（通过 fetch.py 调用 BP API）
- 两级联动审计（Goal/KR/举措 + 下级 BP 承接）
- 生成审计报告

## BP 类型

API 集成类 — 依赖 BP 系统 API 获取数据

## 审计框架

### 第一级
根 BP 自身 Goal + KR + 举措是否拆解清晰、充分

### 第二级
根 BP 的每个 KR/举措，承接方（下级 BP）是否精准承接、有效落地

### 递归深度
只到直接下级 BP，不继续往下追

## 核心原则

- Orchestrator 只调度，不执行
- Brain Only, No Hands
- spawn sub-agent 执行数据获取和分析

---

*创建时间：2026-04-05*
