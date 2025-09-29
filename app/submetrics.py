import os
import math
from pyexpat import model
import re
import time
import json
import requests
import logging
from datetime import datetime, timezone
from typing import * 
from metric import Metric
try:
    from dotenv import load_dotenv # pyright: ignore[reportMissingImports]
    # Load .env and allow .env to override empty env vars set by the `run` script
    load_dotenv(override=True)
except Exception:
    # python-dotenv not installed; tests should still run without env overrides
    pass

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
try:
    os.makedirs('logs', exist_ok=True)
    LOG_FILE = os.path.join('logs', 'submetrics.log')
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(LOG_FILE) for h in logger.handlers):
        fh = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
except Exception:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(sh)
finally:
    logger.propagate = False

logger.info("submetrics initialized; logging to %s", LOG_FILE)

# Read Gen AI Studio API key safely (may be missing). Do not raise on missing key.
GEN_AI_STUDIO_API_KEY = os.environ.get('GEN_AI_STUDIO_API_KEY')
logger.debug("submetrics: GEN_AI_STUDIO_API_KEY present=%s", bool(GEN_AI_STUDIO_API_KEY))


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

        # Utilization factors tuned for realistic model deployment
        # # Based on expected scoring patterns: smaller models score higher on all devices
        # self.utilization_factors = {
        #     "raspberry_pi": 0.5,      # 50% of 2GB = ~1.0GB usable for models
        #     "jetson_nano": 0.7,       # 70% of 4GB = ~2.8GB usable
        #     "desktop_pc": 0.8,        # 80% of 16GB = ~12.8GB usable  
        #     "aws_server": 0.9         # 90% of 64GB = ~57.6GB usable
        # }
        logger.info("SizeMetric metric successfully initialized")
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> Dict[str, float]:
        """Calculate size scores for each hardware type"""
        start_time = time.time()
        
        try:
            # Parse model size from data (expecting JSON with model info)
            model_size_gb = self._get_model_size(model_info)
            logger.info(f"SizeMetric: Detected model size: {model_size_gb:.3f} GB")
            
            scores: Dict[str, float] = {}
            for hardware, limit_gb in self.hardware_limits.items():
                # Calculate effective memory limit after accounting for OS and overhead
                
                usage = limit_gb / model_size_gb
                scores[hardware] = usage if usage <= 1.0 else 1.0


            self._latency = int((time.time() - start_time) * 1000)
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating SizeMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            # Return minimum scores on error
            return {hw: 0.0 for hw in self.hardware_limits.keys()}
    
    def _get_model_size(self, model_info: Dict[str, Any]) -> float:
        """Extract model size in GB from model info"""
        # Priority 1: Use HuggingFace's actual storage data (most accurate)
        if "used_storage" in model_info and model_info["used_storage"]:
            try:
                storage_bytes = float(model_info["used_storage"])
                return storage_bytes / (1024**3)  # Convert bytes to GB
            except Exception:
                pass
        
        # # Priority 2: Try to get size from various other possible fields
        # if "size" in model_info:
        #     try:
        #         raw_size = float(model_info["size"])  # Could be bytes or GB
        #     except Exception:
        #         raw_size = 0.0
        #     # Assume bytes only if >= 1 GiB; otherwise treat as GB to avoid inflating small sizes
        #     if raw_size >= (1024**3):
        #         return raw_size / (1024**3)
        #     else:
        #         return raw_size
        # elif "model_size" in model_info:
        #     return float(model_info["model_size"])
        elif "safetensors" in model_info:
            try:
                st = model_info["safetensors"]
                # HF can return a dict with a 'total' size or a list of files
                if isinstance(st, dict):
                    total_bytes = 0.0
                    if "total" in st:
                        total_bytes = float(st.get("total") or 0)
                    elif "size" in st:
                        total_bytes = float(st.get("size") or 0)
                    return float(total_bytes) / (1024**3)
                elif isinstance(st, list):
                    total_bytes = 0.0
                    for f in st:
                        try:
                            total_bytes += float((f or {}).get("size", 0) or 0)
                        except Exception:
                            continue
                    return float(total_bytes) / (1024**3)
            except Exception:
                pass
        # As a fallback, try summing model weight files from siblings if sizes are present
        try:
            siblings = model_info.get("siblings") or []
            if isinstance(siblings, list) and siblings:
                model_file_indicators = [
                    ".safetensors", "pytorch_model.bin", "tf_model.h5", "model.onnx",
                ]
                total_bytes = 0.0
                for file_info in siblings:
                    name = str((file_info or {}).get("rfilename") or (file_info or {}).get("filename") or (file_info or {}).get("path") or "").lower()
                    if any(ind in name for ind in model_file_indicators):
                        try:
                            total_bytes += float((file_info or {}).get("size", 0) or 0)
                        except Exception:
                            continue
                if total_bytes > 0:
                    return float(total_bytes) / (1024**3)
        except Exception:
            pass
        # Default assumption for unknown size
        return 0.6
    
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
            "lgpl-2.1", "lgpl", "mit", "bsd", "apache-2.0", "apache license 2.0", "apache", "cc0-1.0"
        }
        
        # Problematic licenses (lower scores)  
        self.problematic_licenses = {
            "gpl", "gpl-3.0", "agpl", "cc-by-nc", "proprietary"
        }
        logger.info("LicenseMetric metric successfully initialized")
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            license_text = self._extract_license(model_info)
            
            score = self._score_license(license_text)
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            logger.error(f"Error calculating LicenseMetric: {e}")
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

        # add logic to check model_info['readme] for a line with license: {license} in it
        if "readme" in model_info and model_info["readme"]:
            for line in model_info["readme"].split("\n"):
                if "license:" in line.lower():
                    return line.lower().replace("license:", "").strip()
        
        return ""
    
    def _score_license(self, license_text: str) -> float:
        """Score license based on compatibility and clarity"""
        if not license_text:
            return 0.0  # No license information
        
        license_lower = license_text.lower()
        
        # Check for compatible licenses
        for compatible in self.compatible_licenses:
            if compatible in license_lower:
                return 1.0  # High score for compatible licenses
        
        # Check for problematic licenses  
        for problematic in self.problematic_licenses:
            if problematic in license_lower:
                return 0.4  # Low score for incompatible licenses
        
        # Unknown license means most likely no license
        return 0.0
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class RampUpMetric(Metric):
    """Evaluates ease of getting started with the model"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "ramp_up_time"
        self.weight = 0.125
        logger.info("RampUpMetric metric successfully initialized")
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            
            score = 0.0
            
            # Check for README quality (50% of score)
            readme_score = self._evaluate_readme(model_info.get("readme", ""))
            score += readme_score * 0.5
            
            # Check for clear model card/description (20% of score)
            card_score = self._evaluate_model_card(model_info)
            score += card_score * 0.2
            
            # Check for download/usage statistics (30% of score) 
            popularity_score = self._evaluate_popularity(model_info)
            score += popularity_score * 0.3
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating RampUpMetric: {e}")
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
        if "example" in readme_lower or "```python" in readme_lower:
            score += 0.3
        if "install" in readme_lower:
            score += 0.2
        if len(readme) > 500:  # Substantial documentation
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_model_card(self, model_info: Dict[str, Any]) -> float:
        """Evaluate model card completeness"""
        score = 0.0
        
        if model_info.get("description"):
            score += 0.7
        if model_info.get("datasets"):
            score += 0.2
        if model_info.get("tags"):
            score += 0.1  
        
        return min(1.0, score)
    
    def _evaluate_popularity(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on downloads and likes"""
        # Use safe defaults if fields are missing or None
        downloads_last_month = model_info.get("downloads_last_month") or 0
        likes = model_info.get("likes") or 0
        stars = model_info.get("stars") or 0

        # Normalize scores
        download_score = min(1.0, downloads_last_month / 10000)  # Scale to 10k downloads
        like_score = min(1.0, likes / 100)  # Scale to 100 likes
        stars_score = min(1.0, stars / 100)  # Scale to 100 stars

        return (download_score + like_score + stars_score) / 3
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class BusFactorMetric(Metric):
    """Evaluates knowledge concentration risk (higher = safer)"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "bus_factor"
        self.weight = 0.125
        logger.info("BusFactorMetric metric successfully initialized")
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            score = 0.0
            
            # Organization vs individual author (60% of score)
            org_score = self._evaluate_organization(model_info)
            score += org_score * 0.6
            
            # Number of collaborators/contributors (30% of score)
            contrib_score = self._evaluate_contributors(model_info)
            score += contrib_score * 0.3
            
            # Activity and maintenance (10% of score)
            activity_score = self._evaluate_activity(model_info)
            score += activity_score * 0.1
            
            self._latency = int((time.time() - start_time) * 1000)
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating BusFactorMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_organization(self, model_info: Dict[str, Any]) -> float:
        """Higher score for organizational backing"""
        author = model_info.get("author", "").lower()
        model_id = model_info.get("id", "").lower()
        
        # Known organizations get higher scores
        organizations = [
            "google", "microsoft", "facebook", "meta", "openai", 
            "anthropic", "huggingface", "stanford", "mit", "berkeley",
            "research", "ai", "deepmind", "nvidia", "apple"
        ]
        
        # Check both author and model ID for organization indicators
        search_text = f"{author} {model_id}"
        for org in organizations:
            if org in search_text:
                return 1.0
        
        # Check if it looks like an organization (not individual name)
        if any(indicator in search_text for indicator in ["team", "lab", "corp", "inc", "ltd", "research", "ai", "institute"]):
            return 0.8
        
        return 0.3  # Individual author
    
    def _evaluate_contributors(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on number of contributors"""
        # This would ideally use git metadata, simplified for now
        num_contributors = model_info.get("contributors_count") or 0

        # Ensure num_contributors is an int
        try:
            num_contributors = int(num_contributors)
        except Exception:
            num_contributors = 0

        if num_contributors >= 10:
            return 1.0
        elif num_contributors >= 6:
            return 0.7
        elif num_contributors >= 3:
            return 0.5
        else:
            return 0.2
    
    def _evaluate_activity(self, model_info: Dict[str, Any]) -> float:
        """Evaluate recent activity based on last modified date"""
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
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
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
            logger.error(f"Error calculating AvailableScoreMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_dataset_info(self, model_info: Dict[str, Any]) -> float:
        """Evaluate dataset documentation quality"""
        score = 0.0
        
        # Check for dataset tags/metadata
        datasets = model_info.get("datasets")
        if datasets:
            score += 0.6
        
        # Check README for dataset information
        readme = (model_info.get("readme") or "").lower()
        dataset_terms = ["dataset", "training data", "trained on", "corpus", "data", "pretraining", "fine-tuned", "benchmark"]
        if any(term in readme for term in dataset_terms):
            score += 0.4
        
        # Check tags for dataset information
        tags = model_info.get("tags", [])
        dataset_tags = ["dataset", "corpus", "benchmark", "evaluation"]
        if any(any(tag_term in str(tag or "").lower() for tag_term in dataset_tags) for tag in tags):
            score += 0.2
        
        # Check for model card or description mentioning datasets
        description = (model_info.get("description") or "").lower()
        if description and any(term in description for term in dataset_terms):
            score += 0.3
        
        return min(1.0, score)
    
    def _evaluate_code_availability(self, model_info: Dict[str, Any]) -> float:
        """Evaluate code availability"""
        files = model_info.get("siblings", [])
        readme = (model_info.get("readme") or "").lower()

        score = 0.0
        
        # Check for actual code files
        if files:
            code_indicators = [".py", ".ipynb", ".js", ".ts", ".r", "train", "eval", "inference", "example", "demo", "config", ".json", ".yaml", ".yml", ".csv", ".txt", ".jsonl", ".jsonl.gz", ".jsonl.bz2", ".jsonl.xz", ".jsonl.zst", ".jsonl.lz4", ".jsonl.snappy", ".jsonl.gzip", ".jsonl.bzip2", ".jsonl.xz", ".jsonl.zst", ".jsonl.lz4", ".jsonl.snappy", ".jsonl.gzip", ".jsonl.bzip2", ".jsonl.xz", ".mlmodel"]
            
            for file_info in files:
                filename = str(file_info.get("rfilename") or "").lower()
                for indicator in code_indicators:
                    if indicator in filename:
                        score += 0.2
                        break
        
        # Check README for code examples or usage instructions
        code_terms = ["usage", "example", "code", "import", "from transformers", "model =", "tokenizer =", "```python", "```"]
        if any(term in readme for term in code_terms):
            score += 0.4
        
        # Check for model-specific files that indicate usability
        if files:
            model_files = ["config.json", "tokenizer", "vocab", "model.safetensors", "pytorch_model.bin"]
            for file_info in files:
                filename = str(file_info.get("rfilename") or "").lower()
                if any(model_file in filename for model_file in model_files):
                    score += 0.3
                    break
        
        # If no files but substantial documentation with usage info, still give some credit
        if not files and len(readme) > 500 and any(term in readme for term in ["usage", "how to use", "import"]):
            score = 0.6
        
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
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            # For now, base quality on dataset documentation and known datasets
            # score = self._evaluate_dataset_reputation(model_info)
            if model_info.get('dataset_present'):
                score = 1.0
            else: 
                score = 0.0
            
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            logger.error(f"Error calculating DatasetQualityMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_dataset_reputation(self, model_info: Dict[str, Any]) -> float:
        """Evaluate based on known high-quality datasets"""
        # datasets = model_info.get("datasets", [])
        # if not datasets:
        #     return 0.2
        # homepage = (model_info.get("homepage") or "").lower()
        # if not homepage:
        #     return 0.2
        readme = (model_info.get("readme", "")).lower()
        
        high_quality_datasets = [
            "common_voice", "librispeech", "imagenet", "coco", "squad",
            "glue", "superglue", "wikitext", "bookcorpus", "openwebtext", "arxiv", "wikipedia"
        ]
        
        for dataset in high_quality_datasets:
            if dataset in readme:
                return 1.0
        
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
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            # Simplified code quality assessment
            # score = self._evaluate_code_presence(model_info)
            if model_info.get('code_present'):
                score = 1.0
            else: 
                score = 0.0
            
            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            logger.error(f"Error calculating CodeQualityMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
    
    def _evaluate_code_presence(self, model_info: Dict[str, Any]) -> float:
        """Basic evaluation of code presence and organization"""
        files = model_info.get("siblings") or []
        readme = model_info.get("readme", "").lower()
        
        # If no files but has substantial README, still give some credit
        if not files:
            if len(readme) > 1000 and any(keyword in readme for keyword in ["usage", "example", "code", "implementation"]):
                return 0.5
            return 0.1
        
        score = 0.0
        
        # Look for structured code files
        code_extensions = [".py", ".ipynb", ".js", ".ts", ".r", ".java", ".cpp", ".c"]
        code_files = []
        for f in files:
            name = str((f or {}).get("rfilename") or (f or {}).get("filename") or (f or {}).get("path") or "").lower()
            if any(name.endswith(ext) for ext in code_extensions):
                code_files.append(f)
        if code_files:
            score += 0.4
        
        # Look for configuration files
        config_indicators = ["config", "settings", "hyperparameters", "params"]
        config_files = []
        for f in files:
            name = str((f or {}).get("rfilename") or (f or {}).get("filename") or (f or {}).get("path") or "").lower()
            if any(indicator in name for indicator in config_indicators):
                config_files.append(f)
        if config_files:
            score += 0.3
        
        # Look for requirements or setup files
        setup_indicators = ["requirements", "setup", "environment", "conda", "dockerfile", "makefile", "poetry"]
        for file_info in files:
            filename = str((file_info or {}).get("rfilename") or (file_info or {}).get("filename") or (file_info or {}).get("path") or "").lower()
            if any(indicator in filename for indicator in setup_indicators):
                score += 0.3
                break
        
        # Look for model-specific files that indicate quality
        model_indicators = ["model", "checkpoint", "weights", "tokenizer", "vocab"]
        model_files = []
        for f in files:
            name = str((f or {}).get("rfilename") or (f or {}).get("filename") or (f or {}).get("path") or "").lower()
            if any(indicator in name for indicator in model_indicators):
                model_files.append(f)
        if model_files:
            score += 0.2
        
        # README-based bonus even when files exist (indicates usage and examples)
        readme_code_terms = ["usage", "example", "code", "import", "from transformers", "model =", "tokenizer =", "```python", "```"]
        if any(term in readme for term in readme_code_terms):
            score += 0.2
        
        # Ensure a small baseline if files exist but indicators are sparse
        if score == 0.0:
            score = 0.1
        
        return min(1.0, score)
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)


class PerformanceMetric(Metric):
    """Evaluates evidence of performance claims and benchmarks"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "performance_claims"
        self.weight: float = 0.125
        self.system_prompt: str = self.get_system_prompt()
        logger.info("PerformanceMetric metric successfully initialized")

    def get_system_prompt(self) -> str:
        return """
You are an expert in evaluating machine learning model performance claims based on README content and available benchmark files.
Your task is to assess the credibility and quality of performance information provided for a given model.

When evaluating the README, look for:
- Explicit performance metrics (e.g. accuracy)
- Benchmark results
- Clear descriptions of evaluation methodology
- Numerical results that suggest actual benchmarking was performed
- Thorough explanation on how the model works and what it excels at

OUTPUT REQUIREMENTS:
- Start your response with the determined score and a newline character  (e.g. '0.85\\n')
- Return a float score between 0.0 and 1.0
- The float value should be the only content on the first line
- The float value should always be formatted to two decimal places
"""
    
    def calculate_metric(self, model_info: Dict[str, Any]) -> float:
        start_time = time.time()
        
        try:
            
            score = 0.0
            
            # Have AI check README for performance metrics 
            readme_score = self._evaluate_performance_in_readme(model_info.get("readme", ""))
            score += readme_score

            self._latency = int((time.time() - start_time) * 1000)
            return score
            
        except Exception as e:
            logger.error(f"Error calculating PerformanceMetric: {e}")
            self._latency = int((time.time() - start_time) * 1000)
            return 0.0
        
    def _evaluate_performance_in_readme(self, readme: str) -> float:
        url = "https://genai.rcac.purdue.edu/api/chat/completions"
        # Only include Authorization header when API key is present
        headers = {"Content-Type": "application/json"}
        if GEN_AI_STUDIO_API_KEY:
            headers["Authorization"] = f"Bearer {GEN_AI_STUDIO_API_KEY}"
        else:
            logger.debug("Gen AI Studio API key not present; skipping authenticated header")
        body = {
            "model": "llama4:latest",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": readme}
            ],
            "response_format": {"type": "text"},
        }
        # If API key isn't present, we still can attempt the call but it will
        # likely return 401; the surrounding code handles exceptions and will
        # return 0.0 in that case. We log that the key is missing to aid
        # diagnostics.
        try:
            # time.sleep(1)
            resp = requests.post(url, headers=headers, json=body, timeout=120)
            resp.raise_for_status()

            if resp.status_code != 200:
                text = getattr(resp, 'text', '<no response body>')
                raise requests.exceptions.RequestException(f"API returned status code {resp.status_code}: {text}")
            logger.info("Successful GenAI Studio API response")

            try:
                resp_json = resp.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON from Gen AI Studio response: {e}")
                resp_json = None

            try:
                if not resp_json or not isinstance(resp_json, dict):
                    raise ValueError("Empty or unexpected JSON response")

                # Typical structure: { 'choices': [ { 'message': { 'content': "0.85\n..." } } ] }
                content: str = resp_json['choices'][0]['message']['content']
                # score: float = float(content.split('\n', 1)[0].strip())
                # Require a trailing newline or explicit \n after the number (per test expectations)
                match = re.match(r'^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(?:\n|\\n)', content)
                score: float = float(match.group(1)) if match else 0.0 

                logger.info(f"Successfully received performance score: {score}")
                return clamp(score, 0.0, 1.0)
            
            except Exception as e:
                logger.error(f"Could not extract score from Gen AI Studio response: {e}; resp_json: {resp_json}")
                return 0.0
        except Exception as e:
            logger.error(f"Error calling Gen AI Studio API: {e}")
            return 0.0

    
    
    def calculate_latency(self) -> int:
        return getattr(self, '_latency', 0)
    
def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Clip a float between min and max limits
    
    Why? Performance is faster than `numpy.clip()` and more readable than `min(max())`
    """
    if value < min_value: return min_value
    if value > max_value: return max_value
    return value
