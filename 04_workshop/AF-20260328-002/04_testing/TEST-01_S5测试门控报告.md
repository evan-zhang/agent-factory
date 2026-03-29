# TEST-01 S5 测试门控报告 — AF-20260328-002 cms-sop

- **项目 ID**：AF-20260328-002
- **阶段**：S5 TESTING
- **文档状态**：FINAL
- **版本**：v1.0
- **测试人**：工厂调度员（自测，做一遍审一遍）
- **测试时间**：2026-03-29T09:51~09:55+08:00

---

## 测试结果总览

| 测试编号 | 测试内容 | 结果 | 备注 |
|---|---|---|---|
| T01 | Lite 实例创建（四件套+state.json）| ✅ PASS | mode=lite，所有字段正确 |
| T02a | 状态推进到 PLAN | ✅ PASS | |
| T02b | 未完成确认单时进入 RUNNING 被拒绝 | ✅ PASS | 门控生效 |
| T02c | 确认单完成后正常进入 RUNNING | ✅ PASS | |
| T02d | DONE 不带 --confirm 被拒绝 | ✅ PASS | 高风险门禁生效 |
| T02e | 带 --confirm 正常归档 | ✅ PASS | |
| T03 | Full 实例创建（七件套+state.json）| ✅ PASS | mode=full，confirmCount=0 |
| T04 | 多轮确认：3轮触发介入提示 | ✅ PASS | JSON 中文正常显示（修复后）|
| T05 | Lite→Full 升级：文件继承+state迁移 | ✅ PASS | 七件套完整，继承声明正确 |
| T05b | 已升级实例再次升级被拒绝 | ✅ PASS | mode=full 验证生效 |
| T06 | handover.py 交接流程 | ✅ PASS | HANDOVER_PENDING + owner 切换 |
| T07a | upgrade 已DONE实例被拒绝 | ✅ PASS | status 验证生效 |
| T07b | 不存在的实例路径报错 | ✅ PASS | 清晰错误信息 |
| T07c | wait-user action + waitingFor 字段 | ✅ PASS | resume 字段正确更新 |
| T07d | increment-confirm 中文输出 | ✅ PASS | ensure_ascii=False 修复 |
| T08 | 7个模板文件完整性 | ✅ PASS | 占位符均存在 |
| T09 | 继承声明重复问题 | ✅ PASS | 确认为假阳性，无问题 |

**全部 17 项测试通过。**

---

## 修复记录（测试中发现并修复）

| 编号 | 问题 | 修复 |
|---|---|---|
| BUG-01 | increment-confirm JSON 中文被 unicode 转义 | update_state.py 加 `ensure_ascii=False` |
| BUG-02 | Lite TASK 模板有"继承声明"占位区，升级后出现两个声明块 | 删除模板中的占位区，由 upgrade.py 动态插入 |

---

## 验收结论

**✅ S5 通过，可进入 S6 发布**

---

*S5 测试完成 | 2026-03-29T09:55:00+08:00*
