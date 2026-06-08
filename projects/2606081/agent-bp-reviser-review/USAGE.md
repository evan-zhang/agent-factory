# 使用说明 — agent-bp-reviser-review

> 面向单个 BP 目标的**证据驱动复核修订** Skill
> 版本 1.0.0 ｜ 零外部依赖（纯 Python stdlib）

---

## 一、这个 Skill 是干什么的

康哲 BP 系统里，当有人提出「把某个目标改成绿色 / 改下文字 / 这个进度不对」之类的修订诉求时，
本 Skill 负责**保守地、可追溯地**判断该不该改、怎么改：

- **单目标**：一次只处理一个 BP 目标，不串目标
- **标准优先**：以系统注入的目标标准（TargetStandard）为唯一裁判依据，不以人的口头说法为准
- **用户反馈降级**：任何人的修订诉求先降级为「待验证假设」，必须用证据闭环才放行
- **保守优先**：
  - 标准冲突 → 拦截（BLOCKED）
  - 证据不足 → 挂起（needs_more_evidence）
  - 高风险变更（黑→绿 / 红→绿）→ 强制人工复核（HOLD + review_flag）

输出是一份结构化的修订决策 + 写回补丁（writeback_patch），而不是直接改库。

---

## 二、安装位置

把整个目录放到 OpenClaw 的 skills 目录下即可：

```bash
# 解压
tar -xzf agent-bp-reviser-review-v1.0.0.tar.gz

# 放到 skills 目录（OpenClaw 会自动发现）
mv agent-bp-reviser-review ~/.openclaw/skills/
```

确认安装：

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/run_all.py     # 应输出 Ran 37 tests ... OK
```

---

## 三、两种使用路径

### 路径 A：Agent 跟着 SKILL.md 手动执行（主路径）

这是设计上的**主执行路径**。Agent 读 `SKILL.md`，按 9 步工作流逐步推进：

```
Step 0  目标定位（TargetLocator）—— 关键词锁定唯一目标，模糊则向用户澄清
Step 1  接收目标与标准注入（TargetStandard）
Step 2  降级用户反馈 —— 把诉求变成「待验证假设」
Step 3  责任链检索 —— 沿 responsibility_chain 找证据
Step 4  证据语义分层 —— primary / secondary / background / insufficient
Step 5  独立判灯 —— 不看人的说法，只看证据
Step 6  修订闸门 —— 高风险变更拦截
Step 7  写回联动 —— 生成 writeback_patch
Step 8  一致性校验 —— 文字/色块/证据栏三者同步
Step 9  会话规则记忆 —— 记住本轮被纠正的规则
```

`scripts/` 里的函数是**参考实现和辅助工具**，Agent 可以调用来减少手算，但不是必须。

### 路径 B：直接调用脚本（自动化/批处理）

```python
import sys
sys.path.insert(0, "~/.openclaw/skills/agent-bp-reviser-review/scripts")

from bp_reviser import main_reviser_flow
import json

# 输入
raw_feedback  = "把「完成3个新品种注册」改成绿色"
target_input  = json.load(open("examples/target_standard_sample.json"))
evidence_items = [json.load(open("examples/evidence_bundle_sample.json"))]

# 执行（5 个参数）
result = main_reviser_flow(
    raw_feedback=raw_feedback,
    target_input=target_input,
    evidence_items=evidence_items,
    target_id=None,          # 可选：直接给目标ID则跳过关键词搜索
    current_color="black",   # 系统当前灯色，用于闸门高风险判断
)

print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
```

输出关键字段：

| 字段 | 含义 |
|------|------|
| `revision_status` | approved / hold / blocked / needs_more_evidence / pending |
| `revision_action` | keep / update_color / update_text / mark_pending / revert |
| `review_flag` | 是否需要人工复核（高风险变更为 true） |
| `target_color` | 独立判定出的灯色 |
| `writeback_patch` | 写回补丁（text/color/evidence 三类更新） |
| `blocked_reason` | 被拦截时的原因 |
| `principle_violations` | 触碰核心原则的明细 |

---

## 四、BP API 配置（可选）

需要联网检索 BP 系统目标时，配置以下环境变量（已内置默认值，可覆盖）：

```bash
export XGJK_API_KEY="TsFhRR7OywNULeHPqudePf85STc4EpHI"     # 玄关开放平台统一密钥
export BP_PERIOD_ID="1994002024299085826"                  # 2026年度计划BP周期
export BP_GROUP_ID_PRODUCT="1994002335135023106"           # 产品中心分组
```

- API base：`https://sg-al-cwork-web.mediportal.com.cn/open-api`
- **网络异常自动降级**：任何 API 调用失败都返回空列表，不会崩溃
- 不联网也能用：路径 B 直接传入 target_input/evidence_items 即可

---

## 五、测试

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review

python3 tests/run_all.py                        # 37 个 unittest 全部（推荐）

# 单独跑某一套
python3 tests/test_standard_injection.py        # 标准注入 7 用例
python3 tests/test_evidence_scoping.py          # 证据分层 7 用例
python3 tests/test_revision_gating.py           # 修订闸门 8 用例
python3 tests/test_writeback_consistency.py     # 写回一致性 6 用例
python3 tests/test_bp_api_integration.py        # BP API mock 9 用例（无需网络）
```

---

## 六、目录结构

```
agent-bp-reviser-review/
├── SKILL.md                    # 主工作流定义（Agent 主执行路径，9 步）
├── README.md                   # 项目说明
├── USAGE.md                    # 本文件
├── version.json                # 版本与能力声明
├── scripts/
│   ├── bp_reviser.py           # 核心对象与主流程
│   ├── helpers.py              # BP API + 一致性校验 + 会话记忆等
│   └── __init__.py             # 导出别名
├── references/
│   ├── schema.md               # 数据结构定义（TargetStandard/EvidenceBundle/RevisionOutput）
│   ├── general-rules.md        # 通用规则 GR
│   ├── evidence-rules.md       # 证据规则 ER
│   ├── revision-rules.md       # 修订规则
│   └── api-reference.md        # 脚本函数 API 参考
├── examples/                   # 输入/输出样例（json + 端到端 md）
└── tests/                      # 可执行测试 + md 规格
```

---

## 七、关键设计约束（务必知道）

1. **只生成补丁，不直接改库** —— writeback_patch 需经人工或上层系统落库
2. **跨目标只读** —— 检索别的目标可以，写回别的目标会被一致性校验拦截
3. **绿灯硬门槛** —— 绿灯必须有 primary 证据，否则一致性校验失败
4. **黑灯硬门槛** —— 黑灯不能携带有效证据写回（自相矛盾）
5. **高风险强制复核** —— 黑→绿、红→绿 一律 HOLD + review_flag，不自动放行
6. **未来证据自动排除** —— evidence_time 晚于当前时间的证据自动降级 insufficient
7. **owner 必须是责任链末尾** —— TargetStandard 校验会强制这一点
