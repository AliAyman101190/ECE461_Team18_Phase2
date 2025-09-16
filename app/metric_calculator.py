import os
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

    def calculate_net_score(self, data: str, category: str) -> float:
        with ThreadPoolExecutor() as executor:
            
            # Submit all calculate calls in parallel
            futures = [executor.submit(metric.calculate_metric, data, category) for metric in self.metrics]

            # Collect results as they complete
            results = [future.result() for future in futures]
        # Combine results as needed
        return sum(results) 
    

def test_metric_calculator():
    calculator = MetricCalculator()
    url = ""
    category = "model"
    net_score = calculator.calculate_net_score(url, category)
    print(f"Net Score: {net_score}")

if __name__ == "__main__":
    test_metric_calculator()