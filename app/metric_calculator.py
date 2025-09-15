from typing import *
from metric import Metric
from submetrics import *
from concurrent.futures import ThreadPoolExecutor

class MetricCalculator:
    def __init__(self) -> None:
        self.metrics: list[Metric] = [
            SizeMetric(), LicenseMetric(), RampUpMetric(), BusFactorMetric(), 
            AvailableScoreMetric(), DatasetQualityMetric(), CodeQualityMetric(), PerformanceMetric()
        ]

    def calculate_net_score(self, data: str, type: str) -> float:
        with ThreadPoolExecutor() as executor:
            
            # Submit all calculate calls in parallel
            futures = [executor.submit(metric.calculate_metric, data, type) for metric in self.metrics]

            # Collect results as they complete
            results = [future.result() for future in futures]
        # Combine results as needed
        return sum(results) 
    