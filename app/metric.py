"""
Abstract Metric class to be inherited by all metrics
"""
from abc import ABC, abstractmethod

class Metric(ABC):
    def __init__(self) -> None:
        self.name: str = ""
        self.weight: float = 0.125

    @abstractmethod
    def calculate_metric(self):
        return NotImplementedError("Each metric should implement this method")

    @abstractmethod
    def calculate_latency(self):
        return NotImplementedError("Each metric should implement this method")
