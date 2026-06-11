# bd-eval-cms 升级操作手册

> 适用场景：收到同事发来的 `CMS_投前评估体系_技能包_vX_YYYYMMDD.zip` 升级包后执行。
> 预计耗时：10~15 分钟（不含人工确认时间）。

---

## 升级前准备

1. 确认本地 `bd-eval-cms` 所在目录（`projects/2605281/bd-eval-cms/`）
2. 确认当前 Skill 版本：`cat bd-eval-cms/VERSION`
3. 备份当前 references：`cp -r bd-eval-cms/references/ bd-eval-cms/references_v{PREV_VERSION}.bak`

---

## Step 1：将 zip 包发给工厂 Agent

**发送方式**：
将 zip 文件作为附件发给工厂 Agent（当前对话），并附文字：

```
帮我升级 bd-eval-cms：
/Users/evan/.openclaw/gateways/life/state/media/inbound/{zip文件名}
```

---

## Step 2：Agent 执行 Extract + Diff

工厂 Agent 收到后会：
1. 用 Python 解压 zip（处理 macOS 中文文件名兼容问题）
2. 逐文件 diff 当前版本 vs zip 版本
3. 生成变更报告（文件级 diff 行数）
4. 判断升级类型（Major / Minor / Patch）

**你不需要做任何操作，等待报告即可。**

---

## Step 3：审阅变更报告

Agent 会输出如下格式的变更报告：

```
## {升级包文件名} vs 当前版本 v{X.Y.Z}

变更类型：Major / Minor / Patch

### 新增文件（N个）
...

### 重大变化文件（M个 diff超过200行）
- A-2_bd-cn-agency-rights.md: 668行 diff
- D-1_pharma-bd-due-diligence.md: 512行 diff
...

### 常规变化文件（K个 diff 50~200行）
...

### 小变化文件（L个 diff <50行）
...

建议版本更新：{X.Y.Z} → {X.Y'.Z'}（{Major/Minor/Patch}）
```

**你需要判断**：
- 变更报告是否符合预期？
- 版本号变化是否合理？
- 有没有不认识的技能文件（可能是同事新增的维度）？

---

## Step 4：确认执行升级

**回复** `确认` → Agent 执行替换 + 版本更新 + git commit

**回复** `取消` → 不做任何修改

**回复** `只看 XXX 文件 diff` → Agent 输出指定文件的详细 diff

---

## Step 5：升级后验证

Agent 完成后会自动输出：

```
✅ 升级完成
- 新版本：v{NEW}
- 变更文件：{N}个
- 备份位置：references_v{PREV_VERSION}.bak/

接下来建议：
1. [运行 E2E 测试] — 验证新模板是否正常工作
2. [查看详细 diff] — 关注 {具体文件} 的变化内容
```

---

## 升级类型判断标准

| 类型 | 判断标准 | 版本变化 |
|------|---------|---------|
| **Major** | Gate 编号变了、模板数量变了、框架层文件（SKILL.md/SOP/总规则）有重大变化 | X.Y.Z → X'.Y.Z（主版本+1） |
| **Minor** | 多个模板内容更新、规范文件有变化 | X.Y.Z → X.Y'.Z（次版本+1） |
| **Patch** | 单个或少量模板修复性更新 | X.Y.Z → X.Y.Z'（修订号+1） |

---

## 常见问题

**Q: zip 包里有 EXECUTION.md 和主 SKILL.md 以外的文件，也会被更新吗？**
A: 会。Agent 会 diff 所有 .md 文件，只要和当前目录里的不同，就会列出变更。但 EXECUTION.md 如果在 zip 里，Agent 会提示你确认是否替换（因为 EXECUTION.md 是操作层，通常不应该随着模板包更新）。

**Q: 发现升级包里的某个模板不应该更新，能跳过吗？**
A: 能。在 Step 4 确认时告诉 Agent "跳过 A-2 和 D-1"，Agent 会在执行替换时排除这两个文件。

**Q: 升级后发现新版本有问题，怎么回滚？**
A: `cp -r references_v{PREV_VERSION}.bak/ references/` 恢复备份，然后 `git log` 找到升级前的 commit，用 `git checkout {commit-hash} -- projects/2605281/bd-eval-cms/` 恢复 git 历史。
