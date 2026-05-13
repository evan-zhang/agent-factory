# doc-viewer Skill 功能扩展需求文档

> **文档版本**：v1.0  
> **日期**：2026-05-13  
> **编写**：Agent Factory  
> **目标读者**：doc-viewer Skill 当前开发者  
> **目标**：将 html-page Skill 的「HTML 页面生成」能力合并进 doc-viewer，实现一个 Skill 同时覆盖「快速上传」和「内容创作」两条路径

---

## 一、背景

当前存在两个独立 Skill：

| Skill | 项目编号 | 功能 |
|-------|---------|------|
| doc-viewer | 2605101 | 上传 .md/.html 文件 → 返回预览链接 |
| html-page | 2605121 | 收集素材 → 选风格模板 → 生成 HTML 页面 → 上传 → 返回链接 |

两者共用同一个 Doc Viewer API（`http://doc.20100706.xyz`）。html-page 在最后一步实际上就是调用了 doc-viewer 的上传能力。

**合并理由**：
- 用户不需要判断「该调哪个 Skill」
- 一套 API 配置只维护一处
- 合并后 doc-viewer 变成一个「文件上传 + 内容创作」的统一入口

**合并策略**：保留 doc-viewer 的名字和项目编号（2605101），将 html-page 的生成能力作为新路径加入。

---

## 二、合并后的整体架构

合并后 doc-viewer 有两条执行路径，通过用户的输入自动分流：

```
用户发消息
 │
 ├─ 路径 A（快速路径）：用户提供了现成文件
 │   ├─ 收到 .md / .html / .htm 文件（附件或本地路径）
 │   ├─ 直接调用 Doc Viewer API 上传
 │   └─ 返回预览链接
 │
 ├─ 路径 B（创作路径）：用户描述了内容需求
 │   ├─ 收集素材（标题、内容、数据、图片）
 │   ├─ 选择风格模板
 │   ├─ 生成 HTML 文件
 │   ├─ 调用 Doc Viewer API 上传
 │   └─ 返回预览链接
 │
 └─ 非触发：以上都不匹配 → 不触发本 Skill
```

---

## 三、触发判断规则（需修改 SKILL.md）

合并后的触发判断：

```
收到消息
 ├─ 用户发送了 .md / .html / .htm 文件
 │   → 走路径 A（快速上传）
 │
 ├─ 用户意图包含：生成页面 / 做一个页面 / HTML页面 / 宣传页 / 展示页 / 报告页面
 │   → 走路径 B（内容创作）
 │
 ├─ 用户说：上传文件 / 预览文件 / 生成链接 / 上传到网站
 │   → 检查是否附带文件
 │     ├─ 有文件 → 走路径 A
 │     └─ 无文件 → 走路径 B（将用户内容生成为页面）
 │
 └─ 其他 → 不触发
```

---

## 四、路径 A：快速上传（现有功能，不变）

这部分是 doc-viewer 已有能力，保持原样：

1. 接收文件（附件 / 本地路径 / 用户粘贴文本）
2. 验证文件类型（.md / .html / .htm）
3. 调用 `POST http://doc.20100706.xyz/upload` 上传
4. 返回预览链接

API 调用方式不变：
```bash
# 上传文件
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@<文件路径>;filename=<原始文件名>"

# 上传文本内容
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "content=<文本内容>" -F "format=markdown"
```

---

## 五、路径 B：内容创作（新增功能）

这是从 html-page Skill 合并过来的核心能力。分 5 个步骤：

### Step 1：风格选择

向用户展示可用风格模板，用户选择一个。当前有以下模板：

**风格 01 — Data & AI Report（企业数据智能白皮书）**
- 综合风格，适合完整报告页面
- 模板定义：`templates/style-01-data-ai-report.md`
- HTML 基础骨架：`templates/style-01-base.html`

**风格 02 — Google Cloud / IDC 企业报告视觉系统（6 套变体）**
- 同一视觉体系下的 6 种页面变体
- 模板定义：`templates/style-02-google-cloud-idc.md`
- 变体列表：

| 编号 | 变体名称 | 适用场景 |
|------|----------|----------|
| 02-A | 四色拼贴封面风 | 报告首页/入口页 |
| 02-B | 大图 Hero 章节封面风 | 章节页/观点页 |
| 02-C | 白底咨询报告内容页 | 正文页/分析页 |
| 02-D | 彩色模块矩阵风 | 方法论/模块清单 |
| 02-E | 数据洞察大数字风 | 指标页/数据页 |
| 02-F | 案例/行业卡片风 | 场景页/案例页 |

**风格选择建议规则**（用于 Agent 自动向用户推荐，而非罗列所有选项）：
- 用户说「封面」「首页」→ 推荐 02-A 或 02-B
- 用户说「报告正文」「分析」→ 推荐 02-C
- 用户说「数据」「指标」→ 推荐 02-E
- 用户说「案例」「行业」→ 推荐 02-F
- 用户说「模块」「方法论」→ 推荐 02-D
- 用户没明确偏好 → 推荐 01（综合风格）

