from metrics import Metrics
from submetrics import *
from concurrent.futures import ThreadPoolExecutor

class MetricCalculator:
    def __init__(self) -> None:
        self.metrics: list[Metrics] = [SizeMetric(), LicenseMetric(), RampUpMetric(), BusFactorMetric(), 
                                       AvailableScoreMetric(), DatasetQualityMetric(), CodeQualityMetric(), PerformanceMetric()]
        self.executor = None  # use to handle parallel processing to calculate all submetrics at once
        self.x = 0

    def calculate_net_score(self, data):
        with ThreadPoolExecutor() as executor:
            # Submit all calculate calls in parallel
            futures = [executor.submit(metric.calculate, data) for metric in self.metrics]
            # Collect results as they complete
            results = [future.result() for future in futures]
        # Combine results as needed
        return sum(results) 
    
    