---
name: pharma-market-landscape-report
version: "1.0.0"
skillcode: pharma-market-landscape-report
description: 药品市场全景报告生成技能。三合一全景报告模板（15章x3部分），基于McKinsey结构化框架，治疗领域无关/市场无关，输出单一HTML报告。
tags:
  - pharmaceutical
  - market-landscape
  - kol-mapping
  - channel-strategy
  - market-intelligence
category: professional-skill
author: Agent Factory
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604231/pharma-market-landscape-report
date: "2026-04-23"
changelog: |
  - v1.0.0 (2026-04-23): 初始版本，已验证皮肤科/肾脏科/精神科 x 港台新马
---

# Pharma Market Landscape Report

## Purpose
Generate a high-confidence pharmaceutical market intelligence report for a given product, therapy area, and target market. The report must follow a fixed 15-chapter, 3-part structure and output a single HTML document with inline citations, tables, callouts, and a references section.

## Use this skill when
- The user needs a full market landscape report for a drug or brand in a specific market.
- The user wants epidemiology, treatment landscape, competition, patient distribution, provider/KOL mapping, and access/channel strategy in one document.
- The output should be publication-ready HTML rather than a chat answer.

## Do not use this skill when
- The user only wants a quick summary or a slide deck.
- The user only asks a single market question.
- Reliable sourcing is unavailable and the user does not want a research-first workflow.

## Required inputs
- `product_name`: brand + generic name
- `therapy_area`
- `target_market`
- `language`

## Optional inputs
- `local_brand_name`
- `license_holder`
- `assessment_mode`: `market-only` or `company-specific`
- `special_notes`
- `output_mode`: `full-report` | `research-pack` | `outline-first`

## Hard rules
- Never invent facts.
- Any missing fact must be written as `[未找到]`.
- Every market-specific, quantitative, access-related, KOL-related, pricing-related, and regulatory claim must include a source.
- Prefer primary sources in this order: regulator/government, guideline/journal, hospital/society, company, media.
- Do not begin drafting the final report until chapter-level evidence collection is complete.
- Keep the exact 15-chapter / 3-part report spine unless the user explicitly requests a reduced format.

## Execution model
Follow the detailed step logic in `workflow.md`.

## Inputs validation behavior
Stop and request missing core inputs only if one of these is absent:
- product_name
- therapy_area
- target_market
- language

If language differs from market convention, continue but note the mismatch in the executive summary metadata.
For Singapore and Malaysia, default to bilingual readiness unless the user explicitly requests single-language output.

## Research tracks
Create exactly 3 research tracks:
1. Market Landscape
2. Patient Distribution
3. Channel Deep Dive

Each track must include the product, therapy area, and target market.

## Report spine
### Part I — Market Landscape
1. Epidemiology and disease burden
2. Healthcare system overview
3. Current treatment landscape
4. Competitive landscape and registration
5. KOL identification
6. Promotional channel analysis

### Part II — Patient Distribution
7. Geographic patient distribution and channel structure
8. Treatment channel distribution
9. Reimbursement / formulary / cost structure
10. Patient demographics and diagnosis gap

### Part III — Channel Deep Dive
11. Provider landscape overview
12. Deep dive on top institutions
13. KOL tiering and engagement map
14. Cost structure and health economics
15. X+Y+N coverage strategy and phased action plan

## Minimum full-report output standard
- 1 HTML file
- 15 chapters
- at least 15 references
- at least 15 tables
- at least 10 callout boxes
- inline citations throughout
- reference list with URLs

## Styling system
Use these CSS classes exactly as defined in the template:
- `highlight-box`
- `insight`
- `action-box`
- `tier-1`
- `tier-2`
- `tier-3`
- `patient-flow`
- `num-highlight`
- `pct-bar`
- `exec-summary`
- `part-divider`

## Output behavior by mode
### `outline-first`
Return:
- proposed chapter outline
- chapter-specific data requirements
- identified evidence gaps
- no final HTML

### `research-pack`
Return:
- structured chapter research notes
- references grouped by chapter
- no final HTML unless explicitly requested

### `full-report`
Return:
- single HTML report based on `templates/report_template.html`
- ready for publishing

## Publishing
If publishing is available, publish the final HTML artifact using the required publishing mechanism.

