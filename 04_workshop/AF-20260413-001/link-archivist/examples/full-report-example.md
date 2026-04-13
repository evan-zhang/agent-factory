# Example 1: Full Report — 今日头条 + GitHub 项目

## 输入
用户发送：`https://m.toutiao.com/is/example123/`

## 决策过程
1. 来源判断：今日头条 → 非强制 full/short
2. 抓取内容（r.jina.ai）→ 发现文章介绍了一个 GitHub 开源项目 "MiroFish"
3. 关键词命中："github"、"star"、"开源"
4. decide_mode.py → **full**

## 执行过程
1. r.jina.ai 抓取头条文章 → 提取项目名 MiroFish
2. web_search 补充："MiroFish GitHub 2026"
3. 验证 Star 数（45.9K）、技术栈、团队背景
4. 搜索本地索引 → 发现与 K-260410-002（MCP 协议调研）相关
5. 生成完整报告（含对比分析）
6. 归档到 `{archive_dir}/2026-04-13/K-260413-001-MiroFish群体智能.md`

## 输出（报告节选）

```
# MiroFish：群体智能预测引擎

> 来源：今日头条
> 链接：https://m.toutiao.com/is/example123/
> 调研日期：2026-04-13

## 概述
MiroFish 是一个基于群体智能的开源预测框架...

## 核心功能
### 分布式决策
...

## 关键数据
- Star：45,900+
- 语言：Python + Rust
- ...

## 对比分析
与 K-260410-002（MCP 协议）的差异：MCP 关注通信协议，MiroFish 关注决策算法...
```
