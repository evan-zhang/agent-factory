# Google Cloud / IDC《Data and AI Trends Report》视觉风格拆解与 AI 生成规范

> 用途：把这些风格说明直接交给 AI Agent，用于生成 HTML 页面、Web 汇报页、PPT 风格网页、企业白皮书页面。

---

## 总体判断

这些图片不是一种风格，而是同一套企业报告视觉系统下的 **6 套页面风格变体**。

它们共享统一底层规范：

- Google Cloud / IDC 风格
- 企业级数据与 AI 白皮书
- 大面积留白
- 大标题
- 高纯度 Google 四色
- 真实商业摄影
- 页脚色带
- 杂志化排版
- 内容少、观点强、视觉冲击大

---

# 风格一：Google 四色拼贴封面风

## 风格名称

**Color Block Editorial Cover**

## 适合页面

- 报告首页
- 专题入口页
- 年度趋势报告封面
- 企业 AI 战略入口页

## 视觉特征

- 白色背景
- 超大黑色标题
- 蓝 / 绿 / 黄 / 红色横向色块
- 图片被裁切成长条或小矩形
- 类似杂志封面与品牌海报
- 视觉重心强烈，适合第一屏

## 配色

```css
--blue: #1A73E8;
--green: #34A853;
--yellow: #FBBC05;
--red: #EA4335;
--black: #202124;
--white: #FFFFFF;
```

## 字体

```css
font-family: "Google Sans", "Inter", "Helvetica Neue", sans-serif;
font-weight: 600-700;
letter-spacing: -2px;
```

## 布局关键词

- 横向色块
- 大标题穿插
- 图片条带
- 非对称构图
- 视觉拼贴

## AI 生成 Prompt

```text
请生成一个 Google Cloud 企业报告封面风格的 HTML 页面。
风格为白底、超大黑色标题、Google 四色横向色块、真实商业摄影切片拼贴。
页面要像 Data and AI Trends Report 的封面，使用杂志化布局。
标题巨大，图片和色块穿插在标题之间。
避免 SaaS 后台风、避免深色科技风、避免复杂装饰。
```

---

# 风格二：大图 Hero 章节封面风

## 风格名称

**Full-bleed Chapter Hero**

## 适合页面

- 章节首页
- 趋势介绍页
- 核心观点展示页
- 高管汇报开场页

## 视觉特征

- 整页大图作为背景
- 图片有灰色或暗色遮罩
- 左下角超大白色标题
- 右上角有大章节编号
- 顶部有一条细白线
- 底部有主题色横条

## 配色

根据章节变化：

```css
--theme-green: #34A853;
--theme-blue: #1A73E8;
--theme-red: #EA4335;
--theme-yellow: #FBBC05;
--white: #FFFFFF;
--overlay: rgba(0,0,0,0.25);
```

## 字体

```css
.hero-title {
  font-size: 72px;
  font-weight: 700;
  line-height: 1.05;
  color: white;
  letter-spacing: -2px;
}
```

## 布局关键词

- 大图铺满
- 左下大标题
- 右上章节号
- 底部色带
- 图片暗化
- 电影海报感

## AI 生成 Prompt

```text
请生成一个企业白皮书章节封面 HTML 页面。
使用全屏真实商业摄影背景，叠加轻微暗色遮罩。
左下角放置超大白色标题，右上角放置章节编号。
顶部加一条细白线，底部加一条主题色横条。
整体参考 Google Cloud / IDC 数据与 AI 报告风格。
页面要简洁、高级、企业级。
```

---

# 风格三：白底咨询报告内容页

## 风格名称

**Consulting Report Content Page**

## 适合页面

- 正文分析页
- 趋势解释页
- 方案说明页
- 咨询报告页面

## 视觉特征

- 大面积白底
- 左侧标题 + 正文
- 右侧图片 / 图表 / 数据
- 内容分栏明显
- 页面干净、克制
- 重点文字使用主题色

## 配色

```css
--text: #202124;
--muted: #5F6368;
--green: #34A853;
--blue: #1A73E8;
--red: #EA4335;
--yellow: #FBBC05;
--light-bg: #F8F9FA;
```

## 字体

```css
h1 {
  font-size: 44px;
  font-weight: 600;
  line-height: 1.1;
}

p {
  font-size: 15px;
  line-height: 1.6;
  color: #5F6368;
}
```

## 布局关键词

- 左文右图
- 双栏布局
- 强留白
- 少量正文
- 页脚色带
- 小标签

## AI 生成 Prompt

```text
请生成一个 Google Cloud 白皮书正文页风格的 HTML 页面。
页面采用白底双栏布局，左侧是大标题和短正文，右侧是真实商业图片或数据图表。
标题使用主题色，正文为深灰色。
底部保留一条主题色页脚横条。
整体像咨询公司报告页面，不要像普通网页后台。
```

---

# 风格四：彩色模块矩阵风

## 风格名称

**Color Tile Matrix**

## 适合页面

- 方法论总览
- 模块清单
- 趋势列表
- 产品矩阵
- 能力地图

## 视觉特征

- 白底
- 左侧说明文字
- 右侧 2×3 或 1×5 彩色模块
- 每个模块是纯色大卡片
- 卡片内使用白色大字
- 编号非常小
- 无圆角或极小圆角
- 无阴影

## 配色

```css
--tile-green: #34A853;
--tile-blue: #1A73E8;
--tile-red: #EA4335;
--tile-yellow: #FBBC05;
--white: #FFFFFF;
```

## 字体

```css
.tile-title {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.15;
  color: white;
}
```

## 布局关键词

- 2×3 网格
- 彩色方块
- 方法论地图
- 模块编号
- 左说明右矩阵

