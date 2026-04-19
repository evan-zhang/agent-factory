# DESIGN - cas-chat-archive

## 1) 目标
- 将聊天内容与附件进行 append-only 归档，支持后续检索与审计。
- 支持多 gateway 独立归档，并逐步支持按 agent 隔离归档。

## 2) 边界（不做什么）
- 不做智能知识库推理（只做归档与基础检索）。
- 不替代主业务回复链路（归档失败默认 fail-soft，不阻断用户体验）。

## 3) 用户体验目标
- 用户无感知：不需要额外手工操作。
- 性能可接受：归档动作不明显影响回复体验。
- 可解释：用户可随时问“今天备份了多少”“是否已备份”。

## 4) 核心流程
1. Gateway 事件触发（message:preprocessed / message:sent）
2. Hook 组装 payload（含白名单附件）
3. `record-bundle` 一次写入 inbound/outbound + assets
4. 更新会话状态与日志
5. 可通过 `cas_inspect.py` 做 report/search 查询

## 5) 安全与稳定策略
- Gateway 名称校验，防止路径逃逸。
- 附件路径白名单（默认 gateway uploads + state/media）。
- 并发写入锁 + 原子状态文件写入。
- 磁盘阈值控制（warn/min）。
- 默认 fail-soft，避免影响用户正常聊天。

## 6) 版本策略
- 当前：v1.1.0-test（已实现 agent 隔离能力与手动复盘工具，处于灰度测试）
- 稳定目标：v1.1.0（完成四网关真实流量验收后转正）
