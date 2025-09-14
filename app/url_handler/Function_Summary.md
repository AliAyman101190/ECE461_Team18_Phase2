# URL Handler - Function Summary

## Quick Reference Guide

### Classes and Data Structures

| Class/Enum | Purpose |
|------------|---------|
| `URLCategory` | Enum defining supported categories (GITHUB, NPM, HUGGINGFACE, UNKNOWN) |
| `URLData` | Dataclass containing processed URL information and metadata |
| `URLHandler` | Main processing class for URL validation and extraction |

### Core Processing Methods

| Method | Parameters | Returns | Purpose |
|--------|------------|---------|---------|
| `URLHandler.__init__()` | None | None | Initialize hostname mappings |
| `URLHandler.validate_url()` | `url_string: str` | `bool` | Validate URL format and scheme |
| `URLHandler.classify_hostname()` | `hostname: str` | `URLCategory` | Classify hostname into category |
| `URLHandler.extract_github_identifier()` | `parsed_url` | `Dict[str, Optional[str]]` | Extract GitHub owner/repo |
| `URLHandler.extract_npm_identifier()` | `parsed_url` | `Dict[str, Optional[str]]` | Extract NPM package name |
| `URLHandler.extract_huggingface_identifier()` | `parsed_url` | `Dict[str, Optional[str]]` | Extract HF model/dataset info |
| `URLHandler.extract_unique_identifier()` | `parsed_url, category` | `Dict[str, Optional[str]]` | Route to appropriate extractor |
| `URLHandler.handle_url()` | `url_string: str` | `URLData` | Main processing pipeline |

### File Processing Functions

| Function | Parameters | Returns | Purpose |
|----------|------------|---------|---------|
| `read_urls_from_file()` | `file_path: str` | `List[str]` | Read URLs from file (skip comments) |
| `process_url_file()` | `file_path: str` | `List[URLData]` | Process all URLs in file |

### Utility Functions

| Function | Parameters | Returns | Purpose |
|----------|------------|---------|---------|
| `get_valid_urls()` | `results: List[URLData]` | `List[URLData]` | Filter only valid URLs |
| `get_urls_by_category()` | `results, category` | `List[URLData]` | Filter URLs by category |
| `get_processing_summary()` | `results: List[URLData]` | `Dict[str, Any]` | Generate summary statistics |

### Convenience Functions

| Function | Parameters | Returns | Purpose |
|----------|------------|---------|---------|
| `handle_url()` | `url_string: str` | `URLData` | Process single URL (standalone) |
| `main()` | None | None | Command-line interface |

## Processing Flow

```
URL String → validate_url() → classify_hostname() → extract_unique_identifier() → URLData
```

## Supported URL Patterns

### GitHub
- `https://github.com/owner/repository`
- `https://www.github.com/owner/repository`

### NPM  
- `https://npmjs.com/package/package-name`
- `https://www.npmjs.com/package/@scope/package-name`

### Hugging Face
- `https://huggingface.co/user/model-name`
- `https://huggingface.co/datasets/dataset-name`
- `https://huggingface.co/spaces/user/space-name`

## Key Data Fields

### URLData Object
- `original_url`: Input URL string
- `is_valid`: Boolean validation result
- `category`: Classified category (URLCategory enum)
- `hostname`: Extracted hostname
- `unique_identifier`: Main identifier (e.g., "owner/repo")
- `owner`: Owner/user name (GitHub, HF)
- `repository`: Repository/model name
- `package_name`: Package name (NPM, HF)
- `version`: Version info (when available)
- `error_message`: Error description (if invalid)

## Usage Examples

### Single URL Processing
```python
from url_handler import handle_url

result = handle_url("https://github.com/microsoft/typescript")
print(f"Valid: {result.is_valid}")
print(f"Category: {result.category.value}")
print(f"ID: {result.unique_identifier}")
```

### File Processing
```python
from url_handler import process_url_file, get_processing_summary

results = process_url_file("urls.txt")
summary = get_processing_summary(results)
print(f"Total: {summary['total_urls']}")
print(f"Valid: {summary['valid_count']}")
```

### Category Filtering
```python
from url_handler import get_urls_by_category, URLCategory

github_urls = get_urls_by_category(results, URLCategory.GITHUB)
for url in github_urls:
    print(f"{url.owner}/{url.repository}")
```

## Error Handling

| Error Type | Condition | Result |
|------------|-----------|--------|
| Invalid URL | Empty, malformed, wrong scheme | `is_valid=False` with error message |
| File Not Found | Missing URL file | `FileNotFoundError` exception |
| Unknown Category | Valid URL, unsupported site | `category=UNKNOWN`, `is_valid=True` |
| Extraction Failure | Valid URL, can't parse path | `unique_identifier=None` |

## Command Line Usage

```bash
# Run built-in tests
python url_handler.py --test

# Process URL file
python url_handler.py urls.txt
```
