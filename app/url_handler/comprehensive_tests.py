#!/usr/bin/env python3
"""
Comprehensive Test Suite for URL Handler

This script demonstrates all the different test cases and edge cases
used to validate the URL handler functionality.
"""

from url_handler import URLHandler, handle_url, URLCategory, URLData


def test_url_validation():
    """Test URL validation edge cases."""
    print("🔍 TESTING URL VALIDATION")
    print("=" * 40)
    
    validation_tests = [
        # Valid URLs
        ("https://github.com/user/repo", True, "Standard HTTPS URL"),
        ("http://example.com", True, "Standard HTTP URL"),
        ("https://www.example.com/path", True, "URL with www and path"),
        
        # Invalid URLs
        ("", False, "Empty string"),
        ("not-a-url", False, "String without scheme"),
        ("ftp://example.com", False, "Unsupported scheme"),
        ("https://", False, "Missing hostname"),
        ("://example.com", False, "Missing scheme"),
        ("https://ex ample.com", False, "Space in hostname"),
        ("https://example..com", False, "Double dots in hostname"),
        (None, False, "None value"),
        (123, False, "Non-string input"),
    ]
    
    handler = URLHandler()
    
    for url, expected, description in validation_tests:
        try:
            result = handler.validate_url(url)
            status = "✓" if result == expected else "✗"
            print(f"{status} {description}: '{url}' -> {result}")
        except Exception as e:
            print(f"✗ {description}: '{url}' -> Exception: {e}")
    
    print()


def test_hostname_classification():
    """Test hostname classification for all categories."""
    print("🏷️  TESTING HOSTNAME CLASSIFICATION")
    print("=" * 40)
    
    classification_tests = [
        # GitHub variations
        ("github.com", URLCategory.GITHUB, "GitHub main domain"),
        ("www.github.com", URLCategory.GITHUB, "GitHub with www"),
        ("api.github.com", URLCategory.GITHUB, "GitHub subdomain"),
        
        # NPM variations
        ("npmjs.com", URLCategory.NPM, "NPM main domain"),
        ("www.npmjs.com", URLCategory.NPM, "NPM with www"),
        ("registry.npmjs.com", URLCategory.NPM, "NPM registry"),
        
        # PyPI variations
        ("pypi.org", URLCategory.PYPI, "PyPI main domain"),
        ("www.pypi.org", URLCategory.PYPI, "PyPI with www"),
        ("files.pythonhosted.org", URLCategory.UNKNOWN, "PyPI files domain (unknown)"),
        
        # Unknown domains
        ("example.com", URLCategory.UNKNOWN, "Unknown domain"),
        ("stackoverflow.com", URLCategory.UNKNOWN, "Popular but unknown domain"),
        ("bitbucket.org", URLCategory.UNKNOWN, "Similar to GitHub but unknown"),
    ]
    
    handler = URLHandler()
    
    for hostname, expected, description in classification_tests:
        result = handler.classify_hostname(hostname)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: '{hostname}' -> {result.value}")
    
    print()


