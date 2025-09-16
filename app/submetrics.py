import os
from typing import *
from metric import Metric
from huggingface_hub import HfApi

HF_TOKEN=os.environ["HF_TOKEN"]
GITHUB_TOKEN=os.environ["GITHUB_TOKEN"]
api = HfApi(token=HF_TOKEN)

# ==================================================================================================

class SizeMetric(Metric):
    """Measures the size of the project in terms of lines of code, number of files, etc.""" # add more details later
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "size"
        self.category = category

    def calculate_metric(self, url: str, category: str) -> float:
        # Implement size calculation logic here
        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")

    def calculate_latency(self):
        pass

# ==================================================================================================

class LicenseMetric(Metric):
    """Checks if the project has a license"""
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "license"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement license calculation logic here

        if category == "model":
            return 0.0 # models do not have a license ? 
        elif category == "dataset":
            return 0.0 # datasets do not have a license ? 
        elif category == "code":
            # check if license is present
            if self.find_license(url):
                return 1.0
            else:
                return 0.0
        else:
            raise ValueError("Unsupported category passed")
        
        
    def calculate_latency(self):
        pass

    def find_license(self, url: str, category: str) -> bool:
        # Implement logic to check license here

        # The license can be assumed to be found within the README file,
        # under a markdown header "license" or "License".
        # It must be compatible with the LGPL v2.1 licence.
        return True

# ==================================================================================================

class RampUpMetric(Metric):
    """
    Calculate the ramp-up time of the project by checking 
    the presence of documentation, examples, and ease of setup
    """
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "ramp_up"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement ramp-up calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")
        
        pass

    def calculate_latency(self):
        pass

# ==================================================================================================

class BusFactorMetric(Metric):
    """
    Calculate the bus factor of the project by 
    analyzing the number of contributors to a project
    """
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "bus_factor"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement bus factor calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")
        
        pass

    def calculate_latency(self):
        pass

# ==================================================================================================

class AvailableScoreMetric(Metric):
    """Check if the repository is accessible"""
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "available_score"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement available score calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")
        
        accessible: bool = True # replace with actual logic to check if repo is accessible
        if accessible:
            return 1.0
        else:
            return 0.0
        
    def calculate_latency(self):
        pass

# ==================================================================================================

class DatasetQualityMetric(Metric):
    """
    Assesses the quality of the dataset provided in the repository on 
    5 dimensions: accuracy, completeness, consistency, timeliness, and relevance
    """
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "dataset_quality"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement dataset quality calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")
        
        pass

    def calculate_latency(self):
        pass

# ==================================================================================================

# Maybe use an LLM to evaluate code quality?
class CodeQualityMetric(Metric):
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "code_quality"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement code quality calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")

        pass

    def calculate_latency(self):
        pass

# ==================================================================================================

class PerformanceMetric(Metric):
    """Evaluate the performance claims of the project using an open-source LLM model"""
    def __init__(self, category: str = None) -> None:
        super().__init__()
        self.name: str = "performance"
        self.category = category
        
    def calculate_metric(self, url: str, category: str) -> float:
        # Implement performance calculation logic here

        if category == "model":
            pass
        elif category == "dataset":
            pass
        elif category == "code":
            pass
        else:
            raise ValueError("Unsupported category passed")
        
        pass

    def calculate_latency(self):
        pass

    def connect_to_model(self):
        # Implement logic to connect to an open-source LLM model here
        pass
