import os
import sys
from urllib.parse import urlparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from url_handler import URLHandler
from url_category import URLCategory


def test_validate_url_edge_unicode_and_whitespace():
    h = URLHandler()
    assert h.validate_url('  https://github.com/user/repo  ') is True
    # Unicode hostname should not raise
    assert isinstance(h.validate_url('https://例子.测试'), bool)


def test_classify_hostname_patterns():
    h = URLHandler()
    assert h.classify_hostname('api.github.com') == URLCategory.GITHUB
    assert h.classify_hostname('some-registry.npmjs.com') == URLCategory.NPM
    assert h.classify_hostname('huggingface.co') == URLCategory.HUGGINGFACE


def test_extract_identifiers_with_unexpected_paths():
    h = URLHandler()
    p = urlparse('https://github.com///')
    gh = h.extract_github_identifier(p)
    assert gh['unique_identifier'] is None

    p2 = urlparse('https://www.npmjs.com/package/')
    npm = h.extract_npm_identifier(p2)
    assert npm['unique_identifier'] is None