def test_identifier_extraction():
    """Test unique identifier extraction for each category."""
    print("🔗 TESTING IDENTIFIER EXTRACTION")
    print("=" * 40)
    
    extraction_tests = [
        # GitHub URLs
        {
            "url": "https://github.com/microsoft/vscode",
            "expected_id": "microsoft/vscode",
            "expected_owner": "microsoft",
            "expected_repo": "vscode",
            "description": "Standard GitHub repo"
        },
        {
            "url": "https://github.com/user-name/repo-name",
            "expected_id": "user-name/repo-name",
            "expected_owner": "user-name",
            "expected_repo": "repo-name",
            "description": "GitHub with hyphens"
        },
        {
            "url": "https://github.com/single",
            "expected_id": None,
            "expected_owner": None,
            "expected_repo": None,
            "description": "GitHub with only one path component"
        },
        
        # NPM URLs
        {
            "url": "https://www.npmjs.com/package/express",
            "expected_id": "express",
            "expected_package": "express",
            "description": "Standard NPM package"
        },
        {
            "url": "https://www.npmjs.com/package/@types/node",
            "expected_id": "@types/node",
            "expected_package": "@types/node",
            "description": "Scoped NPM package"
        },
        {
            "url": "https://www.npmjs.com/package/@angular/core",
            "expected_id": "@angular/core",
            "expected_package": "@angular/core",
            "description": "Angular scoped package"
        },
        
        # PyPI URLs
        {
            "url": "https://pypi.org/project/requests/",
            "expected_id": "requests",
            "expected_package": "requests",
            "description": "Standard PyPI package"
        },
        {
            "url": "https://pypi.org/project/django/4.2.0/",
            "expected_id": "django",
            "expected_package": "django",
            "expected_version": "4.2.0",
            "description": "PyPI package with version"
        },
    ]
    
    for test in extraction_tests:
        result = handle_url(test["url"])
        
        print(f"Testing: {test['description']}")
        print(f"  URL: {test['url']}")
        print(f"  Expected ID: {test.get('expected_id')}")
        print(f"  Actual ID: {result.unique_identifier}")
        
        # Check identifier
        id_match = result.unique_identifier == test.get('expected_id')
        print(f"  ID Match: {'✓' if id_match else '✗'}")
        
        # Check additional fields
        if 'expected_owner' in test:
            owner_match = result.owner == test.get('expected_owner')
            print(f"  Owner: {result.owner} {'✓' if owner_match else '✗'}")
        
        if 'expected_repo' in test:
            repo_match = result.repository == test.get('expected_repo')
            print(f"  Repository: {result.repository} {'✓' if repo_match else '✗'}")
        
        if 'expected_package' in test:
            package_match = result.package_name == test.get('expected_package')
            print(f"  Package: {result.package_name} {'✓' if package_match else '✗'}")
        
        if 'expected_version' in test:
            version_match = result.version == test.get('expected_version')
            print(f"  Version: {result.version} {'✓' if version_match else '✗'}")
        
        print()


def test_error_handling():
    """Test comprehensive error handling."""
    print("⚠️  TESTING ERROR HANDLING")
    print("=" * 40)
    
    error_tests = [
        ("", "Invalid URL format"),
        ("not-a-url", "Invalid URL format"),
        ("ftp://example.com", "Invalid URL format"),
        ("https://", "Invalid URL format"),
        ("https://ex ample.com", "Invalid URL format"),
    ]
    
    for url, expected_error_type in error_tests:
        result = handle_url(url)
        
        if result.is_valid:
            print(f"✗ Expected error for '{url}' but got valid result")
        else:
            print(f"✓ '{url}' -> Error: {result.error_message}")
    
    print()


def test_end_to_end_scenarios():
    """Test complete end-to-end scenarios."""
    print("🎯 TESTING END-TO-END SCENARIOS")
    print("=" * 40)
    
    scenarios = [
        {
            "name": "Popular GitHub Repository",
            "url": "https://github.com/torvalds/linux",
            "checks": {
                "is_valid": True,
                "category": URLCategory.GITHUB,
                "unique_identifier": "torvalds/linux",
                "owner": "torvalds",
                "repository": "linux"
            }
        },
        {
            "name": "Popular NPM Package",
            "url": "https://www.npmjs.com/package/react",
            "checks": {
                "is_valid": True,
                "category": URLCategory.NPM,
                "unique_identifier": "react",
                "package_name": "react"
            }
        },
        {
            "name": "Python Package with Version",
            "url": "https://pypi.org/project/numpy/1.21.0/",
            "checks": {
                "is_valid": True,
                "category": URLCategory.PYPI,
                "unique_identifier": "numpy",
                "package_name": "numpy",
                "version": "1.21.0"
            }
        },
        {
            "name": "Unknown but Valid URL",
            "url": "https://stackoverflow.com/questions/123",
            "checks": {
                "is_valid": True,
                "category": URLCategory.UNKNOWN,
                "unique_identifier": None
            }
        },
        {
            "name": "Invalid URL",
            "url": "not-a-valid-url",
            "checks": {
                "is_valid": False,
                "error_message": "Invalid URL format"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        result = handle_url(scenario['url'])
        
        all_passed = True
        for field, expected in scenario['checks'].items():
            actual = getattr(result, field)
            passed = actual == expected
            status = "✓" if passed else "✗"
            print(f"  {status} {field}: {actual} (expected: {expected})")
            if not passed:
                all_passed = False
        
        overall_status = "✓ PASSED" if all_passed else "✗ FAILED"
        print(f"  {overall_status}")
        print()


def run_all_tests():
    """Run the complete test suite."""
    print("🧪 COMPREHENSIVE URL HANDLER TEST SUITE")
    print("=" * 60)
    print()
    
    test_url_validation()
    test_hostname_classification()
    test_identifier_extraction()
    test_error_handling()
    test_end_to_end_scenarios()
    
    print("✅ Test suite completed!")


if __name__ == "__main__":
    run_all_tests()
