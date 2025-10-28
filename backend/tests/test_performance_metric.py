import os
import sys
import json
import pytest
import logging
import requests
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Also add the app/ directory so modules that use top-level imports (e.g. `from metric import Metric`) can be found
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.submetrics import PerformanceMetric

# Ensure logs directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'logs'), exist_ok=True)
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'test_performance_metric.log')

# Configure test logging to write to logs/test_performance_metric.log
logger = logging.getLogger('test_performance_metric')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_PATH, mode='w', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# if not logger.handlers:
logger.handlers = []
logger.addHandler(file_handler)


@pytest.fixture(autouse=True)
def quiet_logging():
    # Keep the app logs quieter during tests but still allow our test logger to output
    logging.getLogger('app').setLevel(logging.WARNING)

class DummyResp:
    def __init__(self, status_code=200, json_obj=None, text=None, json_exc=None):
        self.status_code = status_code
        self._json = json_obj
        self.text = text if text is not None else (json.dumps(json_obj) if json_obj is not None else '')
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._json
    
    def raise_for_status(self):
        # mimic requests.Response.raise_for_status behavior
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")
        return None


def test_valid_response_parses_score():
    logger.info('Starting test_valid_response_parses_score')
    pm = PerformanceMetric()

    resp_json = {'choices': [ {'message': {'content': '0.85\nExplanation here'}} ] }

    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=200, json_obj=resp_json)):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert pytest.approx(score, rel=1e-3) == 0.85
    logger.info('Finished test_valid_response_parses_score')


def test_non_200_response_returns_zero():
    logger.info('Starting test_non_200_response_returns_zero')
    pm = PerformanceMetric()

    resp_json = {'error': 'bad request'}
    # status_code != 200 should cause method to return 0.0
    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=500, json_obj=resp_json)):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert score == 0.0
    logger.info('Finished test_non_200_response_returns_zero')


def test_malformed_json_returns_zero():
    logger.info('Starting test_malformed_json_returns_zero')
    pm = PerformanceMetric()

    # Simulate json() raising a ValueError
    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=200, json_exc=ValueError('no json'))):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert score == 0.0
    logger.info('Finished test_malformed_json_returns_zero')


def test_successful_content_response():
    logger.info('Starting test_successful_content_response')
    pm = PerformanceMetric()

    resp_json = {'choices': [ { 'message': {'content': '0.72\nSome note'} } ] }

    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=200, json_obj=resp_json)):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert pytest.approx(score, rel=1e-3) == 0.72
    logger.info('Finished test_successful_content_response')


def test_numeric_without_newline_returns_zero():
    logger.info('Starting test_numeric_without_newline_returns_zero')
    pm = PerformanceMetric()
    # content without newline: regex expects newline after number, so returns 0.0
    resp_json = {'choices': [ {'message': {'content': '0.99'}} ] }

    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=200, json_obj=resp_json)):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert score == 0.0
    logger.info('Finished test_numeric_without_newline_returns_zero')


def test_json_not_dict_returns_zero():
    logger.info('Starting test_json_not_dict_returns_zero')
    pm = PerformanceMetric()
    # resp.json returns a list (unexpected type)
    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=200, json_obj=['not','a','dict'])):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert score == 0.0
    logger.info('Finished test_json_not_dict_returns_zero')


def test_raise_for_status_error_returns_zero():
    logger.info('Starting test_raise_for_status_error_returns_zero')
    pm = PerformanceMetric()
    # raise_for_status should raise and be caught leading to 0.0
    with patch('app.submetrics.requests.post', return_value=DummyResp(status_code=502, json_obj={'error':'bad'})):
        score = pm._evaluate_performance_in_readme('dummy readme')
        assert score == 0.0
    logger.info('Finished test_raise_for_status_error_returns_zero')


if __name__ == '__main__':
    # Allow running the tests module directly which will invoke pytest programmatically
    # and still create logs in logs/metric_tests.log
    logger.info('Executing tests via __main__')
    sys.exit(pytest.main([os.path.abspath(__file__), '-q']))