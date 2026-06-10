# 源文件到分发版本同步指南

## 1. 目录关系说明

AODW 项目中有三个 `.aodw` 目录，它们的关系如下：

```
项目根目录/
├── .aodw-next/                    ← 【源文件】Source of Truth（开发者在这里修改）
│   ├── aodw-constitution.md
│   ├── rt-manager.md
│   └── ...
│
├── templates/
│   └── .aodw-next/                ← 【分发版本】Distribution Version（打包到 CLI 安装包）
│       ├── aodw-constitution.md
│       ├── rt-manager.md
│       └── ...
│
└── cli/
    └── .aodw-next/                ← 【本地构建版本】Local Build（用于本地测试）
        ├── aodw-constitution.md
        ├── rt-manager.md
        └── ...
```

### 1.1 根目录 `.aodw`（源文件）

**位置**：项目根目录的 `.aodw-next/`

**作用**：
- **源文件（Source of Truth）**
- 开发者在这里修改和开发
- 这是唯一应该手动编辑的目录

**包含内容**：
- 所有 AODW 核心规则文件
- 模板文件
- 开发文档

### 1.2 `templates/.aodw`（分发版本）

**位置**：`templates/.aodw-next/`

**作用**：
- **分发版本（Distribution Version）**
- 用于打包到 CLI 安装包（npm 包）
- 用户安装时，CLI 会从这个目录复制文件到用户项目

**来源**：
- 从根目录 `.aodw` 同步而来
- **不应该**直接在这个目录修改

### 1.3 `cli/.aodw`（本地构建版本）

**位置**：`cli/.aodw-next/`

**作用**：
- **本地构建版本（Local Build）**
- 用于本地测试 CLI
- 运行 `cli/build-local.sh` 时会从 `templates/.aodw` 复制到这里

**来源**：
- 从 `templates/.aodw` 复制而来
- **不应该**直接在这个目录修改

---

## 2. 文件同步流程

### 2.1 开发流程

```
开发者修改
    ↓
根目录 .aodw-next/          ← 【源文件】Source of Truth
    ↓
运行同步脚本
    ↓
templates/.aodw-next/        ← 【分发版本】Distribution Version
    ↓
运行构建脚本（可选）
    ↓
cli/.aodw-next/             ← 【本地构建版本】Local Build（用于测试）
```

### 2.2 发布流程

```
根目录 .aodw-next/          ← 【源文件】
    ↓
publish.sh 自动同步
    ↓
templates/.aodw-next/        ← 【分发版本】
    ↓
publish.sh 复制到 CLI
    ↓
cli/.aodw-next/             ← 【打包到 npm】
    ↓
npm publish
    ↓
用户安装
    ↓
用户项目的 .aodw-next/      ← 【用户项目】
```

> **双版本发布**：`publish.sh` 会根据当前分支自动选择发布渠道  
> - `release/next` 或包含 `-next` 的分支 → 发布 `aodw-skill`  
> - 其他分支 → 发布 `aodw`
> - next 渠道使用独立模板目录：`templates/.aodw-next`、`templates/AODW_Adapters_next`、`templates/docs-next`

---

## 3. 如何同步文件

### 3.1 手动同步（推荐）

运行同步脚本：

```bash
# 在项目根目录运行
./sync-templates.sh
```

这个脚本会：
1. 将根目录 `.aodw` 复制到 `templates/.aodw`
2. 将根目录 `docs` 复制到 `templates/docs`
3. 更新适配器文件（从模板生成）

### 3.2 自动同步（发布时）

`publish.sh` 脚本会自动同步：

```bash
# 在 cli 目录运行
cd cli
./publish.sh patch  # 或 minor, major
```

发布脚本会：
1. 自动从根目录 `.aodw` 同步到 `templates/.aodw`
2. 从 `templates/.aodw` 复制到 `cli/.aodw`
3. 打包并发布到 npm

---

