# AI Coding Rules - Backend Development (Rust)

> **注意**：本文件是 `.aodw-next/03-standards/ai-coding-rules.md` 的子规范文件。  
> 请先阅读主文件了解通用编码原则。

**适用场景**：
- 后端开发（Rust + Axum + SQLx）
- 命令行工具开发
- 高性能组件开发

**依赖规范**：
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Effective Rust](https://www.lurklurk.org/effective-rust/)

## 1. 核心原则 (Core Principals)

### 1.1 稳定性优先 (Stability First)
- **绝对禁止在业务逻辑中使用 `unwrap()` 或 `expect()`**。
    - 仅允许在 `tests/`, `examples/`, 或 `bin/` 的初始化阶段（无法恢复的启动错误）使用。
    - 业务代码必须使用 `match`, `if let`, 或 `?` 传播 `Result`。
- **避免 Panic**：任何可能 Panic 的操作（如数组索引 `arr[i]`）都应使用安全版本（如 `arr.get(i)`）。

### 1.2 错误处理 (Error Handling)
- 使用 `thiserror` 定义库/模块级别的错误枚举。
- 使用 `anyhow` 处理顶层应用（Application）的错误传播。
- **Axum Handler** 必须返回实现了 `IntoResponse` 的 Result 类型（通常自定义 `AppError`）。

### 1.3 异步规范 (Async)
- 避免在异步上下文中执行阻塞操作（如标准 `std::fs` 或大量 CPU 计算）。
- 使用 `tokio::fs` 替代 `std::fs`。
- 长时间计算任务使用 `tokio::task::spawn_blocking`。

---

## 2. 代码风格与命名 (Style & Naming)

遵循 `rustfmt` 默认配置。

- **Types (Structs, Enums, Traits)**: `PascalCase`
- **Functions, Methods, Variables, Modules**: `snake_case`
- **Constants, Statics**: `SCREAMING_SNAKE_CASE`
- **File Names**: `snake_case.rs`

---

## 3. 目录结构规范 (Directory Structure)

```
backend/
  src/
    bin/              # 独立可执行文件（工具脚本）
    routes/           # Axum 路由处理函数 (Handlers)
      mod.rs          # 路由注册
      users.rs        # 用户模块路由
    models/           # 数据模型 (Structs) & DB 映射
    services/         # 业务逻辑层 (可选，复杂逻辑从 routes 剥离)
    utils/            # 通用工具函数
    main.rs           # 应用入口，仅包含启动配置
```

- **Routes**: 负责 HTTP 解析、参数校验、调用 Service/Model、返回响应。
- **Services/Models**: 负责核心业务逻辑和数据持久化，不应依赖 HTTP 层细节。

---

## 4. 最佳实践 (Best Practices)

### 4.1 SQLx 使用
- 优先使用 `sqlx::query_as!` 宏进行编译时 SQL 检查。
- 如果必须使用动态 SQL，确保使用参数化查询 (`bind`) 防止注入。
- 数据库模型 Struct 字段应与 DB 列名一致，或使用 `#[sqlx(rename = "...")]`。

### 4.2 Axum Handler
- 保持 Handler 瘦身：如果逻辑超过 50 行，考虑提取到 Service 层或独立函数。
- 使用 `State` 抽取共享状态（如 DB Pool）。

### 4.3 日志 (Logging)
- 使用 `tracing` 而非 `println!`。
- 关键业务路径必须有 `info!` 日志。
- 错误分支必须有 `error!` 日志，包含上下文信息。

---

## 5. 工具链配置 (Tooling)

所有 Rust 项目必须包含以下配置：

### 5.1 工具初始化（必须）

在开始开发前，必须运行工具初始化：
- 通过 AI 命令："初始化工具" 或 "设置开发工具"
- 通过 CLI 命令：`aodw-skill init-tools`

工具初始化会自动：
- 检测 rustfmt、clippy、cargo 是否已安装
- 从模板生成 `rustfmt.toml` 和 `clippy.toml` 配置文件
- 配置 pre-commit hooks（如果使用）

### 5.2 配置文件

**rustfmt.toml**（从模板生成）：
- 模板位置：`.aodw-next/templates/tools-config/backend/rustfmt.config.template.toml`
- 生成位置：项目根目录 `rustfmt.toml`
- 主要配置：
  ```toml
  edition = "2021"
  max_width = 100
  use_small_heuristics = "Max"
  ```

**clippy.toml**（从模板生成）：
- 模板位置：`.aodw-next/templates/tools-config/backend/clippy.config.template.toml`
- 生成位置：项目根目录 `clippy.toml` 或 `Cargo.toml` 的 `[lints.clippy]` 部分
- 主要配置：
  - 零警告策略：`warn = "all"`, `deny = ["warnings"]`
  - 复杂度限制：`cognitive-complexity-threshold = 15`（见模板 `clippy.config.template.toml`）
  - 文件长度限制：`too_many_lines_threshold = 400`

### 5.3 提交前检查（必须）

所有代码提交前必须通过以下检查：
- `cargo fmt -- --check`（代码格式化检查）
- `cargo clippy -- -D warnings`（零警告策略）
- `cargo test`（单元测试）

这些检查应配置在 pre-commit hooks 中，确保提交前自动执行。

---

## 6. 代码质量指标 (Metrics)

- **函数长度**: 软限制 60 行。超过则拆分。
- **文件长度**: 软限制 400 行。
- **复杂度**: 单个函数 Cyclomatic Complexity < 15。
