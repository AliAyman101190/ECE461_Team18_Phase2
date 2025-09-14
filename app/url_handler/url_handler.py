"""
URL Handler Module

This module provides functionality to handle URL parsing, validation, and classification.
It takes in URL strings, validates them, classifies them by hostname into categories,
extracts unique identifiers, and returns structured data objects.
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum


class URLCategory(Enum):
    """Enumeration of supported URL categories."""
    GITHUB = "github"
    NPM = "npm"
    HUGGINGFACE = "huggingface"
    UNKNOWN = "unknown"


@dataclass
class URLData:
    """Structured data object for URL information."""
    original_url: str
    category: URLCategory
    hostname: str
    is_valid: bool
    unique_identifier: Optional[str] = None
    owner: Optional[str] = None
    repository: Optional[str] = None
    package_name: Optional[str] = None
    version: Optional[str] = None
    error_message: Optional[str] = None


class URLHandler:
    """Main URL handler class for processing URLs."""
    
    def __init__(self):
        """Initialize the URL handler with hostname mappings."""
        self.hostname_categories = {
            'github.com': URLCategory.GITHUB,
            'www.github.com': URLCategory.GITHUB,
            'npmjs.com': URLCategory.NPM,
            'www.npmjs.com': URLCategory.NPM,
            'huggingface.co': URLCategory.HUGGINGFACE,
            'www.huggingface.co': URLCategory.HUGGINGFACE,
        }
    
    def validate_url(self, url_string: str) -> bool:
        """
        Validate if the URL string is a properly formatted URL.
        
        Args:
            url_string (str): The URL string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Basic URL format validation
            if not url_string or not isinstance(url_string, str):
                return False
            
            # Parse the URL
            parsed = urlparse(url_string.strip())
            
            # Check if scheme and netloc are present
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Basic hostname validation
            hostname = parsed.netloc.lower()
            if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
                return False
            
            return True
            
        except Exception:
            return False
    
    def classify_hostname(self, hostname: str) -> URLCategory:
        """
        Classify the hostname into one of the supported categories.
        
        Args:
            hostname (str): The hostname to classify
            
        Returns:
            URLCategory: The category the hostname belongs to
        """
        hostname_lower = hostname.lower()
        
        # Remove www. prefix for classification
        if hostname_lower.startswith('www.'):
            hostname_lower = hostname_lower[4:]
        
        # Direct mapping check
        for known_hostname, category in self.hostname_categories.items():
            if known_hostname.endswith(hostname_lower) or hostname_lower.endswith(known_hostname.replace('www.', '')):
                return category
        
        # Pattern matching for common variations
        if 'github' in hostname_lower:
            return URLCategory.GITHUB
        elif 'npm' in hostname_lower:
            return URLCategory.NPM
        elif 'huggingface' in hostname_lower:
            return URLCategory.HUGGINGFACE
        
        return URLCategory.UNKNOWN
    
    def extract_github_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        """Extract unique identifier from GitHub URLs."""
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repository = path_parts[1]
            unique_id = f"{owner}/{repository}"
            return {
                'unique_identifier': unique_id,
                'owner': owner,
                'repository': repository
            }
        
        return {'unique_identifier': None, 'owner': None, 'repository': None}
    
    def extract_npm_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        """Extract unique identifier from NPM URLs."""
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        # Handle different NPM URL patterns
        if len(path_parts) >= 2 and path_parts[0] == 'package':
            package_name = path_parts[1]
            # Handle scoped packages (@scope/package-name)
            if len(path_parts) >= 3 and path_parts[1].startswith('@'):
                package_name = f"{path_parts[1]}/{path_parts[2]}"
            
            return {
                'unique_identifier': package_name,
                'package_name': package_name
            }
        
        return {'unique_identifier': None, 'package_name': None}
    
    def extract_huggingface_identifier(self, parsed_url) -> Dict[str, Optional[str]]:
        """Extract unique identifier from Hugging Face URLs."""
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
                    return {
                        'unique_identifier': unique_id,
                        'owner': owner,
                        'repository': model_name,
                        'package_name': model_name
                    }
                elif len(path_parts) == 2:
                    # For cases like /datasets/squad (no user)
                    model_name = path_parts[1]
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
                return {
                    'unique_identifier': unique_id,
                    'owner': owner,
                    'repository': model_name,
                    'package_name': model_name
                }
        
        return {'unique_identifier': None, 'owner': None, 'repository': None, 'package_name': None}
    
    def extract_unique_identifier(self, parsed_url, category: URLCategory) -> Dict[str, Optional[str]]:
        """
        Extract unique identifier based on the URL category.
        
        Args:
            parsed_url: Parsed URL object
            category (URLCategory): The category of the URL
            
        Returns:
            Dict[str, Optional[str]]: Dictionary containing extracted identifiers
        """
        if category == URLCategory.GITHUB:
            return self.extract_github_identifier(parsed_url)
        elif category == URLCategory.NPM:
            return self.extract_npm_identifier(parsed_url)
        elif category == URLCategory.HUGGINGFACE:
            return self.extract_huggingface_identifier(parsed_url)
        else:
            return {'unique_identifier': None}
    
    def handle_url(self, url_string: str) -> URLData:
        """
        Main function to handle URL processing.
        
        Args:
            url_string (str): The URL string to process
            
        Returns:
            URLData: Structured data object containing URL information
        """
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
            
            # Step 4: Extract unique identifiers
            if category != URLCategory.UNKNOWN:
                identifiers = self.extract_unique_identifier(parsed_url, category)
                
                # Update url_data with extracted identifiers
                for key, value in identifiers.items():
                    if hasattr(url_data, key):
                        setattr(url_data, key, value)
            
            return url_data
            
        except Exception as e:
            url_data.is_valid = False
            url_data.error_message = f"Error processing URL: {str(e)}"
            return url_data


