# Catalog Validation Specification

## ADDED Requirements

### Requirement: Case Consistency Within Parameter Groups
The system SHALL validate that all values within the same `param_id` follow a consistent capitalization pattern.

#### Scenario: Consistent lowercase values
- **GIVEN** a parameter with `param_id` "color" has values: "красный", "синий", "зелёный"
- **WHEN** validation runs
- **THEN** no case inconsistency errors are reported

#### Scenario: Consistent uppercase values
- **GIVEN** a parameter with `param_id` "brand" has values: "Nike", "Adidas", "Puma"
- **WHEN** validation runs
- **THEN** no case inconsistency errors are reported

#### Scenario: Inconsistent case values
- **GIVEN** a parameter with `param_id` "material" has values: "пластик", "Дерево", "металл", "резина"
- **WHEN** validation runs
- **THEN** "Дерево" is highlighted with comment "Регистр значения не соответствует большинству значений этого параметра (ожидается строчная буква)"

#### Scenario: Mixed case with no clear majority
- **GIVEN** a parameter has 50% lowercase and 50% uppercase values
- **WHEN** validation runs
- **THEN** no case inconsistency errors are reported (no clear majority)

### Requirement: Smart Plural Detection for Categories
The system SHALL detect proper nouns, brand names, and compound expressions in category names and SHALL NOT convert them to plural form.

#### Scenario: Single word category converts to plural
- **GIVEN** category name "Игрушка"
- **WHEN** validation runs
- **THEN** system suggests "Игрушки" with comment "Название категории должно быть во множественном числе"

#### Scenario: Proper noun brand name preserved
- **GIVEN** category name "Детский мир"
- **WHEN** validation runs
- **THEN** no plural conversion is suggested (recognized as proper noun/brand name)

#### Scenario: Compound expression with adjective preserved
- **GIVEN** category name "Красная площадь"
- **WHEN** validation runs
- **THEN** no plural conversion is suggested (recognized as set expression)

#### Scenario: Multi-word common noun phrase converts correctly
- **GIVEN** category name "Мягкая игрушка"
- **WHEN** validation runs
- **THEN** system suggests "Мягкие игрушки" (both words properly inflected)

#### Scenario: Mixed Latin/Cyrillic brand name preserved
- **GIVEN** category name "Apple товары"
- **WHEN** validation runs
- **THEN** no plural conversion is suggested (contains brand name)

### Requirement: Grammar Error Detection and Highlighting
The system SHALL detect spelling and grammar errors using LanguageTool and SHALL highlight affected cells with clear error descriptions.

#### Scenario: Spelling error in category name
- **GIVEN** category name "Игрушкi" (incorrect Cyrillic)
- **WHEN** validation runs and LanguageTool detects error
- **THEN** cell is highlighted and `__comment` contains "Орфография/грамматика"
- **AND** `__correct` contains suggested correction

#### Scenario: Grammar error in parameter value
- **GIVEN** parameter value "красние" (wrong adjective ending)
- **WHEN** validation runs and LanguageTool detects error
- **THEN** cell is highlighted and `__comment` contains "Орфография/грамматика значения параметра"
- **AND** `__correct` contains "красные"

#### Scenario: No grammar errors
- **GIVEN** category name "Игрушки" (correct)
- **WHEN** validation runs
- **THEN** no grammar error is reported
- **AND** cell is not highlighted for grammar issues

### Requirement: Second Word Capitalization in Compound Phrases
The system SHALL lowercase the second word in compound phrases UNLESS the word is a proper noun, brand name, or abbreviation.

#### Scenario: Common compound phrase
- **GIVEN** compound phrase "Другой красный Цвет"
- **WHEN** validation runs
- **THEN** system suggests "Другой красный цвет" (second word lowercased)

#### Scenario: Proper noun preserved
- **GIVEN** compound phrase "Другой iPhone"
- **WHEN** validation runs
- **THEN** no change suggested (iPhone is a brand name)

#### Scenario: Abbreviation preserved
- **GIVEN** compound phrase "Другая USB мышь"
- **WHEN** validation runs
- **THEN** no change suggested (USB is an abbreviation)

#### Scenario: Category name with compound words
- **GIVEN** category "Детские Игрушки"
- **WHEN** validation runs
- **THEN** system suggests "Детские игрушки" (second word lowercased)

### Requirement: Improved "Другой" Pattern Morphology
The system SHALL determine the grammatical gender of "Другой/Другая/Другое" based on the head noun of the associated parameter phrase, not just the first word.

