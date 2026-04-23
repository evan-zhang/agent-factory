执行提示词：

输入：
产品名称：{产品名称}
产品类型：上市前 / 已上市
执行日期：2026-04-23

请依次执行以下 17 个 SP/BP 规划模块，不要并行执行，不要合并不同模块的输出结果，不要跨模块修改其他模块的输出文件。

全局执行要求：
1. 所有模块共享同一组输入参数：
 - 产品名称
 - 产品类型
 - 执行日期
2. 必须先读取对应 Skill 目录下的 SKILL.md 获取方法论，再读取 references/*.md 获取行业数据参考。
3. 每个模块执行时，必须读取所有上游模块已完成报告的结论和关键发现作为上下文输入。上下文通过读取输出目录下已完成的报告文件获取。
4. 每个模块的输出必须严格遵循7部分标准结构：分析目标（表格）→ 工具与方法（2.1/2.2/2.3）→ 推导过程（3.1/3.2/3.3）→ 关键发现（F1-FN）→ 结论（表格）→ 待讨论点 → 数据来源（表格）。
5. 只做分析、推导、记录、写入文件；不做最终战略决策，决策权归用户。
6. 每个模块只写入自己的输出文件到固定目录，不修改其他模块的文件。
7. 如果某个数据缺失，标注缺口来源和已尝试的获取渠道，给出基于合理假设的分析，并在待讨论点中明确标注。不因数据缺失停止执行。
8. 每个模块完成后，简要向用户汇报核心结论和待讨论点，等待用户确认后再继续下一个模块。
9. 输出目录统一为：_runtime/projects/2604231/{产品名称}/
10. 运行日志统一记录到：_runtime/projects/2604231/{产品名称}/runlog.json

请按以下顺序逐个执行：

=== Part1 市场洞察 ===

1. 使用 innovative-drug-market-definition（Skill目录：projects/2604231/innovative-drug-market-definition/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_市场定义_{日期}_v1.md

2. 使用 innovative-drug-competition-and-winning（Skill目录：projects/2604231/innovative-drug-competition-and-winning/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_竞争分析_{日期}_v1.md

3. 使用 innovative-drug-policy-analysis（Skill目录：projects/2604231/innovative-drug-policy-analysis/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_政策环境_{日期}_v1.md

4. 使用 innovative-drug-market-segmentation（Skill目录：projects/2604231/innovative-drug-market-segmentation/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_市场细分_{日期}_v1.md

5. 使用 innovative-drug-positioning-and-messaging（Skill目录：projects/2604231/innovative-drug-positioning-and-messaging/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_产品定位_{日期}_v1.md

6. 使用 innovative-drug-leverage-points（Skill目录：projects/2604231/innovative-drug-leverage-points/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_杠杆点_{日期}_v1.md

--- Part1 完成后，向用户汇报整体市场洞察结论，等待确认 ---

=== Part2 战略规划 ===

7. 使用 innovative-drug-brand-vision（Skill目录：projects/2604231/innovative-drug-brand-vision/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_品牌Vision_{日期}_v1.md

8. 执行五年目标模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_五年目标_{日期}_v1.md

9. 使用 innovative-drug-strategic-pillars（Skill目录：projects/2604231/innovative-drug-strategic-pillars/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_战略支柱_{日期}_v1.md

--- Part2 完成后，向用户汇报战略方向，等待确认 ---

=== Part3 增长规划 ===

10. 使用 innovative-drug-continuous-growth（Skill目录：projects/2604231/innovative-drug-continuous-growth/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_增长举措_{日期}_v1.md

=== Part4 年度BP ===

11. 执行年度目标模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_年度目标_{日期}_v1.md

12. 执行必赢策略模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_必赢策略_{日期}_v1.md

13. 执行整合OKR模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_整合OKR_{日期}_v1.md

14. 执行部门计划模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_部门计划_{日期}_v1.md

15. 执行财务PnL模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_财务PnL_{日期}_v1.md

=== Part5 衡量监控 ===

16. 使用 innovative-drug-metrics-and-standards（Skill目录：projects/2604231/innovative-drug-metrics-and-standards/）
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_指标体系_{日期}_v1.md

17. 执行触发机制模块
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_触发机制_{日期}_v1.md

=== 整合 ===

全部17个模块执行完成后，整合所有模块的核心结论和关键发现，生成最终报告：
 输出文件：_runtime/projects/2604231/{产品名称}/{产品名称}_SPBP完整规划_{日期}_v1.md

最终只简要告诉我：
1. 17个模块报告是否都已生成
2. 最终整合报告是否已生成
3. runlog.json 是否完整记录了所有模块状态
4. 有无模块标注了数据缺口需要补充
