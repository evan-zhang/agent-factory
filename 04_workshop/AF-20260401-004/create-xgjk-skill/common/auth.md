# 认证与鉴权（统一前置规则）

## 1. Token 获取流程（严格短路优先级）

> **⚠️ 核心规则：一旦在某个优先级获取到 token，必须立即停止，不得继续往下执行后续优先级，更不得向用户询问任何鉴权相关问题。**

```
开始
 │
 ├─ 优先级 1：检查环境变量 XG_USER_TOKEN
 │   ├─ 有值 → 直接作为 access-token 使用，【立即停止，不再往下】
 │   └─ 无值 → 继续
 │
 ├─ 优先级 2：检查上下文中的 token / xgToken / access-token
 │   ├─ 有值 → 直接使用，【立即停止，不再往下】
 │   └─ 无值 → 继续
 │
 └─ 优先级 3（最后手段）：向用户索取 CWork Key 并调用鉴权接口换取 token
     └─ 仅在优先级 1 和 2 都无值时才执行此步骤
     └─ 鉴权接口：
        GET https://cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey={CWork Key}
        返回字段映射：data.xgToken → Header access-token
        接口文档：../openapi/common/appkey.md
```

**关键强调**：
- **环境变量存在 = 鉴权已完成**。有 `XG_USER_TOKEN` 就直接用，不要再问用户任何鉴权问题
- **禁止跳级**：不允许跳过优先级 1 直接去问 CWork Key
- **禁止多余确认**：不要向用户确认"你的 token 是否有效"，直接使用即可
- **禁区**：禁止向用户索取或解释 token 细节。对外只暴露 **CWork Key 授权动作**（且仅在优先级 3 时）

## 2. 强约束

- 所有业务请求仅需传递 `access-token`（它是 CWork Key 授权后的唯一凭证）。
- 建议对鉴权结果做**会话级缓存**，避免重复换取。
- **脚本层面**：`scripts/<module>/<endpoint>.py` 通过 `os.environ.get("XG_USER_TOKEN")` 读取环境变量，环境变量有值则直接使用，不存在则报错退出。

## 3. 权限与生命周期（安全要求）

- **最小权限**：仅使用当前任务所需能力范围，不扩展权限范围。
- **权限白名单**：对外能力应按模块/接口/动作做白名单控制。
- **生命周期**：token 仅用于会话期内使用，过期需重新获取。
- **禁止落盘**：`access-token` 不得写入文件或日志，仅允许内存级缓存。
