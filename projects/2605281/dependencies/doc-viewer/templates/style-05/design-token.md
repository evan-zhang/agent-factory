---
name: style-05-design
version: "1.0.0"
layout: 数据看板/指标卡
---

# Style 05 — 数据看板/指标卡 Design Token

## 视觉理念

大数字 + 图表，适合 KPI 展示、数据概览。数字要醒目，色彩对比要强，一眼能抓住关键指标。

## 色彩系统

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg` | `#F5F7FA` | 页面背景 |
| `--card-bg` | `#FFFFFF` | 指标卡背景 |
| `--primary` | `#9A6736` | 主数字（深暖橙） |
| `--accent-green` | `#059669` | 正向指标 |
| `--accent-red` | `#DC2626` | 负向指标 |
| `--accent-yellow` | `#D97706` | 中性/关注指标 |
| `--text` | `#111827` | 主要文字 |
| `--subtext` | `#6B7280` | 辅助文字 |
| `--border` | `#E5E7EB` | 卡片边框 |
| `--shadow` | `0 1px 4px rgba(0,0,0,0.06)` | 卡片阴影 |

## 字体系统

- 主字体：`"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`
- 大数字：`800`，`36pt~48pt`（桌面）
- 指标标签：`500`，`13pt`
- 变化率：`700`，`14pt`
- 描述文字：`400`，`12pt`

## 间距系统

- 页面边距：`40px 48px`（桌面）/ `16px`（移动）
- 卡片间距：`20px`
- 卡片内边距：`24px`
- 数字与标签间距：`4px`

## 组件规范

### 指标卡（MetricCard）
- 背景：`--card-bg`，圆角 `12px`，阴影 `--shadow`
- 大数字：居中或居左，颜色 `--primary`（可改）
- 变化率：带箭头，绿色表示上升，红色表示下降
- 标签：指标名称，`--subtext`
- 可选：迷你图表（柱状/折线）

### 趋势指示（TrendBadge）
- 上升：`--accent-green`，↑ 图标
- 下降：`--accent-red`，↓ 图标
- 持平：`--accent-yellow`，→ 图标

### 图表区（ChartArea）
- 高度：`200px~300px`
- 支持嵌入 Chart.js 或纯 CSS 图表

## 布局结构

```
[Header: 看板标题 + 时间范围选择]
[Metric Cards Row: 4个指标卡]
[Chart Area: 趋势图表]
[Secondary Metrics: 次级指标网格]
[Footer: 数据来源]
```

## Do's

- 大数字要足够大，一眼可读
- 正负变化用颜色直观区分
- 卡片布局要整齐，间距一致
- 移动端指标卡堆叠为单列

## Don'ts

- 不要让数字和标签字号一样大
- 不要在同一个卡片里用太多颜色
- 不要放太多数字卡片，建议一屏不超过 8 个