#### Scenario: Compound parameter with head noun at end
- **GIVEN** parameter "большой красный мяч" (masculine head noun "мяч")
- **WHEN** "Другой" pattern is applied
- **THEN** system uses "Другой большой красный мяч" (masculine form)

#### Scenario: Compound parameter with adjectives
- **GIVEN** parameter "красная спортивная обувь" (feminine head noun "обувь")
- **WHEN** "Другой" pattern is applied
- **THEN** system uses "Другая красная спортивная обувь" (feminine form)

#### Scenario: Simple parameter
- **GIVEN** parameter "цвет" (masculine noun)
- **WHEN** "Другой" pattern is applied
- **THEN** system uses "Другой цвет" (masculine form)

### Requirement: Genitive Case Preservation in "Другой" Pattern
The system SHALL preserve genitive case endings when correcting compound parameter names with "Другой/Другая/Другое" pattern. The system SHALL NOT incorrectly convert genitive case nouns to nominative case.

#### Scenario: Genitive case preserved in compound parameter
- **GIVEN** parameter value "Другой Тип плюшевой игрушка" (incorrect: "игрушка" should be "игрушки")
- **AND** parameter name is "Тип плюшевой игрушки" (genitive case)
- **WHEN** validation runs
- **THEN** system suggests "Другой тип плюшевой игрушки" (genitive "игрушки" preserved)
- **AND** does NOT suggest "Другой тип плюшевой игрушка" (nominative)

#### Scenario: Genitive case in two-word parameter
- **GIVEN** parameter value "Другой марка машинки" (incorrect gender)
- **AND** parameter name is "марка машинки" (genitive case)
- **WHEN** validation runs
- **THEN** system suggests "Другая марка машинки" (genitive "машинки" preserved)
- **AND** gender agrees with "марка" (feminine)

#### Scenario: Nominative plural correctly singularized
- **GIVEN** parameter value "Другой особенности" (nominative plural)
- **AND** parameter name is "особенности" (nominative plural)
- **WHEN** validation runs
- **THEN** system suggests "Другая особенность" (singular nominative)
- **AND** recognizes this is truly plural nominative, not genitive

#### Scenario: Detection logic
- **GIVEN** noun ending in "-и" or "-ы" after another noun
- **WHEN** system analyzes morphology
- **THEN** system checks if word can be genitive singular
- **AND** if word is not first in phrase, preserves ending (likely genitive)
- **AND** if word is first in phrase and only nominative plural parse exists, singularizes it

### Requirement: Results Filtering
The system SHALL output ONLY rows that contain corrections or errors in the validated result file.

#### Scenario: Mixed valid and invalid rows
- **GIVEN** dataset with 1000 rows where 50 rows have errors
- **WHEN** validation completes
- **THEN** output file contains exactly 50 rows
- **AND** all 50 rows have at least one `__correct` column with non-empty value

#### Scenario: All rows valid
- **GIVEN** dataset with 100 rows where all data is correct
- **WHEN** validation completes
- **THEN** output file contains 0 rows
- **OR** system returns message indicating no errors found

#### Scenario: Row with multiple errors
- **GIVEN** row with errors in 3 different columns
- **WHEN** validation completes
- **THEN** row is included in output exactly once
- **AND** all 3 corrections are shown in respective `__correct` columns

### Requirement: Real-time Progress Tracking
The system SHALL provide real-time progress updates via Server-Sent Events (SSE) during validation processing.

#### Scenario: Large file processing
- **GIVEN** CSV file with 10000 rows being processed
- **WHEN** validation starts
- **THEN** client receives SSE progress updates every 500ms
- **AND** progress shows percentage from 0% to 100%
- **AND** status messages describe current operation

#### Scenario: Progress stages
- **GIVEN** validation in progress
- **WHEN** client connects to SSE endpoint
- **THEN** progress updates include stages: "Reading file", "Parsing CSV", "Validating data", "Saving results", "Counting errors"
- **AND** each stage has associated progress percentage

#### Scenario: Error during processing
- **GIVEN** validation encounters error at 45% progress
- **WHEN** error occurs
- **THEN** SSE sends error status with error message
- **AND** client connection closes gracefully
- **AND** progress bar shows error state

#### Scenario: Successful completion
- **GIVEN** validation completes successfully
- **WHEN** progress reaches 100%
- **THEN** SSE sends "completed" status
- **AND** client receives final statistics (rows processed, errors found)
- **AND** client connection closes gracefully
