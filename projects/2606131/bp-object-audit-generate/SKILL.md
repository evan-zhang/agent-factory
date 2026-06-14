---
name: bp-object-audit-generate
description: Audit, question, confirm, generate, revise, and archive BP objects across group, center/business company, department, and key individual levels. Use when the user asks to rebuild, continue, diagnose, review, generate, confirm, write, freeze, or package annual BP content using the target-outcome-measure-initiative-responsibility-cascade logic, especially for 康哲集团 BP work, group-to-center-to-department-to-person承接, or interactive BP generation where the assistant must stop after each BP object, ask confirmation questions with options, and only generate or write after user confirmation.
---
> **Evan 落地 v0.1.5（PROJECT_ROOT 定义见 `references/source_manifest.md` § 2）** — v0.1.4 修复陈舒婷反馈的「7 维度穷举遗漏」问题：core_rules § 10 定义 7 维度+状态机加 dimension_audited+审计表加维度列+SKILL.md 加红线 seven_dimensions_exhaustive 与 closure_self_check。v0.1.5 修复 v0.1.4 评审 6 项必修 + v0.1.5 评审 1 项中等问题（object_templates 闭合检查对齐 § 10）。本 skill 归类为「复杂业务流」档，SKILL.md 行数预算 200 行（按 SOP v2026.6.14 浮动）。

# BP Object Audit Generate

## Purpose

Use this skill to process one BP object at a time across the full organization chain:

`集团 -> 中心/业务公司 -> 部门 -> 关键岗位个人`

The job is not simple writing. The job is to audit the BP object, identify structural and business uncertainties, ask the user for confirmation with suggested options, record confirmed rules, generate the revised BP object, and archive the confirmed result as Markdown.

## Non-Negotiable Rules

| Rule | Requirement |
|---|---|
| `one_object_at_a_time` | At group and center levels, one object = one objective (目标). At department and individual levels, one object = one full BP. Never audit multiple objectives in one cycle unless the user explicitly asks for a batch summary. See `references/core_rules.md` § 1.2 for the full granularity table. |
| `full_level_applicability` | Apply to group, center/business company, department, and key individual BP objects. Do not narrow the skill to group objectives only. |
| `evidence_first` | Read and classify relevant sources before making factual claims. Unread files cannot support conclusions. |
| `question_before_freeze` | If a business rule, metric口径, ownership, level boundary, or承接方式 is unclear, stop and ask before freezing or writing final text. |
| `options_required` | For each material uncertainty, provide a recommended option and alternatives such as A/B/C when possible. |
| `no_silent_fill` | Never silently invent numbers, owners,承接关系, or口径. Mark them as待确认. |
| `confirmed_rules_only` | Convert user answers into confirmed rules before using them in final BP text. |
| `initiative_is_handoff` | Treat关键举措 as the primary downstream承接入口, not成果 by default. |
| `single_accountable_owner` | Each key initiative should have one主责主体. Split rows when real ownership differs. |
| `level_boundary_control` | Keep the BP object at the correct level. Group writes direction, minimum baseline, structural requirement, and承接入口; lower levels decode and amplify. |
| `semantic_chain` | Use the chain: 目标 -> 成果 -> 衡量标准/最终验收物 -> 关键举措 -> 主责主体 -> 承接方式 -> 下级承接对象 -> 过程证据/AI判灯依据. |
| `seven_dimensions_exhaustive` | Before any question, produce a complete audit table for the 7 dimensions in `references/core_rules.md` § 10. No dimension may be skipped or left blank. State `dimension_audited` is required before question-asking. |
| `closure_self_check` | Before drafting, re-verify every ⚠️/❌/📊 row from the dimension table is either confirmed by the user or explicitly recorded as待确认. No silent resolution. See `references/output_package.md` § 4. |
| `output_after_confirmation` | Write or archive Markdown only after the user confirms the generated object or explicitly asks for a draft file. |
| `document_only` | Generate local documents and packages only. Do not push to remote systems, modify external BP platforms, SharePoint, or browser state without explicit user authorization. |

## Progressive Loading

Load only what the current BP object requires:

