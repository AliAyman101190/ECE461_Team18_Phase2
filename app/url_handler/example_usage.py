#!/usr/bin/env python3
"""
Example usage of the URL Handler module.

This script demonstrates how to use the URL handler to process various URLs
and extract structured information from them.
"""

from url_handler import URLHandler, handle_url, URLCategory


def main():
    """Demonstrate URL handler usage with various examples."""
    
    print("URL Handler Example Usage")
    print("=" * 50)
    
    # Create a URL handler instance
    handler = URLHandler()
    
    # Example URLs to process
    example_urls = [
        "https://github.com/nodejs/node",
        "https://www.npmjs.com/package/react",
        "https://pypi.org/project/requests/2.28.1/",
        "https://github.com/facebook/react",
        "https://www.npmjs.com/package/@types/node",
        "https://invalid.url.format",
        "not-a-url",
        "https://unknown-site.com/some/path"
    ]
    
    print("\n1. Using the URLHandler class:")
    print("-" * 30)
    
    for url in example_urls[:4]:  # Process first 4 URLs
        result = handler.handle_url(url)
        
        print(f"\nProcessing: {url}")
        print(f"  Valid: {result.is_valid}")
        print(f"  Category: {result.category.value}")
        print(f"  Hostname: {result.hostname}")
        
        if result.unique_identifier:
            print(f"  Unique ID: {result.unique_identifier}")
        
        if result.owner and result.repository:
            print(f"  GitHub - Owner: {result.owner}, Repo: {result.repository}")
        
        if result.package_name:
            print(f"  Package: {result.package_name}")
            if result.version:
                print(f"  Version: {result.version}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    print("\n\n2. Using the convenience function:")
    print("-" * 40)
    
    for url in example_urls[4:]:  # Process remaining URLs
        result = handle_url(url)
        
        print(f"\nProcessing: {url}")
        if result.is_valid:
            print(f"  ✓ Valid {result.category.value} URL")
            if result.unique_identifier:
                print(f"  ID: {result.unique_identifier}")
        else:
            print(f"  ✗ Invalid URL: {result.error_message}")
    
    print("\n\n3. Processing URLs by category:")
    print("-" * 35)
    
    github_urls = [
        "https://github.com/torvalds/linux",
        "https://github.com/microsoft/vscode"
    ]
    
    npm_urls = [
        "https://www.npmjs.com/package/express",
        "https://www.npmjs.com/package/@angular/cli"
    ]
    
    pypi_urls = [
        "https://pypi.org/project/django/",
        "https://pypi.org/project/flask/2.0.1/"
    ]
    
    print("\nGitHub URLs:")
    for url in github_urls:
        result = handle_url(url)
        if result.category == URLCategory.GITHUB:
            print(f"  {result.owner}/{result.repository}")
    
    print("\nNPM Packages:")
    for url in npm_urls:
        result = handle_url(url)
        if result.category == URLCategory.NPM:
            print(f"  {result.package_name}")
    
    print("\nPyPI Packages:")
    for url in pypi_urls:
        result = handle_url(url)
        if result.category == URLCategory.PYPI:
            version_info = f" (v{result.version})" if result.version else ""
            print(f"  {result.package_name}{version_info}")
    
    print("\n\n4. Error handling examples:")
    print("-" * 30)
    
    error_urls = [
        "",  # Empty string
        "not-a-url",  # No scheme
        "ftp://example.com",  # Unsupported scheme
        "https://",  # No hostname
    ]
    
    for url in error_urls:
        result = handle_url(url)
        print(f"'{url}' -> Error: {result.error_message}")


if __name__ == "__main__":
    main()
