# URL Handler Documentation

## Overview
The URL Handler module provides comprehensive functionality for processing, validating, and classifying URLs from GitHub, NPM, and Hugging Face platforms. It extracts unique identifiers and returns structured data objects for further processing by other modules.

## Supported Platforms
- **GitHub**: Repositories and projects
- **NPM**: JavaScript packages (including scoped packages)
- **Hugging Face**: Models, datasets, and spaces

---

## Classes and Enums

### `URLCategory` (Enum)
**Purpose**: Defines the supported URL categories for classification.

**Values**:
- `GITHUB = "github"` - GitHub repositories
- `NPM = "npm"` - NPM packages
- `HUGGINGFACE = "huggingface"` - Hugging Face models/datasets/spaces
- `UNKNOWN = "unknown"` - Unrecognized or unsupported URLs

### `URLData` (Dataclass)
**Purpose**: Structured data container for URL processing results.

**Fields**:
- `original_url: str` - The original URL string provided for processing
- `category: URLCategory` - The classified category of the URL
- `hostname: str` - The hostname extracted from the URL
- `is_valid: bool` - Whether the URL passed validation
- `unique_identifier: Optional[str]` - The extracted unique identifier (e.g., "owner/repo")
- `owner: Optional[str]` - The owner/user name (for GitHub and Hugging Face)
- `repository: Optional[str]` - The repository/model name
- `package_name: Optional[str]` - The package name (for NPM and Hugging Face)
- `version: Optional[str]` - Version information when available
- `error_message: Optional[str]` - Error description if processing failed

### `URLHandler` (Class)
**Purpose**: Main processing engine for URL validation, classification, and identifier extraction.

---

## Core Methods of URLHandler Class

### `__init__(self)`
**Purpose**: Initialize the URL handler with hostname category mappings.

**Functionality**:
- Sets up a dictionary mapping known hostnames to their respective categories
- Includes variations with and without 'www.' prefix
- Supports: github.com, npmjs.com, huggingface.co

**Parameters**: None

**Returns**: None

---

### `validate_url(self, url_string: str) -> bool`
**Purpose**: Validate if a URL string is properly formatted and uses supported schemes.

**Functionality**:
1. Checks if input is a non-empty string
2. Parses URL using `urlparse`
3. Validates presence of scheme and netloc
4. Ensures scheme is HTTP or HTTPS
5. Performs basic hostname format validation using regex

**Parameters**:
- `url_string (str)`: The URL string to validate

**Returns**:
- `bool`: True if URL is valid, False otherwise

**Validation Rules**:
- Must be a string
- Must have scheme (http/https)
- Must have hostname
- Hostname must contain only alphanumeric characters, dots, and hyphens

---

### `classify_hostname(self, hostname: str) -> URLCategory`
**Purpose**: Classify a hostname into one of the supported categories.

**Functionality**:
1. Converts hostname to lowercase
2. Removes 'www.' prefix if present
3. Checks direct mapping in hostname_categories dictionary
4. Performs pattern matching for variations
5. Returns appropriate URLCategory

**Parameters**:
- `hostname (str)`: The hostname to classify

**Returns**:
- `URLCategory`: The determined category (GITHUB, NPM, HUGGINGFACE, or UNKNOWN)

**Classification Logic**:
- Direct hostname mapping (exact match)
- Pattern matching for subdomains and variations
- Fallback to UNKNOWN for unrecognized hostnames

---

### `extract_github_identifier(self, parsed_url) -> Dict[str, Optional[str]]`
**Purpose**: Extract owner and repository information from GitHub URLs.

**Functionality**:
1. Splits URL path into components
2. Expects format: `/owner/repository`
3. Extracts owner and repository names
4. Creates unique identifier in "owner/repository" format

**Parameters**:
- `parsed_url`: Parsed URL object from `urlparse`

**Returns**:
- `Dict[str, Optional[str]]`: Dictionary containing:
  - `unique_identifier`: "owner/repository" string
  - `owner`: Repository owner name
  - `repository`: Repository name

**Expected URL Format**: `https://github.com/owner/repository`

---

### `extract_npm_identifier(self, parsed_url) -> Dict[str, Optional[str]]`
**Purpose**: Extract package name from NPM URLs, including scoped packages.

**Functionality**:
1. Splits URL path into components
2. Expects format: `/package/package-name`
3. Handles scoped packages (e.g., `@types/node`)
4. Returns package name as unique identifier

**Parameters**:
- `parsed_url`: Parsed URL object from `urlparse`

**Returns**:
- `Dict[str, Optional[str]]`: Dictionary containing:
  - `unique_identifier`: Package name
  - `package_name`: Package name

**Supported Formats**:
- Standard packages: `https://npmjs.com/package/express`
- Scoped packages: `https://npmjs.com/package/@types/node`

---

### `extract_huggingface_identifier(self, parsed_url) -> Dict[str, Optional[str]]`
**Purpose**: Extract model, dataset, or space information from Hugging Face URLs.

