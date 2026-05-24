# Ralph Loop v3 改造方案（修订版）

> 基于 autoresearch 设计思想 + Codex 第一轮审核反馈修订。
> v3.0.0 范围：变更 1 + 2 + 4（拆分文件 + verify.sh + Simplicity Criterion）
> 变更 3（state 简化）和变更 5（NEVER STOP）留后续版本。

---

## 一、v3.0.0 变更清单

### 变更 1：拆分 SKILL.md → SKILL.md + PROTOCOL.md

**做什么**：
- `PROTOCOL.md`：核心循环协议，只讲规则。Agent 每次迭代只读这个文件。
- `SKILL.md`：入口文件，保留安装、配置、模式选择、决策树。循环细节指向 PROTOCOL.md。

**PROTOCOL.md 结构**（约 120 行）：
1. 文件权限（可修改 vs 只读）
2. 循环规则（读状态 → 执行 → 验证 → commit 或 reset → 记录 → 下一轮）
3. 评估标准（verify.sh 输出解读）
4. Simplicity Criterion
5. 结果记录格式（results.tsv）
6. 反模式（什么时候该停止）

**上下文注入方式**：每次迭代，Runner 将三个文件拼成 prompt：
1. `PROTOCOL.md` — 循环规则（固定，每轮相同）
2. `state.json` — 当前状态（每轮不同）
3. `PROMPT.md` — 任务描述（固定，每轮相同）

PROTOCOL.md 是规则来源，不是唯一输入。

**注意**：v3.0.0 中 PROMPT.md 是只读的（被 hash 保护）。自主者模式如果需要更新任务描述，应写入工作目录中的其他文件（如 `NOTES.md`），而不是修改 PROMPT.md。

**风险**：低。纯文件拆分。

---

### 变更 2：引入 verify.sh（只读评估器）

**做什么**：
每个 Ralph Loop 任务提供一个 `verify.sh`，定义验证标准。Runner 在循环前计算文件 hash，循环后校验——如果 hash 变了说明 Agent 篡改了验证器，该轮自动判为失败。

**verify.sh 规范**：

输入：无（从工作目录读取代码）
输出：**最后一行**必须是 JSON，格式固定：
```json
{"status":"PASS","score":0.234,"details":"3/3 tests passed"}
```
或：
```json
{"status":"FAIL","score":1.0,"details":"tsc --noEmit exit 1"}
```

退出码：0 = 整体验证通过，1 = 失败

**score 约定**：
- 统一"越小越好"（0 = 完美，类似 loss）
- 对于无连续分数的任务（如"全部通过/不通过"），PASS 时 score=0，FAIL 时 score=1
- score 用于跨迭代比较效果

**只读保护机制**（Runner 实现）：

保护范围：`verify.sh`、`PROMPT.md`、`PROTOCOL.md` 三个文件均不可修改。

```bash
# macOS 兼容的 hash 函数
file_hash() {
  if command -v sha256sum &>/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

# 循环前：计算三个只读文件的 hash，存入临时文件
CHECKSUM_FILE=$(mktemp /tmp/ralph-checksums-XXXXXX)
for f in verify.sh PROMPT.md PROTOCOL.md; do
  echo "$f $(file_hash "$f")" >> "$CHECKSUM_FILE"
done

# ... Agent 执行 ...

# 循环后：校验
TAMPERED=0
while IFS=' ' read -r f expected_hash; do
  actual_hash=$(file_hash "$f")
  if [ "$actual_hash" != "$expected_hash" ]; then
    echo "⚠️  $f 被篡改，本轮自动判为失败"
    git checkout -- "$f"  # 恢复
    TAMPERED=1
  fi
done < "$CHECKSUM_FILE"
rm -f "$CHECKSUM_FILE"

if [ "$TAMPERED" -eq 1 ]; then
  # 回滚本轮全部改动：staged + unstaged + untracked
  git reset --hard HEAD
  git clean -fd
  # 写入 results.tsv：篡改 = 本轮失败
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${iteration}" "${score_before}" "${score_before}" "crash" "0" "只读文件被篡改，全部回滚" >> results.tsv
  continue  # 跳过本轮，不执行后续验证和 commit
fi
```

**模板和生成**：
提供 `references/verify-template.sh`，降低每个任务的启动成本。模板包含：
- 基本的 test/lint 调用框架
- JSON 输出格式
- score 计算占位符
- macOS 兼容的 hash 检测函数

**风险**：中。增加启动成本（需要准备 verify.sh），但提供模板降低门槛。

---

### 变更 4：Simplicity Criterion

**做什么**：
在 PROTOCOL.md 中加入简化准则，作为每次迭代的评估维度之一。

**规则**：
- 删代码且验证通过 → 必须保留（简化胜利）
- 同样效果但更简单 → 保留
- 新增代码 + 微小改善 → 撤回（但阈值不硬编码，由 verify.sh 的 score 语义决定）

**不硬编码阈值**（Codex 审核反馈）：
原方案"新增 10 行且 score 改善 < 0.01 → discard"太死板。不同任务的 score 量级不同（有的任务 score 在 0-1，有的在 100-1000）。

改为：PROTOCOL.md 中描述原则，具体阈值由任务在 PROMPT.md 中配置（可选，不配则只看 PASS/FAIL）。

