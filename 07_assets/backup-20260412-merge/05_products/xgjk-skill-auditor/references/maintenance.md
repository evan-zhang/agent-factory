# 维护信息

## 基本信息

- 版本：见 `_meta.json`
- ClawHub slug：`xgjk-skill-auditor`

## GitHub 地址

- 仓库：https://github.com/evan-zhang/agent-factory
- Skill 目录：`05_products/xgjk-skill-auditor/`

## 如何提 Issue

1. 访问 https://github.com/evan-zhang/agent-factory/issues/new
2. 选择 Label：`xgjk-skill-auditor`
3. 填写：
   - **Title**：简短描述问题
   - **Body**：问题描述 + 复现步骤 + 环境信息
   - **Label**：xgjk-skill-auditor

## 如何更新

**工厂内部开发：**
1. 修改 Skill 内容
2. 更新 `_meta.json` 版本号
3. 执行 `clawhub publish`

**ClawHub 用户：**
```bash
clawhub update xgjk-skill-auditor
```

## 相关规范

- 评分维度定义：`references/scoring-rubric.md`
- 类型权重矩阵：`references/factory-weights.md`
- 安全扫描模式：`references/security-patterns.md`

---

*最后更新：2026-04-05*