**Functionality**:
1. Splits URL path into components
2. Handles three types: models, datasets, spaces
3. For datasets/spaces: expects `/datasets/user/name` or `/spaces/user/name`
4. For models: expects `/user/model-name`
5. Handles cases with or without user ownership

**Parameters**:
- `parsed_url`: Parsed URL object from `urlparse`

**Returns**:
- `Dict[str, Optional[str]]`: Dictionary containing:
  - `unique_identifier`: Identifier string
  - `owner`: Owner name (if applicable)
  - `repository`: Model/dataset/space name
  - `package_name`: Same as repository

**Supported Formats**:
- Models: `https://huggingface.co/microsoft/DialoGPT-medium`
- Datasets: `https://huggingface.co/datasets/squad`
- Spaces: `https://huggingface.co/spaces/gradio/hello_world`

---

### `extract_unique_identifier(self, parsed_url, category: URLCategory) -> Dict[str, Optional[str]]`
**Purpose**: Route identifier extraction to the appropriate category-specific method.

**Functionality**:
1. Determines which extraction method to use based on category
2. Calls the appropriate extraction function
3. Returns extracted identifiers or None for unknown categories

**Parameters**:
- `parsed_url`: Parsed URL object
- `category (URLCategory)`: The determined category

**Returns**:
- `Dict[str, Optional[str]]`: Extracted identifiers specific to the category

---

### `handle_url(self, url_string: str) -> URLData`
**Purpose**: Main orchestration method that processes a URL through the complete pipeline.

**Functionality**:
1. **Validation**: Validates URL format
2. **Parsing**: Parses URL into components
3. **Classification**: Determines category based on hostname
4. **Extraction**: Extracts unique identifiers
5. **Assembly**: Creates and returns URLData object

**Parameters**:
- `url_string (str)`: The URL string to process

**Returns**:
- `URLData`: Complete structured data object with all extracted information

**Processing Flow**:
1. Initialize URLData with defaults
2. Validate URL format → set error if invalid
3. Parse URL → extract hostname
4. Classify hostname → determine category
5. Extract identifiers → populate fields
6. Return complete URLData object

---

## File Processing Functions

### `read_urls_from_file(file_path: str) -> List[str]`
**Purpose**: Read URLs from a file, one URL per line, with comment support.

