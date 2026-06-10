# 编码规范验收清单

> **注意**：本清单用于检查代码是否符合项目编码规范（`.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md` 和 `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md`）。

---

## 前端编码规范验收（如涉及）

### 工具检查
- [ ] ESLint 检查全部通过（`npm run lint` 或 `npx eslint .`）
- [ ] Prettier 格式化已运行（`npm run format` 或 `npx prettier --write .`）
- [ ] 工具初始化状态正常（检查 `.aodw-next/tools-status.yaml`）

### 目录结构检查
- [ ] 目录结构符合规范（pages / features / shared）
- [ ] 页面放在 `src/pages/<PageName>/` 下
- [ ] 可复用业务逻辑放在 `src/features/<domain>/` 下
- [ ] 通用组件/hooks/工具放在 `src/shared/` 下
- [ ] 依赖关系符合规范（pages → features/shared, features → shared）

### 代码质量检查
- [ ] 文件大小符合规范：
  - [ ] 页面入口组件（index.tsx）≤ 300 行
  - [ ] 普通组件/hooks/store 文件 ≤ 200 行
- [ ] 函数大小符合规范：
  - [ ] 单个函数 ≤ 60 行
- [ ] 复杂度符合规范：
  - [ ] 复杂度 ≤ 10

### TypeScript 规范检查
- [ ] 是否启用严格模式
- [ ] 是否避免使用 any
- [ ] API 层是否使用 DTO 类型和 Response 类型

### React 编码规范检查
- [ ] 是否使用函数组件 + Hooks
- [ ] 数据请求是否封装在 features/*/api 或页面专用 hooks
- [ ] 是否不在组件中直接调用 fetch/axios

---

## 后端编码规范验收（如涉及）

### 依赖管理检查
- [ ] 使用 `uv + pip-tools` 管理依赖
- [ ] 存在 `requirements.in` 和 `requirements-dev.in` 文件
- [ ] 只编辑 `.in` 文件，不直接编辑 `.txt` 文件
- [ ] 添加依赖时使用版本约束（如 `package>=1.0.0,<2.0.0`）
- [ ] 通过 `make compile-deps && make sync` 更新依赖

### 工具检查
- [ ] Ruff 检查全部通过（`ruff check .`）
- [ ] Black 格式化已运行（`black .`）
- [ ] pre-commit hooks 已安装（如适用）
- [ ] 工具初始化状态正常（检查 `.aodw-next/tools-status.yaml`）

### 分层架构检查
- [ ] 分层架构符合规范（api → services → repositories）
- [ ] API 层未直接导入 models（如适用）
- [ ] Services 层未直接导入 api
- [ ] 依赖关系符合规范（不跨层调用）

### 代码质量检查
- [ ] 文件大小符合规范：
  - [ ] Python 模块 ≤ 300 行（Ruff 自动检查）
- [ ] 函数大小符合规范：
  - [ ] 单个函数 ≤ 60 行（Ruff PLR0915 自动拦截）
- [ ] 复杂度符合规范：
  - [ ] 复杂度 ≤ 10（Ruff PLR 规则自动检查）

### API 设计检查
- [ ] API 端点是否符合 RESTful 规范
- [ ] 请求/响应格式是否统一
- [ ] 错误处理是否完善

### 安全检查
- [ ] 输入数据是否已验证
- [ ] 是否防止 SQL 注入、XSS 等安全漏洞
- [ ] 认证和授权是否正确实现

---

## 通用编码规范验收

### 文件大小检查
- [ ] 文件大小符合规范（参考 `.aodw-next/03-standards/ai-coding-rules-common.md`）

### 函数/方法长度检查
- [ ] 函数/方法长度符合规范

### 复杂度检查
- [ ] 复杂度符合规范

### 命名规范检查
- [ ] 命名规范符合要求（参考具体编码规范文件）

---

## LLM 行为规范验收

### 实现前对齐检查
- [ ] 已明确声明关键假设（输入、边界、依赖、预期行为）
- [ ] 存在歧义时，已列出多个解释并给出推荐与理由
- [ ] 已将任务转换为可验证成功标准（测试、验收条件或回归路径）
- [ ] 已说明当前方案为何是最小必要改动

### 过度实现检查
- [ ] 未实现用户未请求的额外功能
- [ ] 未引入一次性逻辑的过早抽象
- [ ] 未增加未被请求的配置项或“未来扩展”结构

### 外科手术式改动检查
- [ ] 变更仅覆盖与当前请求直接相关的代码
- [ ] 不存在无关重构、无关格式化、无关注释清理
- [ ] 仅清理由本次变更引入的孤儿代码（unused import/var/function）

---

## 验收结果

- [ ] 所有检查项已通过
- [ ] 如有未通过项，已记录原因并说明：
  - 未通过项：
  - 原因说明：
  - 后续处理计划：

---

**验收人**：_________________  
**验收日期**：_________________
