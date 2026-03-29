# Skills 规范校验清单

用于检查一个 Skills 包是否符合当前标准。执行时逐项核对即可。

> 本清单与 `XGJK_SKILL_PROTOCOL.md` 第四章保持同步。如有冲突，以协议文档为准。

## A. 结构与目录

- [ ] 存在 `SKILL.md`
- [ ] `SKILL.md` 包含宪章
- [ ] `SKILL.md` 包含工作流
- [ ] `SKILL.md` 包含目录树（capability tree）
- [ ] `SKILL.md` 包含模块索引表
- [ ] `SKILL.md` 包含当前版本与接口版本（如有版本约定）
- [ ] `SKILL.md` 包含能力概览（模块清单）
- [ ] `common/auth.md` 存在
- [ ] `common/conventions.md` 存在
- [ ] `openapi/common/appkey.md` 存在
- [ ] 每个业务模块都有 `openapi/<module>/api-index.md`
- [ ] 每个业务接口都有独立文档 `openapi/<module>/<endpoint>.md`
- [ ] 每个业务接口都有对应脚本 `scripts/<module>/<endpoint>.py`（`openapi/common/` 下的固定参考文档除外）
- [ ] `examples/<module>/README.md` 存在
- [ ] `scripts/<module>/README.md` 存在
- [ ] **所有脚本均为 Python（`.py`）文件**，不存在其他语言脚本

## B. 模块与目录一致性

- [ ] `SKILL.md` 能力概览中的模块名 = `openapi/` 下模块目录
- [ ] `SKILL.md` 模块索引表中的模块名 = `openapi/` 下模块目录
- [ ] `SKILL.md` 目录树（capability tree）= 实际目录结构
- [ ] `openapi/<module>/api-index.md` 中列出的接口文档都存在
- [ ] `api-index.md` 中列出的脚本路径都存在
- [ ] `examples/<module>/README.md` 与模块索引表一一对应
- [ ] `scripts/<module>/...` 与模块索引表一一对应
- [ ] 不存在未在索引表中出现的"孤立模块"或"孤立文件"

## C. 内容与一致性

- [ ] `SKILL.md` 仅作为索引（不包含完整接口参数）
- [ ] `api-index.md` 仅列接口清单与脚本映射
- [ ] 每个接口文档包含：作用、Headers、参数表、Schema、脚本映射
- [ ] 全文不存在绝对路径
- [ ] 全文不存在占位符（如 `<module>`、`<endpoint>`、`<skill-name>`）

## D. 鉴权与安全

- [ ] 鉴权优先级为：`XG_USER_TOKEN` → 上下文 token → `CWork Key`
- [ ] 业务请求仅需 `access-token`
- [ ] `common/auth.md` 与 `openapi/common/appkey.md` 的登录授权描述一致
- [ ] 不向用户泄露 token/userId/personId 等敏感字段
- [ ] `common/auth.md` 明确最小权限/白名单/生命周期/禁止落盘规则
- [ ] `common/conventions.md` 明确输入校验与日志审计要求

## E. 脚本完整性（重点！）

> 以下检查仅针对 `scripts/<module>/` 下的业务脚本。`openapi/common/` 下的固定参考文档不在此检查范围内。

- [ ] 每个业务接口都有对应 `.py` 脚本（不允许"暂无脚本"；`openapi/common/appkey.md` 除外，它是固定参考文档）
- [ ] 每个业务脚本读取环境变量 `XG_USER_TOKEN`
- [ ] 每个业务脚本的 `API_URL` 硬写完整 URL（含域名），与对应 `endpoint.md` 一致
- [ ] 每个业务脚本有 `main()` 函数和 `if __name__ == "__main__"` 守卫
- [ ] 每个业务脚本的入参字段与对应 `endpoint.md` 的参数表一致

## F. 异步、超时与重试

- [ ] 需要轮询的接口明确轮询间隔与最大次数
- [ ] 长耗时接口明确超时策略
- [ ] **接口调用/脚本执行出错时，重试间隔 ≥ 1 秒、最多重试 3 次**
- [ ] **不存在无限循环重试的逻辑**
- [ ] 超过最大重试次数后终止并上报错误

## G. 危险操作

- [ ] 存在"危险操作友好拒绝"的规则声明
- [ ] 若请求可能造成数据泄露、破坏、越权或高风险副作用，应拒绝并给出安全替代方案

## H. 输出规范

- [ ] 对用户输出最小必要信息：摘要/必要输入/链接
- [ ] 仅 `open-link` 可以输出带 token 的完整 URL
- [ ] 仅在必须时输出最小 ID（如 notebookId/sourceId）
- [ ] 不回显完整 JSON 响应
