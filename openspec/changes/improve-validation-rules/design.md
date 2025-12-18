# Design: Improve Validation Rules

## Context
The current validation system in `check_catalog.py` applies rule-based checks to Russian e-commerce catalog data. Three validation rules need improvement based on real-world usage:
1. Case format validation is too strict (forces lowercase globally)
2. Plural form conversion is too aggressive (breaks proper nouns)
3. Grammar highlighting needs verification

## Goals / Non-Goals

**Goals:**
- Detect case inconsistency within parameter groups (same `param_id`)
- Prevent plural conversion of proper nouns and compound expressions
- Ensure grammar errors are properly highlighted

**Non-Goals:**
- Not changing the overall validation pipeline architecture
- Not modifying Excel output format or highlighting logic
- Not adding new external dependencies

## Decisions

### Decision 1: Case Consistency Check Per param_id

**Approach:** Build a profile of predominant case patterns per `param_id` (similar to existing `build_param_pos_profile`), then flag values that don't match the majority pattern.

**Logic:**
1. Pre-scan all values for each `param_id`
2. Count: `lowercase_start` (e.g., "красный") vs `uppercase_start` (e.g., "Красный")
3. Determine majority pattern (threshold: >60% or configurable)
4. During validation, flag values not matching the majority

**Alternatives considered:**
- Force all lowercase (current) → Rejected: too rigid, doesn't respect existing data patterns
- Manual configuration per parameter → Rejected: not scalable

**Code location:** Add `build_param_case_profile()` similar to `build_param_pos_profile()` at check_catalog.py:310

### Decision 2: Smart Plural Detection with Linguistic Analysis

**Approach:** Use pymorphy3 and heuristics to detect multi-word expressions and proper nouns before attempting plural conversion.

**Detection heuristics:**
1. **Multi-word check:** If name contains 2+ words, analyze each word separately
2. **Proper noun detection:** Check if all words are capitalized (except prepositions/conjunctions)
3. **Brand name patterns:** Contains Latin characters, numbers, or mixed case (e.g., "iPhone")
4. **Named entity patterns:** Common patterns like "Детский мир", "Красная площадь"

**Pymorphy3 tags to check:**
- `Name` tag indicates proper noun
- Check if inflection to plural changes semantic meaning (compare normal form)

**Code location:** Add `is_proper_noun_or_compound()` before check_catalog.py:160 (before `ensure_category_plural`)

**Alternatives considered:**
- Whitelist approach (expand `_CATEGORY_MASS_LIKE`) → Rejected: not scalable, requires constant updates
- ML-based NER → Rejected: adds complexity and dependencies
- Disable plural check entirely → Rejected: loses valuable validation for regular categories

### Decision 3: Grammar Error Highlighting Verification

**Approach:** Verify existing `check_spelling()` function properly surfaces LanguageTool errors. No major changes needed - mostly testing and documentation.

**Verification steps:**
1. Test with known problematic words
2. Ensure `__comment` column receives clear error descriptions
3. Check that cell highlighting works correctly

**Code location:** check_catalog.py:84-110 (`check_spelling` function)

## Risks / Trade-offs

**Risk:** Proper noun detection may have false negatives/positives
- **Mitigation:** Use conservative heuristics (prefer not converting if uncertain) + allow manual exception list override

**Risk:** Case consistency check may flag legitimate mixed-case parameters
- **Mitigation:** Set reasonable threshold (60%+) and only flag if clear majority exists

**Trade-off:** Performance impact from additional pre-scanning
- **Impact:** Minimal - similar to existing `build_param_pos_profile()` which is already fast enough
- **Acceptable:** Data processing is already row-by-row sequential, one more pass is negligible

## Migration Plan

**Rollout:**
1. Implement changes in `check_catalog.py`
2. Test on historical datasets to verify no regressions
3. Compare old vs new validation results
4. Deploy updated script

**Rollback:**
- No database/schema changes, can rollback by reverting code
- Old Excel outputs remain compatible

**Backwards compatibility:**
- Excel output format unchanged
- Configuration structure unchanged
- All changes are additive/corrective to validation logic

## Open Questions

- **Q:** Should case consistency threshold be configurable in `CONFIG`?
  - **A:** Yes, add `case_consistency_threshold: 0.6` to CONFIG for flexibility

- **Q:** Should we log when proper noun detection prevents plural conversion?
  - **A:** Yes, add optional verbose logging mode for debugging
