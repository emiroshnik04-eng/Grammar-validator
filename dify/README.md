# Dify Integration Files

This directory contains all necessary files to integrate the Catalog Grammar Validator with Dify platform.

## Directory Structure

```
dify/
├── README.md                    # This file
├── INTEGRATION_GUIDE.md         # Detailed integration instructions
├── openapi.yaml                 # OpenAPI 3.0 specification
├── tool_provider.yaml           # Dify tool provider configuration
├── tools/                       # Individual tool definitions
│   ├── validate_catalog.yaml
│   ├── suggest_category_name.yaml
│   └── check_health.yaml
└── _assets/                     # Icons and images
    └── validator.svg
```

## Quick Start

### For Dify Cloud Users

1. Go to https://cloud.dify.ai/admin
2. Navigate to **Tools** → **Add Custom Tool**
3. Choose **Import from OpenAPI**
4. Upload or paste content from `openapi.yaml`
5. Save and test

### For Self-Hosted Dify

1. Copy all files to your Dify tools directory:
   ```bash
   cp -r dify/* /path/to/dify/tools/catalog_validator/
   ```
2. Restart Dify services:
   ```bash
   docker-compose restart
   ```
3. The tools will appear in Tools panel

## Available Tools

### 1. validate_catalog
Validates CSV catalog files for Russian grammar and case agreement.

**Input:** CSV file
**Output:** Task ID for tracking validation progress

### 2. suggest_category_name
Uses LLM to suggest correct category name (singular/plural).

**Input:** Category name and path
**Output:** Suggested name with explanation

### 3. check_health
Checks if the validator service is operational.

**Input:** None
**Output:** Status and configuration info

## Configuration

### Base URL
```
https://catalog-validator.onrender.com
```

### Authentication
Optional API key authentication (not required by default).

### Rate Limits
- 100 requests per hour per IP
- 10MB max file size

## Example Workflows

See `INTEGRATION_GUIDE.md` for detailed workflow examples including:
- Simple catalog validation
- Category name validator with suggestions
- Batch processing

## Testing

Test the tools using cURL:

```bash
# Health check
curl https://catalog-validator.onrender.com/api/health

# Suggest category name
curl -X POST https://catalog-validator.onrender.com/suggest-category-name \
  -H "Content-Type: application/json" \
  -d '{"name": "Игрушка", "path": "Детские товары / Игрушка"}'

# Validate catalog
curl -X POST https://catalog-validator.onrender.com/api/validate \
  -F "file=@test_catalog.csv"
```

## Support

- **Issues:** https://github.com/emiroshnik04-eng/Grammar-validator/issues
- **Documentation:** See `INTEGRATION_GUIDE.md`
- **Validator URL:** https://catalog-validator.onrender.com

## Version

Current version: 1.0.0

## License

See main project LICENSE file.
