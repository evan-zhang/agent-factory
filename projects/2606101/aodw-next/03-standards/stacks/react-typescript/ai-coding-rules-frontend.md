# AI Coding Rules - Frontend Development

> **注意**：本文件是 `.aodw-next/03-standards/ai-coding-rules.md` 的子规范文件。  
> 请先阅读主文件了解通用编码原则，再阅读本文件了解前端特定规范。

**适用场景**：
- 前端开发（React + TypeScript + Vite）
- UI 组件开发
- 前端工具配置

**必须与以下规范配合使用**：
- `.aodw-next/03-standards/ai-coding-rules.md`（主文件，包含通用原则）
- `.aodw-next/03-standards/ai-coding-rules-common.md`（通用编码规范）
- `.aodw-next/05-tooling/ai-tools-init-rules.md`（工具初始化规则，如果通过 AI 方式初始化工具）

**⚠️ 强制要求**：所有前端开发必须严格遵守 `docs/frontend-guidelines.md` 中的规范。

---

## 1. 技术栈确认

适用项目技术栈：
- 框架：React 18/19 + TypeScript + Vite
- UI：Tailwind CSS + Radix UI + 自定义组件库
- 状态：Zustand
- 工具：ESLint + Prettier

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
5. 检查 `tools_init.frontend.typescript_path_alias.configured` 是否为 `true`

### 2.2 工具要求

**前端开发必须使用以下工具**：
- **ESLint**：代码质量检查（语法错误、未使用变量、import 排序、复杂度检查）
- **Prettier**：代码格式化（统一代码风格）
- **TypeScript Path Alias**：模块路径别名（@app、@pages、@features、@shared）

**工具作用**：
- ESLint：自动拦截怪物函数、复杂代码、未使用变量等
- Prettier：自动统一代码格式，避免风格争议
- TypeScript Path Alias：支持模块路径别名，便于代码组织

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
- ESLint 配置模板：`eslint.config.template.json`
- Prettier 配置模板：`prettier.config.template.json`
- TypeScript Path Alias 模板：`tsconfig.paths.template.json`

**如果工具已初始化**：
- 配置应已符合 AODW 规范
- 配置文件应已生成或合并
- 工具应已正确安装和配置

**如果需要对配置进行调整**：
- 可以再次运行工具初始化
- 或参考配置模板手动调整

---

## 3. 目录结构规范

### 3.1 顶层结构

```
frontend/
  src/
    app/                 # 应用入口、路由、全局 Provider
    pages/               # 页面级（路由入口）
    features/            # 可复用业务模块（跨页面）
    shared/              # 跨业务通用：组件/工具/类型
    config/              # 配置、环境相关
    styles/              # 全局样式
    assets/              # 静态资源
```

### 3.2 详细结构说明

- `app/`：应用入口、路由、全局 Provider
  - `router/`：路由定义
  - `providers/`：全局 Provider（主题、QueryClient 等）
  - `layout/`：顶层布局（如 AppShell）
- `pages/`：按路由拆目录，每个页面一个文件夹
  - `ProjectEditorPage/`
    - `index.tsx`：页面入口（路由组件）
    - `Header.tsx`, `Sidebar.tsx`, `Canvas.tsx` 等子组件
    - `modals/`：页面专用模态框
    - `hooks/`：页面专用 hooks
    - `store/`：页面专用 store
- `features/`：按业务域拆目录（project、user、auth…）
  - `project/`
    - `components/`：项目相关可复用组件
    - `hooks/`：项目相关可复用 hooks
    - `store/`：项目相关 store（全局/跨页面）
    - `api/`：与项目相关的 API 封装
- `shared/`：跨业务通用
  - `components/`：通用组件（Button、Card、Table、Dialog 等）
  - `hooks/`：通用 hooks（useDebounce、useResizeObserver 等）
  - `store/`：通用全局状态
  - `utils/`：工具函数（日期、格式化、日志）
  - `types/`：通用类型/接口声明

### 3.3 依赖关系规则

- `pages/`：可以依赖 `features/` 和 `shared/`
- `features/`：可以依赖 `shared/`，但尽量不要彼此深度耦合
- `shared/`：只能依赖 `shared` 自身，不依赖 `pages` 或 `features`

---

## 4. 命名规范

### 4.1 文件命名

- React 组件文件：PascalCase（如 `ProjectEditorPage/index.tsx`、`Header.tsx`）
- hooks 文件：`useXxx.ts`（如 `useProjectEditorData.ts`）
- Zustand store：`xxx.store.ts`（如 `projectEditor.store.ts`）
- 类型声明：`xxx.types.ts` 或集中放在 `shared/types` 中
- 工具函数：`xxx.utils.ts` 或放在 `shared/utils` 下

### 4.2 组件和变量命名

- 组件：PascalCase
- 变量/函数：camelCase
- 常量：SCREAMING_SNAKE_CASE
- hooks：以 `use` 开头，返回 `[state, actions]` 或对象

---

## 5. TypeScript 规范

- 启用严格模式：`"strict": true`
- 禁止滥用 `any`：使用 `unknown` + 类型收窄 或 合理定义接口
- API 层优先使用：
  - DTO 类型（请求）
  - Response 类型（响应）
