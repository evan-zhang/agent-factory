# Interactive State Machine

## 1. Operating Principle

Every BP object must pass through an interactive audit-confirm-generate loop. Do not jump from source reading directly to final BP writing when there are unresolved business choices.

Default loop:

`锁定对象 -> 读取证据 -> 审计诊断 -> 初步判断 -> 问题块 -> 用户确认 -> 已确认规则 -> 生成草案 -> 二次校验 -> 用户确认 -> 归档`

## 2. States

| State | Meaning | Allowed Next Step |
|---|---|---|
| `material_received` | User has provided a source document containing one or more BP objects | If one object: `object_locked`. If multiple objects: list them and ask user to select one, then `object_locked`. |
| `object_locked` | One BP object and level are selected | source reading |
| `sources_classified` | Sources are read and status-labeled | 7-dimension exhaustive audit |
| `dimension_audited` | All 7 audit dimensions (level/OKR/acceptance/caliber/evidence/owner/freeze) have been judged ✅/⚠️/❌/📊 with a complete table output (see `core_rules.md` § 10 and SKILL.md Step 4.5). | question block if any ⚠️/❌/📊, else draft |
| `diagnosis_ready` | Issues and risks are identified (legacy state, kept for compatibility; new flows should pass through `dimension_audited` first) | question block or draft if no issue |
| `pending_user_confirmation` | At least one business rule requires user decision | ask one question |
| `rule_confirmed` | User answer has been converted into a reusable rule | update draft or ask next question |
| `draft_generated` | BP object draft has been generated | closure check |
| `closure_pending` | Draft has unresolved issues | ask question or revise |
| `ready_to_archive` | User has confirmed and closure check passed | write Markdown |
| `archived` | Markdown and package status files updated | After archiving, proactively list the next unprocessed BP object from the same source document (if any) and ask: "Would you like to continue with [next objective]?" Wait for user confirmation before locking the next object. Update `00_BP对象生成总目录.md` to reflect progress. |
| `resumed` | User reopens a previously started BP object | load confirmed rules from archive file, re-enter at `diagnosis_ready` or `pending_user_confirmation` depending on prior progress |

## 3. Question Rules

**Question preview.** Before asking the first question, produce a one-line summary stating the total number of required confirmations:

> "本轮共发现 N 个需确认问题，将逐一提问。以下是第 1 个。"

This sets user expectations and allows them to request a batch if they prefer.

Ask one focused confirmation block at a time unless the user asks for a batch.

Each question block must include:

1. question number;
2. what is uncertain;
3. why it matters;
4. AI preliminary judgment;
5. 2-3 options with the recommended option first;
6. effect of each option.

Do not ask vague questions such as "please confirm." Ask a decision-ready question.

## 4. Answer Handling

When the user answers:

1. restate the selected option;
2. convert it into an `已确认规则`;
3. state the affected BP field or row;
4. continue to the next unresolved question, or generate the draft if all required questions are closed.

Example:

```markdown
已确认规则 BP-R07：O2集团层不单列自主研发矩阵病种要求，只保留全产品战略覆盖；自主研发矩阵作为产品中心内部路径下沉到产品中心BP。
影响字段：O2成果2.2、关键举措表。
```

## 5. Audit Dimensions

For every BP object, audit these dimensions:

| Dimension | Check |
|---|---|
| 层级边界 | Is this content appropriate for group, center, department, or individual level? |
| OKR语义 | Is目标 a result state, 成果 a key result, 衡量标准 judgeable, 举措 an implementation path? |
| 成果验收 | Does each成果 have measurable or judgeable final acceptance conditions? |
| 举措承接 | Does each关键举措 have主责主体 and承接方式? |
| 单主责 | Are multiple real owners merged into one vague row? |
| 下级承接 | Does complete BP承接 produce downstream one-to-many decomposition? |
| 口径 | Are figures, period, unit,含税/不含税, management/report口径 clear? |
| 证据 | Are source and monthly evidence paths clear? |
| 冻结 | Are placeholders,待确认, and unsupported claims removed before final? |

## 6. Draft Gate

Generate a draft only when:

1. all blocking business rules are confirmed; or
2. the user explicitly asks for a "待确认草案"; and
3. every unconfirmed part is visibly marked `待确认`, not smoothed into final text.

## 7. Archive Gate

Archive as confirmed Markdown only when:

1. the user confirms the object;
2. no blocking open issue remains;
3. the source status and confirmed rules are recorded;
4. closure check passes.

