# CAS 巡检异常记录

**时间**：2026-04-04 09:00
**Gateway**：life
**错误类型**：工具循环检测异常

## 错误详情

```bash
[2026-04-03 19:03]
> ⚠️ 🔌 Gateway: `tools.loopDetection` failed

[2026-04-03 19:03]
> ⚠️ ✉️ Message failed

[2026-04-03 19:03]
> raise RuntimeError(f"[ERROR generating API key for cwork_client. $ | raise ValueError |
```

## ✅ 根本原因（已确认）

### 1. **接口格式错误**（非 API Key 问题）
- **误判**：最初认为 CWORK_APP_KEY 失效
- **实际原因**：`searchEmpByName` 接口需要 POST + JSON body，而非 GET + Query 参数
- **验证**：2026-04-04 09:13 测试 BP 接口正常返回数据
- **API Key 状态**：✅ `TsFhRR7OywNULeHPqudePf85STc4EpHI` **完全有效**

### 2. 工具循环检测误判
- **触发条件**：连续调用 CMS 相关工具
- **检测阈值**：过于敏感（warningThreshold=8, criticalThreshold=15）
- **业务场景**：正常的工作协同处理被拦截

### 3. Gateway 状态
- **实际状态**：✅ life gateway 运行正常（PID 39050）
- **连接状态**：✅ Telegram/Discord 连接正常
- **资源占用**：✅ 正常

## 后续建议

### 立即修复
1. **修正 Skill 中的接口调用格式**：
   ```python
   # ❌ 错误方式
   curl -GET "https://.../searchEmpByName?searchKey=张"
   
   # ✅ 正确方式
   curl -X POST -H "Content-Type: application/json" \
        -d '{"searchKey":"张"}' \
        "https://.../searchEmpByName"
   ```

2. **调整循环检测阈值**（减少误报）：
   ```json
   "loopDetection": {
     "warningThreshold": 15,    // 从 8 提升到 15
     "criticalThreshold": 25     // 从 15 提升到 25
   }
   ```

3. **监控日志**：
   ```bash
   tail -f ~/.openclaw/chat-archive/life/logs/2026-04-*.md
   ```

### 长期优化
1. **接口适配层**：
   - 统一封装 API 调用格式
   - 自动处理 POST/GET 差异
   - 添加重试机制

2. **增强错误处理**：
   - 区分接口格式错误 vs API Key 错误
   - 提供更明确的错误提示

3. **监控告警**：
   - 设置工具调用异常监控
   - 定期检查 API 接口健康状态

## 状态跟踪

| 日期 | 状态 | 处理人 | 备注 |
|------|------|--------|------|
| 2026-04-03 | 发现 | Evan | 初次出现 |
| 2026-04-04 09:00 | 诊断中 | Orchestrator | 怀疑 API Key 问题 |
| 2026-04-04 09:13 | **已确认** | Evan | **非 API Key 问题，接口格式错误** |
| 2026-04-04 | 待修复 | Orchestrator | 需调整循环检测阈值 |

---

## 📋 最终结论

**问题类型**：**接口格式错误 + 循环检测误报** ⚠️

**紧急程度**：🟡 **中等**
- ✅ **API Key 正常**：`TsFhRR7OywNULeHPqudePf85STc4EpHI` 有效
- ✅ **Gateway 正常**：life gateway 运行稳定
- ⚠️ **需修复**：调整循环检测阈值，避免误报
- ⚠️ **需优化**：统一 API 调用格式

**影响范围**：
- 不影响核心功能
- 仅监控日志出现误报
- 工作协同功能正常运行

---

*记录人：Factory Orchestrator*
*记录时间：2026-04-04 09:00*
*更新时间：2026-04-04 09:15*