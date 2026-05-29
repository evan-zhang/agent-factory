# CMS 投前评估流水线（bd-eval-cms）

> 康哲药业专属 BD 投前评估体系，基于 19 个技能 + 6-Gate 门控。

## Skill 组成

| Skill | 路径 | 必需 | 说明 |
|-------|------|------|------|
| bd-eval-cms | bd-eval-cms/ | ✅ | 主流水线 |
| doc-viewer | dependencies/doc-viewer/ | ✅ | HTML 报告生成 |
| multi-search | dependencies/multi-search/ | ✅ | 搜索基础设施 |

## 安装

```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605281/bd-eval-cms
```

## 版本

0.1.0（初始版本，从 2605152 迁移）
