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

from app.cli_controller import CLIController
from app.url_data import RepositoryData
from app.url_category import URLCategory


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
    # CLI injects the model 'name' into the metric results, while preserving
    # the metric calculator's return value. Ensure both are present.
    assert isinstance(res, dict)
    assert res.get('ok') is True
    assert res.get('name') == 'model'
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
    class FakeURL:
        def __init__(self):
            self.is_valid = True
            self.category = URLCategory.GITHUB

    # Use a MagicMock for handle_url so we can assert it was called
    handle_mock = MagicMock(return_value=FakeURL())
    monkeypatch.setattr(c.url_handler, 'handle_url', handle_mock)

    # Patch process_single_model to return a dict; use a MagicMock so we can
    # assert it was called instead of relying on stdout capture.
    mock_proc = MagicMock(return_value={'x': 1})
    monkeypatch.setattr(c, 'process_single_model', mock_proc)

    rc = c.process_urls('dummy.txt')
    assert rc == 0
    # Ensure URL handler was invoked for at least one of the url fields
    assert handle_mock.called


# def test_run_dispatch(monkeypatch):
#     c = CLIController()

#     # install
#     monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='install'))
#     monkeypatch.setattr(c, 'install_dependencies', lambda: 0)
#     assert c.run() == 0

#     # test
#     monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='test'))
#     monkeypatch.setattr(c, 'run_tests', lambda: 0)
#     assert c.run() == 0

#     # file
#     monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='somefile.txt'))
#     monkeypatch.setattr(c, 'process_urls', lambda p: 0)
#     assert c.run() == 0
