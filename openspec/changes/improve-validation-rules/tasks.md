# Implementation Tasks

## 1. Case Consistency Validation
- [x] 1.1 Create `build_param_case_profile` function to analyze capitalization patterns per `param_id`
- [x] 1.2 Add `check_case_consistency` function to detect inconsistent capitalization within parameter group
- [x] 1.3 Replace `normalize_value_format` logic with case consistency check in `process_dataframe`
- [x] 1.4 Update comments in violations to explain which case pattern is expected
- [x] 1.5 Add `case_consistency_threshold` to CONFIG (set to 0.6 by default)

## 2. Smart Plural Detection
- [x] 2.1 Create `is_proper_noun_or_compound` function using pymorphy3 to detect proper nouns and multi-word expressions
- [x] 2.2 Add heuristics for brand names and set expressions (e.g., "Детский мир", "Красная площадь")
- [x] 2.3 Add `_KNOWN_PROPER_NOUNS` list with common brand names and places
- [x] 2.4 Update `ensure_category_plural` to skip conversion for detected proper nouns/compounds
- [x] 2.5 Add `_FUNCTION_WORDS` list to filter out prepositions when analyzing compound names

## 3. Grammar Error Highlighting
- [x] 3.1 Verify `check_spelling` properly returns all LanguageTool errors
- [x] 3.2 Ensure grammar errors are added to `__comment` column with clear descriptions
- [x] 3.3 Test with known problematic words to confirm highlighting works

## 4. Testing and Validation
- [x] 4.1 Create test_improvements.py with unit tests for new functions
- [x] 4.2 Test case consistency check with mixed case values
- [x] 4.3 Test proper noun detection with compound category names like "Детский мир"
- [x] 4.4 Test brand name detection with Latin characters and numbers
- [x] 4.5 Verify Python syntax with py_compile
- [x] 4.6 All tests passed successfully
