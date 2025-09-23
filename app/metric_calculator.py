import os 
import time
import json
from typing import * 
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from metric import Metric
from submetrics import *

os.makedirs('logs', exist_ok=True)
LOG_FILE = os.path.join('logs', 'metric_calculator.log')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MetricCalculator:
    """
    Calculates all metrics for a model in parallel and computes net score.
    Handles timing for individual metrics and overall calculation.
    """
    
    def __init__(self) -> None:
        """Initialize all metric calculators with appropriate weights."""
        self.metrics: List[Metric] = [
            SizeMetric(),
            LicenseMetric(), 
            RampUpMetric(),
            BusFactorMetric(),
            AvailableScoreMetric(),
            DatasetQualityMetric(),
            CodeQualityMetric(),
            PerformanceMetric()
        ]
        
        # Configure weights based on Sarah's priorities from spec
        self._configure_weights()
    
    def _configure_weights(self) -> None:
        """Configure metric weights based on Sarah's stated priorities."""
        # Sarah's concerns prioritized: ramp-up time, quality, documentation, maintainability
        weight_config: Dict[str, float] = {
            "ramp_up_time": 0.20,      # High priority - ease of use
            "license": 0.15,           # High priority - legal compliance  
            "dataset_and_code_score": 0.15,  # High priority - documentation
            "bus_factor": 0.15,        # High priority - maintainability
            "performance_claims": 0.10, # Medium priority - evidence of quality
            "code_quality": 0.10,      # Medium priority - code standards
            "dataset_quality": 0.10,   # Medium priority - data quality
            "size_score": 0.05        # Lower priority - deployment consideration
        }
        
        for metric in self.metrics:
            # if metric.name in weight_config:
            # metric.weight = weight_config[metric.name]
            metric.weight = 0.125
    
    def calculate_all_metrics(self, model_data: str, category: str = "MODEL") -> Dict[str, Any]:
        """
        Calculate all metrics for a model in parallel and return complete results.
        
        Args:
            model_data: JSON string containing model information from HuggingFace API
            category: Type of resource being evaluated (MODEL, DATASET, CODE)
            
        Returns:
            Dictionary containing all metric scores, latencies, and net score
        """
        start_time = time.time()
        
        # Initialize results structure
        results = {
            "category": category,
            "net_score": 0.0,
            "net_score_latency": 0
        }
        
        # Execute all metrics in parallel
        metric_results = self._calculate_metrics_parallel(model_data)
        
        # Process results and calculate net score
        net_score = 0.0
        for metric, (score, latency) in metric_results.items():
            
            # Handle size metric special case (returns dict)
            if isinstance(score, dict):
                results[f"{metric.name}"] = score
                # For net score, use average of hardware compatibility
                avg_score = sum(score.values()) / len(score) if score else 0.0
                net_score += avg_score * metric.weight
            else:
                results[metric.name] = float(score)
                net_score += float(score) * metric.weight
            
            results[f"{metric.name}_latency"] = latency
        
        # Finalize net score and latency
        results["net_score"] = min(1.0, max(0.0, net_score))
        results["net_score_latency"] = int((time.time() - start_time) * 1000)
        
        return results
    
    def _calculate_metrics_parallel(self, model_data: str) -> Dict[Metric, Tuple[Any, int]]:
        """
        Execute all metric calculations in parallel using ThreadPoolExecutor.
        
        Args:
            model_data: Model information as JSON string
            
        Returns:
            Dictionary mapping metrics to (score, latency) tuples
        """
        results = {}
        
        # Determine optimal thread count (don't exceed number of metrics or system cores)
        max_workers: int = min(len(self.metrics), os.cpu_count() or 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all metric calculations
            future_to_metric = {
                executor.submit(self._safe_calculate_metric, metric, model_data): metric
                for metric in self.metrics
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                try:
                    score, latency = future.result(timeout=30)  # 30 second timeout per metric
                    results[metric] = (score, latency)
                except Exception as e:
                    logger.warning(f"Metric {metric.name} failed: {e}")
                    results[metric] = (0.0, 0)  # Default values on failure
        
        return results
    
    def _safe_calculate_metric(self, metric: Metric, model_data: str) -> Tuple[Any, int]:
        """
        Safely calculate a single metric with error handling and timing.
        
        Args:
            metric: The metric calculator to run
            model_data: Model information
            
        Returns:
            Tuple of (score, latency_ms)
        """
        try:
            # Calculate the metric score
            score = metric.calculate_metric(model_data)
            
            # Get the latency from the metric
            latency = metric.calculate_latency()
            
            return score, latency
            
        except Exception as e:
            logger.error(f"Error calculating {metric.name}: {e}")
            return 0.0, 0
    
    def get_metric_weights(self) -> Dict[str, float]:
        """Return the current metric weights for transparency."""
        # check if self.metrics is not None
        if not self.metrics:
            return {}
        return {metric.name: metric.weight for metric in self.metrics}


def test_metric_calculator():
    """Simple test function to verify MetricCalculator functionality."""
    
    # Sample HuggingFace model data for testing
    sample_model_data = {
        "author": "google",
        "downloads": 150000,
        "likes": 1500,
        "license": "lgpl-2.1",
        "lastModified": "2025-08-15T10:30:00Z",
        "readme": """# Model Name: Gemini-2.5

        ## license: lgpl-2.1
        
        ## Usage
        This model can be used for text generation tasks.
        
        ## Training Data
        Trained on a curated dataset of high-quality text.
        
        ## Performance
        Achieves 95.2% accuracy on benchmark tasks.
        F1 score: 0.92
        BLEU: 0.99
        """,
        # "siblings": [
        #     {"rfilename": "config.json"},
        #     {"rfilename": "pytorch_model.bin"},
        #     {"rfilename": "example.py"},
        #     {"rfilename": "requirements.txt"}
        # ],
        "tags": ["text-generation", "pytorch"],
        "datasets": ["common_voice"],
        "size": 1073741824  # 1GB in bytes
    }
    
    calculator = MetricCalculator()
    
    # Convert to JSON string as expected by the calculator
    model_data_json = json.dumps(sample_model_data)
    
    # Calculate all metrics
    results = calculator.calculate_all_metrics(model_data_json, "MODEL")
    
    # Display results
    print("Metric Calculation Results:")
    print(f"Net Score: {results['net_score']:.3f}")
    print(f"Net Score Latency: {results['net_score_latency']}ms")
    print()
    
    # Display individual metric scores
    for metric in calculator.metrics:
        if f"{metric.name}_latency" in results:
            score = results.get(metric.name, 0.0)
            latency = results[f"{metric.name}_latency"]
            
            if isinstance(score, dict):
                print(f"{metric.name}: {score} (latency: {latency}ms)")
            else:
                print(f"{metric.name}: {score:.3f} (latency: {latency}ms)")


if __name__ == "__main__":
    test_metric_calculator()