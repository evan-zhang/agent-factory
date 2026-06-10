# AI 知识规则摘要

## 1. 文档分类

- **Spec 文档**：spec.md / rt-lite.md（需求定义）
- **Plan 文档**：plan.md / rt-lite.md §2（实现方案）
- **过程文档**：impact.md / invariants.md / tests.md / changelog.md
- **知识文档**：模块 README / modules-index.yaml

## 2. Spec-Lite 的 rt-lite.md

不再创建独立的 spec-lite.md 和 plan-lite.md，全部整合在 rt-lite.md 中。

## 3. 文档同步原则

- 代码改动后必须同步更新相关文档
- 文档与代码不一致视为 Bug
- RT 完成前必须执行知识蒸馏（更新模块文档和 modules-index.yaml）

## 4. 知识蒸馏（RT 完成前提）

合并前必须：
1. 读取 modules-index.yaml 找到受影响模块
2. 更新对应模块 README
3. 确认文档反映最新代码状态
