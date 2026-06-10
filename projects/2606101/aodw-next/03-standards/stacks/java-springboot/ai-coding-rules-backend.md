# AI Coding Rules - Backend Development

> **注意**：本文件是 `.aodw-next/03-standards/ai-coding-rules.md` 的子规范文件。  
> 请先阅读主文件了解通用编码原则，再阅读本文件了解后端特定规范。

**适用场景**：
- 后端开发（Spring Boot 2.7.18 + Java 21）
- API 开发 (RESTful)
- 数据库操作 (MySQL / MyBatis / Spring Data JPA)
- 后端工具配置

---

## 1. 技术栈确认

适用项目技术栈：
- **核心框架**：Spring Boot 2.7.18
- **JDK 版本**：Java 21
- **依赖管理**：Maven
- **注册/配置中心**：Nacos
- **数据库**：MySQL
- **持久层中间件**：xg-cloud-mysql (基于 Spring Boot Starter)
- **缓存**：Redis
- **消息中间件**：RabbitMQ

**必须与以下规范配合使用**：
- `.aodw-next/03-standards/ai-coding-rules.md`（主文件，包含通用原则）
- `.aodw-next/03-standards/ai-coding-rules-common.md`（通用编码规范）
- `.aodw-next/05-tooling/ai-tools-init-rules.md`（工具初始化规则，如果通过 AI 方式初始化工具）

**⚠️ 强制要求**：所有后端开发必须严格遵守 `docs/backend-guidelines.md` 中的规范（如果存在）。

---

## 2. 工具初始化检查（必须）

> **⚠️ 重要**：所有后端开发必须使用工具强制执行规范，不能只靠自觉。  
> 本项目的后端规范通过 **工具自动化质量体系** 实现：
> - ✅ 编辑器即时提示 → Git 提交前阻断 → CI 自动失败 → AI 自动服从

在开始任何后端开发前，AI 必须检查工具初始化状态：

### 2.1 工具初始化状态检查

**AI 必须检查**：
- [ ] 是否已运行工具初始化？
- [ ] `.aodw-next/tools-status.yaml` 中 `initialized: true` 且后端工具状态为 `configured: true`？

**检查方法**：
1. 读取 `.aodw-next/tools-status.yaml` 文件
2. 检查 `tools_init.initialized` 是否为 `true`
3. 检查 `tools_init.backend.maven.configured` 是否为 `true`（Maven 依赖管理）
4. 检查 `tools_init.backend.checkstyle.configured` 是否为 `true`（如果使用 Checkstyle）
5. 检查 `tools_init.backend.spotless.configured` 是否为 `true`（如果使用 Spotless）
6. 检查 `tools_init.backend.pre_commit.configured` 和 `hooks_installed` 是否为 `true`

### 2.2 工具要求

**Java 后端开发推荐使用以下工具**：
- **Maven**：依赖管理（必须）
- **Checkstyle**：代码风格检查（推荐）
- **Spotless**：代码格式化（推荐）
- **pre-commit**：Git 提交前强制检查（推荐）
- **Maven Wrapper**：确保 Maven 版本一致性（推荐）

**工具作用**：
- **Maven**：依赖管理，确保依赖版本一致性和可重现性
- **Checkstyle**：自动检查代码风格，确保符合 Java 编码规范
- **Spotless**：自动统一代码格式，避免风格争议
- **pre-commit**：不合格的代码连 commit 都提不上去，实现"提交前阻断"

**工具工作流程**：
- 每次执行 `git commit` 时，将自动触发：
  1. Checkstyle 检查：发现代码风格问题 → ❌ 直接中断提交
  2. Spotless 格式化：格式不统一 → ❌ 强制格式化后重新提交
  3. 全部通过 → ✅ 才允许提交

### 2.3 工具未初始化时的处理

**如果工具未初始化或未配置**：
1. **AI 必须立即停止编码**
2. **AI 必须提示用户运行工具初始化**：
   - **CLI 方式**：运行 `aodw` 选择"工具初始化"，或运行 `aodw init-tools`
   - **AI 方式**：说"初始化工具"或"设置开发工具"
3. **AI 必须说明**：工具初始化会引导用户完成工具的安装和配置
4. **在工具初始化完成前，不能开始编码**

### 2.4 工具配置参考

**配置模板位置**：`.aodw-next/templates/tools-config/backend/`
- Checkstyle 配置模板：`checkstyle.config.template.xml`（如果存在）
- Spotless 配置模板：`spotless.config.template.xml`（如果存在）
- pre-commit 配置模板：`pre-commit.config.template.yaml`