**results.tsv schema**（每次迭代由 Runner 自动写入）：
```
iteration\tscore_before\tscore_after\tstatus\tdiff_stat\treason
1\t0.000\t0.234\tkeep\t+12/-3\tbaseline
2\t0.234\t0.198\tkeep\t+5/-8\t简化 attention 层
3\t0.198\t0.245\tdiscard\t+45/-2\t复杂度增加但 score 恶化
```

字段说明：
- iteration：迭代编号
- score_before：改动前的 verify.sh score
- score_after：改动后的 verify.sh score
- status：keep / discard / crash
- diff_stat：`git diff --stat` 摘要（+行/-行）
- reason：一句话说明为什么保留或撤回（由 Agent 填写）

**实现方式**：
Runner 不强制执行 Simplicity Criterion。它是 PROTOCOL.md 中的指导原则，由 Agent 自行判断。这和 autoresearch 一样——Simplicity Criterion 是给 Agent 读的，不是硬编码的规则。

**风险**：低。

---

## 二、不变的部分（v3.0.0 保持 v2.0.0 现状）

- **ralph-loop.sh**：继续用 bash + python3，不重写。v3.1.0 再考虑 Python runner。
- **state.json**：保持 v2 的完整结构，不砍字段。变更 3 留后续版本。
- **双模式**：执行者模式 + 自主者模式继续保留。
- **journal**：保留 v2 的 journal 格式。不砍掉也不外置。
- **MAX_ITERATIONS**：默认 20，保持安全上限。NEVER STOP 留 v4.0.0。

**为什么保守**：Codex 审核指出砍 journal、砍 route、砍 state 字段会削弱自主者模式。v3.0.0 聚焦三个低风险高价值的变更，先落地验证效果。

---

## 三、v3.0.0 新增文件清单

| 文件 | 用途 |
|------|------|
| `PROTOCOL.md` | 核心循环协议（Agent 每次迭代读这个） |
| `references/verify-template.sh` | verify.sh 模板 |
| `references/v3-proposal.md` | 本方案文件（保留做追溯） |
| `references/v3-proposal-reviewed.md` | 本修订版方案 |

**修改文件**：
| 文件 | 改动 |
|------|------|
| `SKILL.md` | 精简，循环细节指向 PROTOCOL.md。版本号 → 3.0.0 |
| `scripts/ralph-loop.sh` | 新增 verify.sh hash 校验逻辑、results.tsv 写入 |
| `scripts/init-state.sh` | 新增 --verify 参数支持 |
| `version.json` | 版本号 → 3.0.0 |

---

## 四、决策结论（基于 Codex 审核已定）

| 决策点 | 结论 | 理由 |
|--------|------|------|
| D1 journal | 保留 v2 格式 | Codex 指出砍掉会削弱自主者模式 |
| D2 score 方向 | 统一"越小越好"，允许无 score 任务降级为 0/1 | Codex 建议 |
| D3 shell 引擎 | v3 继续 bash，v3.1 考虑 Python | 渐进式，降低风险 |
| D4 双模式 | 保留两种 | 执行者模式覆盖面广 |

---

## 五、验收标准（v3.0.0）

1. PROTOCOL.md 独立存在，约 120 行，只讲循环规则
2. SKILL.md 精简到约 150 行（安装 + 配置 + 模式选择 + 指向 PROTOCOL.md）
3. verify.sh 模板可用（`bash verify-template.sh` 能跑通示例）
4. ralph-loop.sh 支持 `--verify` 参数，循环前后做 hash 校验（macOS 兼容）
5. ralph-loop.sh 每轮迭代写入 results.tsv（含 schema: iteration, score_before, score_after, status, diff_stat, reason）
6. 版本号三处同步更新为 3.0.0

**Smoke 测试清单**（实施后必须全部通过）：
- [ ] `ralph-loop.sh --help` 输出正确
- [ ] `init-state.sh --mode executor` 初始化 state.json 成功
- [ ] `init-state.sh --mode autonomous` 初始化 state.json 成功
- [ ] `init-state.sh --verify` 新参数正确写入 state.json
- [ ] verify.sh PASS 时 score=0，FAIL 时 score=1
- [ ] verify.sh 输出格式错误（非 JSON）时 Runner 报错而非崩溃
- [ ] 篡改 verify.sh 后 Runner 自动检测并恢复
- [ ] 篡改 PROMPT.md 后 Runner 自动检测
- [ ] 篡改 PROTOCOL.md 后 Runner 自动检测
- [ ] results.tsv 每轮追加一行，schema 正确
- [ ] version.json / SKILL.md frontmatter / VERSION 三处版本号一致

---

## 六、后续版本路线

- **v3.1.0**：Python runner（替代 bash 核心引擎）
- **v3.2.0**：简化 state.json + journal 外置到 journal.tsv
- **v4.0.0**：NEVER STOP 模式（需配合成本上限 + 熔断 + wall-clock + worktree 隔离）

---

## 七、参考资料

- autoresearch program.md: https://github.com/karpathy/autoresearch/blob/master/program.md
- Geoffrey Huntley Ralph Loop: https://ghuntley.com/loop/
- Codex 审核报告：第一轮审核（2026-05-23）
