# AODW — AI 编排开发工作流

## 规则文件索引

详细索引见 `manifest.yaml`。分层概览：

### 01-core（核心规范）
- `aodw-constitution.md` — 最高行为准则
- `git-discipline.md` — Git + Worktree + 确认门控
- `ai-interaction-rules.md` — AI 提问与交互协议
- `ai-knowledge-rules.md` — 文档系统与知识同步
- `csf-thinking-framework.md` — CSF 决策思考框架
- `module-doc-rules.md` — 模块文档编写规范

### 02-workflow（工作流）
- `rt-manager.md` — RT 完整生命周期管理
- `spec-full-profile.md` — Spec-Full 执行规范（复杂变更）
- `spec-lite-profile.md` — Spec-Lite 执行规范（简单变更）
- `ui-workflow-rules.md` — UI 专项开发流程
- `rt-id-generation-rules.md` — RT ID 本地生成规则

### 03-standards（编码规范）
- `ai-coding-rules.md` — 通用编码规范
- `ai-coding-rules-common.md` — 通用规范补充
- `stacks/` — 技术栈专项规范（按需加载）

### 04-auditors（审计器）
- `aodw-requirement-auditor-rules.md` — 需求审计
- `aodw-development-auditor-rules.md` — 开发审计
- `aodw-full-auditor-rules.md` — 完整审计规则集

### 05-tooling（工具配置）
- `ai-tools-init-rules.md` — 开发工具初始化

### 06-project（项目特化层 — 每个项目单独配置）
- `ai-overview.md` — 项目技术栈与架构概览 ⚠️
- `modules-index.yaml` — 项目模块索引 ⚠️

### templates（文档模板）
RT 生命周期各阶段文档的标准模板。

---

## 新项目安装

1. 将 `.aodw-next/` 目录复制到新项目根目录
2. 重写项目特化文件：
   - `06-project/ai-overview.md` — 填写技术栈、架构、模块结构
   - `06-project/modules-index.yaml` — 填写模块列表
3. 在项目的 AI 配置文件中添加引用（如 CLAUDE.md）

---

## 版本信息

- AODW 版本：0.5.1
- Spec-Full Profile：v2.0（Skill 化）
- Spec-Lite Profile：v2.0（Skill 化）
- git-discipline：v2.0（Worktree + 确认门控）