## AI 生成 Prompt

```text
请生成一个企业方法论总览 HTML 页面。
左侧放置标题和简短说明，右侧使用 2×3 彩色模块矩阵。
模块颜色使用 Google 四色：蓝、绿、黄、红。
每个模块中有小编号和白色大标题。
整体参考 IDC methodology 页面，白底、大留白、无阴影、无复杂装饰。
```

---

# 风格五：数据洞察大数字风

## 风格名称

**Insight Metrics Bubble**

## 适合页面

- 数据洞察页
- 关键指标页
- 统计结论页
- 经营分析页面
- AI 结果展示页

## 视觉特征

- 白底
- 右侧或中间放大数字
- 数字放在半透明圆形气泡中
- 圆形浅色背景
- 页面文字很少
- 数字极大，成为视觉中心
- 可搭配人物头像、引用、短说明

## 配色

```css
--green: #34A853;
--yellow: #FBBC05;
--red: #EA4335;
--bubble-green: rgba(52,168,83,0.10);
--bubble-yellow: rgba(251,188,5,0.12);
--bubble-red: rgba(234,67,53,0.10);
```

## 字体

```css
.metric {
  font-size: 72px;
  font-weight: 700;
  color: var(--green);
}
```

## 布局关键词

- 大数字
- 半透明圆形
- 气泡分布
- 极简统计页
- 数据即主角

## AI 生成 Prompt

```text
请生成一个企业数据洞察 HTML 页面。
页面以白底为主，使用几个半透明浅色圆形气泡承载大数字指标。
数字要非常大，使用绿色或黄色作为强调色。
左侧放置短标题和简短说明，右侧展示 2-3 个关键数据。
整体参考 Google Cloud 数据报告中的指标页，保持极简和高级。
```

---

# 风格六：案例 / 行业卡片风

## 风格名称

**Industry Case Cards**

## 适合页面

- 行业案例页
- 解决方案场景页
- 客户应用页
- 三类客户 / 三类业务展示
- 风险管理案例页

## 视觉特征

- 白底
- 顶部标题
- 下方 3 列案例卡片
- 每张卡片包含图片 + 小标题 + 简短说明
- 图片比例统一
- 内容密度适中
- 强调行业应用场景

## 配色

```css
--text: #202124;
--muted: #5F6368;
--green: #34A853;
--border: #E5E7EB;
--white: #FFFFFF;
```

## 字体

```css
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.card-text {
  font-size: 13px;
  line-height: 1.5;
  color: #5F6368;
}
```

## 布局关键词

- 三列卡片
- 图片在上
- 标题 + 简短正文
- 行业场景
- 企业案例

## AI 生成 Prompt

```text
请生成一个企业行业案例 HTML 页面。
页面白底，顶部为主题标题，下方使用三列案例卡片。
每张卡片包含真实商业摄影图片、行业名称、简短说明。
整体参考 Google Cloud / IDC 报告中的行业场景页。
保持留白、简洁、咨询报告风，不要使用复杂阴影和圆角。
```

---

# 六套风格对照表

| 编号 | 风格名称 | 主要用途 | 视觉关键词 |
|---|---|---|---|
| 1 | Google 四色拼贴封面风 | 报告首页 / 入口页 | 大标题、色块、图片拼贴 |
| 2 | 大图 Hero 章节封面风 | 章节页 / 观点页 | 全屏大图、白色大字、底部色带 |
| 3 | 白底咨询报告内容页 | 正文页 / 分析页 | 双栏、留白、文字克制 |
| 4 | 彩色模块矩阵风 | 方法论 / 模块清单 | 2×3 色块、白字、编号 |
| 5 | 数据洞察大数字风 | 指标页 / 数据页 | 大数字、圆形气泡、极简 |
| 6 | 案例 / 行业卡片风 | 场景页 / 案例页 | 三列卡片、图片、短说明 |

---

# 统一页面规范

## 页面尺寸建议

```css
max-width: 1440px;
min-height: 900px;
padding: 72px 96px;
```

## 字体建议

```css
font-family: "Google Sans", "Inter", "Helvetica Neue", Arial, sans-serif;
```

## 统一页脚

```css
.footer-bar {
  height: 36px;
  background: var(--theme-color);
  color: white;
  font-size: 12px;
}
```

## 推荐图片类型

- 企业办公
- 数据中心
- 机器人
- 工厂自动化
- 城市与道路
- 会议协作
- 抽象建筑
- 楼梯 / 通道 / 门 / 机场 / 飞机

## 避免图片类型

- 卡通插画
- 赛博朋克
- 霓虹科技线
- 低质量素材图
- 过度 AI 感图片
- 复杂 UI 截图

---

# 总 Prompt：一次生成多套页面

```text
请基于 Google Cloud / IDC《Data and AI Trends Report》的视觉体系，生成 6 套不同风格的 HTML 页面模板。

统一要求：
- 企业级数据与 AI 白皮书风格
- 使用 Google 四色：蓝 #1A73E8、绿 #34A853、黄 #FBBC05、红 #EA4335
- 字体使用 Google Sans / Inter / Helvetica Neue
- 大面积留白
- 杂志化排版
- 真实商业摄影
- 少量文字
- 强视觉中心
- 避免 SaaS 后台风、深色科技风、炫酷粒子风

需要生成的 6 套风格：
1. Google 四色拼贴封面风
2. 大图 Hero 章节封面风
3. 白底咨询报告内容页
4. 彩色模块矩阵风
5. 数据洞察大数字风
6. 行业案例卡片风

每套页面都请生成完整 HTML + CSS，可以直接运行。
```
