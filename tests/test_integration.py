#!/usr/bin/env python3
"""
Integration tests for URL Handler + Data Retrieval workflow.

These tests verify that the complete pipeline from URL processing
to data retrieval works correctly together.
"""

import pytest
import warnings
from _pytest.warning_types import PytestUnknownMarkWarning

import sys
import os
from unittest.mock import patch, Mock

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from url_handler import handle_url, process_url_file, URLCategory
from data_retrieval import retrieve_data_for_url, retrieve_data_for_urls, RepositoryData


class TestURLToDataPipeline:
    """Test the complete pipeline from URL to data retrieval."""
    
    def test_github_url_to_data_flow(self):
        """Test complete flow for GitHub URL."""
        url = "https://github.com/microsoft/typescript"
        
        # Step 1: Process URL
        url_data = handle_url(url)
        
        assert url_data.is_valid == True
        assert url_data.category == URLCategory.GITHUB
        assert url_data.unique_identifier == "microsoft/typescript"
        assert url_data.owner == "microsoft"
        assert url_data.repository == "typescript"
        
        # Step 2: Mock data retrieval (to avoid network calls in tests)
        with patch('url_handler.data_retrieval.GitHubAPIClient.get_repository_data') as mock_api:
            mock_api.return_value = RepositoryData(
                platform="github",
                identifier="microsoft/typescript",
                name="TypeScript",
                description="TypeScript language",
                stars=100000,
                success=True
            )
            
            repo_data = retrieve_data_for_url(url_data)
            
            assert repo_data.success == True
            assert repo_data.platform == "github"
            assert repo_data.name == "TypeScript"
            assert repo_data.stars == 100000
            
            # Verify API was called with correct parameters
            mock_api.assert_called_once_with("microsoft", "typescript")
    
    def test_npm_url_to_data_flow(self):
        """Test complete flow for NPM URL."""
        url = "https://www.npmjs.com/package/express"
        
        # Step 1: Process URL
        url_data = handle_url(url)
        
        assert url_data.is_valid == True
        assert url_data.category == URLCategory.NPM
        assert url_data.unique_identifier == "express"
        assert url_data.package_name == "express"
        
        # Step 2: Mock data retrieval
        with patch('url_handler.data_retrieval.NPMAPIClient.get_package_data') as mock_api:
            mock_api.return_value = RepositoryData(
                platform="npm",
                identifier="express",
                name="express",
                description="Fast web framework",
                version="4.18.2",
                downloads_last_month=2000000,
                success=True
            )
            
            repo_data = retrieve_data_for_url(url_data)
            
            assert repo_data.success == True
            assert repo_data.platform == "npm"
            assert repo_data.name == "express"
            assert repo_data.version == "4.18.2"
            assert repo_data.downloads_last_month == 2000000
            
            # Verify API was called with correct parameters
            mock_api.assert_called_once_with("express")
    
    def test_huggingface_url_to_data_flow(self):
        """Test complete flow for Hugging Face URL."""
        url = "https://huggingface.co/microsoft/DialoGPT-medium"
        
        # Step 1: Process URL
        url_data = handle_url(url)
        
        assert url_data.is_valid == True
        assert url_data.category == URLCategory.HUGGINGFACE
        assert url_data.unique_identifier == "microsoft/DialoGPT-medium"
        assert url_data.owner == "microsoft"
        assert url_data.repository == "DialoGPT-medium"
        
        # Step 2: Mock data retrieval
        with patch('url_handler.data_retrieval.HuggingFaceAPIClient.get_model_data') as mock_api:
            mock_api.return_value = RepositoryData(
                platform="huggingface",
                identifier="microsoft/DialoGPT-medium",
                name="DialoGPT-medium",
                description="Conversational AI model",
                downloads_last_month=50000,
                language="text-generation",
                success=True
            )
            
            repo_data = retrieve_data_for_url(url_data)
            
            assert repo_data.success == True
            assert repo_data.platform == "huggingface"
            assert repo_data.name == "DialoGPT-medium"
            assert repo_data.downloads_last_month == 50000
            assert repo_data.language == "text-generation"
            
            # Verify API was called with correct parameters
            mock_api.assert_called_once_with("microsoft/DialoGPT-medium")