### Step 2：素材收集

通过对话逐项收集，用户可能一次给齐，也可能分多次：

**必填项**：
- 页面标题（主标题）
- 页面内容（正文/观点/数据，用户口述即可，Agent 负责结构化）

**可选项**（用户不提供则用模板默认值）：
- 副标题
- 数据点（如 "73% 的企业已采用 AI"）
- 图片（用户发送附件，或使用占位图）
- 作者/来源信息
- 页脚信息

### Step 3：HTML 页面生成

1. 读取所选风格模板的规范文件（`templates/style-XX.md`）
2. 参考 HTML 基础骨架（`templates/style-01-base.html`）
3. 根据内容结构和模板规范，生成完整 HTML 文件

**HTML 规范**：
- 单文件，内联 CSS
- 使用 TailwindCSS CDN（`<script src="https://cdn.tailwindcss.com">`）
- 轻量动效：fade-in、slide-up、counter（数字跳动）
- 响应式设计（移动端适配）
- 图片使用用户提供的 URL 或占位图
- 不使用 JavaScript 框架，纯 HTML + CSS + 原生 JS
- 文件大小 < 1MB（不含图片，图片使用外链）

### Step 4：上传与交付

调用路径 A 同一套 API：

```bash
curl -s -X POST http://doc.20100706.xyz/upload \
  -F "file=@output.html;filename=<标题>.html"
```

返回预览链接：`http://doc.20100706.xyz/view/<doc_id>`

### Step 5：迭代修改（可选）

用户查看后可要求修改。使用 Doc Viewer 更新接口（链接不变）：

```bash
curl -X PUT http://doc.20100706.xyz/api/{doc_id} \
  -F "file=@updated.html;filename=<标题>.html"
```

---

## 六、需要迁移的文件

从 html-page（项目 2605121）迁移到 doc-viewer（项目 2605101）的文件：

| 源文件 | 目标位置 | 说明 |
|--------|---------|------|
| `2605121/html-page/templates/style-01-data-ai-report.md` | `2605101/doc-viewer/templates/style-01-data-ai-report.md` | 风格 01 定义 |
| `2605121/html-page/templates/style-01-base.html` | `2605101/doc-viewer/templates/style-01-base.html` | HTML 基础骨架 |
| `2605121/html-page/templates/style-02-google-cloud-idc.md` | `2605101/doc-viewer/templates/style-02-google-cloud-idc.md` | 风格 02 定义（含 6 变体） |

迁移完成后 `2605121/html-page/` 目录可以废弃标记。

---

## 七、合并后的 SKILL.md frontmatter

```yaml
---
name: doc-viewer
description: "文件上传预览 + HTML 内容页面生成器。提供现成文件可直接上传预览；描述内容需求可自动生成风格化 HTML 页面并上传。触发词：上传文件、预览文件、生成链接、生成页面、HTML页面、宣传页、报告页面"
version: "2.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/2605101/doc-viewer/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels=doc-viewer
---
```

**版本号跳到 2.0.0**：因为这是一个重大功能合并，不是小版本迭代。

---

## 八、合并后的目录结构

```
projects/2605101/doc-viewer/
 ├─ SKILL.md                          # 合并后的 Skill 定义
 ├─ version.json                      # {"skillcode":"doc-viewer","version":"2.0.0"}
 ├─ .gitignore
 └─ templates/                        # 新增目录（从 html-page 迁移）
     ├─ style-01-data-ai-report.md    # 风格 01 定义
     ├─ style-01-base.html            # HTML 基础骨架
     └─ style-02-google-cloud-idc.md  # 风格 02 定义（含 6 变体）
```

---

## 九、失败处理（合并后）

| 场景 | 处理 |
|------|------|
| 路径 A：文件 > 10MB | 告知用户文件大小限制 |
| 路径 A：非 md/html 文件 | 告知仅支持 Markdown 和 HTML |
| 路径 B：用户素材不足 | 提示缺少哪些必填项，不强行生成 |
| 路径 B：生成失败 | 重试一次，仍失败则报告错误 |
| 上传失败（两条路径共用） | 重试一次，仍失败则报告错误 |
| Doc Viewer 服务不可用 | 告知用户服务暂时不可用 |
| 路径 B 生成文件超过 10MB | 将 HTML 文件直接发送给用户作为附件 |

---

## 十、验收标准

合并完成的标志：

1. ✅ SKILL.md 包含路径 A 和路径 B 的完整描述
2. ✅ `templates/` 目录包含所有 3 个模板文件
3. ✅ version.json 版本号为 2.0.0
4. ✅ 路径 A（上传现成文件）功能不受影响
5. ✅ 路径 B（内容创作 → HTML 生成 → 上传）完整可用
6. ✅ 两条路径共用同一套 Doc Viewer API，无重复配置
7. ✅ 原有 API 接口（/upload、/view、/raw、/api、/api/list）描述完整保留
8. ✅ 「配置与授权」和「问题反馈」节符合工厂规范
