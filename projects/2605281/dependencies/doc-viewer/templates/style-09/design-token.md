# Style 09 — Notion（文档编辑器风）

## 风格定位
Notion 风格，以文档阅读为中心、Markdown 优先、极简边框、编辑部风格。

## 核心气质
- Documentation, readability, calm editorial
- 内容为王，极简干扰
- 清晰的信息层级
- 舒适的阅读体验
- 专业的文档呈现

## 颜色体系

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#FFFFFF` | 主背景（纯白） |
| `--bg-alt` | `#F7F6F3` | 次背景（Notion 浅灰） |
| `--bg-card` | `#FFFFFF` | 卡片背景 |
| `--accent` | `#C97842` | 强调色（暖橙替代 Notion 蓝） |
| `--text` | `#37352F` | 主文字（深灰黑） |
| `--text-secondary` | `#9B9A97` | 次文字（辅助灰） |
| `--border` | `#E9E9E7` | 边框色（Notion 灰边框） |
| `--code-bg` | `#F7F6F3` | 代码块背景 |

## 字体

中文："PingFang SC", -apple-system, "MiSans", sans-serif
英文：-apple-system, "Inter", "SF Pro Text", sans-serif

正文：font-size 15pt, line-height 1.7
标题：font-weight 600/700
代码：monospace, "Menlo", "Consolas", monospace

## 布局特征
- 内容区 max-width: 720px（阅读最佳宽度）
- 左侧可选侧边导航
- 居中主内容区
- 极简边框（border: 1px solid #E9E9E7）
- 大量留白（padding: 80px 40px）
- 边框圆角 8-12px

## 元素样式
- 代码块：浅灰背景、等宽字体、小圆角
- 表格：极简、无边框、浅灰底色交替
- 引用：左边线 + 灰色背景
- 列表：极简符号、充足间距
- 分隔线：细线、浅灰色

## 适用场景
- 技术文档
- API 文档
- 用户手册
- 知识库
- 研究报告