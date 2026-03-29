# AF-STD-02 Skill 设计档案与学习复盘模板

状态：ACTIVE
适用范围：所有 Skill 项目（AF 编号）

---

## A. 目录模板（放在每个 Skill 目录下）

```text
{skill-root}/
  SKILL.md
  scripts/
  design/
    DESIGN.md
    DISCUSSION-LOG.md
    LEARNING-LOOP.md
    SHARE-LOG.jsonl
```

---

## B. DESIGN.md 模板

```markdown
# DESIGN - {skill-name}

## 1) 目标
- 这个 Skill 解决什么问题
- 不解决什么问题（边界）

## 2) 用户体验目标
- 无感知目标
- 失败兜底策略（fail-soft / strict）

## 3) 核心流程
- 输入 -> 处理 -> 输出
- 关键路径

## 4) 风险与防护
- 安全风险
- 性能风险
- 数据一致性风险

## 5) 版本策略
- 当前版本
- 升级原则
```

---

## C. DISCUSSION-LOG.md 模板

```markdown
# DISCUSSION LOG - {skill-name}

## {date} {time}
- 触发背景：
- 用户反馈/诉求：
- 关键决策：
- 需要修改的内容：
- 执行结果：
- 待办：
```

---

## D. LEARNING-LOOP.md 模板

```markdown
# LEARNING LOOP - {skill-name}

## Daily
- 今日问题修复沉淀（Problem -> Rule）
- 今日预期偏差校正（Mismatch -> Preference）
- 今日用户模式更新（Pattern -> Twin）
- 明日改进行动（>=3条）

## Weekly
- 重复问题 Top3
- 生效规则清单
- 下周优化计划

## Monthly
- 数字分身逼近度评估
- 系统性问题与改进路线图
```

---

## E. SHARE-LOG.jsonl 字段规范

每行一条 JSON：

```json
{"period":"daily","key":"2026-03-27","skill":"cas-chat-archive","shared":true,"channel":"telegram:group:xxx","sharedAt":"2026-03-27T21:05:00+08:00","messageId":"12345"}
```

字段说明：
- period: daily|weekly|monthly
- key: 日期或周号或月份标识
- skill: Skill 名称
- shared: 是否已分享
- channel: 分享目标
- sharedAt: 分享时间
- messageId: 目标平台消息ID（可空）

---

## F. 执行规则

1. 每次讨论结束，必须先更新 `DISCUSSION-LOG.md`。
2. 涉及设计变更时，必须同步更新 `DESIGN.md`。
3. 涉及改进建议时，必须同步更新 `LEARNING-LOOP.md`。
4. 分享动作必须写入 `SHARE-LOG.jsonl`，避免重复分享。
5. 用户未要求“强制分享”时，命中已分享记录应自动跳过。
