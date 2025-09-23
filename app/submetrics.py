import time
import json
import re
import logging
from datetime import datetime, timezone
from typing import * 
from metric import Metric

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename='metric_calculator.log', filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class SizeMetric(Metric):
    """Calculates size compatibility scores for different hardware platforms"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "size_score"
        self.weight = 0.125
        
        # Hardware compatibility thresholds in GB 
        self.hardware_limits = {
            "raspberry_pi": 2.0,
            "jetson_nano": 4.0, 
            "desktop_pc": 16.0,
            "aws_server": 64.0
        }
        logger.info("SizeMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> Dict[str, float]:
        """Calculate size scores for each hardware type"""
        start_time = time.time()
        
        try:
            # Parse model size from data (expecting JSON with model info)
            model_info = json.loads(data) if isinstance(data, str) else data
            model_size_gb = self._get_model_size(model_info)
            
            scores = {}
            for hardware, limit in self.hardware_limits.items():
                if model_size_gb <= limit:
                    # Linear scoring: smaller models get higher scores
                    scores[hardware] = max(0.0, 1.0 - (model_size_gb / limit))
                else:
                    scores[hardware] = 0.0
                    
            self._latency = int((time.time() - start_time) * 1000)
            return scores
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            # Return minimum scores on error
            return {hw: 0.0 for hw in self.hardware_limits.keys()}
    
    def _get_model_size(self, model_info: Dict[str, Any]) -> float:
        """Extract model size in GB from model info"""
        # Try to get size from various possible fields
        if "size" in model_info:
            return float(model_info["size"]) / (1024**3)  # Convert bytes to GB
        elif "model_size" in model_info:
            return float(model_info["model_size"])
        elif "safetensors" in model_info:
            return sum(float(f.get("size", 0)) for f in model_info["safetensors"]) / (1024**3)
        else:
            # Default assumption for unknown size
            return 1.0
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class LicenseMetric(Metric):
    """Evaluates license clarity and LGPL v2.1 compatibility"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "license"
        self.weight = 0.125
        
        # LGPL v2.1 compatible licenses (higher scores)
        self.compatible_licenses = {
            "lgpl-2.1", "lgpl", "mit", "bsd", "apache-2.0", "apache", "cc0-1.0"
        }
        
        # Problematic licenses (lower scores)  
        self.problematic_licenses = {
            "gpl", "gpl-3.0", "agpl", "cc-by-nc", "proprietary"
        }
        logger.info("LicenseMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            license_text = self._extract_license(model_info)
            
            score = self._score_license(license_text)
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _extract_license(self, model_info: Dict[str, Any]) -> str:
        """Extract license information from model data"""
        # Check various fields where license might be stored
        license_fields = ["license", "license_name", "license_type"]
        
        for field in license_fields:
            if field in model_info and model_info[field]:
                return str(model_info[field]).lower()
        
        # Check in tags or metadata
        if "tags" in model_info:
            for tag in model_info["tags"]:
                if "license:" in str(tag).lower():
                    return str(tag).lower().replace("license:", "").strip()
        
        return ""
    
    def _score_license(self, license_text: str) -> float:
        """Score license based on compatibility and clarity"""
        if not license_text:
            return 0.1  # No license information
        
        license_lower = license_text.lower()
        
        # Check for compatible licenses
        for compatible in self.compatible_licenses:
            if compatible in license_lower:
                return 0.9  # High score for compatible licenses
        
        # Check for problematic licenses  
        for problematic in self.problematic_licenses:
            if problematic in license_lower:
                return 0.3  # Low score for incompatible licenses
        
        # Unknown license but present
        return 0.5
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class RampUpMetric(Metric):
    """Evaluates ease of getting started with the model"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "ramp_up_time"
        self.weight = 0.125
        logger.info("RampUpMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            score = 0.0
            
            # Check for README quality (30% of score)
            readme_score = self._evaluate_readme(model_info.get("readme", ""))
            score += readme_score * 0.3
            
            # Check for example code/notebooks (25% of score)
            examples_score = self._check_examples(model_info)
            score += examples_score * 0.25
            
            # Check for clear model card/description (25% of score)
            card_score = self._evaluate_model_card(model_info)
            score += card_score * 0.25
            
            # Check for download/usage statistics (20% of score) 
            popularity_score = self._evaluate_popularity(model_info)
            score += popularity_score * 0.2
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_readme(self, readme: str) -> float:
        """Evaluate README quality"""
        if not readme:
            return 0.0
        
        readme_lower = readme.lower()
        score = 0.0
        
        # Check for key sections
        if "usage" in readme_lower or "how to use" in readme_lower:
            score += 0.3
        if "installation" in readme_lower or "install" in readme_lower:
            score += 0.3
        if "example" in readme_lower:
            score += 0.2
        if len(readme) > 500:  # Substantial documentation
            score += 0.2
        
        return min(1.0, score)
    
    def _check_examples(self, model_info: Dict[str, Any]) -> float:
        """Check for example code or notebooks"""
        files = model_info.get("siblings", [])
        if not files:
            return 0.0
        
        example_indicators = ["example", "demo", "notebook", ".ipynb", "sample"]
        
        for file_info in files:
            filename = file_info.get("rfilename", "").lower()
            for indicator in example_indicators:
                if indicator in filename:
                    return 1.0
        
        return 0.0
    
    def _evaluate_model_card(self, model_info: Dict[str, Any]) -> float:
        """Evaluate model card completeness"""
        score = 0.0
        
        if model_info.get("description"):
            score += 0.4
        if model_info.get("tags"):
            score += 0.3  
        if model_info.get("datasets"):
            score += 0.3
        
        return min(1.0, score)
    
    def _evaluate_popularity(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on downloads and likes"""
        downloads = model_info.get("downloads", 0)
        likes = model_info.get("likes", 0)
        
        # Normalize scores
        download_score = min(1.0, downloads / 10000)  # Scale to 10k downloads
        like_score = min(1.0, likes / 100)  # Scale to 100 likes
        
        return (download_score + like_score) / 2
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class BusFactorMetric(Metric):
    """Evaluates knowledge concentration risk (higher = safer)"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "bus_factor"
        self.weight = 0.125
        logger.info("BusFactorMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            score = 0.0
            
            # Organization vs individual author (40% of score)
            org_score = self._evaluate_organization(model_info)
            score += org_score * 0.4
            
            # Number of collaborators/contributors (30% of score)
            contrib_score = self._evaluate_contributors(model_info)
            score += contrib_score * 0.3
            
            # Activity and maintenance (30% of score)
            activity_score = self._evaluate_activity(model_info)
            score += activity_score * 0.3
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_organization(self, model_info: Dict[str, Any]) -> float:
        """Higher score for organizational backing"""
        author = model_info.get("author", "").lower()
        
        # Known organizations get higher scores
        organizations = [
            "google", "microsoft", "facebook", "meta", "openai", 
            "anthropic", "huggingface", "stanford", "mit", "berkeley"
        ]
        
        for org in organizations:
            if org in author:
                return 1.0
        
        # Check if it looks like an organization (not individual name)
        if any(indicator in author for indicator in ["team", "lab", "corp", "inc", "ltd"]):
            return 0.8
        
        return 0.3  # Individual author
    
    def _evaluate_contributors(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on number of contributors"""
        # This would ideally use git metadata, simplified for now
        contributors = model_info.get("contributors", [])
        
        if len(contributors) >= 5:
            return 1.0
        elif len(contributors) >= 3:
            return 0.7
        elif len(contributors) >= 2:
            return 0.5
        else:
            return 0.2
    
    def _evaluate_activity(self, model_info: Dict[str, Any]) -> float:
        """Evaluate recent activity"""
        last_modified = model_info.get("lastModified")
        if not last_modified:
            return 0.2
        
        # Parse date and calculate days since last update
        try:
            last_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            days_old = (datetime.now(timezone.utc) - last_date).days
            
            if days_old <= 30:
                return 1.0
            elif days_old <= 90:
                return 0.7
            elif days_old <= 365:
                return 0.4
            else:
                return 0.1
        except:
            return 0.2
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class AvailableScoreMetric(Metric):
    """Evaluates availability of dataset and code documentation"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "dataset_and_code_score"
        self.weight = 0.125
        logger.info("AvailableScoreMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            score = 0.0
            
            # Dataset documentation (50% of score)
            dataset_score = self._evaluate_dataset_info(model_info)
            score += dataset_score * 0.5
            
            # Code availability (50% of score)
            code_score = self._evaluate_code_availability(model_info)
            score += code_score * 0.5
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_dataset_info(self, model_info: Dict[str, Any]) -> float:
        """Evaluate dataset documentation quality"""
        score = 0.0
        
        # Check for dataset tags/metadata
        if model_info.get("datasets"):
            score += 0.6
        
        # Check README for dataset information
        readme = model_info.get("readme", "").lower()
        if any(term in readme for term in ["dataset", "training data", "trained on"]):
            score += 0.4
        
        return min(1.0, score)
    
    def _evaluate_code_availability(self, model_info: Dict[str, Any]) -> float:
        """Evaluate code availability"""
        files = model_info.get("siblings", [])
        if not files:
            return 0.0
        
        score = 0.0
        code_indicators = [".py", ".ipynb", "train", "eval", "inference"]
        
        for file_info in files:
            filename = file_info.get("rfilename", "").lower()
            for indicator in code_indicators:
                if indicator in filename:
                    score += 0.2
                    break
        
        return min(1.0, score)
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class DatasetQualityMetric(Metric):
    """Evaluates quality of associated datasets"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "dataset_quality"  
        self.weight = 0.125
        logger.info("DatasetQualityMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            # For now, base quality on dataset documentation and known datasets
            score = self._evaluate_dataset_reputation(model_info)
            
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_dataset_reputation(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on known high-quality datasets"""
        datasets = model_info.get("datasets", [])
        if not datasets:
            return 0.2
        
        high_quality_datasets = [
            "common_voice", "librispeech", "imagenet", "coco", "squad",
            "glue", "superglue", "wikitext", "bookcorpus", "openwebtext"
        ]
        
        for dataset in datasets:
            dataset_lower = str(dataset).lower()
            for quality_dataset in high_quality_datasets:
                if quality_dataset in dataset_lower:
                    return 0.9
        
        # Unknown datasets get moderate score
        return 0.5
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class CodeQualityMetric(Metric):
    """Evaluates code style and maintainability"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "code_quality"
        self.weight = 0.125
        logger.info("CodeQualityMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            # Simplified code quality assessment
            score = self._evaluate_code_presence(model_info)
            
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_code_presence(self, model_info: Dict[str, Any]) -> float:
        """Basic evaluation of code presence and organization"""
        files = model_info.get("siblings", [])
        if not files:
            return 0.1
        
        score = 0.0
        
        # Look for structured code files
        python_files = [f for f in files if f.get("rfilename", "").endswith(".py")]
        if python_files:
            score += 0.4
        
        # Look for configuration files
        config_files = [f for f in files if "config" in f.get("rfilename", "").lower()]
        if config_files:
            score += 0.3
        
        # Look for requirements or setup files
        setup_indicators = ["requirements", "setup", "environment"]
        for file_info in files:
            filename = file_info.get("rfilename", "").lower()
            if any(indicator in filename for indicator in setup_indicators):
                score += 0.3
                break
        
        return min(1.0, score)
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class PerformanceMetric(Metric):
    """Evaluates evidence of performance claims and benchmarks"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "performance_claims"
        self.weight = 0.125
        logger.info("PerformanceMetric metric successfully initialized")
    
    def calculate_metric(self, data: str) -> float:
        start_time = time.time()
        
        try:
            model_info = json.loads(data) if isinstance(data, str) else data
            
            score = 0.0
            
            # Check README for performance metrics (60% of score)
            readme_score = self._evaluate_performance_in_readme(model_info.get("readme", ""))
            score += readme_score * 0.6
            
            # Check for evaluation files (40% of score)  
            eval_score = self._check_evaluation_files(model_info)
            score += eval_score * 0.4
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_performance_in_readme(self, readme: str) -> float:
        """Look for performance metrics in README"""
        if not readme:
            return 0.0
        
        readme_lower = readme.lower()
        performance_indicators = [
            "accuracy", "f1", "bleu", "rouge", "perplexity", 
            "benchmark", "evaluation", "performance", "results"
        ]
        
        score = 0.0
        for indicator in performance_indicators:
            if indicator in readme_lower:
                score += 0.2
        
        # Look for numerical results (suggests actual benchmarking)
        if re.search(r'\d+\.\d+', readme) and any(ind in readme_lower for ind in performance_indicators):
            score += 0.3
        
        return min(1.0, score)
    
    def _check_evaluation_files(self, model_info: Dict[str, Any]) -> float:
        """Check for evaluation or benchmark files"""
        files = model_info.get("siblings", [])
        if not files:
            return 0.0
        
        eval_indicators = ["eval", "benchmark", "test", "metric"]
        
        for file_info in files:
            filename = file_info.get("rfilename", "").lower()
            for indicator in eval_indicators:
                if indicator in filename:
                    return 1.0
        
        return 0.0
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)