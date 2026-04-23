# Example Input

```yaml
product_name: Velphoro (sucroferric oxyhydroxide)
therapy_area: Nephrology / CKD / Hyperphosphatemia
target_market: Taiwan
language: 繁體中文
license_holder: Rxilient Medical Taiwan
assessment_mode: market-only
output_mode: full-report
special_notes:
  - Focus on dialysis-related provider channels
  - Prioritize TFDA, NHI, nephrology society, and major medical center sources
```

# Expected behavior
- Build 3 research tracks
- Collect chapter-level evidence first
- Generate 15-chapter HTML report
- Mark any missing facts as `[未找到]`
