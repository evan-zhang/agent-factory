# 工具配置模板

本目录包含 AODW 规范要求的开发工具配置模板。

## 目录结构

```
tools-config/
├── frontend/          # 前端工具配置模板
│   ├── eslint.config.template.json
│   ├── prettier.config.template.json
│   └── tsconfig.paths.template.json
├── backend/           # 后端工具配置模板
│   ├── ruff.config.template.toml          # Python 代码质量检查
│   ├── black.config.template.toml         # Python 代码格式化
│   ├── rustfmt.config.template.toml       # Rust 代码格式化
│   ├── clippy.config.template.toml        # Rust 代码质量检查
│   └── pre-commit.config.template.yaml    # Git 提交前检查（通用）
└── README.md
```

## 使用方式

### 方式 1：通过 CLI 命令

```bash
aodw-skill init-tools
```

CLI 会自动检测项目类型，并使用相应的模板生成配置文件。

### 方式 2：通过 AI 命令

在 AI 工具（Cursor/Claude 等）中说：
- "初始化工具"
- "设置开发工具"
- "配置工具"

AI 会引导您完成工具初始化和配置。

## 配置说明

### 前端配置

#### ESLint 配置
- 文件：`.eslintrc.json` 或 `eslint.config.js`
- 模板：`frontend/eslint.config.template.json`
- 包含：TypeScript、React、Hooks、Import、可访问性规则
- 限制：文件大小、函数长度、复杂度

#### Prettier 配置
- 文件：`.prettierrc.json` 或 `prettier.config.js`
- 模板：`frontend/prettier.config.template.json`
- 包含：代码格式化规则

#### TypeScript Path Alias
- 文件：`tsconfig.json`
- 模板：`frontend/tsconfig.paths.template.json`
- 包含：路径别名配置（@app、@pages、@features、@shared）

### 后端配置

#### Python 项目工具

**Ruff 配置**：
- 文件：`pyproject.toml`（合并到 `[tool.ruff]` 部分）
- 模板：`backend/ruff.config.template.toml`
- 包含：代码质量检查、复杂度限制

**Black 配置**：
- 文件：`pyproject.toml`（合并到 `[tool.black]` 部分）
- 模板：`backend/black.config.template.toml`
- 包含：代码格式化规则

#### Rust 项目工具

**rustfmt 配置**：
- 文件：`rustfmt.toml`（项目根目录）
- 模板：`backend/rustfmt.config.template.toml`
- 包含：代码格式化规则（edition、max_width、imports 等）

**clippy 配置**：
- 文件：`clippy.toml`（项目根目录）或 `Cargo.toml` 的 `[lints.clippy]` 部分
- 模板：`backend/clippy.config.template.toml`
- 包含：代码质量检查、复杂度限制、零警告策略

#### Java 项目工具

**Checkstyle 配置**（推荐）：
- 文件：`checkstyle.xml`（项目根目录）
- 模板：`backend/checkstyle.config.template.xml`（如果存在）
- 包含：Java 代码风格检查规则
- 配置方式：在 `pom.xml` 中添加 `maven-checkstyle-plugin`

**Spotless 配置**（推荐）：
- 文件：`pom.xml` 中的 `spotless-maven-plugin` 配置
- 模板：`backend/spotless.config.template.xml`（如果存在）
- 包含：Java 代码格式化规则（Google Java Format）
- 配置方式：在 `pom.xml` 中添加 `spotless-maven-plugin`

#### 通用工具配置

**pre-commit 配置**：
- 文件：`.pre-commit-config.yaml`
- 模板：`backend/pre-commit.config.template.yaml`
- 包含：Git 提交前检查钩子（支持 Python、Rust、Java 等）

## 注意事项

1. **配置文件合并**：如果配置文件已存在，工具初始化会询问您是否合并配置
2. **模板更新**：模板更新不会自动应用到已有项目，需要重新运行工具初始化
3. **自定义配置**：您可以在工具初始化后手动调整配置，但建议保持核心规范不变