class TestBatchProcessing:
    """Test batch processing of multiple URLs."""
    
    def test_batch_url_processing_and_data_retrieval(self):
        """Test processing multiple URLs and retrieving data for all."""
        urls = [
            "https://github.com/facebook/react",
            "https://www.npmjs.com/package/lodash",
            "https://huggingface.co/bert-base-uncased"
        ]
        
        # Step 1: Process all URLs
        url_results = [handle_url(url) for url in urls]
        
        # Verify all processed correctly
        assert len(url_results) == 3
        assert all(result.is_valid for result in url_results)
        assert url_results[0].category == URLCategory.GITHUB
        assert url_results[1].category == URLCategory.NPM
        assert url_results[2].category == URLCategory.HUGGINGFACE
        
        # Step 2: Mock batch data retrieval
        mock_responses = [
            RepositoryData(platform="github", identifier="facebook/react", name="React", success=True),
            RepositoryData(platform="npm", identifier="lodash", name="lodash", success=True),
            RepositoryData(platform="huggingface", identifier="bert-base-uncased", name="bert-base-uncased", success=True)
        ]
        
        with patch('url_handler.data_retrieval.DataRetriever.retrieve_batch_data') as mock_batch:
            mock_batch.return_value = mock_responses
            
            repo_data_list = retrieve_data_for_urls(url_results)
            
            assert len(repo_data_list) == 3
            assert all(data.success for data in repo_data_list)
            assert repo_data_list[0].platform == "github"
            assert repo_data_list[1].platform == "npm"
            assert repo_data_list[2].platform == "huggingface"
            
            # Verify batch function was called
            mock_batch.assert_called_once_with(url_results)


class TestErrorPropagation:
    """Test error handling across the pipeline."""
    
    def test_invalid_url_error_handling(self):
        """Test error handling for invalid URLs."""
        url = "not-a-valid-url"
        
        # Step 1: Process invalid URL
        url_data = handle_url(url)
        
        assert url_data.is_valid == False
        assert url_data.error_message is not None
        
        # Step 2: Data retrieval should handle invalid input
        repo_data = retrieve_data_for_url(url_data)
        
        assert repo_data.success == False
        assert repo_data.error_message is not None
    
    def test_api_failure_error_handling(self):
        """Test error handling when API calls fail."""
        url = "https://github.com/test/repo"
        
        # Step 1: Process valid URL
        url_data = handle_url(url)
        assert url_data.is_valid == True
        
        # Step 2: Mock API failure
        with patch('url_handler.data_retrieval.GitHubAPIClient.get_repository_data') as mock_api:
            mock_api.return_value = RepositoryData(
                platform="github",
                identifier="test/repo",
                name="repo",
                success=False,
                error_message="Repository not found"
            )
            
            repo_data = retrieve_data_for_url(url_data)
            
            assert repo_data.success == False
            assert "not found" in repo_data.error_message.lower()
    
    def test_unknown_category_handling(self):
        """Test handling of unknown URL categories."""
        url = "https://stackoverflow.com/questions/123"
        
        # Step 1: Process URL (should be valid but unknown category)
        url_data = handle_url(url)
        
        assert url_data.is_valid == True
        assert url_data.category == URLCategory.UNKNOWN
        
        # Step 2: Data retrieval should handle unknown category
        repo_data = retrieve_data_for_url(url_data)
        
        assert repo_data.success == False
        assert "invalid url data" in repo_data.error_message.lower()