**如果工具已初始化**：
- 配置应已符合 AODW 规范
- 配置文件应已生成或合并
- 工具应已正确安装和配置
- pre-commit hooks 应已安装

**如果需要对配置进行调整**：
- 可以再次运行工具初始化
- 或参考配置模板手动调整

---

## 3. 目录结构规范

### 2.1 标准 Maven 结构
```
backend/
  src/
    main/
      java/
        com/xgjktech/pms/
          business/    # 业务核心模块
          sys/         # 系统管理模块
          bpsp/        # 任务同步模块
          base/        # 基础组件与配置
      resources/
        bootstrap.properties
        logback-spring.xml
    test/              # 单元测试与集成测试
  pom.xml              # 依赖定义
```

### 2.2 模块内分层 (Layered Architecture)
- **controller**: 路由入口，仅负责参数校验与响应封装。
- **service**: 业务逻辑层，核心业务实现。
- **mapper / dao**: 数据访问层，SQL 映射或 JPA Repository。
- **data/entity**: 数据库实体类。
- **data/vo**: 接口返回对象。
- **data/param**: 接口请求参数。

---

## 4. 命名规范

- **类名**: PascalCase (如 `ProjectService`)。
- **接口名**: 无需 `I` 前缀。
- **方法/变量**: camelCase。
- **Mapper XML**: 建议与 Mapper 接口同名且位于对应包路径下。

---

## 5. Spring Boot 编码规范

### 4.1 注解使用
- 优先使用构造函数注入 (`@RequiredArgsConstructor`) 代替 `@Autowired`。
- 控制器统一使用 `@RestController` 和 `@RequestMapping`。

### 4.2 异常处理
- 严禁捕获异常后不做任何处理。
- 业务异常应抛出自定义异常类，由全局异常处理器统一拦截。

### 4.3 数据库操作
- 严禁在循环内执行 SQL 查询。
- 复杂 SQL 必须写在 Mapper XML 中。

---

## 6. 依赖管理 (Maven)

- **pom.xml**：
  - 代码变更涉及新依赖时，必须更新 `pom.xml`。
  - 优先检查 `xg-common-parent` 中定义的版本，避免冲突。
  - 依赖范围必须准确（compile, provided, test 等）。

---

## 7. AI 实现流程约束

### 7.1 生成粒度
- 遵循“一个文件一次生成”原则。
- 复杂功能应先生成 Entity/Repository，再生成 Service，最后生成 Controller。

### 7.2 代码质量
- 所有的 POJO 类建议使用 `@Data` (Lombok) 以减少冗余。
- API 接口必须符合 RESTful 设计原则。

---

## 8. Java 代码提交前检查清单

在提交 Java 代码前，必须完成以下检查：

### 8.1 工具初始化检查（参考 `.aodw-next/03-standards/stacks/java-springboot/ai-coding-rules-backend.md` 第 2 节）

- [ ] **工具是否已初始化**：
  - [ ] 检查 `.aodw-next/tools-status.yaml` 中 `initialized: true`
  - [ ] **Maven** 是否已安装并配置？
  - [ ] **Checkstyle** 是否已安装并配置？（如果使用）
  - [ ] **Spotless** 是否已安装并配置？（如果使用）
  - [ ] **pre-commit** 是否已安装并配置？
  - [ ] pre-commit hooks 是否已安装？

### 8.2 依赖管理检查

- [ ] **Maven 依赖管理**：
  - [ ] 是否使用 Maven 管理依赖？
  - [ ] `pom.xml` 是否已更新？
  - [ ] 依赖版本是否与 `xg-common-parent` 一致？
  - [ ] 依赖范围是否准确（compile, provided, test 等）？

### 8.3 代码质量检查（工具自动）

- [ ] **Checkstyle 静态检查**（如果使用）：
  - [ ] `mvn checkstyle:check` 是否通过？
  - [ ] 代码风格是否符合规范？
- [ ] **Spotless 格式化**（如果使用）：
  - [ ] `mvn spotless:apply` 是否已运行？
  - [ ] 代码格式是否统一？

### 8.4 目录结构检查

- [ ] **分层架构检查**：
  - [ ] controller 层是否未直接导入 mapper/dao？
  - [ ] service 层是否未直接导入 controller？
  - [ ] 依赖关系是否符合规范？

### 8.5 最终验证

- [ ] **运行完整检查**：
  ```bash
  mvn clean compile
  mvn checkstyle:check  # 如果使用 Checkstyle
  mvn spotless:apply    # 如果使用 Spotless
  mvn test
  pre-commit run --all-files  # 如果使用 pre-commit
  ```
- [ ] **所有检查通过后，才能提交代码**
