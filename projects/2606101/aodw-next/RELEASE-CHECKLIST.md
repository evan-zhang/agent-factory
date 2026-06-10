# 编码规范融入 AODW - 发布前检查清单

## ✅ 最终检查结果

### 1. 核心流程文档修改 ✅

- [x] **spec-full-profile.md**
  - [x] Plan 模板添加"代码结构与分层设计"章节（第 4 节）
  - [x] 添加"开发阶段要求"章节（第 6 节）
  - [x] checklists 部分添加编码规范验收项
  - [x] 已同步到 `templates/.aodw-next/02-workflow/spec-full-profile.md`

- [x] **spec-lite-profile.md**
  - [x] Plan-Lite 模板添加"代码结构与分层设计"章节（第 3 节）
  - [x] 流程中添加开发准备、开发过程中、开发结束前自检要求
  - [x] 已同步到 `templates/.aodw-next/02-workflow/spec-lite-profile.md`

- [x] **git-discipline.md**
  - [x] 添加"合并前检查清单"章节（第 5 节）
  - [x] 编码规范检查作为合并的硬性要求
  - [x] 自动化检查中添加编码规范检查（Step 2）
  - [x] 已同步到 `templates/.aodw-next/01-core/git-discipline.md`

- [x] **rt-manager.md**
  - [x] Intake 流程中添加技术约束要求（第 180 行）
  - [x] 已同步到 `templates/.aodw-next/02-workflow/rt-manager.md`

### 2. 模板文件修改 ✅

- [x] **rt-intake-template.md**
  - [x] 添加"相关技术约束/规范"字段（第 6 节，可选）
  - [x] 已同步到 `templates/.aodw-next/templates/rt-intake-template.md`

- [x] **coding-standards-template.md**（新建）
  - [x] 创建编码规范验收清单模板（103 行）
  - [x] 包含前端、后端、通用编码规范验收项
  - [x] 已同步到 `templates/.aodw-next/templates/checklists/coding-standards-template.md`

### 3. 文件同步验证 ✅

- [x] 所有核心流程文档已同步到模板目录
- [x] 所有模板文件已同步到模板目录
- [x] 新建的 checklists 目录已创建并同步

### 4. 内容完整性验证 ✅

- [x] Plan 模板包含完整的代码结构与分层设计内容
- [x] 开发阶段要求包含完整的检查清单
- [x] 合并前检查清单包含完整的编码规范检查项
- [x] Intake 模板包含技术约束字段

### 5. 引用路径验证 ✅

- [x] 所有编码规范文件引用路径正确（`.aodw-next/ai-coding-rules-*.md`）
- [x] 模板文件引用路径正确（`.aodw-next/templates/checklists/coding-standards-template.md`）

### 6. 格式和语法验证 ✅

- [x] Markdown 格式正确
- [x] 标题层级正确
- [x] 列表格式正确
- [x] 代码块格式正确
- [x] 无 Linter 错误

---

## 📋 修改文件清单

### 核心流程文档（4 个文件）
1. ✅ `.aodw-next/02-workflow/spec-full-profile.md` → `templates/.aodw-next/02-workflow/spec-full-profile.md`
2. ✅ `.aodw-next/02-workflow/spec-lite-profile.md` → `templates/.aodw-next/02-workflow/spec-lite-profile.md`
3. ✅ `.aodw-next/01-core/git-discipline.md` → `templates/.aodw-next/01-core/git-discipline.md`
4. ✅ `.aodw-next/02-workflow/rt-manager.md` → `templates/.aodw-next/02-workflow/rt-manager.md`

### 模板文件（2 个文件）
5. ✅ `.aodw-next/templates/rt-intake-template.md` → `templates/.aodw-next/templates/rt-intake-template.md`
6. ✅ `.aodw-next/templates/checklists/coding-standards-template.md`（新建）→ `templates/.aodw-next/templates/checklists/coding-standards-template.md`

### 其他相关文件（已存在，本次未修改）
- `.aodw-next/03-standards/ai-coding-rules.md`（已包含按需加载机制）
- `.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md`（已存在）
- `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md`（已存在）
- `.aodw-next/03-standards/ai-coding-rules-common.md`（已存在）

---

## 🎯 融入效果确认

### ✅ 方案设计阶段
- Plan 模板强制要求代码结构与分层设计
- 编码规范符合性说明作为必填项
- 防止"想到哪里写到哪里"

### ✅ 开发阶段
- 开发准备要求工具初始化和编码规范加载
- 开发过程中要求遵守编码规范
- 开发结束前要求自检

### ✅ 提交/合并阶段
- 编码规范检查作为合并的硬性要求
- 未通过编码规范检查的代码不能合并
- 确保代码质量

### ✅ 测试/验收阶段
- 编码规范验收清单模板已创建
- 可作为补充验收项使用

### ✅ 需求分析阶段
- 技术约束字段已添加（可选）
- AI 根据情况填写

---

## ✅ 最终结论

**所有检查通过，可以提交新版本**

编码规范已成功融入 AODW 的各个关键节点：
- ✅ 不再是"挂一个子流程"，而是"嵌入到主流程的每个节点"
- ✅ 编码规范成为流程的必经步骤
- ✅ 编码规范成为质量门槛
- ✅ 编码规范从设计阶段就开始参与

所有文件已正确修改并同步到模板目录，可以提交新版本。

---

## 📝 提交建议

建议提交信息：
```
feat(aodw): 将编码规范融入 AODW 各阶段流程

- 在 Plan 模板中添加代码结构与分层设计章节（必须）
- 在开发阶段添加编码规范要求（必须）
- 在合并前检查清单中添加编码规范检查（必须）
- 创建编码规范验收清单模板（可选）
- 在 Intake 模板中添加技术约束字段（可选）

编码规范已从"子流程"转变为"主流程的必经步骤"，
确保代码质量从设计阶段就开始参与。

Refs: [RT-ID]
```
