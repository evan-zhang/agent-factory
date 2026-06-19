## 评审结论

**总体评级**：FAIL

**评审对象**：C 类代码改动 — Link Archivist v2.0.0 / KB Graph v0.3.2 合并（lib/kb_index/ + scripts/ + 配置/版本同步）
**评审时间**：2026-06-19
**设计基准**：projects/2604131/link-archivist/docs/MERGE_PLAN_v2.md（v2.1 PASS）

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|---|---|---|
| 正确性 | 2 | 手写 YAML 解析器无法解析 relationships 嵌套结构，污染 entries.json 并令 build_graph.py 崩溃；archive_report.py 缺 `--tags`，与设计文档强制规定的调用命令冲突 |
| 安全性 | 4 | fcntl 锁 + 原子写到位，凭证从环境变量读取，无注入/越权迹象，只写 archive_dir |
| 健壮性 | 3 | dirty/自愈、归档不阻塞设计良好，但坏 relationships 静默扩散、orphan 仅比对 basename 易漏判 |
| 可维护性 | 3 | 两套图谱构建逻辑并存（derive_graph_data vs build_graph_from_entries）；手写 YAML 解析器脆弱；--setup 把 `_migration_*` 写入 config |
| 测试覆盖 | 2 | 7/7 通过但完全未覆盖 relationships、--tags、build_graph、force-llm，恰好漏掉本次两处 release-blocking 缺陷 |

---

**关键问题**（最多 5 个）

1. [严重度：高] `parse_frontmatter.parse_yaml_frontmatter` 无法解析 relationships 的 list-of-dict 结构 —— 实测仅把首行 `- type: reference` 当成字符串收集，得到 `relationships: ["type: reference"]`，丢失 target/description。该坏数据写入事实源 entries.json 后，`build_graph.py` 直接抛 `'str' object has no attribute 'get'`，`kb_lint` 的 dangling-ref 检测也失效。phase3/report 模板均要求 LLM 输出 relationships，真实归档必然触发。→ 修复建议：改用 `yaml.safe_load`（或正确实现嵌套解析），并在 parse_entry 中校验 relationships 为 list[dict]，非法则降级为 []。

2. [严重度：高] `archive_report.py` 未实现 `--tags` 参数，但 `references/phase3-prompt-template.md` §Orchestrator 实现明确要求 orchestrator 调用 `archive_report.py ... --tags '[...]'`。实测传 `--tags` 导致 argparse 退出码 2，归档主流程整体失败。→ 修复建议：新增 `--tags` 参数并写入 frontmatter；或同步修正设计文档移除该参数（二者口径必须一致）。

3. [严重度：中] tags 永不落盘：archive_report.py 生成 YAML 头时硬编码 `tags: []`，既不接收也不写入 tags。即便 Phase 3 产出 tags，新归档的 entry tag 覆盖率恒为 0，按 tag 建边/检索能力对增量归档失效。→ 修复建议：与问题 2 合并修复，将 tags 真正写入 frontmatter 头。

4. [严重度：中] 图谱构建存在两条不一致路径：增量路径用 `update_single.derive_graph_data`（忽略 relationships，故不崩），全量重建用 `build_graph.build_graph_from_entries`（处理 relationships，故在坏数据上崩）。导致"增量正常、全量报错"的隐蔽不一致，且 relationship 边只在全量出现。→ 修复建议：统一为单一图谱构建实现，修复问题 1 后回归全量重建。

5. [严重度：低] `lint.detect_orphan_files` 用 `Path(path).name` 仅按文件名比对，跨月份目录同名文件会被误判为已索引（漏判 orphan）。→ 修复建议：改为按 archive 相对路径（entries 的 key）比对。

---

**最重要的一条建议**

先修问题 1（relationships 解析）—— 它污染事实源 entries.json 并令已发布的 build_graph.py/kb_lint 在真实数据上崩溃；同时补一条覆盖 relationships + 全量重建的测试，避免同类缺陷再次从 7/7 绿测中漏过。

---

备注：版本号 6 处同步全部正确（LA 2.0.0×3 / kb-graph 0.3.2×3），kb-graph deprecation 头到位，改动范围未越界（被评审改动均落在限定路径内）。问题 1/2 属代码层根因缺陷且测试未覆盖，故评 FAIL，建议回 S4 修复后重做 C 类复评。
