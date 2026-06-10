# AI Coding Rules - Frontend Development

> **注意**：本文件是 `.aodw-next/03-standards/ai-coding-rules.md` 的子规范文件。  
> 请先阅读主文件了解通用编码原则，再阅读本文件了解前端特定规范。

**适用场景**：
- 前端开发（Vue 2.6 + Webpack 4 + Element-UI）
- UI 组件开发
- 前端工具配置

**必须与以下规范配合使用**：
- `.aodw-next/03-standards/ai-coding-rules.md`（主文件，包含通用原则）
- `.aodw-next/03-standards/ai-coding-rules-common.md`（通用编码规范）
- `.aodw-next/05-tooling/ai-tools-init-rules.md`（工具初始化规则，如果通过 AI 方式初始化工具）

**⚠️ 强制要求**：所有前端开发必须严格遵守 `docs/frontend-guidelines.md` 中的规范（如果存在）。

---

## 1. 技术栈确认

适用项目技术栈：
- **框架**：Vue 2.6.14 (Option API)
- **UI 组件库**：Element-UI 2.15.7
- **工程化**：Webpack 4 + Babel
- **状态管理**：Vuex (如有) 或 Vue.observable
- **网络请求**：Axios (0.18.1)
- **样式**：SASS/SCSS + PostCSS

---

## 2. 工具初始化检查（必须）

> **⚠️ 重要**：所有前端开发必须使用工具强制执行规范，不能只靠自觉。  
> 本项目的后端规范通过 **工具自动化质量体系** 实现：
> - ✅ 编辑器即时提示 → Git 提交前阻断 → CI 自动失败 → AI 自动服从

在开始任何前端开发前，AI 必须检查工具初始化状态：

### 2.1 工具初始化状态检查

**AI 必须检查**：
- [ ] 是否已运行工具初始化？
- [ ] `.aodw-next/tools-status.yaml` 中 `initialized: true` 且前端工具状态为 `configured: true`？

**检查方法**：
1. 读取 `.aodw-next/tools-status.yaml` 文件
2. 检查 `tools_init.initialized` 是否为 `true`
3. 检查 `tools_init.frontend.eslint.configured` 是否为 `true`
4. 检查 `tools_init.frontend.prettier.configured` 是否为 `true`
5. 检查 ESLint 配置是否适用于 Vue 2

### 2.2 工具要求

**Vue 2 前端开发必须使用以下工具**：
- **ESLint**：代码质量检查（语法错误、未使用变量、Vue 2 特定规则）
- **Prettier**：代码格式化（统一代码风格）
- **PostCSS**：CSS 后处理（兼容性配置）

**工具作用**：
- ESLint：自动拦截代码质量问题，确保符合 Vue 2 编码规范
- Prettier：自动统一代码格式，避免风格争议
- PostCSS：处理 CSS 兼容性问题

### 2.3 工具未初始化时的处理

**如果工具未初始化或未配置**：
1. **AI 必须立即停止编码**
2. **AI 必须提示用户运行工具初始化**：
   - **CLI 方式**：运行 `aodw` 选择"工具初始化"，或运行 `aodw init-tools`
   - **AI 方式**：说"初始化工具"或"设置开发工具"
3. **AI 必须说明**：工具初始化会引导用户完成工具的安装和配置
4. **在工具初始化完成前，不能开始编码**

### 2.4 工具配置参考

**配置模板位置**：`.aodw-next/templates/tools-config/frontend/`
- ESLint 配置模板：`eslint.config.template.json`（需要适配 Vue 2）
- Prettier 配置模板：`prettier.config.template.json`

**Vue 2 特定配置要求**：
- ESLint 必须包含 `eslint-plugin-vue` 插件
- ESLint 配置必须设置为 Vue 2 模式（`vue/no-v-for-template-key` 等规则）
- Prettier 配置需要兼容 Vue 2 的单文件组件格式

**如果工具已初始化**：
- 配置应已符合 AODW 规范
- 配置文件应已生成或合并
- 工具应已正确安装和配置

**如果需要对配置进行调整**：
- 可以再次运行工具初始化
- 或参考配置模板手动调整

---

## 3. 目录结构规范