- 类型命名：
  - 接口/类型：`Project`, `ProjectDetail`, `UserProfile`
  - 不建议 `IProject` 这种前缀

---

## 6. React 编码规范

### 6.1 组件类型

- 优先使用函数组件 + Hooks
- 不使用 class 组件
- 每个文件聚焦一个主要组件
- 如果一个文件内存在多个复杂组件 → 拆文件

### 6.2 状态管理策略

- 页面局部状态：`useState` / `useReducer`
- 页面内复杂状态：页面专用 `hooks/` + `store/`（Zustand）
- 跨页面共享业务状态：放在 `features/*/store`
- 全局通用状态：放在 `shared/store`
- **原则**：能局部就不全局，能 hook 就不 store

### 6.3 副作用 & 数据请求

- 所有数据请求封装在：
  - `features/*/api`
  - 或页面专用 hooks：`pages/*/hooks`
- **禁止**在组件中直接调用 `fetch/axios`
- 统一用 `apiClient` / 封装方法

---

## 7. Tailwind & Radix 使用规范

### 7.1 Tailwind

- 使用 `className` 写原子类，尽量保持每个组件的 `className` 长度可读
- 复杂样式组合抽离到：
  - `cn()` 帮助函数结合条件类
  - 或封装为组件，例如 `<PrimaryButton />`
- 不在逻辑代码里到处写硬编码颜色，优先用设计系统中的 token（在 Tailwind config 中定义）

### 7.2 Radix UI

- Radix 组件作为"基础交互组件"，在 `shared/components` 中封装
- 例如 Dialog、Popover、DropdownMenu 封装为：
  - `SharedDialog.tsx`
  - `DropdownMenu.tsx`
- 页面或业务组件不直接大量拼 Radix 基础元素，而是复用封装后的组件

---

## 8. AI 实现流程约束（强制要求）

AI 在编写前端代码时必须遵守以下流程：

### 8.1 第一步：输出目录与文件拆分方案（必须）

- 必须先给出目录和文件拆分方案
- 解释每个文件的职责
- 确保符合文件大小限制：
  - 页面入口组件（index.tsx）≤ 300 行（推荐 ≤ 250 行）
  - 普通组件 / hooks / store 文件 ≤ 200 行
  - 单个函数 ≤ 60 行
  - 复杂度控制：complexity ≤ 10
- **等待用户确认拆分方案**

### 8.2 第二步：按文件逐步实现

- 每次只实现一个文件
- 每次只输出一个文件的完整代码
- 确保每个文件符合规范

### 8.3 第三步：重构大文件

- 在已有大文件重构时，优先拆分成多个小文件
- 不要继续追加代码到已有大文件

### 8.4 禁止行为

- ❌ 禁止一次性生成巨型文件
- ❌ 禁止把所有代码都写在一个目录或一个文件里
- ❌ 禁止在未输出拆分方案前就开始编码
- ❌ 禁止在用户未确认拆分方案前就开始编码
- ❌ 禁止在工具配置未完成前就开始编码

---

## 9. 前端代码提交前检查清单

在提交前端代码前，必须完成以下检查：

- [ ] **工具初始化检查**（参考 `.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md` 第 2 节）：
  - [ ] 工具是否已初始化？（检查 `.aodw-next/tools-status.yaml`）
  - [ ] ESLint 是否已安装并配置？
  - [ ] Prettier 是否已安装并配置？
  - [ ] TypeScript path alias 是否已配置？
- [ ] **目录结构检查**：
  - [ ] 新页面是否放在 `src/pages/<PageName>/` 下？
  - [ ] 可复用业务逻辑是否放在 `src/features/<domain>/` 下？
  - [ ] 通用组件/hooks/工具是否放在 `src/shared/` 下？
  - [ ] 依赖关系是否符合规范（pages → features/shared, features → shared）？
- [ ] **文件大小检查**（参考 `.aodw-next/03-standards/ai-coding-rules-common.md`）：
  - [ ] 页面入口组件（index.tsx）是否 ≤ 300 行？
  - [ ] 普通组件/hooks/store 文件是否 ≤ 200 行？
  - [ ] 单个函数是否 ≤ 60 行？
  - [ ] 复杂度是否 ≤ 10？
- [ ] **命名规范检查**：
  - [ ] React 组件文件是否使用 PascalCase？
  - [ ] hooks 文件是否以 `use` 开头？
  - [ ] Zustand store 是否使用 `xxx.store.ts` 命名？
  - [ ] 组件是否使用 PascalCase，变量/函数是否使用 camelCase？
- [ ] **TypeScript 规范检查**：
  - [ ] 是否启用严格模式？
  - [ ] 是否避免使用 any？
  - [ ] API 层是否使用 DTO 类型和 Response 类型？
- [ ] **React 编码规范检查**：
  - [ ] 是否使用函数组件 + Hooks？
  - [ ] 数据请求是否封装在 features/*/api 或页面专用 hooks？
  - [ ] 是否不在组件中直接调用 fetch/axios？
- [ ] **Tailwind & Radix 使用规范检查**：
  - [ ] 是否使用 className 写原子类？
  - [ ] 复杂样式是否抽离到 cn() 或封装为组件？
  - [ ] Radix UI 是否在 shared/components 中封装？