# File processing functions
def read_urls_from_file(file_path: str) -> List[str]:
    """
    Read URLs from a file, one URL per line.
    
    Args:
        file_path (str): Path to the file containing URLs
        
    Returns:
        List[str]: List of URL strings
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = []
            for line_num, line in enumerate(file, 1):
                url = line.strip()
                if url and not url.startswith('#'):  # Skip empty lines and comments
                    urls.append(url)
            return urls
    except FileNotFoundError:
        raise FileNotFoundError(f"URL file not found: {file_path}")
    except Exception as e:
        raise IOError(f"Error reading URL file {file_path}: {str(e)}")


def process_url_file(file_path: str) -> List[URLData]:
    """
    Process all URLs from a file and return results.
    
    Args:
        file_path (str): Path to the file containing URLs
        
    Returns:
        List[URLData]: List of processed URL data objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    urls = read_urls_from_file(file_path)
    handler = URLHandler()
    
    results = []
    for url in urls:
        result = handler.handle_url(url)
        results.append(result)
    
    return results


def get_valid_urls(results: List[URLData]) -> List[URLData]:
    """
    Filter and return only valid URLs from processing results.
    
    Args:
        results (List[URLData]): List of URL processing results
        
    Returns:
        List[URLData]: List containing only valid URL data
    """
    return [result for result in results if result.is_valid]


def get_urls_by_category(results: List[URLData], category: URLCategory) -> List[URLData]:
    """
    Filter URLs by category from processing results.
    
    Args:
        results (List[URLData]): List of URL processing results
        category (URLCategory): Category to filter by
        
    Returns:
        List[URLData]: List of URLs matching the specified category
    """
    return [result for result in results if result.category == category and result.is_valid]


