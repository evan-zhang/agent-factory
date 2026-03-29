# 已加载 upgrade-rules.md

## 触发条件

执行中发现以下任一情况，调用 `scripts/upgrade.py`：
1. 预计耗时超过 20 分钟
2. 涉及 ≥ 2 个系统
3. 需要多轮人工确认
4. 需要发布/重启等高影响操作
5. 涉及跨 gateway 协作
6. 需要完整审计链路

---

## upgrade.py 执行步骤

1. 验证：读取 Lite 实例 state.json，确认 `mode=lite` 且 `status` 非 DONE/ARCHIVED
2. TASK.md：在顶部插入继承声明区
3. LOG.md：所有内容行前加 `[继承自Lite]` 标记，追加分隔线
4. 创建：PLAN.md / DECISIONS.md / ARTIFACTS.md（从 full/ 模板）
5. 更新 state.json：
   - `mode: "full"`
   - `status: "DISCUSSING"`
   - `upgradedFrom: "<原lite实例id>"`
   - `confirmCount: 0`
   - `resume.nextAction: "补充 PLAN.md 执行计划"`
6. 原 Lite 实例 state.json 的 status 设为 `UPGRADED`

---

## 继承声明区格式

```markdown
## 继承声明

- **升级自**：{{原lite实例ID}}
- **升级时间**：{{createdAt}}
- **升级原因**：{{reason}}
- **继承文件**：TASK.md、LOG.md

> 原 Lite 实例：[{{原lite实例ID}}]({{原lite实例路径}})
```

---

## 注意事项

1. **不删除原 Lite 实例**：原实例 status 设为 UPGRADED，保留可审计
2. **Full 实例 status 重置为 DISCUSSING**：让用户重新规划执行路径
3. **confirmCount 重置为 0**：新 Full 实例从零开始确认计数
4. **升级只升一次**：Full 实例不能再升级
