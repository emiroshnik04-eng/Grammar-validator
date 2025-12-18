# Change: Improve Validation Rules

## Why
Current validation has three issues:
1. **Case format check is too strict** - checks global lowercase rule instead of consistency within each parameter group
2. **Plural form conversion is too aggressive** - converts compound names like "Детский мир" to "Детские миры", changing meaning (proper nouns, set expressions)
3. **Grammar errors need better highlighting** - spelling/grammar issues should be more visible

These issues cause false positives and reduce validation accuracy.

## What Changes
- **Case consistency per param_id**: Replace global lowercase check with per-parameter consistency check - all values within one `param_id` should use same capitalization pattern
- **Smart plural detection for categories**: Add linguistic analysis to detect proper nouns, brand names, and compound expressions that should not be converted to plural
- **Grammar error detection**: Ensure LanguageTool errors are properly highlighted and reported in `__comment` column

## Impact
- Affected specs: catalog-validation (new spec)
- Affected code:
  - `check_catalog.py`: functions `normalize_value_format`, `ensure_category_plural`, `build_param_pos_profile`, `process_dataframe`
  - May need to add new helper functions for compound name detection
