# pharma-market-landscape-report

A multi-file skill package for generating structured pharmaceutical market landscape reports.

## Package structure
- `SKILL.md` — main orchestration skill
- `workflow.md` — execution phases and handoff rules
- `templates/report_template.html` — HTML output skeleton
- `checklists/qa_checklist.md` — pre-publish QA checklist
- `schemas/research_note_schema.json` — chapter evidence schema
- `examples/input_example.md` — example invocation inputs

## Recommended execution model
1. Intake and validation
2. Research planning
3. Evidence collection across 3 tracks
4. Chapter assembly
5. HTML rendering
6. QA validation
7. Publish

## Why multi-file
This report type is too large and too constrained for a single monolithic prompt file. Separating orchestration, execution workflow, output template, and QA rules improves stability, maintainability, and auditability.
