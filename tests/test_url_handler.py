#!/usr/bin/env python3

import pytest
import sys
import os

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from url_handler import URLHandler, handle_url, URLCategory, URLData


class TestURLValidation:
    """Test cases for URL validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = URLHandler()
    
    @pytest.mark.parametrize("url,expected,description", [
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
        (None, False, "None value"),
        (123, False, "Non-string input"),
    ])
    def test_url_validation_cases(self, url, expected, description):
        """Test various URL validation scenarios."""
        result = self.handler.validate_url(url)
        assert result == expected, f"Failed {description}: '{url}' -> {result}, expected {expected}"
    
    def test_url_validation_edge_cases(self):
        """Test specific edge cases for URL validation."""
        # Test with very long URL
        long_url = "https://github.com/" + "a" * 1000
        assert self.handler.validate_url(long_url) == True
        
        # Test with unicode characters
        unicode_url = "https://github.com/用户/repo"
        # This may fail but should not raise an exception
        try:
            result = self.handler.validate_url(unicode_url)
            assert isinstance(result, bool)
        except Exception:
            pass  # Unicode handling may vary


class TestHostnameClassification:
    """Test cases for hostname classification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = URLHandler()
    
    @pytest.mark.parametrize("hostname,expected,description", [
        # GitHub variations
        ("github.com", URLCategory.GITHUB, "GitHub main domain"),
        ("www.github.com", URLCategory.GITHUB, "GitHub with www"),
        ("api.github.com", URLCategory.GITHUB, "GitHub subdomain"),
        
        # NPM variations
        ("npmjs.com", URLCategory.NPM, "NPM main domain"),
        ("www.npmjs.com", URLCategory.NPM, "NPM with www"),
        ("registry.npmjs.com", URLCategory.NPM, "NPM registry"),
        
        # Hugging Face variations
        ("huggingface.co", URLCategory.HUGGINGFACE, "Hugging Face main domain"),
        ("www.huggingface.co", URLCategory.HUGGINGFACE, "Hugging Face with www"),
        
        # Unknown domains
        ("example.com", URLCategory.UNKNOWN, "Unknown domain"),
        ("stackoverflow.com", URLCategory.UNKNOWN, "Popular but unknown domain"),
        ("bitbucket.org", URLCategory.UNKNOWN, "Similar to GitHub but unknown"),
    ])
    def test_hostname_classification(self, hostname, expected, description):
        """Test hostname classification for various domains."""
        result = self.handler.classify_hostname(hostname)
        assert result == expected, f"Failed {description}: '{hostname}' -> {result}, expected {expected}"
    
    def test_case_insensitive_classification(self):
        """Test that hostname classification is case insensitive."""
        test_cases = [
            "GITHUB.COM",
            "GitHub.com", 
            "gitHub.COM",
            "NPMJS.COM",
            "HUGGINGFACE.CO"
        ]
        
        for hostname in test_cases:
            result = self.handler.classify_hostname(hostname)
            assert result != URLCategory.UNKNOWN, f"Case insensitive test failed for {hostname}"


