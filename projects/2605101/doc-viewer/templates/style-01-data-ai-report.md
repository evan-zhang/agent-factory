# 风格模板 01：Data & AI Report（企业数据智能白皮书）

> 来源：Evan 基于 Google Cloud 2023 Data and AI Trends Report 参考图提炼

---

## 1. 整体视觉定位

**风格关键词：**
- 企业级、国际咨询公司风格
- Google / IDC / Gartner 风格
- Data + AI + Enterprise
- 极简信息化、高级白底设计
- 大面积留白、强秩序感
- 杂志化排版、PPT 转网页风格

**整体感觉：** "企业战略报告 + 数据智能 + 高端咨询公司视觉体系"
- 不是互联网产品 UI，不是 SaaS 后台
- 更像：年度战略报告、AI 趋势白皮书、企业数据治理方案、高管汇报材料

---

## 2. 色彩体系

### 主蓝色（核心科技色）
- `#4285F4` / `#2F6FE4` / `#5B8DEF`
- 用途：主标题区、Hero Banner、科技感背景、核心数据区
- 视觉感受：Google Enterprise, Cloud / AI / Data

### 主绿色（数据治理色）
- `#34A853` / `#2FA24A` / `#43B866`
- 用途：数据治理、风险管理、AI 数据分类、信息架构
- 视觉感受：安全、数据可信、Enterprise AI

### 黄色（辅助分析色）
- `#FBBC05` / `#F4B400`
- 用途：Analytics、BI、强调模块

### 红色（风险/警告）
- `#EA4335` / `#E8453C`
- 用途：风险、DataSphere、Warning、安全议题

### 中性色
- 背景白：`#FFFFFF`
- 浅灰背景：`#F5F6F7` / `#EFEFEF` / `#E5E7EB`
- 文字灰：`#5F6368` / `#6B7280` / `#4B5563`

---

## 3. 字体风格

### 推荐字体
```css
font-family: "Google Sans", "Inter", "Helvetica Neue", "Segoe UI", sans-serif;
```

### 标题风格
- Hero 大标题：`font-size: 64px; font-weight: 700; line-height: 1.05; letter-spacing: -2px;`
- 特点：极大字号、超低行距、强压迫感、左对齐

### 正文风格
- `font-size: 16px; font-weight: 400; line-height: 1.7; color: #5F6368;`

### 数据数字
- `font-size: 72px; font-weight: 700; color: #34A853;`

---

## 4. 布局风格

### 核心原则
1. 大量留白：`padding: 80px 120px;`
2. 强网格系统：12 列 Grid，`gap: 32px;`
3. 内容极少：每页一个核心观点、一个视觉焦点、少量文字

### 页面结构
- **Hero 区**：大图背景 → 超大标题 → 一句副标题
- **内容区**：左标题+说明 / 右图片/数据/卡片
- **数据区**：大数字 + 一句解释
- **结尾区**：极简总结、Logo、页码

---

## 5. 卡片风格

### IDC 彩色方块风格
- 纯色背景、白色文字、无阴影、无描边、大面积块状
- `border-radius: 0; box-shadow: none; padding: 32px; color: white;`

### 图片卡片风格
- 图片占大面积、文字很少、底部细色条
- `border-bottom: 8px solid #34A853;`

---

## 6. 图片风格

- 偏好：建筑、飞机、楼梯、城市、企业办公、抽象空间
- 避免：二次元、插画、复杂 UI、花哨渐变
- 统一处理：`filter: brightness(0.95) contrast(1.02) saturate(0.9);`

---

## 7. 数据可视化风格

- 极简、大数字、少坐标轴、少边框
- 类似 Google Data Studio 风格
- 圆形数据块：`width: 240px; height: 240px; border-radius: 999px; background: rgba(52,168,83,0.08);`

---

## 8. 动效风格

- 仅 fade、slight move up、opacity
- `transition: all 0.25s ease;`
- 不要：炫酷粒子、3D翻转、科技线条乱飞

---

## 9. AI 生成 Prompt 模板

```
请参考 Google / IDC 企业数据智能白皮书风格设计页面。

整体视觉风格：
- 国际咨询公司风格
- 极简企业级
- Data + AI + Enterprise
- 大面积留白、强网格系统
- Google 风格配色
- 白底 + 高纯度色块
- 大标题、少量文字、杂志化排版

颜色体系：
- 蓝色 #4285F4
- 绿色 #34A853
- 黄色 #FBBC05
- 红色 #EA4335
- 大量白色和浅灰背景

字体：Google Sans / Inter，超大粗体标题，极简正文
布局：左文右图、12列 Grid、卡片式区块、超强留白
图片：建筑、飞机、楼梯、企业办公、抽象空间感

避免：SaaS后台风、深色赛博朋克、花哨渐变、复杂边框、过度动画
输出：现代化 HTML + TailwindCSS
```