def get_processing_summary(results: List[URLData]) -> Dict[str, Any]:
    """
    Generate a summary of URL processing results for other modules.
    
    Args:
        results (List[URLData]): List of URL processing results
        
    Returns:
        Dict[str, Any]: Summary statistics and categorized results
    """
    total_urls = len(results)
    valid_urls = get_valid_urls(results)
    invalid_urls = [result for result in results if not result.is_valid]
    
    # Count by category
    github_urls = get_urls_by_category(results, URLCategory.GITHUB)
    npm_urls = get_urls_by_category(results, URLCategory.NPM)
    huggingface_urls = get_urls_by_category(results, URLCategory.HUGGINGFACE)
    unknown_urls = get_urls_by_category(results, URLCategory.UNKNOWN)
    
    return {
        'total_urls': total_urls,
        'valid_count': len(valid_urls),
        'invalid_count': len(invalid_urls),
        'categories': {
            'github': len(github_urls),
            'npm': len(npm_urls),
            'huggingface': len(huggingface_urls),
            'unknown': len(unknown_urls)
        },
        'valid_urls': valid_urls,
        'invalid_urls': invalid_urls,
        'github_urls': github_urls,
        'npm_urls': npm_urls,
        'huggingface_urls': huggingface_urls,
        'unknown_urls': unknown_urls
    }


# Convenience function for easy access
def handle_url(url_string: str) -> URLData:
    """
    Convenience function to handle a single URL.
    
    Args:
        url_string (str): The URL string to process
        
    Returns:
        URLData: Structured data object containing URL information
    """
    handler = URLHandler()
    return handler.handle_url(url_string)


# Command-line interface and main execution
def main():
    """Main function for command-line execution."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python url_handler.py <url_file_path>")
        print("       python url_handler.py --test")
        sys.exit(1)
    
    if sys.argv[1] == "--test":
        # Run built-in tests
        test_urls = [
            "https://github.com/octocat/Hello-World",
            "https://www.npmjs.com/package/express",
            "https://huggingface.co/microsoft/DialoGPT-medium",
            "https://invalid-url",
            "not-a-url-at-all",
            "https://github.com/microsoft/typescript",
            "https://www.npmjs.com/package/@angular/core",
            "https://huggingface.co/datasets/squad",
        ]
        
        handler = URLHandler()
        
        print("URL Handler Test Results:")
        print("=" * 50)
        
        for url in test_urls:
            result = handler.handle_url(url)
            print(f"\nURL: {url}")
            print(f"Valid: {result.is_valid}")
            print(f"Category: {result.category.value}")
            print(f"Hostname: {result.hostname}")
            print(f"Unique ID: {result.unique_identifier}")
            if result.owner:
                print(f"Owner: {result.owner}")
            if result.repository:
                print(f"Repository: {result.repository}")
            if result.package_name:
                print(f"Package: {result.package_name}")
            if result.version:
                print(f"Version: {result.version}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            print("-" * 30)
    else:
        # Process file
        file_path = sys.argv[1]
        try:
            print(f"Processing URLs from file: {file_path}")
            results = process_url_file(file_path)
            summary = get_processing_summary(results)
            
            print(f"\nProcessing Summary:")
            print(f"Total URLs: {summary['total_urls']}")
            print(f"Valid URLs: {summary['valid_count']}")
            print(f"Invalid URLs: {summary['invalid_count']}")
            print(f"GitHub URLs: {summary['categories']['github']}")
            print(f"NPM URLs: {summary['categories']['npm']}")
            print(f"Hugging Face URLs: {summary['categories']['huggingface']}")
            print(f"Unknown URLs: {summary['categories']['unknown']}")
            
            print(f"\nDetailed Results:")
            print("=" * 50)
            for result in results:
                status = "✓" if result.is_valid else "✗"
                print(f"{status} {result.original_url}")
                if result.is_valid:
                    print(f"   Category: {result.category.value}")
                    if result.unique_identifier:
                        print(f"   ID: {result.unique_identifier}")
                else:
                    print(f"   Error: {result.error_message}")
                print()
            
        except (FileNotFoundError, IOError) as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()