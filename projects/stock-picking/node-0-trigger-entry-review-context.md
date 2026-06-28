# Node 0 Review Context — External Trigger Entry

Project: stock-picking modular stock research / selection SOP.
Stage: S2 requirement baseline discussion.
Date: 2026-06-23.

## Current Baseline

Node 0 is "External Trigger Entry": user manual request, Gateway cron, or another SOP calls the stock-picking SOP.

Current old implementation problem:
- Existing `stock-picking-v2/SKILL.md` embeds cron schedules for HK, CN, and US markets.
- Weekly review, position monitoring, and portfolio drawdown monitoring triggers are also described inside the same skill.

Current proposed direction:
- `stock-picking` should not own cron.
- Gateway / runtime ops should own scheduling.
- `stock-picking` should define the callable contract and audit metadata.

Suggested input fields:
- `market`: `US | HK | CN`
- `strategy_id`: `taroc | chokepoint | mixed | custom`
- `run_mode`: `discovery | validation | tracking | monitor | full`
- `dry_run`: `true | false`
- `trigger_source`: `manual | cron | sop`
- `run_date`: `YYYY-MM-DD`

Initial recommended stance from orchestrator:
- Multi-market runs may be allowed at the user-facing layer, but should split into independent per-market runs internally.
- `mixed` should be SOP-level orchestration of multiple strategies, not a hidden black-box strategy.
- Selection / validation / tracking should default to `dry_run: true`.
- Only a future risk-execution gateway may discuss `dry_run: false`, with separate approval, dry-run, and audit logging.

## Questions To Review

1. Is the boundary correct: trigger scheduling outside the skill, callable contract inside the skill?
2. Are the proposed input fields sufficient and not overdesigned?
3. How should multi-market and multi-strategy triggering be represented?
4. What should be the default `dry_run` policy?
5. What acceptance criteria should this node have before S2 baseline approval?

## Required Output

Give a concise proposal with:
- recommended boundary
- recommended input contract
- risks / missing fields
- acceptance criteria
- disagreements, if any, with the orchestrator stance
