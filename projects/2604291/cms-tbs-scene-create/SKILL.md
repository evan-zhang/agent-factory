---
name: cms-tbs-scene-create
description: TBS训战场景创建的编排主控。当用户表达"创建场景/新建场景/开始创建/训战场景/对练场景/生成场景"时，按顺序调度 4 个原子 Skill 完成完整流程。本 Skill 只做调度和 state 管理，不生成任何业务内容。
skillcode: cms-tbs-scene-create
version: 2.0.0
dependencies:
  - cms-auth-skills
  - cms-tbs-scene-config
  - cms-tbs-scene-collect
  - cms-tbs-scene-generate
  - cms-tbs-scene-submit
---

# cms-tbs-scene-create（编排主控）

## 核心定位
编排主控，只做两件事：
1. **State 管理**：创建并维护 `state.json`，推进 currentStep
2. **步骤调度**：按顺序读取并执行 4 个原子 Skill

不生成任何业务内容，不做用户交互（交互由原子 Skill 负责）。

## 强制前置
进入编排链路前，必须先通过 `cms-auth-skills` 获取有效 TBS `access-token`。

## State 读写约定
详见项目根目录 `STATE-CONTRACT.md`。

## 编排流程

### Step 0：初始化
1. 识别用户是"执行动作"还是"纯咨询"。仅当用户表达创建意图时进入编排链路。
2. 调用 `cms-auth-skills` 获取 access-token。
3. 创建 `state.json`，写入 `config.access_token`，设置 `currentStep: "config"`。

### Step 1：配置拉取
- 读取 `cms-tbs-scene-config` 的 SKILL.md 并执行
- 完成后检查 `state.config.businessDomains` 非空
- 推进 `currentStep: "collect"`

### Step 2：信息收集
- 读取 `cms-tbs-scene-collect` 的 SKILL.md 并执行
- 完成后检查 `state.collect.title` 和 `state.collect.sceneBackground` 非空
- 推进 `currentStep: "generate"`

### Step 3：场景生成
- 读取 `cms-tbs-scene-generate` 的 SKILL.md 并执行
- 完成后检查 `state.generate.knowledgeIds` 和缺失情况
- 若有缺失知识主题：输出上报草稿，**不推进**，等待用户处理
- 若全部匹配且用户确认：推进 `currentStep: "submit"`

### Step 4：落库提交
- 读取 `cms-tbs-scene-submit` 的 SKILL.md 并执行
- 完成后检查 `state.submit.sceneDbId`
- 向用户报告最终结果

### 异常处理
- 任一步骤失败：暂停编排，向用户说明原因和建议
- 用户中断：保留 state.json，下次可从 currentStep 继续
- access-token 过期：重新调用 `cms-auth-skills`，更新 state 后重试当前步骤

## 配置与授权

### 必填配置
- **TBS access-token**：通过 `cms-auth-skills` 获取
- 4 个原子 Skill 必须已安装

### 可选配置
- **环境切换**：`TBS_ENV` 环境变量（dev/staging/prod）
- 或 `TBS_BASE_URL` 直接指定

### 配置文件位置
- state.json：由编排 Skill 在运行时创建
- 各原子 Skill 从 state.json 读取配置

## 问题反馈

- **Issue 地址**：https://github.com/xgjk/xg-skills/issues
- **标题格式**：`[cms-tbs-scene-create] 简要描述问题`
- **建议包含的信息**：
  - 失败步骤（config/collect/generate/submit）
  - state.json 中相关 section 的内容（脱敏 access-token）
  - 执行命令和完整报错输出
  - 环境：Python 版本、TBS_ENV、网络环境
