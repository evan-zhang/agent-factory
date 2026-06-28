# DESIGN - Link Archivist

## 1) 目标

- **解决**：外部资料（URL/文件/文本）的采集、调研、归档、索引、查询一体化管理
- **解决**：手工项目文档的归档沉淀（M 编号），与外部资料（K 编号）区分
- **不解决**：渠道发送（Agent 自行决定）、文件解析（PDF/Word/PPT 由 md2md 处理）、跨设备同步、wiki 主题页合成（memory-wiki 插件）

## 2) 用户体验目标

- **无感知目标**：用户发链接后立即收到"已安排后台处理"通知，不阻塞主对话；sub-agent 完成后自动汇报
- **失败兜底**：Phase 2 抓取失败 → 降级处理（references/degradation-rules.md）；Phase 4 验证失败 → 循环补充直到通过；mode=ask → 问用户
- **进度可见**：每个 Phase 发送进度提示，用户可据此监督和干预

## 3) 核心流程

```
输入（URL/文件/文本/手工文档）
  → Phase 1: 初始化配置检测
  → Phase 2: 抓取内容 + 模式判定（full/short/ask）
  → Phase 3: 执行调研 + 生成报告
  → Phase 4: 报告验证（validate_report.py）
  → Phase 5: 归档 + 索引（archive_report.py）
  → 输出：归档文件（K/M 编号）+ 增量索引
```

关键路径：Phase 1-5 阻塞式管线，禁止跳步，每步有门控条件。

执行模式：
- sub-agent 模式（推荐）：主 Agent spawn worker，不阻塞对话
- 直接执行模式：主 Agent 自行执行，适合调试

## 4) 风险与防护

| 风险 | 防护 |
|------|------|
| Agent 绕过脚本手拼 frontmatter | 强制 archive_report.py 执行，脚本重写 frontmatter |
| 索引文件损坏 | SHA256 校验 + dirty flag + 自愈机制 |
| 多文件索引并发写 | 原子写（tmp → rename） |
| 视频下载失败阻塞流程 | 抖音失败不阻塞，YouTube 失败报错 |
| 归档日期用 LLM 推断 | 强制 datetime.now()，禁止 LLM 生成时间 |
| 配置迁移丢数据 | .bak 备份不删除 |

## 5) 版本策略

- 当前版本：2.6.1
- 升级原则：向后兼容，archive_dir 结构不变；增量索引基于 SHA256 自动检测变更
- 版本号两处同步：VERSION 文件、version.json（不写入 SKILL.md frontmatter）

## 6) 关键决策记录

- v2.0：KB Graph 合并入 Link Archivist（原独立 Skill），统一索引
- v2.5：OKF 对齐评估完成，保守定位为 OKF-style，不承诺 full compliance
- v3.0 living wiki：**不做**，OpenClaw memory-wiki 插件已覆盖，按工厂红线不造轮子
- frontmatter 由 archive_report.py 强制生成，禁止 Agent 手拼（v2.5.0+ 纪律）
