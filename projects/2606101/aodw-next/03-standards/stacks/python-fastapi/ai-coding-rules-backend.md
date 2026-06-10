# AI Coding Rules - Backend Development

> **注意**：本文件是 `.aodw-next/03-standards/ai-coding-rules.md` 的子规范文件。  
> 请先阅读主文件了解通用编码原则，再阅读本文件了解后端特定规范。

**适用场景**：
- 后端开发（FastAPI / Python、Node.js、Go 等）
- API 开发
- 数据库操作
- 后端工具配置

**必须与以下规范配合使用**：
- `.aodw-next/03-standards/ai-coding-rules.md`（主文件，包含通用原则）
- `.aodw-next/03-standards/ai-coding-rules-common.md`（通用编码规范）
- `.aodw-next/05-tooling/ai-tools-init-rules.md`（工具初始化规则，如果通过 AI 方式初始化工具）

**⚠️ 强制要求**：所有后端开发必须严格遵守 `docs/backend-guidelines.md` 中的规范（如果存在）。

---

## 1. 技术栈确认

### 1.1 Python / FastAPI 技术栈

适用项目技术栈：
- 语言：Python 3.11+
- Web 框架：FastAPI
- 运行：Uvicorn / Gunicorn+Uvicorn worker
- 数据库：MySQL / PostgreSQL / SQLite 等
- ORM：可选 SQLAlchemy / Tortoise ORM / 其他
- **依赖管理**：uv + pip-tools（必须）
- 工具：Ruff + Black/Blue + pre-commit

### 1.2 其他技术栈

根据项目实际情况确认技术栈（Node.js、Go、Java 等）。

---

## 2. 工具初始化检查（必须）

> **⚠️ 重要**：后端规范必须通过工具强制执行，不能只靠自觉。  
> 本项目的后端规范通过 **"后端四件套"自动化质量体系** 实现：
> - ✅ 编辑器即时提示 → Git 提交前阻断 → CI 自动失败 → AI 自动服从

在开始任何后端开发前，AI 必须检查工具初始化状态：

### 2.1 工具初始化状态检查

**AI 必须检查**：
- [ ] 是否已运行工具初始化？
- [ ] `.aodw-next/tools-status.yaml` 中 `initialized: true` 且后端工具状态为 `configured: true`？

**检查方法**：
1. 读取 `.aodw-next/tools-status.yaml` 文件
2. 检查 `tools_init.initialized` 是否为 `true`
3. 检查 `tools_init.backend.dependency_manager.configured` 是否为 `true`（uv + pip-tools）
4. 检查 `tools_init.backend.ruff.configured` 是否为 `true`
5. 检查 `tools_init.backend.black.configured` 是否为 `true`
6. 检查 `tools_init.backend.pre_commit.configured` 和 `hooks_installed` 是否为 `true`

### 2.2 工具要求

**后端开发必须使用以下工具**：
- **uv + pip-tools**：依赖管理（必须）
- **Ruff**：代码质量 & 复杂度检查（核心工具）
- **Black**：代码格式化（统一风格）
- **pre-commit**：Git 提交前强制检查（关键）
- **import-linter**：目录结构/模块边界检查（可选，推荐）

**工具作用**：
- **uv + pip-tools**：依赖管理，确保依赖版本一致性和可重现性
- **Ruff**：自动拦截"怪物函数"、复杂 Service、未使用变量、import 乱序等
- **Black**：自动统一代码格式，避免风格争议
- **pre-commit**：不合格的代码连 commit 都提不上去，实现"提交前阻断"
- **import-linter**：强制分层架构，防止违反目录结构规范

**工具工作流程**：
- 每次执行 `git commit` 时，将自动触发：
  1. Ruff 检查：发现怪物函数 → ❌ 直接中断提交
  2. Black 格式化：格式不统一 → ❌ 强制格式化后重新提交
  3. 全部通过 → ✅ 才允许提交

### 2.3 工具未初始化时的处理

**如果工具未初始化或未配置**：
1. **AI 必须立即停止编码**
2. **AI 必须提示用户运行工具初始化**：
   - **CLI 方式**：运行 `aodw-skill` 选择"工具初始化"，或运行 `aodw-skill init-tools`
   - **AI 方式**：说"初始化工具"或"设置开发工具"
