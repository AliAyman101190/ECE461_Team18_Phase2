import os
import re
import sys
import importlib
import types
import logging
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional, Union, List
# from dataclasses import dataclass
# from enum import Enum
from url_category import URLCategory
from url_data import URLData

os.makedirs('logs', exist_ok=True)
LOG_FILE = os.path.join('logs', 'url_handler.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(LOG_FILE) for h in logger.handlers):
    fh = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
logger.propagate = False

logger.info("url_handler initialized; logging to %s", LOG_FILE)


class URLHandler:
    def __init__(self):
        self.hostname_categories = {
            'github.com': URLCategory.GITHUB,
            'www.github.com': URLCategory.GITHUB,
            'npmjs.com': URLCategory.NPM,
            'www.npmjs.com': URLCategory.NPM,
            'huggingface.co': URLCategory.HUGGINGFACE,
            'www.huggingface.co': URLCategory.HUGGINGFACE,
        }
    
    def validate_url(self, url_string: str) -> bool:
        try:
            # Basic URL format validation
            if not url_string or not isinstance(url_string, str):
                logger.debug("validate_url: invalid input type or empty string: %r", url_string)
                return False
            
            # Parse the URL
            parsed = urlparse(url_string.strip())
            
            # Check if scheme and netloc are present
            if not parsed.scheme or not parsed.netloc:
                logger.debug("validate_url: missing scheme or netloc in parsed URL: %s", parsed)
                return False
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                logger.debug("validate_url: unsupported scheme %s", parsed.scheme)
                return False
            
            # Basic hostname validation
            hostname = parsed.netloc.lower()
            if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
                logger.debug("validate_url: invalid hostname format: %s", hostname)
                return False
            
            return True
            
        except Exception:
            logger.exception("validate_url: unexpected error while validating %r", url_string)
            return False
    
    def classify_hostname(self, hostname: str) -> URLCategory:
        hostname_lower = hostname.lower()
        
        # Remove www. prefix for classification
        if hostname_lower.startswith('www.'):
            hostname_lower = hostname_lower[4:]
        
        # Direct mapping check
        for known_hostname, category in self.hostname_categories.items():
            if known_hostname.endswith(hostname_lower) or hostname_lower.endswith(known_hostname.replace('www.', '')):
                logger.debug("classify_hostname: matched %s -> %s", hostname, category)
                return category
        
        # Pattern matching for common variations
        if 'github' in hostname_lower:
            logger.debug("classify_hostname: pattern matched github for %s", hostname)
            return URLCategory.GITHUB
        elif 'npm' in hostname_lower:
            logger.debug("classify_hostname: pattern matched npm for %s", hostname)
            return URLCategory.NPM
        elif 'huggingface' in hostname_lower:
            logger.debug("classify_hostname: pattern matched huggingface for %s", hostname)
            return URLCategory.HUGGINGFACE
        
        return URLCategory.UNKNOWN
    
    def extract_github_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repository = path_parts[1]
            unique_id = f"{owner}/{repository}"
            logger.debug("extract_github_identifier: extracted %s from path %s", unique_id, parsed_url.path)
            return {
                'unique_identifier': unique_id,
                'owner': owner,
                'repository': repository
            }
        
        return {'unique_identifier': None, 'owner': None, 'repository': None}
    
    def extract_npm_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        # Handle different NPM URL patterns
        if len(path_parts) >= 2 and path_parts[0] == 'package':
            package_name = path_parts[1]
            # Handle scoped packages (@scope/package-name)
            if len(path_parts) >= 3 and path_parts[1].startswith('@'):
                package_name = f"{path_parts[1]}/{path_parts[2]}"
            logger.debug("extract_npm_identifier: extracted package %s from path %s", package_name, parsed_url.path)
            
            return {
                'unique_identifier': package_name,
                'package_name': package_name
            }
        
        return {'unique_identifier': None, 'package_name': None}
    
    def extract_huggingface_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        # Handle different Hugging Face URL patterns
        # Examples: /username/model-name, /datasets/username/dataset-name, /spaces/username/space-name
        if len(path_parts) >= 2:
            if path_parts[0] in ['datasets', 'spaces']:
                # For datasets and spaces: /datasets/user/name or /spaces/user/name
                if len(path_parts) >= 3:
                    owner = path_parts[1]
                    model_name = path_parts[2]
                    unique_id = f"{owner}/{model_name}"
                    logger.debug("extract_huggingface_identifier: extracted %s (owner=%s) from %s", unique_id, owner, parsed_url.path)
                    return {
                        'unique_identifier': unique_id,
                        'owner': owner,
                        'repository': model_name,
                        'package_name': model_name
                    }
                elif len(path_parts) == 2:
                    # For cases like /datasets/squad (no user)
                    model_name = path_parts[1]
                    logger.debug("extract_huggingface_identifier: extracted dataset/space name %s from %s", model_name, parsed_url.path)
                    return {
                        'unique_identifier': model_name,
                        'owner': None,
                        'repository': model_name,
                        'package_name': model_name
                    }
            else:
                # For models: /username/model-name
                owner = path_parts[0]
                model_name = path_parts[1]
                unique_id = f"{owner}/{model_name}"
                logger.debug("extract_huggingface_identifier: extracted model %s from %s", unique_id, parsed_url.path)
                return {
                    'unique_identifier': unique_id,
                    'owner': owner,
                    'repository': model_name,
                    'package_name': model_name
                }
        
        return {'unique_identifier': None, 'owner': None, 'repository': None, 'package_name': None}
    
    def extract_unique_identifier(self, parsed_url, category: URLCategory) -> Dict[str, Optional[str]]:
        if category == URLCategory.GITHUB:
            return self.extract_github_identifier(parsed_url)
        elif category == URLCategory.NPM:
            return self.extract_npm_identifier(parsed_url)
        elif category == URLCategory.HUGGINGFACE:
            return self.extract_huggingface_identifier(parsed_url)
        else:
            return {'unique_identifier': None}
    
    def handle_url(self, url_string: str) -> URLData:
        # Initialize default response
        url_data = URLData(
            original_url=url_string,
            category=URLCategory.UNKNOWN,
            hostname="",
            is_valid=False
        )
        
        # Step 1: Validate URL
        if not self.validate_url(url_string):
            url_data.error_message = "Invalid URL format"
            logger.warning("handle_url: invalid URL provided: %r", url_string)
            return url_data
        
        try:
            # Step 2: Parse URL
            parsed_url = urlparse(url_string.strip())
            hostname = parsed_url.netloc.lower()
            url_data.hostname = hostname
            url_data.is_valid = True
            
            # Step 3: Classify hostname
            category = self.classify_hostname(hostname)
            url_data.category = category
            logger.info("handle_url: %s classified as %s", hostname, category.value)
            
            # Step 4: Extract unique identifiers
            if category != URLCategory.UNKNOWN:
                identifiers = self.extract_unique_identifier(parsed_url, category)
                
                # Update url_data with extracted identifiers
                for key, value in identifiers.items():
                    if hasattr(url_data, key):
                        setattr(url_data, key, value)
                logger.info("handle_url: extracted identifiers for %s: %s", url_string, {k: v for k, v in identifiers.items() if v is not None})
            
            return url_data
            
        except Exception as e:
            url_data.is_valid = False
            url_data.error_message = f"Error processing URL: {str(e)}"
            logger.exception("handle_url: unexpected error processing %r", url_string)
            return url_data
        
    # File processing functions
    def read_urls_from_file(self, file_path: str) -> List[Dict[str, str]]:
        try:
            logger.info("read_urls_from_file: reading URLs from %s", file_path)
            urls = []
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    result = {}
                    line = line.strip()
                    code_url, dataset_url, model_url = line.split(',') # <code, dataset, model>
                    # print(code_url, dataset_url, model_url)
                    result['code'] = code_url.strip()
                    result['dataset'] = dataset_url.strip()
                    result['model'] = model_url.strip()
                    urls.append(result)
            return urls
                # urls = []
                # for line_num, line in enumerate(file, 1):
                #     url = line.strip()
                #     if url and not url.startswith('#'):  # Skip empty lines and comments
                #         urls.append(url)
                # logger.info("read_urls_from_file: found %d candidate URLs", len(urls))
                # return urls
        except FileNotFoundError:
            raise FileNotFoundError(f"URL file not found: {file_path}")
        except Exception as e:
            raise IOError(f"Error reading URL file {file_path}: {str(e)}")


# # File processing functions
# def read_urls_from_file(file_path: str) -> List[str]:
#     try:
#         logger.info("read_urls_from_file: reading URLs from %s", file_path)
#         with open(file_path, 'r', encoding='utf-8') as file:
#             urls = []
#             for line_num, line in enumerate(file, 1):
#                 url = line.strip()
#                 if url and not url.startswith('#'):  # Skip empty lines and comments
#                     urls.append(url)
#             logger.info("read_urls_from_file: found %d candidate URLs", len(urls))
#             return urls
#     except FileNotFoundError:
#         raise FileNotFoundError(f"URL file not found: {file_path}")
#     except Exception as e:
#         raise IOError(f"Error reading URL file {file_path}: {str(e)}")


# def process_url_file(file_path: str) -> List[URLData]:
#     logger.info("process_url_file: starting processing for %s", file_path)
#     urls = read_urls_from_file(file_path)
#     handler = URLHandler()
    
#     results = []
#     for url in urls:
#         logger.debug("process_url_file: handling URL %s", url)
#         result = handler.handle_url(url)
#         results.append(result)
#     logger.info("process_url_file: completed processing %d URLs", len(results))
    
#     return results


# def get_valid_urls(results: List[URLData]) -> List[URLData]:
#     return [result for result in results if result.is_valid]


# def get_urls_by_category(results: List[URLData], category: URLCategory) -> List[URLData]:
#     return [result for result in results if result.category == category and result.is_valid]


# def get_processing_summary(results: List[URLData]) -> Dict[str, Any]:
#     total_urls = len(results)
#     valid_urls = get_valid_urls(results)
#     invalid_urls = [result for result in results if not result.is_valid]
    
#     # Count by category
#     github_urls = get_urls_by_category(results, URLCategory.GITHUB)
#     npm_urls = get_urls_by_category(results, URLCategory.NPM)
#     huggingface_urls = get_urls_by_category(results, URLCategory.HUGGINGFACE)
#     unknown_urls = get_urls_by_category(results, URLCategory.UNKNOWN)
    
#     return {
#         'total_urls': total_urls,
#         'valid_count': len(valid_urls),
#         'invalid_count': len(invalid_urls),
#         'categories': {
#             'github': len(github_urls),
#             'npm': len(npm_urls),
#             'huggingface': len(huggingface_urls),
#             'unknown': len(unknown_urls)
#         },
#         'valid_urls': valid_urls,
#         'invalid_urls': invalid_urls,
#         'github_urls': github_urls,
#         'npm_urls': npm_urls,
#         'huggingface_urls': huggingface_urls,
#         'unknown_urls': unknown_urls
#     }


# # Convenience function for easy access
# def handle_url(url_string: str) -> URLData:
#     handler = URLHandler()
#     return handler.handle_url(url_string)


# # Command-line interface and main execution
# def main():
#     import sys
    
#     if len(sys.argv) < 2:
#         print("Usage: python url_handler.py <url_file_path>")
#         print("       python url_handler.py --test")
#         sys.exit(1)
    
#     if sys.argv[1] == "--test":
#         # Run built-in tests
#         test_urls = [
#             "https://github.com/octocat/Hello-World",
#             "https://www.npmjs.com/package/express",
#             "https://huggingface.co/microsoft/DialoGPT-medium",
#             "https://invalid-url",
#             "not-a-url-at-all",
#             "https://github.com/microsoft/typescript",
#             "https://www.npmjs.com/package/@angular/core",
#             "https://huggingface.co/datasets/squad",
#         ]
        
#         handler = URLHandler()
        
#         print("URL Handler Test Results:")
#         print("=" * 50)
        
#         for url in test_urls:
#             result = handler.handle_url(url)
#             print(f"\nURL: {url}")
#             print(f"Valid: {result.is_valid}")
#             print(f"Category: {result.category.value}")
#             print(f"Hostname: {result.hostname}")
#             print(f"Unique ID: {result.unique_identifier}")
#             if result.owner:
#                 print(f"Owner: {result.owner}")
#             if result.repository:
#                 print(f"Repository: {result.repository}")
#             if result.package_name:
#                 print(f"Package: {result.package_name}")
#             if result.version:
#                 print(f"Version: {result.version}")
#             if result.error_message:
#                 print(f"Error: {result.error_message}")
#             print("-" * 30)
#     else:
#         # Process file
#         file_path = sys.argv[1]
#         try:
#             print(f"Processing URLs from file: {file_path}")
#             results = process_url_file(file_path)
#             summary = get_processing_summary(results)
            
#             print(f"\nProcessing Summary:")
#             print(f"Total URLs: {summary['total_urls']}")
#             print(f"Valid URLs: {summary['valid_count']}")
#             print(f"Invalid URLs: {summary['invalid_count']}")
#             print(f"GitHub URLs: {summary['categories']['github']}")
#             print(f"NPM URLs: {summary['categories']['npm']}")
#             print(f"Hugging Face URLs: {summary['categories']['huggingface']}")
#             print(f"Unknown URLs: {summary['categories']['unknown']}")
            
#             print(f"\nDetailed Results:")
#             print("=" * 50)
#             for result in results:
#                 status = "✓" if result.is_valid else "✗"
#                 print(f"{status} {result.original_url}")
#                 if result.is_valid:
#                     print(f"   Category: {result.category.value}")
#                     if result.unique_identifier:
#                         print(f"   ID: {result.unique_identifier}")
#                 else:
#                     print(f"   Error: {result.error_message}")
#                 print()
            
#         except (FileNotFoundError, IOError) as e:
#             print(f"Error: {e}")
#             sys.exit(1)


# if __name__ == "__main__":
#     main()

# --- Compatibility shim for tests expecting package-style imports ---
# Allows: from url_handler import ... (already works when this module
# is imported as url_handler), and from url_handler.url_handler import ...
# by exposing this module under the package-style name at runtime when
# imported as top-level module via sys.path insertion in tests.

# module_name = __name__
# if module_name == "url_handler":
#     # Pretend to be a package to allow submodule imports
#     try:
#         __path__  # type: ignore # may already exist
#     except NameError:
#         __path__ = []  # type: ignore

#     # Ensure attribute access for url_handler.url_handler resolves to this module
#     sys.modules.setdefault("url_handler.url_handler", sys.modules[module_name])

#     # Map url_handler.data_retrieval to the top-level data_retrieval module
#     try:
#         dr_mod = importlib.import_module("data_retrieval")
#         sys.modules.setdefault("url_handler.data_retrieval", dr_mod)
#     except Exception:
#         # If data_retrieval isn't importable yet, skip mapping; typical test imports
#         # import url_handler first which triggers this mapping before importing
#         # data_retrieval via package path in later imports.
#         pass
#     # Export expected attributes when importing the package name alone
#     __all__ = [
#         "URLHandler",
#         "handle_url",
#         "URLCategory",
#         "URLData",
#         "read_urls_from_file",
#         "process_url_file",
#         "get_valid_urls",
#         "get_urls_by_category",
#         "get_processing_summary",
#     ]