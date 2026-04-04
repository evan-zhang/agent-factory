# cms-cwork 设计讨论日志

## v3.0.0 — Agent-First 重构 (2026-04-03)

### 背景
应 Orchestrator 指令，将 cms-cwork 从 TypeScript 源码模式重构为 **Agent-First** 架构。

### 讨论摘要

#### 重构目标
1. 6个 Python 编排脚本，替代 TypeScript 源码
2. 所有脚本输出 JSON 到 stdout
3. argparse 命令行参数处理
4. 姓名自动解析为 empId
5. 交互模式和干跑模式支持

#### 架构决策

**决策1: Python over TypeScript**
- 原因：Agent 调用 Python 脚本比 Node.js 更轻量，无环境依赖
- 影响：保留 TypeScript 源码在 `references/` 供高级用户参考

**决策2: 单一脚本单一职责**
- 6个脚本对应6个核心操作域
- 不做功能合并，保持脚本职责清晰

**决策3: JSON 输出规范**
- 所有脚本 stdout 输出 JSON
- stderr 输出调试信息（干跑预览、交互提示）
- 错误统一 `{"success": false, "message": "..."}` 格式

**决策4: 姓名自动解析**
- 所有人员参数（--to, --cc, --assignee等）自动调用 searchEmpByName API
- 如需直接传 empId，使用 --emp-id 参数

#### 文件结构
```
cms-cwork/
├── SKILL.md
├── scripts/
│   ├── cwork_client.py           # 共享客户端
│   ├── cwork-query-report.py     # 汇报查询
│   ├── cwork-query-tasks.py      # 任务查询
│   ├── cwork-review-report.py     # 审阅回复
│   ├── cwork-nudge-report.py     # 催办通知
│   ├── cwork-create-task.py      # 创建任务
│   └── cwork-submit-report.py    # 提交汇报
└── references/
    ├── api-endpoints.md          # API 端点文档
    └── api-client.md             # Python Client 参考
```

#### API 映射

| 脚本 | 主要 API |
|------|----------|
| query-report | inbox, outbox, unread, detail |
| query-tasks | searchPage, getSimplePlanAndReportInfo |
| review-report | reply, markRead |
| nudge-report | submit (type=12 催收汇报) |
| create-task | createPlan |
| submit-report | submit |

### 后续计划
- [ ] 添加单元测试
- [ ] 完善错误处理
- [ ] 添加更多汇报类型支持

---

## 历史版本讨论

### v2.1.2 (2026-03-31)
- 上一稳定版本
- TypeScript 源码模式

### v1.4.0 (更早)
- 早期版本
- 功能基础