3. **AI 必须说明**：工具初始化会引导用户完成工具的安装和配置
4. **在工具初始化完成前，不能开始编码**

### 2.4 工具配置参考

**配置模板位置**：`.aodw-next/templates/tools-config/backend/`
- Ruff 配置模板：`ruff.config.template.toml`（需要合并到 `pyproject.toml`）
- Black 配置模板：`black.config.template.toml`（需要合并到 `pyproject.toml`）
- pre-commit 配置模板：`pre-commit.config.template.yaml`

**如果工具已初始化**：
- 配置应已符合 AODW 规范
- 配置文件应已生成或合并
- 工具应已正确安装和配置
- pre-commit hooks 应已安装

**如果需要对配置进行调整**：
- 可以再次运行工具初始化
- 或参考配置模板手动调整

### 2.5 其他语言工具配置

根据项目使用的语言，检查相应的工具配置：
- **Node.js**：ESLint + Prettier + husky
- **Go**：gofmt + golangci-lint + pre-commit
- **Java**：Checkstyle + Spotless + pre-commit

**注意**：其他语言的工具配置模板和初始化流程，将在后续版本中添加。

---

## 3. 依赖管理规范（uv + pip-tools）⚡

> **⚠️ 重要**：本项目使用 **uv + pip-tools** 管理依赖，严格遵循以下规则。

### 3.1 核心原则

**必须遵守**：
- ✅ **只编辑 `.in` 文件**（`requirements.in` / `requirements-dev.in`）
- ❌ **禁止直接编辑 `.txt` 文件**（`requirements.txt` / `requirements-dev.txt` 由工具自动生成）
- ❌ **禁止使用 `pip install package`** 直接安装
- ❌ **禁止使用 `pip freeze > requirements.txt`**

### 3.2 添加依赖的正确流程

#### 3.2.1 添加生产依赖

```bash
# 1. 编辑 requirements.in（使用版本约束）
echo "httpx>=0.25.0,<1.0.0" >> requirements.in

# 2. 重新编译依赖锁定文件
make compile-deps
# 或: uv pip compile requirements.in -o requirements.txt

# 3. 同步到当前环境
make sync
# 或: uv pip sync requirements-dev.txt

# 4. 提交所有文件到 Git
git add requirements.in requirements.txt requirements-dev.txt
```

#### 3.2.2 添加开发依赖

```bash
# 1. 编辑 requirements-dev.in
echo "pytest-mock>=3.12.0" >> requirements-dev.in

# 2. 编译依赖
make compile-deps

# 3. 同步环境
make sync
```

### 3.3 AI 必须遵守的规则

**当 AI 建议安装新包时**：
- ❌ **禁止说**："运行 `pip install package`"
- ✅ **正确做法**："将 `package>=1.0.0` 添加到 `requirements.in`，然后运行 `make compile-deps && make sync`"

**当 AI 询问如何添加依赖时**：
- 总是提供完整流程（编辑 .in → compile → sync）
- 说明依赖应该加到 `requirements.in` 还是 `requirements-dev.in`

**当需要数据库/缓存等依赖时**：
- 明确告知在 `requirements.in` 中添加哪些包
- 提供合适的版本约束（如 `>=2.0.0,<3.0.0`）

**禁止的操作**：
- ❌ `pip install package`
- ❌ 直接编辑 `requirements.txt`
- ❌ `pip freeze > requirements.txt`
- ❌ 不使用版本约束（如只写 `package` 而不是 `package>=1.0.0`）

### 3.4 常用命令参考

```bash
make install-dev   # 安装开发依赖
make compile-deps   # 编译 .in -> .txt
make sync          # 同步环境
make update        # 更新所有依赖
```

### 3.5 版本约束建议

```bash
# ✅ 推荐：指定最小版本 + 主版本上限
fastapi>=0.104.0,<1.0.0

# ⚠️ 可接受：只指定最小版本（谨慎使用）
fastapi>=0.104.0

# ❌ 不推荐：完全锁定（除非有特殊原因）
fastapi==0.104.0

# ❌ 禁止：无版本约束
fastapi
```

