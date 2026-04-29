---
name: cms-tbs-scene-create
description: 提供【TBS场景创建】全流程编排能力(Step1-4)。当用户表达"创建场景/新建场景/开始创建/训战场景/对练场景/生成场景"时,按 references/step1-4 编排并在用户确认且知识齐全后落库。本 Skill 通过依赖 `cms-auth-skills` 获取 `AppKey` 并完成鉴权后,才允许进入脚本调用链路。
skillcode: cms-tbs-scene-create
github: https://github.com/xgjk/xg-skills/tree/main/cms-tbs-scene-create
dependencies:
  - cms-auth-skills
version: 1.0.1
---

# cms-tbs-scene-create

## 核心定位
本 Skill **只做编排**:按 `references/step1-4/*.md` 组织用户交互。Step3 先确认基础信息;Step4 先生成场景草稿,再确认产品知识主题,最后在条件满足时调用脚本完成落库。

## 强制前置(必须遵循)
调用任何 `scripts/*.py` 前,必须先通过依赖 Skill `cms-auth-skills` 获取有效 TBS `access-token`,
并先读取 `references/auth.md`,确认鉴权前置与注入方式。
并按脚本入参注入到命令参数中(例如:`--access-token "$ACCESS_TOKEN"`)。
未鉴权时,不允许执行任何 Python 脚本。

## 标准执行流程(必须遵循)
1. 识别用户是"执行动作"还是"纯咨询"。仅当用户表达创建意图时进入该 Skill 编排链路。
2. Step1-4 编排:
   - Step1:读取 `references/step1/tbs-scene-fetch-config.md`
   - Step2:读取 `references/step2/interaction-echo-confirmation.md`
   - Step3:读取 `references/step3/tbs-scene-validate.md`,校验通过后生成并确认 `title + sceneBackground`(规则见该文件 passed=true 分支)
   - Step4.1:读取 `references/step4/tbs-knowledge-topic-generate.md`(仅在 `title + sceneBackground` 已确认后执行),基于"医生核心顾虑+代表目标"生成 2-4 条产品知识主题,回显给用户逐条确认/可修改
   - Step4.2:将用户最终确认主题按"科室+品种+主题"做存在性匹配,存在则写入 `knowledgeIds`,缺失则进入上报并阻断落库
3. 若 Step4.2 触发"产品知识缺失上报":
   - 不调用落库脚本
   - 输出"工作汇报草稿(上报载荷字段)/本次不允许落库"
4. 若产品知识全部存在且用户明确确认提交:
   - 读取 `references/step4/tbs-scene-create.md`
   - 执行:`python3 scripts/tbs-scene-create.py --params-json "<当前会话拼装的入参>" --access-token "$ACCESS_TOKEN"`

## 配置与授权

### 必填配置
- **TBS access-token**:通过依赖 Skill `cms-auth-skills` 获取,不可手动输入或从环境变量读取
- 详细鉴权规则见 `references/auth.md`

### 可选配置
- **环境切换**：通过环境变量 `TBS_ENV` 指定运行环境
  - `TBS_ENV=dev`：测试环境（默认）
  - `TBS_ENV=staging`：预发布环境
  - `TBS_ENV=prod`：生产环境
  - 也可通过 `TBS_BASE_URL` 直接指定完整地址（优先级低于 `--base-url` 参数）
- `--base-url`：直接指定 TBS 后台地址（命令行参数，优先级最高）

### 无需配置即可用的能力
- Step3 校验(`tbs-scene-validate.py`)不依赖 access-token,可在无鉴权状态下运行

### 配置文件位置
- 脚本内置默认 base-url,无需额外配置文件
- access-token 通过 Skill 调用链自动注入

## 问题反馈

- **Issue 地址**:https://github.com/xgjk/xg-skills/issues
- **标题格式**:`[cms-tbs-scene-create] 简要描述问题`
- **建议包含的信息**:
  - 重现步骤(Step1-4 哪一步出错)
  - 相关脚本名称(`tbs-scene-fetch-config.py` / `tbs-scene-validate.py` / `tbs-scene-create.py`)
  - 执行命令和完整报错输出
  - access-token 是否已正常获取(脱敏后提供前4位即可)
  - 环境:Python 版本、网络环境(内网/外网)