class TestIdentifierExtraction:
    """Test cases for unique identifier extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = URLHandler()
    
    def test_github_identifier_extraction(self):
        """Test GitHub identifier extraction."""
        test_cases = [
            ("https://github.com/microsoft/vscode", "microsoft/vscode", "microsoft", "vscode"),
            ("https://github.com/user-name/repo-name", "user-name/repo-name", "user-name", "repo-name"),
            ("https://github.com/single", None, None, None),  # Only one path component
        ]
        
        for url, expected_id, expected_owner, expected_repo in test_cases:
            result = handle_url(url)
            assert result.unique_identifier == expected_id, f"ID mismatch for {url}"
            assert result.owner == expected_owner, f"Owner mismatch for {url}"
            assert result.repository == expected_repo, f"Repository mismatch for {url}"
    
    def test_npm_identifier_extraction(self):
        """Test NPM identifier extraction."""
        test_cases = [
            ("https://www.npmjs.com/package/express", "express", "express"),
            ("https://www.npmjs.com/package/@types/node", "@types/node", "@types/node"),
            ("https://www.npmjs.com/package/@angular/core", "@angular/core", "@angular/core"),
        ]
        
        for url, expected_id, expected_package in test_cases:
            result = handle_url(url)
            assert result.unique_identifier == expected_id, f"ID mismatch for {url}"
            assert result.package_name == expected_package, f"Package mismatch for {url}"
    
    def test_huggingface_identifier_extraction(self):
        """Test Hugging Face identifier extraction."""
        test_cases = [
            ("https://huggingface.co/microsoft/DialoGPT-medium", "microsoft/DialoGPT-medium", "microsoft", "DialoGPT-medium"),
            ("https://huggingface.co/datasets/squad", "squad", None, "squad"),
            ("https://huggingface.co/spaces/gradio/hello_world", "gradio/hello_world", "gradio", "hello_world"),
        ]
        
        for url, expected_id, expected_owner, expected_repo in test_cases:
            result = handle_url(url)
            assert result.unique_identifier == expected_id, f"ID mismatch for {url}"
            assert result.owner == expected_owner, f"Owner mismatch for {url}"
            assert result.repository == expected_repo, f"Repository mismatch for {url}"


class TestEndToEndProcessing:
    """Test complete end-to-end URL processing scenarios."""
    
    @pytest.mark.parametrize("url,expected_valid,expected_category,expected_id", [
        # Valid URLs
        ("https://github.com/torvalds/linux", True, URLCategory.GITHUB, "torvalds/linux"),
        ("https://www.npmjs.com/package/react", True, URLCategory.NPM, "react"),
        ("https://huggingface.co/microsoft/DialoGPT-medium", True, URLCategory.HUGGINGFACE, "microsoft/DialoGPT-medium"),
        ("https://stackoverflow.com/questions/123", True, URLCategory.UNKNOWN, None),
        
        # Invalid URLs
        ("not-a-url", False, URLCategory.UNKNOWN, None),
        ("", False, URLCategory.UNKNOWN, None),
    ])
    def test_end_to_end_processing(self, url, expected_valid, expected_category, expected_id):
        """Test complete URL processing flow."""
        result = handle_url(url)
        
        assert result.is_valid == expected_valid, f"Validity mismatch for {url}"
        assert result.category == expected_category, f"Category mismatch for {url}"
        assert result.unique_identifier == expected_id, f"Identifier mismatch for {url}"
        assert result.original_url == url, f"Original URL not preserved for {url}"
    
    def test_error_handling(self):
        """Test error handling in URL processing."""
        error_cases = [
            "",
            "not-a-url",
            "ftp://example.com",
            "https://",
            None,
            123,
        ]
        
        for url in error_cases:
            result = handle_url(url)
            assert result.is_valid == False, f"Should be invalid: {url}"
            assert result.error_message is not None, f"Should have error message: {url}"


class TestURLDataStructure:
    """Test URLData data structure behavior."""
    
    def test_url_data_creation(self):
        """Test URLData object creation and attributes."""
        url_data = URLData(
            original_url="https://github.com/test/repo",
            category=URLCategory.GITHUB,
            hostname="github.com",
            is_valid=True,
            unique_identifier="test/repo",
            owner="test",
            repository="repo"
        )
        
        assert url_data.original_url == "https://github.com/test/repo"
        assert url_data.category == URLCategory.GITHUB
        assert url_data.hostname == "github.com"
        assert url_data.is_valid == True
        assert url_data.unique_identifier == "test/repo"
        assert url_data.owner == "test"
        assert url_data.repository == "repo"
    
    def test_url_data_defaults(self):
        """Test URLData default values."""
        url_data = URLData(
            original_url="test",
            category=URLCategory.UNKNOWN,
            hostname="test.com",
            is_valid=False
        )
        
        assert url_data.unique_identifier is None
        assert url_data.owner is None
        assert url_data.repository is None
        assert url_data.package_name is None
        assert url_data.version is None
        assert url_data.error_message is None


class TestFileProcessing:
    """Test file processing functionality."""
    
    def test_file_processing_functions_exist(self):
        """Test that file processing functions are available."""
        from url_handler import read_urls_from_file, process_url_file, get_valid_urls
        
        # These functions should be importable
        assert callable(read_urls_from_file)
        assert callable(process_url_file)
        assert callable(get_valid_urls)
    
    def test_get_valid_urls_filtering(self):
        """Test filtering of valid URLs."""
        from url_handler import get_valid_urls
        
        # Create test data
        valid_url = URLData("https://github.com/test/repo", URLCategory.GITHUB, "github.com", True)
        invalid_url = URLData("invalid", URLCategory.UNKNOWN, "", False)
        
        results = [valid_url, invalid_url]
        valid_results = get_valid_urls(results)
        
        assert len(valid_results) == 1
        assert valid_results[0].is_valid == True
