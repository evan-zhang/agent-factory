# spec-contract-delivery

将模糊需求转化为可执行、可验证、可验收的需求契约，按 Spec-Driven Development + Contract Verification 流程指导 AI 编程 Agent 完成交付。

## 安装

```bash
# 方式一：git sparse-checkout
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605262/spec-contract-delivery

# 方式二：ClawHub
clawhub install spec-contract-delivery
```

安装后将 Skill 目录复制到 Agent 的 skills 目录即可。

## 使用

给 Agent 的指令：

> 请使用 spec-contract-delivery skill 处理这个开发需求。不要直接写代码，先生成需求契约、技术方案和开发任务，然后再实现并输出交付验证报告。
