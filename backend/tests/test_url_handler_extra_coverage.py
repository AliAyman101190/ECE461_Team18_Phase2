#!/usr/bin/env python3

import os
import sys
import tempfile
import pytest
from urllib.parse import urlparse

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from url_handler import URLHandler
from url_category import URLCategory


class TestReadUrlsFromFile:
    def test_read_urls_success(self):
        handler = URLHandler()
        content = "https://github.com/owner/repo, https://huggingface.co/datasets/squad, https://huggingface.co/user/model\n"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            path = f.name
        try:
            items = handler.read_urls_from_file(path)
            assert isinstance(items, list)
            assert len(items) == 1
            row = items[0]
            assert row['code'].startswith('https://github.com/')
            assert row['dataset'].startswith('https://huggingface.co/')
            assert row['model'].startswith('https://huggingface.co/')
        finally:
            os.unlink(path)

    def test_read_urls_not_found(self):
        handler = URLHandler()
        with pytest.raises(FileNotFoundError):
            handler.read_urls_from_file('/tmp/definitely/does/not/exist.txt')

    def test_read_urls_malformed_line_raises_ioerror(self):
        handler = URLHandler()
        # Missing commas should trigger the generic Exception path -> IOError
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("only-one-url-here\n")
            path = f.name
        try:
            with pytest.raises(IOError):
                handler.read_urls_from_file(path)
        finally:
            os.unlink(path)


class TestHandleUrlExceptionalPath:
    def test_handle_url_catches_internal_errors(self, monkeypatch):
        handler = URLHandler()

        def boom(hostname: str):
            raise RuntimeError('boom')

        # Force classify_hostname to raise so we exercise the except branch
        monkeypatch.setattr(handler, 'classify_hostname', boom)
        res = handler.handle_url('https://github.com/owner/repo')
        assert res.is_valid is False
        assert res.error_message is not None


class TestPatternHostnameClassification:
    def test_github_pattern_subdomain(self):
        handler = URLHandler()
        assert handler.classify_hostname('code.github.enterprise.example.com') == URLCategory.GITHUB

    def test_huggingface_pattern_alt_domain(self):
        handler = URLHandler()
        # Any hostname containing 'huggingface' should map to HUGGINGFACE per pattern rule
        assert handler.classify_hostname('mirror.huggingface.tech') == URLCategory.HUGGINGFACE


class TestExtractUniqueIdentifier:
    def test_unknown_category_returns_none_identifier(self):
        handler = URLHandler()
        parsed = urlparse('https://example.com/something')
        result = handler.extract_unique_identifier(parsed, URLCategory.UNKNOWN)
        assert isinstance(result, dict)
        assert result.get('unique_identifier') is None