## 4. 最佳实践

### 4.1 开发时

1. ✅ **只在根目录 `.aodw` 修改文件**
2. ✅ **修改后运行同步脚本**：`./sync-templates.sh`
3. ✅ **提交更改**：包括根目录 `.aodw` 和 `templates/.aodw`

### 4.2 发布前

1. ✅ **确保已同步**：运行 `./sync-templates.sh`
2. ✅ **检查 templates/.aodw**：确保包含最新更改
3. ✅ **运行发布脚本**：`cd cli && ./publish.sh [patch|minor|major]`

### 4.3 本地测试

1. ✅ **运行构建脚本**：`cd cli && ./build-local.sh`
2. ✅ **测试 CLI**：`cd cli && node bin/aodw.js init`
3. ✅ **验证文件**：检查生成的文件是否正确

---

## 5. 常见问题

### 5.1 为什么有两个 .aodw 目录？

**原因**：
- **根目录 `.aodw`**：源文件，开发者在这里修改
- **`templates/.aodw`**：分发版本，用于打包

**好处**：
- 清晰的职责分离
- 源文件和分发版本分离
- 便于版本控制和发布管理

### 5.2 我修改了根目录的 .aodw，但用户安装的还是旧版本

**原因**：
- 没有同步到 `templates/.aodw`
- 发布时使用的是旧的 `templates/.aodw`

**解决**：
1. 运行 `./sync-templates.sh` 同步文件
2. 提交更改
3. 重新发布

### 5.3 可以直接修改 templates/.aodw 吗？

**不推荐**：
- `templates/.aodw` 应该从根目录 `.aodw` 同步而来
- 直接修改会导致源文件和分发版本不一致
- 下次同步时会覆盖你的修改

**正确做法**：
- 在根目录 `.aodw` 修改
- 运行同步脚本
- 提交更改

### 5.4 如何确保打包的是最新版本？

**检查清单**：
1. ✅ 根目录 `.aodw` 包含最新更改
2. ✅ 运行了 `./sync-templates.sh`
3. ✅ `templates/.aodw` 包含最新更改
4. ✅ 提交了所有更改
5. ✅ 运行了 `cd cli && ./publish.sh`

---

## 6. 同步脚本说明

### 6.1 sync-templates.sh

**位置**：项目根目录的 `sync-templates.sh`

**功能**：
1. 同步 `.aodw` 目录：根目录 → `templates/.aodw`
2. 同步 `docs` 目录：根目录 → `templates/docs`
3. 更新适配器文件：从模板生成适配器文件

**使用方法**：
```bash
# 在项目根目录运行
./sync-templates.sh
```

### 6.2 publish.sh

**位置**：`cli/publish.sh`

**功能**：
1. 自动同步根目录 `.aodw` → `templates/.aodw`
2. 自动同步根目录 `docs` → `templates/docs`
3. 复制 `templates/.aodw` → `cli/.aodw`
4. 打包并发布到 npm

**使用方法**：
```bash
cd cli
./publish.sh patch  # 或 minor, major
```

---

## 7. 文件同步检查清单

在发布前，确保：

- [ ] 根目录 `.aodw` 包含所有最新更改
- [ ] 运行了 `./sync-templates.sh`
- [ ] `templates/.aodw` 与根目录 `.aodw` 一致
- [ ] 适配器文件已更新（从模板生成）
- [ ] 所有更改已提交到 Git
- [ ] 运行了 `cd cli && ./publish.sh`

---

## 8. 相关文件

- **同步脚本**：`sync-templates.sh`（项目根目录）
- **发布脚本**：`cli/publish.sh`
- **构建脚本**：`cli/build-local.sh`
- **更新适配器脚本**：`cli/bin/update-adapters-from-template.js`

---

## 9. 版本历史

- **v4.0.0**：引入源文件到分发版本的同步机制
- **v4.0.1**：添加同步脚本和文档