### 3.6 依赖管理检查清单

在开始后端开发前，AI 必须检查：

- [ ] 项目是否使用 `uv + pip-tools` 管理依赖？
- [ ] 是否存在 `requirements.in` 和 `requirements-dev.in` 文件？
- [ ] 是否存在 `Makefile` 或相关编译脚本？
- [ ] 是否已安装 `uv` 和 `pip-tools`？

**如果项目未使用 uv + pip-tools**：
- AI 必须提醒用户：本项目要求使用 uv + pip-tools 管理依赖
- AI 可以提供迁移建议（如果需要）

---

## 4. 目录结构规范

### 3.1 FastAPI 项目结构（强制要求）

```
backend/
  app/
    api/
      v1/
        endpoints/        # API 端点（路由层）
        schemas/          # Pydantic 模型（请求/响应）
    core/
      config.py          # 配置
      security.py        # 安全相关
    db/
      base.py            # 数据库基类
      session.py         # 数据库会话
    models/              # SQLAlchemy 模型（ORM 层）
    services/            # 业务逻辑层
    repositories/        # 数据访问层（可选，如果使用 Repository 模式）
    utils/               # 工具函数
  tests/                 # 测试文件
```

### 3.2 分层架构规则（强制要求）

**依赖关系规则**（必须严格遵守）：
- **api/**（路由层）：
  - ✅ 可以导入：`schemas/`、`services/`
  - ❌ **禁止**直接导入：`models/`、`repositories/`
- **services/**（业务逻辑层）：
  - ✅ 可以导入：`repositories/`、`models/`、`schemas/`
  - ❌ **禁止**直接导入：`api/`
- **repositories/**（数据访问层）：
  - ✅ 可以导入：`models/`
  - ❌ **禁止**直接导入：`api/`、`services/`
- **models/**（ORM 层）：
  - ✅ 只能包含 ORM 模型定义
  - ❌ **禁止**导入其他业务层

**工具强制检查**：
- 如果配置了 `import-linter`，违反上述规则将直接报错
- 即使未配置 `import-linter`，AI 也必须严格遵守这些规则

### 3.3 其他框架结构

根据项目使用的框架，遵循相应的目录结构规范，但必须保持分层架构原则。

---

## 4. 命名规范

### 4.1 Python 命名规范

- 模块名：小写字母，单词间用下划线（`user_service.py`）
- 类名：PascalCase（`UserService`）
- 函数/方法名：小写字母，单词间用下划线（`get_user_by_id`）
- 常量：SCREAMING_SNAKE_CASE（`MAX_RETRY_COUNT`）
- 私有方法/属性：以下划线开头（`_internal_method`）

### 4.2 API 端点命名

- RESTful API：使用名词复数形式（`/api/v1/users`）
- 操作使用 HTTP 方法（GET、POST、PUT、DELETE）
- 嵌套资源：`/api/v1/users/{user_id}/orders`

---

## 5. API 设计规范

### 5.1 请求/响应格式

- 使用 Pydantic 模型定义请求和响应结构
- 统一响应格式：
  ```python
  {
    "code": 200,
    "message": "success",
    "data": {...}
  }
  ```

### 5.2 错误处理

- 使用 HTTP 状态码表示错误类型
- 统一错误响应格式
- 提供详细的错误信息（开发环境）

### 5.3 分页

- 统一分页参数：`page`、`page_size`
- 统一分页响应格式

---

## 6. 数据库操作规范

### 6.1 ORM 使用

- 优先使用 ORM，避免直接写 SQL
- 使用事务管理数据库操作
- 注意 N+1 查询问题

### 6.2 数据迁移

- 使用数据库迁移工具（Alembic、Django Migrations 等）
- 迁移文件必须可回滚
- 生产环境迁移前必须备份

---

## 7. 安全规范

### 7.1 认证与授权

- 使用 JWT 或其他标准认证方式
- 实现基于角色的访问控制（RBAC）
- 验证用户权限

### 7.2 数据验证

- 所有输入数据必须验证
- 使用 Pydantic 或其他验证库
- 防止 SQL 注入、XSS 等安全漏洞

---

## 8. 性能优化

### 8.1 数据库查询优化

- 使用索引优化查询
- 避免 N+1 查询问题
- 使用连接池管理数据库连接

### 8.2 缓存策略

- 合理使用缓存（Redis、Memcached 等）
- 设置合适的缓存过期时间
- 处理缓存穿透、缓存击穿、缓存雪崩

---

## 9. 测试规范

### 9.1 单元测试

- 为所有业务逻辑编写单元测试
- 测试覆盖率 ≥ 80%
- 使用 pytest、unittest 等测试框架

### 9.2 集成测试

- 为 API 端点编写集成测试
- 测试数据库操作
- 测试认证和授权

---

## 10. AI 实现流程约束（强制要求）

AI 在编写后端代码时必须遵守以下流程和规则：

### 10.1 目录与分层（强制要求）

- **路由层**：`app/api/v1/endpoints/`
- **业务逻辑层**：`app/services/`
- **数据访问层**：`app/repositories/`（如果使用 Repository 模式）
- **Pydantic 模型**：`app/api/v1/schemas/`
- **ORM 模型**：`app/models/`
- **工具函数**：`app/utils/`

**禁止行为**：
- ❌ 不允许把路由、业务逻辑、数据库操作写在同一个文件
- ❌ 不允许在路由中直接写数据库查询
- ❌ 不允许违反分层架构的依赖关系

### 10.2 代码复杂度（强制要求）

- **单个路由文件**：≤ 300 行
- **单个 service / repository 文件**：≤ 300 行
- **单个函数**：≤ 60 行
- **分支过多**：必须拆函数

**工具自动检查**：
- Ruff 的 PLR 规则会自动拦截违反上述限制的代码
- 如果函数超过 60 行，Ruff 会直接报错

### 10.3 生成流程（强制要求）

**第一步：输出文件列表和职责（必须）**
- 新功能必须先输出【涉及的文件列表 + 每个函数职责】
- 说明每个文件属于哪一层（api/services/repositories/models）
- 说明文件之间的依赖关系

**第二步：按文件逐步实现**
- 按"一个文件一次"的方式逐个生成
- 不允许一次性输出多个层的所有代码混在一起

**第三步：验证工具检查**
- 每个文件生成后，运行 `ruff check .` 验证
- 运行 `black .` 格式化代码
- 确保通过检查后再继续下一个文件

### 10.4 类型与异步（强制要求）

- **所有函数必须有完整类型注解**
- **FastAPI handler 使用 `async def`**
- **不允许在路由中直接写数据库查询**

### 10.5 依赖管理约束提醒

**AI 必须明确告知用户**：
- "本项目使用 uv + pip-tools 管理依赖"
- "添加依赖时，必须编辑 requirements.in 或 requirements-dev.in，然后运行 make compile-deps && make sync"
- "禁止使用 pip install 直接安装依赖"
- "禁止直接编辑 requirements.txt 文件"

### 10.6 工具约束提醒

**AI 必须明确告知用户**：
- "本项目启用了 Ruff + Black + pre-commit"
- "任何不符合规范的代码最终都会被拒绝提交"
- "生成的代码必须通过 Ruff 检查才能提交"

---

## 11. 后端代码提交前检查清单

在提交后端代码前，必须完成以下检查：

### 11.1 工具初始化检查（参考 `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md` 第 2 节）

- [ ] **工具是否已初始化**：
  - [ ] 检查 `.aodw-next/tools-status.yaml` 中 `initialized: true`
  - [ ] **依赖管理工具**（uv + pip-tools）是否已安装并配置？
  - [ ] Ruff 是否已安装并配置？
  - [ ] Black 是否已安装并配置？
  - [ ] pre-commit 是否已安装并配置？
  - [ ] pre-commit hooks 是否已安装？

### 11.2 依赖管理检查（参考 `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md` 第 3 节）

- [ ] **依赖管理规范**：
  - [ ] 是否使用 `uv + pip-tools` 管理依赖？
  - [ ] 是否存在 `requirements.in` 和 `requirements-dev.in` 文件？
  - [ ] 是否只编辑 `.in` 文件，不直接编辑 `.txt` 文件？
  - [ ] 添加依赖时是否使用版本约束（如 `package>=1.0.0,<2.0.0`）？
  - [ ] 是否通过 `make compile-deps && make sync` 更新依赖？

### 11.3 代码质量检查（工具自动）

- [ ] **Ruff 静态检查**：
  - [ ] `ruff check .` 是否通过？
  - [ ] 是否拦截了怪物函数、复杂代码？
  - [ ] 是否有未使用的导入？
  - [ ] 是否有语法错误？
- [ ] **Black 格式化**：
  - [ ] `black .` 是否已运行？
  - [ ] 代码格式是否统一？

### 11.4 文件大小检查（工具自动）

- [ ] **Ruff PLR 规则检查**：
  - [ ] Python 模块是否 ≤ 300 行？（Ruff 自动检查）
  - [ ] 单个函数是否 ≤ 60 行？（Ruff PLR0915 自动拦截）
  - [ ] 复杂度是否 ≤ 10？（Ruff PLR 规则自动检查）

### 11.5 目录结构检查

- [ ] **分层架构检查**：
  - [ ] api 层是否未直接导入 models？
  - [ ] services 层是否未直接导入 api？
  - [ ] 依赖关系是否符合规范？
  - [ ] 如果配置了 import-linter，是否通过检查？

### 11.6 API 设计检查

- [ ] API 端点是否符合 RESTful 规范？
- [ ] 请求/响应格式是否统一？
- [ ] 错误处理是否完善？

### 11.7 安全检查

- [ ] 输入数据是否已验证？
- [ ] 是否防止 SQL 注入、XSS 等安全漏洞？
- [ ] 认证和授权是否正确实现？

### 11.8 测试检查

- [ ] 是否编写了单元测试？
- [ ] 是否编写了集成测试？
- [ ] 测试是否通过？

### 11.9 最终验证

- [ ] **运行完整检查**：
  ```bash
  ruff check .
  black .
  pre-commit run --all-files
  ```
- [ ] **所有检查通过后，才能提交代码**

---

## 12. 依赖管理快速参考

### 12.1 添加依赖的标准流程

```bash
# 1. 编辑 requirements.in（生产依赖）或 requirements-dev.in（开发依赖）
echo "package>=1.0.0,<2.0.0" >> requirements.in

# 2. 编译依赖锁定文件
make compile-deps
# 或: uv pip compile requirements.in -o requirements.txt

# 3. 同步到当前环境
make sync
# 或: uv pip sync requirements-dev.txt

# 4. 提交所有文件
git add requirements.in requirements.txt requirements-dev.txt
```

### 12.2 常用命令

```bash
make install-dev   # 安装开发依赖
make compile-deps  # 编译 .in -> .txt
make sync         # 同步环境
make update       # 更新所有依赖
```

### 12.3 版本约束格式

```bash
# ✅ 推荐
package>=1.0.0,<2.0.0

# ⚠️ 可接受
package>=1.0.0

# ❌ 禁止
package
package==1.0.0  # 除非有特殊原因
```

---

## 13. 工具配置参考

### 13.1 配置模板位置

**配置模板**：`.aodw-next/templates/tools-config/backend/`
- Ruff 配置模板：`ruff.config.template.toml`（需要合并到 `pyproject.toml`）
- Black 配置模板：`black.config.template.toml`（需要合并到 `pyproject.toml`）
- pre-commit 配置模板：`pre-commit.config.template.yaml`

### 13.2 工具工作流程

```
编辑器编写代码
    ↓
Ruff 实时检查（编辑器插件）
    ↓
git commit
    ↓
pre-commit 触发
    ↓
Ruff 检查 → ❌ 失败则中断提交
    ↓
Black 格式化 → ❌ 失败则中断提交
    ↓
✅ 全部通过 → 允许提交
    ↓
CI/CD 再次验证（可选）
```

### 13.3 工具初始化

**如果工具未初始化**：
- 运行 `aodw-skill init-tools` 或通过 AI 命令"初始化工具"
- 工具初始化会引导您完成工具的安装和配置
- 配置模板会自动应用到项目中
