---
name: style-06-design
version: "1.0.0"
layout: 产品介绍页
---

# Style 06 — 产品介绍页 Design Token

## 视觉理念

多 section + hero，适合产品/服务介绍页。强调品牌感、清晰结构、视觉层次丰富。适合药企产品页、公司介绍页。

## 色彩系统

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg` | `#FFFFFF` | 页面背景 |
| `--hero-bg` | `#5C3D0A` | Hero 区背景（深暖橙） |
| `--section-alt` | `#F8FAFC` | 交替 section 背景 |
| `--primary` | `#5C3D0A` | 主色（深暖橙） |
| `--accent` | `#D98B52` | 强调色（蓝） |
| `--gold` | `#D97706` | 金色点缀 |
| `--text` | `#111827` | 主要文字 |
| `--subtext` | `#4B5563` | 辅助文字 |
| `--light-text` | `#9CA3AF` | 浅色文字（Hero区） |
| `--border` | `#E5E7EB` | 分割线 |

## 字体系统

- 主字体：`"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`
- Hero 标题：`800`，`36pt`（桌面）
- Section 标题：`700`，`22pt`
- 卡片标题：`600`，`16pt`
- 正文：`400`，`14pt`

## 间距系统

- 页面边距：`0`（全宽 Hero），内容区 `48px`（桌面）/ `16px`（移动）
- Section 间距：`64px`（垂直）
- 卡片间距：`20px`

## 组件规范

### Hero Section
- 全宽背景（深暖橙渐变或图片）
- 白色大标题居中或居左
- 副标题：浅色
- CTA 按钮：金色背景 + 深色文字

### Feature Card
- 图标 + 标题 + 描述
- 图标：48px × 48px，圆形背景（accent 色 10% 透明度）
- 悬停：阴影加深，卡片上移

### Specs Table
- 两列布局：标签 + 内容
- 交替行背景
- 左列加粗

### CTA Block
- 全宽背景条（accent 色）
- 居中文字 + 按钮

## 布局结构

```
[Hero: 产品名 + 标语 + CTA按钮]
[Overview: 一段话产品定位]
[Features: 图标功能区（3列卡片）]
[Specs: 规格参数表]
[Indications/Use Cases: 适应症/应用场景]
[CTA: 行动召唤栏]
[Footer: 免责声明]
```

## Do's

- Hero 视觉冲击力要强
- Features 区用图标让信息快速扫描
- Specs 表要整齐，数据导向
- 移动端 Hero 缩小但保持结构完整

## Don'ts

- 不要在一个页面上堆太多文字
- 不要让 CTA 按钮太小或太多
- 不要混用太多颜色，保持主次分明
