import os
import sys
import json
import tempfile
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.url_handler import URLHandler, handle_url, URLCategory, read_urls_from_file, process_url_file, get_processing_summary, get_valid_urls, get_urls_by_category, URLData
import app.url_handler as uh
from urllib.parse import urlparse

def test_validate_url_basic_and_invalid():
    h = URLHandler()
    assert h.validate_url('https://github.com/user/repo') is True
    assert h.validate_url('http://example.com/path') is True
    assert h.validate_url('ftp://example.com') is False
    assert h.validate_url('not-a-url') is False
    assert h.validate_url('') is False
    assert h.validate_url(None) is False


def test_classify_hostname_various():
    h = URLHandler()
    assert h.classify_hostname('github.com') == URLCategory.GITHUB
    assert h.classify_hostname('www.github.com') == URLCategory.GITHUB
    assert h.classify_hostname('api.github.com') == URLCategory.GITHUB
    assert h.classify_hostname('npmjs.com') == URLCategory.NPM
    assert h.classify_hostname('registry.npmjs.com') == URLCategory.NPM
    assert h.classify_hostname('huggingface.co') == URLCategory.HUGGINGFACE
    assert h.classify_hostname('unknown-domain.com') == URLCategory.UNKNOWN


def test_extract_github_identifier_edge_cases():
    h = URLHandler()
    # normal
    parsed = urlparse('https://github.com/owner/repo')
    res = h.extract_github_identifier(parsed)
    assert res['unique_identifier'] == 'owner/repo'
    # only owner
    parsed2 = urlparse('https://github.com/owner')
    res2 = h.extract_github_identifier(parsed2)
    assert res2['unique_identifier'] is None


def test_extract_npm_identifier_scoped_and_unscoped():
    h = URLHandler()
    p1 = urlparse('https://www.npmjs.com/package/express')
    r1 = h.extract_npm_identifier(p1)
    assert r1['unique_identifier'] == 'express'

    p2 = urlparse('https://www.npmjs.com/package/@types/node')
    r2 = h.extract_npm_identifier(p2)
    assert r2['unique_identifier'] == '@types/node'

    p3 = urlparse('https://www.npmjs.com/')
    r3 = h.extract_npm_identifier(p3)
    assert r3['unique_identifier'] is None


def test_extract_huggingface_various():
    h = URLHandler()
    p1 = urlparse('https://huggingface.co/microsoft/DialoGPT-medium')
    r1 = h.extract_huggingface_identifier(p1)
    assert r1['unique_identifier'] == 'microsoft/DialoGPT-medium'

    p2 = urlparse('https://huggingface.co/datasets/squad')
    r2 = h.extract_huggingface_identifier(p2)
    assert r2['unique_identifier'] == 'squad'

    p3 = urlparse('https://huggingface.co/spaces/gradio/hello_world')
    r3 = h.extract_huggingface_identifier(p3)
    assert r3['unique_identifier'] == 'gradio/hello_world'


def test_handle_url_invalid_and_valid():
    # invalid
    res = handle_url('not-a-url')
    assert res.is_valid is False
    assert res.error_message is not None

    # valid github
    res2 = handle_url('https://github.com/microsoft/vscode')
    assert res2.is_valid is True
    assert res2.category == URLCategory.GITHUB
    assert res2.unique_identifier == 'microsoft/vscode'


def test_read_and_process_file_and_summary(tmp_path):
    p = tmp_path / 'urls.txt'
    content = '\n'.join([
        'https://github.com/facebook/react',
        'https://www.npmjs.com/package/lodash',
        'https://huggingface.co/bert-base-uncased',
        'not-a-url'
    ])
    p.write_text(content)

    urls = read_urls_from_file(str(p))
    assert len(urls) == 4

    results = process_url_file(str(p))
    assert len(results) == 4

    summary = get_processing_summary(results)
    assert summary['total_urls'] == 4
    # valid_count should be 3
    assert summary['valid_count'] == 3
    assert summary['invalid_count'] == 1
    assert summary['categories']['github'] >= 1
    assert summary['categories']['npm'] >= 1
    assert summary['categories']['huggingface'] >= 1


def test_get_valid_and_category_filters():
    # prepare some URLData objects
    good = URLData(original_url='a', category=URLCategory.GITHUB, hostname='github.com', is_valid=True, unique_identifier='a/a')
    bad = URLData(original_url='b', category=URLCategory.UNKNOWN, hostname='x', is_valid=False)
    npm = URLData(original_url='c', category=URLCategory.NPM, hostname='npmjs.com', is_valid=True, unique_identifier='pkg')

    results = [good, bad, npm]
    valids = get_valid_urls(results)
    assert len(valids) == 2
    githubs = get_urls_by_category(results, URLCategory.GITHUB)
    assert githubs == [good]


# def test_url_handler_main_test_flag(capsys, monkeypatch):
#     # Ensure the --test branch runs and prints expected header    

#     monkeypatch.setattr('sys.argv', ['url_handler.py', '--test'])
#     # run main which will print output for built-in tests
#     try:
#         uh.main()
#     except SystemExit:
#         # main exits at the end, ignore
#         pass

#     captured = capsys.readouterr()
#     assert 'URL Handler Test Results' in captured.out


def test_read_urls_from_file_not_found(tmp_path):
    # read_urls_from_file should raise FileNotFoundError for missing file    
    missing = tmp_path / 'nope.txt'
    try:
        uh.read_urls_from_file(str(missing))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