class TestDataConsistency:
    """Test data consistency between URL processing and data retrieval."""
    
    def test_identifier_consistency(self):
        """Test that identifiers are consistent between modules."""
        test_cases = [
            ("https://github.com/microsoft/vscode", "microsoft/vscode"),
            ("https://www.npmjs.com/package/@types/node", "@types/node"),
            ("https://huggingface.co/datasets/squad", "squad"),
        ]
        
        for url, expected_identifier in test_cases:
            url_data = handle_url(url)
            
            assert url_data.is_valid == True
            assert url_data.unique_identifier == expected_identifier
            
            # Mock data retrieval to verify identifier is passed correctly
            with patch('url_handler.data_retrieval.DataRetriever.retrieve_data') as mock_retrieve:
                mock_retrieve.return_value = RepositoryData(
                    platform=url_data.category.value,
                    identifier=expected_identifier,
                    name="test",
                    success=True
                )
                
                repo_data = retrieve_data_for_url(url_data)
                
                # Verify the identifier was passed through correctly
                assert repo_data.identifier == expected_identifier
                mock_retrieve.assert_called_once_with(url_data)


class TestFileProcessingIntegration:
    """Test integration with file processing capabilities."""
    
    def test_file_processing_pipeline(self):
        """Test complete pipeline with file input."""
        import tempfile
        import os
        
        # Create temporary file with test URLs
        test_urls = [
            "https://github.com/facebook/react",
            "https://www.npmjs.com/package/express",
            "https://huggingface.co/bert-base-uncased",
            "invalid-url"  # Include an invalid URL to test error handling
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for url in test_urls:
                f.write(f"{url}\n")
            temp_file_path = f.name
        
        try:
            # Step 1: Process URLs from file
            url_results = process_url_file(temp_file_path)
            
            assert len(url_results) == 4  # All URLs processed
            valid_results = [r for r in url_results if r.is_valid]
            assert len(valid_results) == 3  # Only 3 are valid
            
            # Step 2: Mock data retrieval for valid URLs
            with patch('url_handler.data_retrieval.DataRetriever.retrieve_batch_data') as mock_batch:
                mock_responses = [
                    RepositoryData(platform="github", identifier="facebook/react", name="React", success=True),
                    RepositoryData(platform="npm", identifier="express", name="express", success=True),
                    RepositoryData(platform="huggingface", identifier="bert-base-uncased", name="bert-base-uncased", success=True)
                ]
                mock_batch.return_value = mock_responses
                
                repo_data_list = retrieve_data_for_urls(valid_results)
                
                assert len(repo_data_list) == 3
                assert all(data.success for data in repo_data_list)
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)


# Performance/timing tests - marked as slow
class TestPerformanceIntegration:
    """Test performance characteristics of the integration."""
    
    def test_processing_performance(self):
        """Test that URL processing is fast enough."""
        import time
        
        urls = [
            "https://github.com/microsoft/typescript",
            "https://www.npmjs.com/package/react",
            "https://huggingface.co/bert-base-uncased"
        ] * 10  # Process 30 URLs
        
        start_time = time.time()
        
        # Process all URLs
        results = [handle_url(url) for url in urls]
        
        processing_time = time.time() - start_time
        
        # Should process URLs very quickly (< 1 second for 30 URLs)
        assert processing_time < 1.0, f"URL processing too slow: {processing_time:.2f}s"
        assert len(results) == 30
        assert all(r.is_valid for r in results)
    
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_rate_limiting_behavior(self, mock_sleep):
        """Test that rate limiting works in batch processing."""
        from url_handler.data_retrieval import DataRetriever
        
        urls = [
            "https://github.com/test1/repo1",
            "https://github.com/test2/repo2",
            "https://github.com/test3/repo3"
        ]
        
        url_results = [handle_url(url) for url in urls]
        
        with patch('url_handler.data_retrieval.GitHubAPIClient.get_repository_data') as mock_api:
            mock_api.return_value = RepositoryData(
                platform="github", identifier="test/repo", name="repo", success=True
            )
            
            retriever = DataRetriever(rate_limit_delay=0.1)
            retriever.retrieve_batch_data(url_results)
            
            # Verify rate limiting was applied (sleep called between requests)
            assert mock_sleep.call_count >= len(url_results) - 1
