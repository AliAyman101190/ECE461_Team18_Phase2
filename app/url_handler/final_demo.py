#!/usr/bin/env python3
"""
Final Demo: Updated URL Handler
Only accepts GitHub, Hugging Face, and NPM URLs

This demonstrates the updated URL handler that supports exactly three categories:
1. GitHub repositories
2. NPM packages  
3. Hugging Face models/datasets/spaces
"""

from url_handler import handle_url, URLCategory


def demonstrate_supported_categories():
    """Demonstrate all three supported URL categories."""
    
    print("🎯 SUPPORTED URL CATEGORIES")
    print("=" * 50)
    
    test_cases = [
        {
            "category": "GitHub",
            "urls": [
                "https://github.com/microsoft/typescript",
                "https://github.com/facebook/react",
                "https://www.github.com/nodejs/node"
            ]
        },
        {
            "category": "NPM",
            "urls": [
                "https://www.npmjs.com/package/express",
                "https://npmjs.com/package/@types/node",
                "https://www.npmjs.com/package/@angular/core"
            ]
        },
        {
            "category": "Hugging Face",
            "urls": [
                "https://huggingface.co/microsoft/DialoGPT-medium",
                "https://huggingface.co/datasets/squad",
                "https://huggingface.co/spaces/gradio/hello_world"
            ]
        }
    ]
    
    for category_info in test_cases:
        print(f"\n📂 {category_info['category']} URLs:")
        print("-" * 30)
        
        for url in category_info['urls']:
            result = handle_url(url)
            if result.is_valid:
                print(f"✓ {url}")
                print(f"  Category: {result.category.value}")
                print(f"  ID: {result.unique_identifier}")
                if result.owner and result.repository:
                    print(f"  Owner: {result.owner}, Repo: {result.repository}")
                elif result.package_name:
                    print(f"  Package: {result.package_name}")
            else:
                print(f"✗ {url}")
                print(f"  Error: {result.error_message}")
            print()


def demonstrate_unsupported_urls():
    """Demonstrate URLs that are no longer supported."""
    
    print("🚫 UNSUPPORTED/REMOVED CATEGORIES")
    print("=" * 50)
    
    unsupported_urls = [
        ("https://pypi.org/project/django/", "PyPI (removed)"),
        ("https://pypi.org/project/numpy/", "PyPI (removed)"),
        ("https://bitbucket.org/user/repo", "Bitbucket (never supported)"),
        ("https://gitlab.com/user/project", "GitLab (never supported)"),
        ("https://stackoverflow.com/questions/123", "Stack Overflow (never supported)")
    ]
    
    for url, description in unsupported_urls:
        result = handle_url(url)
        status = "unknown" if result.is_valid else "invalid"
        print(f"• {description}")
        print(f"  URL: {url}")
        print(f"  Status: {status} ({result.category.value})")
        if result.error_message:
            print(f"  Error: {result.error_message}")
        print()


def demonstrate_validation_flow():
    """Demonstrate the complete validation flow."""
    
    print("🔍 VALIDATION FLOW DEMONSTRATION")
    print("=" * 50)
    
    flow_examples = [
        {
            "url": "https://github.com/torvalds/linux",
            "description": "Valid GitHub repository"
        },
        {
            "url": "https://www.npmjs.com/package/react",
            "description": "Valid NPM package"
        },
        {
            "url": "https://huggingface.co/bert-base-uncased",
            "description": "Valid Hugging Face model"
        },
        {
            "url": "not-a-valid-url",
            "description": "Invalid URL format"
        },
        {
            "url": "https://pypi.org/project/requests/",
            "description": "Valid URL but unsupported category (PyPI)"
        }
    ]
    
    for example in flow_examples:
        print(f"\nTesting: {example['description']}")
        print(f"URL: {example['url']}")
        
        result = handle_url(example['url'])
        
        print(f"Step 1 - URL Validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
        if not result.is_valid:
            print(f"         Error: {result.error_message}")
            continue
        
        print(f"Step 2 - Hostname Classification: {result.category.value}")
        
        if result.category in [URLCategory.GITHUB, URLCategory.NPM, URLCategory.HUGGINGFACE]:
            print(f"Step 3 - Identifier Extraction: {result.unique_identifier}")
            print(f"Step 4 - Result: ✓ ACCEPTED ({result.category.value})")
        else:
            print(f"Step 3 - Result: ⚠️  VALID BUT UNKNOWN CATEGORY")
        
        print("-" * 30)


def main():
    """Run the complete demonstration."""
    
    print("🚀 URL HANDLER - FINAL CONFIGURATION")
    print("=" * 60)
    print("Supports: GitHub, NPM, Hugging Face")
    print("Removed: PyPI")
    print("=" * 60)
    
    demonstrate_supported_categories()
    demonstrate_unsupported_urls()
    demonstrate_validation_flow()
    
    print("\n✅ DEMONSTRATION COMPLETE!")
    print("\nThe URL handler now only accepts:")
    print("  • GitHub repositories")
    print("  • NPM packages")  
    print("  • Hugging Face models/datasets/spaces")
    print("\nPyPI support has been completely removed.")


if __name__ == "__main__":
    main()
