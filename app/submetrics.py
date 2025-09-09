from .metric import Metric

class SizeMetric(Metric):
    """Measures the size of the project in terms of lines of code, number of files, etc.""" # add more details later
    def __init__(self):
        super().__init__()
        self.name: str = "size"

    def calculate_metric(self, url) -> float:
        # Implement size calculation logic here
        pass

    def calculate_latency(self):
        pass

class LicenseMetric(Metric):
    """Checks if the project has a license"""
    def __init__(self):
        super().__init__()
        self.name: str = "license"
        
    def calculate_metric(self, url) -> float:
        # Implement license calculation logic here
                
        # check if license is present
        if self.find_license(url):
            return 1.0
        else:
            return 0.0
        
    def calculate_latency(self):
        pass

    def find_license(self, url) -> bool:
        # Implement logic to check license here
        return True

class RampUpMetric(Metric):
    def __init__(self):
        super().__init__()
        self.name: str = "ramp_up"
        
    def calculate_metric(self, url) -> float:
        # Implement ramp-up calculation logic here
        pass

    def calculate_latency(self):
        pass

class BusFactorMetric(Metric):
    def __init__(self):
        super().__init__()
        self.name: str = "bus_factor"
        
    def calculate_metric(self, url) -> float:
        # Implement bus factor calculation logic here
        pass

    def calculate_latency(self):
        pass

class AvailableScoreMetric(Metric):
    def __init__(self):
        super().__init__()
        self.name: str = "available_score"
        
    def calculate_metric(self, url) -> float:
        # Implement available score calculation logic here

        accessible: bool = True # replace with actual logic to check if repo is accessible
        if accessible:
            return 1.0
        else:
            return 0.0
        
    def calculate_latency(self):
        pass

class DatasetQualityMetric(Metric):
    """
    Assesses the quality of the dataset provided in the repository on 
    5 dimensions: accuracy, completeness, consistency, timeliness, and relevance
    """
    def __init__(self):
        super().__init__()
        self.name: str = "dataset_quality"
        
    def calculate_metric(self, url) -> float:
        # Implement dataset quality calculation logic here
        pass

    def calculate_latency(self):
        pass

# Maybe use an LLM to evaluate code quality?
class CodeQualityMetric(Metric):
    def __init__(self):
        super().__init__()
        self.name: str = "code_quality"
        
    def calculate_metric(self, url) -> float:
        # Implement code quality calculation logic here
        pass

    def calculate_latency(self):
        pass

class PerformanceMetric(Metric):
    """Evaluate the performance claims of the project using an open-source LLM model"""
    def __init__(self):
        super().__init__()
        self.name: str = "performance"
        
    def calculate_metric(self, url) -> float:
        # Implement performance calculation logic here
        pass

    def calculate_latency(self):
        pass

    def connect_to_model(self):
        # Implement logic to connect to an open-source LLM model here
        pass
