# 产出交付协议

> 本文档回答一个问题：**TPR 产出文件写到哪里，命名规范是什么。**
>
> 同步由 `openclaw-xgkb-sync` 服务自动处理，详见 SKILL.md。

---

## 目录结构

每个 TPR 项目对应本地一个目录，结构如下：

```
{RT根目录}/
└── {项目编号}/
    ├── DISCOVERY.md
    ├── DISCOVERY.html          ← 关键报告才生成 HTML
    ├── GRV.md
    ├── GRV.html
    ├── BATTLE-R{n}-{角色}.md  ← 过程记录，只写 MD
    ├── BATTLE-R{n}-{角色}.html
    ├── output/                 ← 执行阶段交付物
    │   └── A{nnn}-OUT-{nn}.md
    └── P-ACPT-{nn}.md         ← 验收文档
```

**RT 根目录**由 AGENTS.md 的 `rt_root_dir` 配置决定。

---

## 命名规范

| 阶段 | 文件名 | 说明 |
|------|---------|------|
| DISCOVERY | `DISCOVERY.md` / `.html` | 洞察报告 |
| GRV | `GRV.md` / `.html` | 项目契约 |
| Battle R1 | `BATTLE-R1-AUDITOR.md` / `BATTLE-R1-EXECUTOR.md` | 审查侧 / 执行侧 |
| Battle R2 | `BATTLE-R2-AUDITOR.md` / `BATTLE-R2-EXECUTOR.md` | 同上 |
| Implementation | `A{nnn}-OUT-{nn}.md` | 交付物，nnn=阶段序号，nn=交付物序号 |
| Closure | `P-ACPT-{nn}.md` | 验收文档 |

---

## 哪些文件生成 HTML

| 文件 | 生成 HTML | 理由 |
|------|----------|------|
| DISCOVERY.md | ✅ | 用户需要审阅洞察报告 |
| GRV.md | ✅ | 用户需要审阅契约 |
| Battle 记录 | ❌ | 过程记录，只有 AI 需要看 |
| 执行日志 | ❌ | 过程记录 |
| 最终交付物 (A-OUT) | ✅ | 用户需要审阅成果 |
| 验收文档 (P-ACPT) | ✅ | 用户需要确认验收 |

---

## HTML 生成规范

### 风格选择

| 文件类型 | 推荐风格 | 理由 |
|----------|---------|------|
| DISCOVERY（洞察报告） | 02-C（白底咨询报告） | 分析型内容，适合阅读 |
| GRV（项目契约） | 02-D（彩色模块矩阵） | 结构化内容，模块清晰 |
| 最终交付物 | 02-C 或按内容类型选择 | 视交付物性质而定 |
| 验收文档 | 01（综合风格） | 简洁确认型内容 |

### HTML 技术规范

- 单文件，内联 CSS
- 使用 TailwindCSS CDN
- 响应式设计
- 文件大小 < 1MB

---

## 阶段完成检查清单

### DISCOVERY 完成后
- [ ] `DISCOVERY.md` 已写入本地目录
- [ ] 如需 HTML，`DISCOVERY.html` 已生成

### GRV 完成后
- [ ] `GRV.md` 已写入本地目录
- [ ] 如需 HTML，`GRV.html` 已生成

### Battle 每轮完成后
- [ ] `BATTLE-R{n}-AUDITOR.md` 已写入
- [ ] `BATTLE-R{n}-EXECUTOR.md` 已写入
- [ ] 如 GRV 有修订，同步更新

### Implementation 完成后
- [ ] 交付物.md 已写入 `output/` 目录
- [ ] 如需 HTML，交付物.html 已生成

### Closure 完成后
- [ ] `P-ACPT-{nn}.md` 已写入
- [ ] 通知用户：项目完成，文件路径

---

## 同步说明

**编排者只管写本地文件，同步由 `openclaw-xgkb-sync` 服务自动处理。**

- 服务每 120s 自动扫描本地目录，双向同步（bidirectional）
- TPR 编排者无需参与任何同步操作

---

*版本：3.1.0*
*更新：2026-05-14 — 按 issue #5：删除动态注册/注销 mapping 逻辑，改为纯全局 mapping 方案*
