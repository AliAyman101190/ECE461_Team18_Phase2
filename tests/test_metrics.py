import os
import sys
import json
import time
import pytest
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Also add the app/ directory so modules that use top-level imports (e.g. `from metric import Metric`) can be found
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.metric_calculator import MetricCalculator
from app.submetrics import *


# Ensure logs directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'logs'), exist_ok=True)
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'metric_tests.log')

# Configure test logging to write to logs/metric_tests.log
logger = logging.getLogger('metric_tests')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_PATH, mode='w')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(file_handler)


@pytest.fixture(autouse=True)
def quiet_logging():
    # Keep the app logs quieter during tests but still allow our test logger to output
    logging.getLogger('app').setLevel(logging.WARNING)


def sample_model_data_dict():
    return {
        "author": "google",
        "downloads": 50000,
        "likes": 150,
        "license": "apache-2.0",
        "lastModified": "2024-08-15T10:30:00Z",
        "readme": """# Model Name
        
        ## Usage
        This model can be used for text generation tasks.
        
        ## Training Data
        Trained on a curated dataset of high-quality text.
        
        ## Performance
        Achieves 85.2% accuracy on benchmark tasks.
        """,
        "siblings": [
            {"rfilename": "config.json"},
            {"rfilename": "pytorch_model.bin"},
            {"rfilename": "example.py"},
            {"rfilename": "requirements.txt"}
        ],
        "tags": ["text-generation", "pytorch"],
        "datasets": ["common_voice"],
        "size": 1073741824  # 1GB in bytes
    }


def test_metric_calculator_happy_path():
    logger.info('Starting test_metric_calculator_happy_path')
    calc = MetricCalculator()
    data = sample_model_data_dict()
    results = calc.calculate_all_metrics(json.dumps(data), "MODEL")

    # Basic structure
    assert results["category"] == "MODEL"
    assert "net_score" in results
    assert results["net_score_latency"] >= 0

    # Each metric present
    for metric in calc.metrics:
        logger.debug(f'Verifying metric present: {metric.name}')
        assert metric.name in results
        assert f"{metric.name}_latency" in results

    # Net score in range
    assert 0.0 <= results["net_score"] <= 1.0
    logger.info('Finished test_metric_calculator_happy_path')


def test_metric_calculator_malformed_json():
    logger.info('Starting test_metric_calculator_malformed_json')
    calc = MetricCalculator()
    # Not JSON - _safe_calculate_metric should handle and return defaults
    results = calc.calculate_all_metrics("not a json", "MODEL")

    assert results["net_score"] >= 0.0
    assert results["net_score_latency"] >= 0
    logger.info('Finished test_metric_calculator_malformed_json')


@pytest.mark.parametrize("cls", [
    SizeMetric, LicenseMetric, RampUpMetric, BusFactorMetric,
    AvailableScoreMetric, DatasetQualityMetric, CodeQualityMetric, PerformanceMetric,
])
def test_submetrics_basic_contract(cls):
    """Test that submetric classes implement calculate_metric and calculate_latency with expected returns."""
    logger.info(f'Starting test_submetrics_basic_contract for {cls.__name__}')
    instance = cls()

    # Should accept both dict and json string for consistency (some implementations expect json)
    data = sample_model_data_dict()
    # call with json string
    score = instance.calculate_metric(json.dumps(data), "MODEL")

    # score should be float or dict (size-like results). Accept 0.0 as placeholder.
    assert isinstance(score, (float, dict))

    # latency should be int-like
    latency = instance.calculate_latency()
    assert isinstance(latency, int)
    assert latency >= 0
    logger.info(f'Finished test_submetrics_basic_contract for {cls.__name__}')


def test_all_submetric_edge_cases():
    """Exhaustively test edge cases across submetrics: missing fields, empty lists, weird types."""
    logger.info('Starting test_all_submetric_edge_cases')
    # Empty model info
    empty = {}

    # SizeMetric: missing size -> default 1.0 GB
    sm = SizeMetric()
    scores = sm.calculate_metric(empty, "MODEL")
    assert isinstance(scores, dict)
    for k, v in scores.items():
        assert 0.0 <= v <= 1.0

    # LicenseMetric: unknown license -> low but non-zero
    lm = LicenseMetric()
    assert lm.calculate_metric({}, "MODEL") in (0.1, 0.5, 0.3)

    # RampUpMetric: no README, no siblings
    rm = RampUpMetric()
    rscore = rm.calculate_metric({}, "MODEL")
    assert 0.0 <= rscore <= 1.0

    # BusFactorMetric: missing dates and contributors
    bm = BusFactorMetric()
    bscore = bm.calculate_metric({}, "MODEL")
    assert 0.0 <= bscore <= 1.0

    # AvailableScoreMetric: siblings empty
    am = AvailableScoreMetric()
    ascore = am.calculate_metric({}, "MODEL")
    assert 0.0 <= ascore <= 1.0

    # DatasetQualityMetric: unknown dataset
    dm = DatasetQualityMetric()
    dscore = dm.calculate_metric({"datasets": ["some_weird_dataset"]}, "MODEL")
    assert 0.0 <= dscore <= 1.0

    # CodeQualityMetric: siblings present but non-typical names
    cm = CodeQualityMetric()
    cscore = cm.calculate_metric({"siblings": [{"rfilename": "weird.bin"}]}, "MODEL")
    assert 0.0 <= cscore <= 1.0

    # PerformanceMetric: numeric in README but no indicators
    pm = PerformanceMetric()
    pscore = pm.calculate_metric({"readme": "Value 0.99"}, "MODEL")
    assert 0.0 <= pscore <= 1.0

    logger.info('Finished test_all_submetric_edge_cases')


def test_metric_calculator_timeout_handling(monkeypatch):
    logger.info('Starting test_metric_calculator_timeout_handling')
    calc = MetricCalculator()

    # Create a slow metric that sleeps but still returns; ensure safe handling
    class SlowMetric:
        def __init__(self):
            self.name = "slow_metric"
            self.weight = 0.1
        def calculate_metric(self, data, category):
            time.sleep(0.01)
            return 1.0
        def calculate_latency(self):
            return 10

    calc.metrics.append(SlowMetric())

    # Create a failing metric
    class FailingMetric:
        def __init__(self):
            self.name = "failing"
            self.weight = 0.1
        def calculate_metric(self, data, category):
            raise RuntimeError("boom")
        def calculate_latency(self):
            return 0

    calc.metrics.append(FailingMetric())

    results = calc.calculate_all_metrics(json.dumps(sample_model_data_dict()), "MODEL")
    # ensure added metrics are present and failures didn't crash
    assert "slow_metric" in [m.name for m in calc.metrics]
    assert "failing" in [m.name for m in calc.metrics]

    # net score present
    assert "net_score" in results
    logger.info('Finished test_metric_calculator_timeout_handling')


if __name__ == '__main__':
    # Allow running the tests module directly which will invoke pytest programmatically
    # and still create logs in logs/metric_tests.log
    logger.info('Executing tests via __main__')
    sys.exit(pytest.main([os.path.abspath(__file__), '-q']))
