import os
import sys
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from cli_controller import CLIController
from url_data import RepositoryData


def test_normalize_repo_with_dict_and_object_and_datetime():
    c = CLIController()

    # dict input with datetime
    dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
    d = {'updated_at': dt, 'name': 'test'}
    norm = c._normalize_repo(d)
    assert isinstance(norm['updated_at'], str) and '2020' in norm['updated_at']

    # object input
    class Dummy:
        a = 1
        b = 'x'

    obj = Dummy()
    norm2 = c._normalize_repo(obj)
    assert norm2.get('a') == 1
    assert norm2.get('b') == 'x'


def test_process_single_model_merges_and_calls_metrics(monkeypatch):
    c = CLIController()

    # Prepare fake RepositoryData returns for code, dataset, model
    repo_code = RepositoryData(platform='github', identifier='o/c', name='code', success=True)
    repo_dataset = RepositoryData(platform='huggingface', identifier='u/d', name='data', success=True)
    repo_model = RepositoryData(platform='github', identifier='m/r', name='model', success=True)

    # Patch data_retriever.retrieve_data to return repos in order
    c.data_retriever.retrieve_data = MagicMock(side_effect=[repo_code, repo_dataset, repo_model])

    # Patch metric_calculator.calculate_all_metrics to capture merged dict
    captured = {}

    def fake_calc(merged, cat):
        captured['merged'] = merged
        captured['cat'] = cat
        return {'ok': True}

    c.metric_calculator.calculate_all_metrics = fake_calc

    data = {'code': 'x', 'dataset': 'y', 'model': 'z'}
    res = c.process_single_model(data)
    assert res == {'ok': True}
    assert captured['cat'] == 'MODEL'
    # merged should contain name keys coming from RepositoryData attributes
    assert 'name' in captured['merged']


def test_process_urls_reads_and_prints(monkeypatch, capsys):
    c = CLIController()
    # Provide a fake list of url dicts
    fake_list = [
        {'code': 'c1', 'dataset': 'd1', 'model': 'm1'},
    ]

    monkeypatch.setattr(c.url_handler, 'read_urls_from_file', lambda p: fake_list)

    # Patch url_handler.handle_url to return objects that pass validation
    from url_category import URLCategory
    class FakeURL:
        def __init__(self):
            self.is_valid = True
            self.category = URLCategory.GITHUB

    def fh(url):
        return FakeURL()

    monkeypatch.setattr(c.url_handler, 'handle_url', fh)

    # Patch process_single_model to return a dict so it prints
    monkeypatch.setattr(c, 'process_single_model', lambda obj: {'x': 1})

    rc = c.process_urls('dummy.txt')
    captured = capsys.readouterr()
    assert rc == 0
    assert '{"x": 1}' in captured.out or '{\"x\": 1}' in captured.out


def test_run_dispatch(monkeypatch):
    c = CLIController()

    # install
    monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='install'))
    monkeypatch.setattr(c, 'install_dependencies', lambda: 0)
    assert c.run() == 0

    # test
    monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='test'))
    monkeypatch.setattr(c, 'run_tests', lambda: 0)
    assert c.run() == 0

    # file
    monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='somefile.txt'))
    monkeypatch.setattr(c, 'process_urls', lambda p: 0)
    assert c.run() == 0