### 3.1 核心目录
```
frontend/
  src/
    api/              # 接口请求定义
    assets/           # 静态资源 (图片、字体、全局样式)
    components/       # 通用业务组件
    directive/        # 自定义指令
    filters/          # 全局过滤器
    layout/           # 页面布局
    router/           # 路由定义
    store/            # Vuex 状态管理
    utils/            # 工具函数
    views/            # 页面组件
    App.vue           # 根组件
    main.js           # 入口文件
```

### 3.2 依赖规则
- **views**: 依赖组件、API、Store。
- **components**: 依赖 API、Utils，不建议依赖 views。
- **api**: 仅负责数据请求。

---

## 4. 命名规范

- **组件文件**: PascalCase (如 `ProjectList.vue`)。
- **目录名**: kebab-case 或 camelCase。
- **变量/函数**: camelCase。
- **生命周期钩子**: 严格按照 Vue 2 官方推荐顺序排列。

---

## 5. Vue 2 编码规范

### 5.1 组件定义
- 必须包含 `name` 属性，便于调试。
- `data` 必须是一个函数。
- `props` 必须定义类型、默认值或是否必传。

### 5.2 样式约定
- 组件样式建议使用 `scoped`，避免污染全局。
- 优先使用项目定义的 SASS 变量。

### 5.3 跨组件通信
- 父子组件：Props & Emit。
- 跨级组件：Provide / Inject 或 Vuex。
- 兄弟组件：EventBus (谨慎使用) 或 Vuex。

---

## 6. AI 实现流程约束

### 6.1 文件拆分原则
- 单个 `.vue` 文件代码量建议 ≤ 500 行。
- 复杂的业务逻辑建议拆分到 `src/utils` 或通过 Mixin (慎用) 提取。
- 超过 300 行的 `template` 应当考虑拆分子组件。

### 6.2 代码生成策略
- 优先生成符合 Vue 2 语法的代码（Option API）。
- 确保所有的 `import` 路径正确（使用项目中定义的别名，如 `@`）。

---

## 7. Vue 2 代码提交前检查清单

在提交 Vue 2 代码前，必须完成以下检查：

### 7.1 工具初始化检查（参考 `.aodw-next/03-standards/stacks/vue2/ai-coding-rules-frontend.md` 第 2 节）

- [ ] **工具是否已初始化**：
  - [ ] 检查 `.aodw-next/tools-status.yaml` 中 `initialized: true`
  - [ ] ESLint 是否已安装并配置？（必须支持 Vue 2）
  - [ ] Prettier 是否已安装并配置？
  - [ ] PostCSS 是否已配置？

### 7.2 目录结构检查

- [ ] **目录结构是否符合规范**：
  - [ ] 页面组件是否放在 `src/views/` 下？
  - [ ] 通用组件是否放在 `src/components/` 下？
  - [ ] API 请求是否放在 `src/api/` 下？
  - [ ] 工具函数是否放在 `src/utils/` 下？

### 7.3 文件大小检查

- [ ] **文件大小是否符合规范**：
  - [ ] 单个 `.vue` 文件是否 ≤ 500 行？
  - [ ] `template` 部分是否 ≤ 300 行？
  - [ ] 单个函数是否 ≤ 60 行？

### 7.4 Vue 2 编码规范检查

- [ ] **组件定义**：
  - [ ] 是否包含 `name` 属性？
  - [ ] `data` 是否是一个函数？
  - [ ] `props` 是否定义了类型、默认值或是否必传？
- [ ] **样式约定**：
  - [ ] 组件样式是否使用了 `scoped`？
  - [ ] 是否优先使用项目定义的 SASS 变量？

### 7.5 代码质量检查（工具自动）

- [ ] **ESLint 静态检查**：
  - [ ] `npm run lint` 或 `npx eslint .` 是否通过？
  - [ ] 是否有语法错误？
  - [ ] 是否有未使用的变量？
  - [ ] Vue 2 特定规则是否通过？
- [ ] **Prettier 格式化**：
  - [ ] `npm run format` 或 `npx prettier --write .` 是否已运行？
  - [ ] 代码格式是否统一？

### 7.6 最终验证

- [ ] **运行完整检查**：
  ```bash
  npm run lint      # ESLint 检查
  npm run format    # Prettier 格式化
  npm run build     # 构建检查
  ```
- [ ] **所有检查通过后，才能提交代码**
