# Project Context

## Purpose
This project is a **catalog quality validation tool** for e-commerce product data exports. It validates and corrects Russian-language product catalog exports by checking:
- Grammar and spelling of category names at all levels
- Parameter names and values
- Morphological consistency (plural/singular forms)
- Part-of-speech uniformity within parameter groups
- Pattern-based corrections (e.g., "Другой/Другое/Другая + parameter name")

The tool processes CSV exports, applies rule-based and LLM-enhanced validation, and produces Excel reports with highlighted errors and suggested corrections.

## Tech Stack
- **Python 3.x** - Main programming language
- **pandas** - CSV/Excel data processing
- **openpyxl** - Excel file manipulation and cell styling
- **pymorphy3** - Russian morphological analysis
- **language-tool-python** - Grammar and spelling checking (requires Java runtime)
- **FastAPI** - HTTP service for semantic category analysis
- **uvicorn** - ASGI server for FastAPI
- **httpx** - Async HTTP client for LLM API calls
- **Playwright** (TypeScript/Node.js) - Automated testing framework
- **OpenAI-compatible LLM API** - External service for semantic category name recommendations

## Project Conventions

### Code Style
- Python code follows standard conventions with descriptive function and variable names in Russian comments
- Type hints used for function signatures (`typing` module)
- Configuration centralized in `CONFIG` dictionary constant
- Error handling: graceful degradation when optional services unavailable (LanguageTool, LLM API)
- String handling: explicit `.strip()` and null checks throughout
- Environment variables for sensitive data: `LLM_API_KEY`, `LLM_API_URL`, `SEMANTIC_URL`

### Architecture Patterns
- **Separation of concerns**: Main validation logic ([check_catalog.py](check_catalog.py)) separate from LLM service ([semantic_service.py](semantic_service.py))
- **Service-oriented**: FastAPI microservice for semantic analysis can be deployed independently
- **Rule-based pipeline**: Sequential validation rules applied to each data row
- **Profile-based validation**: Pre-analysis phase (`build_param_pos_profile`) to determine expected patterns
- **Graceful fallbacks**: System continues working if optional components (Java/LanguageTool, LLM API) are unavailable

### Testing Strategy
- Playwright configured for automated testing (see [playwright.config.ts](playwright.config.ts))
- Tests located in [tests/](tests/) directory
- Configuration includes TypeScript support with `@playwright/test` and `@types/node`

### Git Workflow
- Repository currently not initialized as git repository
- GitHub workflows configuration present in [.github/](.github/) directory

## Domain Context
**E-commerce catalog validation for Russian marketplace:**

1. **Category Naming Rules:**
   - Categories must be in plural form (множественное число) with exceptions for mass/uncountable nouns
   - Exceptions list: "клей", "молоко", "масло", "сахар", "транспорт", "игрушечный транспорт"
   - Category hierarchy: up to 5 levels (category_level_1_name through category_level_5_name)

2. **Parameter Value Rules:**
   - "Другой/Другое/Другая/Другие" pattern must match parameter name gender/number morphologically
   - Values should be in singular form for item characteristics (colors, materials, etc.)
   - First letter lowercase for common words (not brands/abbreviations)
   - Part-of-speech consistency within same `param_id` group

3. **Morphological Analysis:**
   - Russian language processing via pymorphy3
   - Gender detection: masc/femn/neut
   - Number detection: sing/plur
   - Part-of-speech tagging: NOUN, ADJF (full adjective), ADJS (short adjective)

4. **Input/Output Format:**
   - Input: CSV with `;` delimiter, `cp1251` encoding (standard Windows Russian)
   - Output: Excel (.xlsx) with original data + `__correct` and `__comment` columns for each validated field
   - Error highlighting: cells with errors colored with fill pattern

## Important Constraints
- **Java Runtime Required**: LanguageTool dependency needs Java installed for grammar checking
- **Encoding**: Input files must be `cp1251` (Windows Cyrillic), not UTF-8
- **LLM API Key**: Semantic service requires `LLM_API_KEY` environment variable for OpenAI-compatible endpoint
- **Windows Environment**: File paths and Excel handling optimized for Windows (indicated by `.xlsx` lock files)
- **Performance**: Sequential row-by-row processing - may be slow for very large catalogs
- **Language**: System is Russian-specific and not designed for multilingual catalogs

## External Dependencies
- **LanguageTool**: Grammar/spelling checker (runs locally, requires Java)
- **OpenAI-compatible LLM API**:
  - Default endpoint: `https://api.openai.com/v1/chat/completions`
  - Default model: `gpt-4.1-mini`
  - Used for semantic category name recommendations
  - Configurable via `LLM_API_URL` and `LLM_MODEL` environment variables
- **Semantic Service** ([semantic_service.py](semantic_service.py)):
  - FastAPI service running on `http://127.0.0.1:8000` (default)
  - `/analyze-category` endpoint for LLM-based category analysis
  - Optional dependency - validation continues without it
