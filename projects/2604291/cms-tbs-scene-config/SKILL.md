---
name: cms-tbs-scene-config
description: TBS场景创建 Step1：拉取训练上下文主数据（业务领域/科室/品种/产品知识）。纯 API 调用，无用户交互。
skillcode: cms-tbs-scene-config
version: 2.0.0
dependencies:
  - cms-auth-skills
---

# cms-tbs-scene-config（配置拉取）

## 核心定位
从 TBS 后台拉取主数据，写入 state.json 的 config section。无用户交互。

## 输入（从 state.json 读取）
- `state.config.access_token`（必填）
- `state.config.baseUrl`（可选，默认 dev 环境）

## 执行
```bash
python3 scripts/tbs-scene-fetch-config.py --access-token "$ACCESS_TOKEN" --base-url "$BASE_URL"
```

## 输出（写入 state.json）
- `state.config.businessDomains`：业务领域列表
- `state.config.departments`：科室列表
- `state.config.drugs`：品种列表
- `state.config.productKnowledges`：产品知识主数据列表

## 成功判定
脚本 stdout 输出 `success: true` 且 resolved 字段非空。

## 失败处理
- 脚本返回 `success: false`：向用户报告错误，不继续
- access-token 无效：提示重新鉴权

## 配置与授权
- 必填：TBS access-token（从 state.json 读取，由编排 Skill 写入）
- 可选：TBS_ENV / TBS_BASE_URL 环境变量

## 问题反馈
- Issue 地址：https://github.com/xgjk/xg-skills/issues
- 标题格式：`[cms-tbs-scene-config] 简要描述问题`
- 建议包含：脚本完整输出、access-token 前4位、TBS_ENV 值