| Need | Read |
|---|---|
| Core BP semantics and hierarchy | `references/core_rules.md` |
| Interactive question-confirm-generate workflow | `references/interactive_state_machine.md` |
| Table formats and Markdown object templates | `references/object_templates.md` |
| Source file policy and default project paths | `references/source_manifest.md` |
| Archiving, package, and status files | `references/output_package.md` |

If the platform does not support file reading, see the **Embedded Minimum Rules** below. If the user asks to update the skill itself, edit `SKILL.md` and the relevant reference files directly.

> **Important**: This skill is semantic-, workflow-, and template-only. It does NOT bundle any specific business BP files. When the user asks to audit a concrete BP object (e.g., 康哲集团 / a specific center / a specific person), the user must confirm or provide the source path first (see `references/source_manifest.md` § 3 and § 6). Do not assume any specific 康哲集团 source files are present.

## Default Workflow

0. **Entry check** (multi-objective documents). If the user provides a document with multiple 目标 (e.g., a full center BP with 10 objectives), do NOT start auditing all at once. List the objectives found and ask the user which to start with. If only one objective is present, skip to step 1. See `references/core_rules.md` § 1.2 and `references/interactive_state_machine.md` state `material_received`.
1. Identify the BP object and level (group objective, center objective, department BP, or key individual BP) and confirm granularity per `references/core_rules.md` § 1.2.
2. Read `references/core_rules.md` and `references/interactive_state_machine.md` (if file reading is available).
3. Build a source reading list from `references/source_manifest.md` and the user's named files. If PROJECT_ROOT is not yet set, ask the user to confirm it before reading source files.
4. Read only relevant source sections. Mark each source per `source_manifest.md` § 1.
5. **7-dimension exhaustive audit (mandatory checkpoint).** Before asking any question, produce the dimension audit table from `references/core_rules.md` § 10. For each of the 7 dimensions, output ✅/⚠️/❌/📊 plus a one-line finding. The table itself is the audit judgment; no separate "审计判断" step is needed. Transition to state `dimension_audited` (see `references/interactive_state_machine.md`).
6. Ask one focused confirmation block at a time for each ⚠️/❌/📊 row in the dimension table. Before the first question, state the total count so the user can request a batch if they prefer. See `object_templates.md` § 3.
7. After each user answer, summarize the confirmed rule before proceeding.
8. **Closure self-check.** Before generating the draft, re-verify every ⚠️/❌/📊 row is either confirmed by the user or explicitly recorded as待确认 in the package status files. See `references/output_package.md` § 4.
9. Generate or revise the BP object only after required confirmations.
10. Run a closure check: no unclear口径, no wrong level, no dual主责, no missing承接方式, no unsupported fact, no one-to-one empty hierarchy.
11. If the user confirms, archive the BP object and update package status files per `references/output_package.md`. After archiving, proactively list the next unprocessed BP object from the same source document (if any) and ask whether to continue. See state `archived` in `references/interactive_state_machine.md`.

## Embedded Minimum Rules (No-Tool Fallback)

1. **One object at a time.** Group/center = one objective; department/individual = one full BP. Never audit multiple in one turn.
2. **Semantic chain:** 目标 → 成果 → 衡量标准 → 关键举措 → 主责主体 → 承接方式 → 下级承接对象 → 过程证据。
3. **Level boundary:** Group writes direction and minimum baseline; centers decode and amplify; departments and individuals provide coverage and evidence.
4. **Ask before freeze.** Unclear口径/owner/承接方式 → BP-Q<N> question block first.
5. **Option format:** A (recommended) / B / C with effects stated.
6. **Rule before draft.** Convert each user answer to 已确认规则 BP-R<N>.
7. **No silent fill.** Mark unknowns as 待确认.
8. **Output only after confirmation.**
9. **Single accountable owner.** Split rows if two real owners exist.
10. **Do not freeze** placeholders, empty thresholds, question-marked metrics, or unconfirmed facts.

## Output Behavior

During discussion, prefer tables in the chat. No files for every intermediate thought. On user confirmation, create Markdown per `references/object_templates.md` and package per `references/output_package.md`. Skill packaging includes `SKILL.md` + `agents/agent.yaml` + all `references/`.
