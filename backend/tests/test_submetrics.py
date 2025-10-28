import os
import sys
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from submetrics import SizeMetric, LicenseMetric, PerformanceMetric, clamp


def test_size_metric_various_inputs():
    sm = SizeMetric()

    # bytes field -> should convert to GB and score accordingly
    model = {'size': 1024**3 * 2}  # 2 GB
    scores = sm.calculate_metric(model)
    assert isinstance(scores, dict)
    assert 'desktop_pc' in scores

    # safetensors list
    model2 = {'safetensors': [{'size': 1024**3}, {'size': 1024**3 * 3}]}
    s2 = sm._get_model_size(model2)
    assert s2 > 0


def test_license_metric_scores():
    lm = LicenseMetric()
    assert lm.calculate_metric({'license': 'MIT'}) == 1.0
    assert lm.calculate_metric({'license': 'GPL-3.0'}) == 0.4
    assert lm.calculate_metric({}) == 0.0


def test_performance_metric_parsing_and_clamp(monkeypatch):
    pm = PerformanceMetric()

    # Patch requests.post to return a fake response
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        'choices': [ {'message': {'content': '0.85\nAdditional text'}} ]
    }

    with patch('submetrics.requests.post', return_value=fake_resp):
        score = pm._evaluate_performance_in_readme('Some README with numbers')
        assert 0.84 < score < 0.86

    # Test clamp boundaries
    assert clamp(-1.0) == 0.0
    assert clamp(2.0) == 1.0
    assert clamp(0.5) == 0.5