**Functionality**:
1. Opens file with UTF-8 encoding
2. Reads line by line
3. Strips whitespace from each line
4. Skips empty lines and comments (lines starting with #)
5. Returns list of clean URL strings

**Parameters**:
- `file_path (str)`: Path to file containing URLs

**Returns**:
- `List[str]`: List of URL strings

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `IOError`: If file cannot be read

**File Format**:
```
# Comments start with #
https://github.com/user/repo
https://npmjs.com/package/name

# Empty lines are ignored
https://huggingface.co/model
```

---

### `process_url_file(file_path: str) -> List[URLData]`
**Purpose**: Process all URLs from a file and return complete results.

**Functionality**:
1. Reads URLs from file using `read_urls_from_file`
2. Creates URLHandler instance
3. Processes each URL individually
4. Collects all results into a list

**Parameters**:
- `file_path (str)`: Path to file containing URLs

**Returns**:
- `List[URLData]`: List of processed URL data objects

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `IOError`: If file cannot be read

---

## Utility Functions

### `get_valid_urls(results: List[URLData]) -> List[URLData]`
**Purpose**: Filter and return only valid URLs from processing results.

**Functionality**:
- Filters URLData objects where `is_valid` is True
- Returns new list containing only valid results

**Parameters**:
- `results (List[URLData])`: List of URL processing results

**Returns**:
- `List[URLData]`: Filtered list containing only valid URLs

---

### `get_urls_by_category(results: List[URLData], category: URLCategory) -> List[URLData]`
**Purpose**: Filter URLs by category from processing results.

**Functionality**:
1. Filters URLData objects by specified category
2. Only includes valid URLs (is_valid = True)
3. Returns filtered list

**Parameters**:
- `results (List[URLData])`: List of URL processing results
- `category (URLCategory)`: Category to filter by

**Returns**:
- `List[URLData]`: URLs matching the specified category

---

### `get_processing_summary(results: List[URLData]) -> Dict[str, Any]`
**Purpose**: Generate comprehensive summary statistics and categorized results.

**Functionality**:
1. Counts total, valid, and invalid URLs
2. Categorizes URLs by type (GitHub, NPM, Hugging Face, Unknown)
3. Separates valid and invalid URLs
4. Creates comprehensive summary dictionary

**Parameters**:
- `results (List[URLData])`: List of URL processing results

**Returns**:
- `Dict[str, Any]`: Comprehensive summary containing:
  - `total_urls`: Total number of URLs processed
  - `valid_count`: Number of valid URLs
  - `invalid_count`: Number of invalid URLs
  - `categories`: Count breakdown by category
  - `valid_urls`: List of valid URLData objects
  - `invalid_urls`: List of invalid URLData objects
  - `github_urls`: List of GitHub URLs
  - `npm_urls`: List of NPM URLs
  - `huggingface_urls`: List of Hugging Face URLs
  - `unknown_urls`: List of unknown category URLs

---

## Convenience Functions

### `handle_url(url_string: str) -> URLData`
**Purpose**: Standalone convenience function for processing a single URL.

**Functionality**:
1. Creates URLHandler instance
2. Processes single URL
3. Returns result

**Parameters**:
- `url_string (str)`: The URL string to process

**Returns**:
- `URLData`: Processed URL data object

**Usage**: Ideal for single URL processing without creating URLHandler instance manually.

---

## Command Line Interface

### `main()`
**Purpose**: Provide command-line interface for URL processing.

**Functionality**:
1. **Test Mode** (`--test`): Runs built-in test suite with sample URLs
2. **File Mode**: Processes URLs from specified file

**Command Line Usage**:
```bash
# Run built-in tests
python url_handler.py --test

# Process file
python url_handler.py path/to/urls.txt
```

**Test Mode Output**:
- Processes 8 sample URLs covering all categories
- Shows detailed results for each URL
- Demonstrates validation, classification, and extraction

**File Mode Output**:
- Processing summary with counts
- Detailed results for each URL
- Success/failure indicators

---

## Error Handling

### Validation Errors
- **Empty/None input**: Returns invalid URLData with "Invalid URL format"
- **Missing scheme**: Returns invalid URLData with "Invalid URL format"
- **Unsupported scheme**: Returns invalid URLData with "Invalid URL format"
- **Malformed hostname**: Returns invalid URLData with "Invalid URL format"

### File Processing Errors
- **File not found**: Raises `FileNotFoundError` with descriptive message
- **Read permissions**: Raises `IOError` with descriptive message
- **Encoding issues**: Handled gracefully with UTF-8 encoding

### Processing Errors
- **Parsing exceptions**: Caught and converted to URLData with error message
- **Extraction failures**: Return None values for identifiers
- **Unknown categories**: Classified as UNKNOWN, not errors

---

## Integration with Other Modules

### For Metrics Module
The URL handler provides clean APIs for metrics calculation:

```python
# Process file and get summary
results = process_url_file('urls.txt')
summary = get_processing_summary(results)

# Access specific categories
github_repos = summary['github_urls']
npm_packages = summary['npm_urls']
huggingface_models = summary['huggingface_urls']

# Calculate metrics per category
for repo in github_repos:
    # Process GitHub-specific metrics
    owner = repo.owner
    repository = repo.repository
    
for package in npm_packages:
    # Process NPM-specific metrics
    package_name = package.package_name
    
for model in huggingface_models:
    # Process Hugging Face-specific metrics
    identifier = model.unique_identifier
```

### Data Access Patterns
- **Batch Processing**: Use `process_url_file()` for file-based processing
- **Single URL**: Use `handle_url()` for individual URLs
- **Filtering**: Use utility functions for category-specific processing
- **Summary Statistics**: Use `get_processing_summary()` for overview metrics

---

## Performance Characteristics

### Time Complexity
- **Single URL**: O(1) - Constant time processing
- **File Processing**: O(n) - Linear with number of URLs
- **Filtering**: O(n) - Linear scan through results

### Memory Usage
- **Efficient**: Processes URLs one at a time
- **Scalable**: Memory usage scales linearly with number of URLs
- **No caching**: Each URL processed independently

### Error Recovery
- **Graceful degradation**: Invalid URLs don't stop processing
- **Individual failures**: One bad URL doesn't affect others
- **Comprehensive logging**: Detailed error messages for debugging

---

## Testing and Validation

### Built-in Test Suite
The module includes comprehensive tests covering:
- **Valid URLs**: All three supported categories
- **Invalid URLs**: Various malformed formats
- **Edge Cases**: Scoped packages, datasets, spaces
- **Error Conditions**: Empty strings, unsupported schemes

### Test Categories
1. **URL Validation**: 12+ test cases for validation logic
2. **Hostname Classification**: All hostname variations
3. **Identifier Extraction**: Complex extraction scenarios
4. **End-to-End**: Complete processing workflows
5. **File Processing**: Batch processing validation

### Quality Assurance
- **100% category coverage**: All supported platforms tested
- **Error path testing**: All error conditions validated
- **Edge case handling**: Boundary conditions tested
- **Integration testing**: File processing and team interface tested

---

## Future Extensibility

### Adding New Categories
To add support for new platforms:
1. Add new value to `URLCategory` enum
2. Add hostname mapping in `__init__`
3. Implement category-specific extraction method
4. Update `extract_unique_identifier` routing
5. Update summary generation and tests

### Modifying Extraction Logic
- **Category-specific**: Modify individual extraction methods
- **Generic changes**: Update `handle_url` main flow
- **Validation rules**: Modify `validate_url` method

### Performance Optimization
- **Caching**: Add hostname classification caching
- **Async processing**: Convert to async for large file processing
- **Streaming**: Add streaming support for very large files

---

## Conclusion

The URL Handler module provides a robust, extensible foundation for URL processing in the package registry system. It cleanly separates concerns between validation, classification, and extraction while providing both single-URL and batch processing capabilities. The module is designed to integrate seamlessly with other system components while maintaining high performance and reliability.
