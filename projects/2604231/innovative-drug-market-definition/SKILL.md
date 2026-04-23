---
name: innovative-drug-market-definition
version: "1.0.0"
skillcode: innovative-drug-market-definition
description: 创新药市场定义模块。用于界定市场边界（TAM/SAM/SOM），分析当前市场规模和未来增长潜力，支持市场机会量化评估。
tags:
  - pharmaceutical
  - market-analysis
  - tam-sam-som
  - innovative-drug
  - strategic-planning
category: professional-skill
author: Agent Factory
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604231/innovative-drug-market-definition
date: "2026-04-23"
changelog: |
  - v1.0.0 (2026-04-23): 初始版本
---

# 市场定义

## 角色定位

市场定义是 SP/BP 规划的起点，负责量化市场机会的边界和规模。核心任务是回答"这个产品能服务多大的市场"。

## 核心任务

- 界定 TAM（Total Addressable Market）：理论最大市场规模
- 界定 SAM（Serviceable Addressable Market）：可服务目标市场
- 界定 SOM（Serviceable Obtainable Market）：可获得市场份额
- 分析当前市场规模 vs 未来潜力
- 识别市场增长驱动因素和约束条件

## 工具与方法

### 2.1 市场规模测算

**用途**：量化市场边界  
**方法论**：自上而下（Top-down）与自下而上（Bottom-up）交叉验证  
**应用**：通过公开数据（IQVIA、NMPA、CDE、药企年报）测算TAM，再按适应症覆盖率、渠道可及性逐步收窄至SAM和SOM

### 2.2 疾病负担分析

**用途**：论证市场刚需性  
**方法论**：流行病学数据（患病率、发病率、诊断率、治疗率）  
**应用**：从疾病负担（DALY/QALY）推导治疗需求未满足程度

### 2.3 竞争态势扫描

**用途**：识别直接竞品和替代疗法  
**方法论**：药品注册数据库 + 招投标数据 + 处方数据  
**应用**：通过靶点、给药途径、疗效安全性对比，定位市场机会窗口

## 推导过程

### 3.1 数据收集
1. 收集目标适应症的流行病学数据（患病率、发病率）
2. 调研现有治疗方案及市场份额
3. 汇总在研竞品管线及预期上市时间

### 3.2 市场规模测算
1. 以流行病学数据为基准，计算理论市场空间（TAM）
2. 按患者流（诊断→治疗→用药）筛选可触及人群（SAM）
3. 结合竞争格局和准入能力，估算可获得市场（SOM）

### 3.3 趋势分析
1. 识别市场增长驱动因素（老龄化、政策松绑、新适应症）
2. 评估市场约束（集采压力、同靶点竞争、技术迭代）
3. 给出5年市场规模的基准/乐观/悲观预测

## 关键发现

- **F1**：TAM规模及测算依据
- **F2**：SAM收窄逻辑及关键假设
- **F3**：SOM估算及竞争位势
- **F4**：市场增长/约束因素

## 结论

| 维度 | 结论 | 置信度 |
|------|------|--------|
| TAM | 当前市场规模 XX 亿元，5年CAGR约XX% | 高/中/低 |
| SAM | 可服务市场约 XX 亿元（适应症+渠道筛选后） | 高/中/低 |
| SOM | 3年内可获得市场约 XX 亿元 | 高/中/低 |

## 待讨论点

1. 市场规模测算的数据来源是否权威？
2. SAM收窄的关键假设是否成立？
3. 集采对价格和市场份额的冲击是否充分考虑？
4. 在研竞品的时间线是否准确？

## 参考文档

详细行业数据和资料来源见 `references/china-market-data-2024-2026.md`

## 数据来源

| 数据 | 来源 | 可靠性 | 时间 |
|------|------|--------|------|
| 流行病学数据 | NMPA/CDE/文献 | 高/中/低 | YYYY-MM |
| 市场规模参考 | IQVIA/米内/药企年报 | 高/中/低 | YYYY-MM |
| 在研管线 | CDE临床试验登记 | 高 | YYYY-MM |
| 集采/医保数据 | 医保局/招标平台 | 高 | YYYY-MM |

## 版本

- SKILL.md: v1.0.0 (2026-04-23)
- 规则依据: SPBP主控编排器规则总结2026-04-01更新版
