import requests
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json

from url_handler import URLData, URLCategory


@dataclass
class RepositoryData:
    platform: str
    identifier: str
    name: str
    description: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    watchers: Optional[int] = None
    issues_count: Optional[int] = None
    contributors_count: Optional[int] = None
    language: Optional[str] = None
    license: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    downloads_last_month: Optional[int] = None
    dependencies: Optional[List[str]] = None
    dev_dependencies: Optional[List[str]] = None
    version: Optional[str] = None
    homepage: Optional[str] = None
    repository_url: Optional[str] = None
    error_message: Optional[str] = None
    success: bool = True


class GitHubAPIClient:
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ECE461-Package-Analyzer"
        })
    
    def get_repository_data(self, owner: str, repo: str) -> RepositoryData:
        try:
            # Get basic repository information
            repo_url = f"{self.base_url}/repos/{owner}/{repo}"
            response = self.session.get(repo_url)
            
            if response.status_code == 404:
                return RepositoryData(
                    platform="github",
                    identifier=f"{owner}/{repo}",
                    name=repo,
                    success=False,
                    error_message="Repository not found"
                )
            elif response.status_code == 403:
                return RepositoryData(
                    platform="github",
                    identifier=f"{owner}/{repo}",
                    name=repo,
                    success=False,
                    error_message="Rate limit exceeded"
                )
            
            response.raise_for_status()
            repo_data = response.json()
            
            # Get contributors count (separate API call)
            contributors_count = self._get_contributors_count(owner, repo)
            
            # Parse dates
            created_at = None
            updated_at = None
            if repo_data.get('created_at'):
                created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
            if repo_data.get('updated_at'):
                updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
            
            return RepositoryData(
                platform="github",
                identifier=f"{owner}/{repo}",
                name=repo_data.get('name', repo),
                description=repo_data.get('description'),
                stars=repo_data.get('stargazers_count', 0),
                forks=repo_data.get('forks_count', 0),
                watchers=repo_data.get('watchers_count', 0),
                issues_count=repo_data.get('open_issues_count', 0),
                contributors_count=contributors_count,
                language=repo_data.get('language'),
                license=repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                created_at=created_at,
                updated_at=updated_at,
                homepage=repo_data.get('homepage'),
                repository_url=repo_data.get('html_url'),
                success=True
            )
            
        except requests.exceptions.RequestException as e:
            return RepositoryData(
                platform="github",
                identifier=f"{owner}/{repo}",
                name=repo,
                success=False,
                error_message=f"API request failed: {str(e)}"
            )
        except Exception as e:
            return RepositoryData(
                platform="github",
                identifier=f"{owner}/{repo}",
                name=repo,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _get_contributors_count(self, owner: str, repo: str) -> Optional[int]:
        try:
            contributors_url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
            response = self.session.get(contributors_url, params={"per_page": 1})
            
            if response.status_code == 200:
                # Check if there's a Link header for pagination
                link_header = response.headers.get('Link', '')
                if 'rel="last"' in link_header:
                    # Extract page count from last page link
                    import re
                    last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if last_page_match:
                        return int(last_page_match.group(1))
                
                # If no pagination, count current page
                contributors = response.json()
                return len(contributors) if contributors else 0
            
            return None
        except:
            return None


class NPMAPIClient:
    def __init__(self):
        """Initialize NPM API client."""
        self.base_url = "https://registry.npmjs.org"
        self.downloads_url = "https://api.npmjs.org/downloads"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ECE461-Package-Analyzer"
        })
    
    def get_package_data(self, package_name: str) -> RepositoryData:
        try:
            # Get package information
            package_url = f"{self.base_url}/{package_name}"
            response = self.session.get(package_url)
            
            if response.status_code == 404:
                return RepositoryData(
                    platform="npm",
                    identifier=package_name,
                    name=package_name,
                    success=False,
                    error_message="Package not found"
                )
            
            response.raise_for_status()
            package_data = response.json()
            
            # Get download statistics
            downloads_last_month = self._get_download_count(package_name)
            
            # Extract latest version data
            latest_version = package_data.get('dist-tags', {}).get('latest', '')
            version_data = package_data.get('versions', {}).get(latest_version, {})
            
            # Parse dependencies
            dependencies = list(version_data.get('dependencies', {}).keys())
            dev_dependencies = list(version_data.get('devDependencies', {}).keys())
            
            # Parse dates
            created_at = None
            updated_at = None
            time_data = package_data.get('time', {})
            if time_data.get('created'):
                created_at = datetime.fromisoformat(time_data['created'].replace('Z', '+00:00'))
            if time_data.get('modified'):
                updated_at = datetime.fromisoformat(time_data['modified'].replace('Z', '+00:00'))
            
            # Extract repository URL if available
            repository_info = version_data.get('repository', {})
            repository_url = None
            if isinstance(repository_info, dict):
                repository_url = repository_info.get('url', '').replace('git+', '').replace('.git', '')
            
            return RepositoryData(
                platform="npm",
                identifier=package_name,
                name=package_data.get('name', package_name),
                description=version_data.get('description', package_data.get('description')),
                version=latest_version,
                downloads_last_month=downloads_last_month,
                dependencies=dependencies,
                dev_dependencies=dev_dependencies,
                created_at=created_at,
                updated_at=updated_at,
                homepage=version_data.get('homepage'),
                repository_url=repository_url,
                license=version_data.get('license'),
                success=True
            )
            
        except requests.exceptions.RequestException as e:
            return RepositoryData(
                platform="npm",
                identifier=package_name,
                name=package_name,
                success=False,
                error_message=f"API request failed: {str(e)}"
            )
        except Exception as e:
            return RepositoryData(
                platform="npm",
                identifier=package_name,
                name=package_name,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _get_download_count(self, package_name: str) -> Optional[int]:
        try:
            downloads_url = f"{self.downloads_url}/point/last-month/{package_name}"
            response = self.session.get(downloads_url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('downloads', 0)
            
            return None
        except:
            return None


class HuggingFaceAPIClient:
    def __init__(self):
        self.base_url = "https://huggingface.co/api"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ECE461-Package-Analyzer"
        })
    
    def get_model_data(self, identifier: str) -> RepositoryData:
        try:
            # Try to get model information first
            model_url = f"{self.base_url}/models/{identifier}"
            response = self.session.get(model_url)
            
            if response.status_code == 404:
                # Try as dataset
                dataset_url = f"{self.base_url}/datasets/{identifier}"
                response = self.session.get(dataset_url)
                
                if response.status_code == 404:
                    return RepositoryData(
                        platform="huggingface",
                        identifier=identifier,
                        name=identifier.split('/')[-1],
                        success=False,
                        error_message="Model/dataset not found"
                    )
            
            response.raise_for_status()
            model_data = response.json()
            
            # Parse dates
            created_at = None
            updated_at = None
            if model_data.get('createdAt'):
                created_at = datetime.fromisoformat(model_data['createdAt'].replace('Z', '+00:00'))
            if model_data.get('lastModified'):
                updated_at = datetime.fromisoformat(model_data['lastModified'].replace('Z', '+00:00'))
            
            return RepositoryData(
                platform="huggingface",
                identifier=identifier,
                name=model_data.get('id', identifier).split('/')[-1],
                description=model_data.get('description'),
                downloads_last_month=model_data.get('downloads', 0),
                created_at=created_at,
                updated_at=updated_at,
                language=model_data.get('pipeline_tag'),  # Using pipeline_tag as language equivalent
                license=model_data.get('license'),
                repository_url=f"https://huggingface.co/{identifier}",
                success=True
            )
            
        except requests.exceptions.RequestException as e:
            return RepositoryData(
                platform="huggingface",
                identifier=identifier,
                name=identifier.split('/')[-1],
                success=False,
                error_message=f"API request failed: {str(e)}"
            )
        except Exception as e:
            return RepositoryData(
                platform="huggingface",
                identifier=identifier,
                name=identifier.split('/')[-1],
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )


class DataRetriever:
    def __init__(self, github_token: Optional[str] = None, rate_limit_delay: float = 0.1):
        self.github_client = GitHubAPIClient(github_token)
        self.npm_client = NPMAPIClient()
        self.huggingface_client = HuggingFaceAPIClient()
        self.rate_limit_delay = rate_limit_delay
    
    def retrieve_data(self, url_data: URLData) -> RepositoryData:
        if not url_data.is_valid or not url_data.unique_identifier:
            return RepositoryData(
                platform=url_data.category.value,
                identifier=url_data.unique_identifier or "unknown",
                name="unknown",
                success=False,
                error_message="Invalid URL data provided"
            )
        
        # Add rate limiting delay
        time.sleep(self.rate_limit_delay)
        
        if url_data.category == URLCategory.GITHUB:
            owner = url_data.owner
            repo = url_data.repository
            if owner is None or repo is None:
                return RepositoryData(
                    platform="github",
                    identifier=url_data.unique_identifier or "unknown",
                    name=repo or "unknown",
                    success=False,
                    error_message="Missing owner or repository for GitHub URL"
                )
            return self.github_client.get_repository_data(owner, repo)
        elif url_data.category == URLCategory.NPM:
            package_name = url_data.package_name
            if package_name is None:
                return RepositoryData(
                    platform="npm",
                    identifier=url_data.unique_identifier or "unknown",
                    name="unknown",
                    success=False,
                    error_message="Missing package name for NPM URL"
                )
            return self.npm_client.get_package_data(package_name)
        elif url_data.category == URLCategory.HUGGINGFACE:
            identifier = url_data.unique_identifier
            if identifier is None:
                return RepositoryData(
                    platform="huggingface",
                    identifier="unknown",
                    name="unknown",
                    success=False,
                    error_message="Missing identifier for Hugging Face URL"
                )
            return self.huggingface_client.get_model_data(identifier)
        else:
            identifier = url_data.unique_identifier or "unknown"
            name = identifier.split('/')[-1] if '/' in identifier else identifier
            return RepositoryData(
                platform=url_data.category.value,
                identifier=identifier,
                name=name,
                success=False,
                error_message=f"Unsupported platform: {url_data.category.value}"
            )
    
    def retrieve_batch_data(self, url_data_list: List[URLData]) -> List[RepositoryData]:
        results = []
        
        for i, url_data in enumerate(url_data_list):
            print(f"Retrieving data {i+1}/{len(url_data_list)}: {url_data.unique_identifier}")
            result = self.retrieve_data(url_data)
            results.append(result)
        
        return results


# Convenience functions
def retrieve_data_for_urls(url_data_list: List[URLData], github_token: Optional[str] = None) -> List[RepositoryData]:
    retriever = DataRetriever(github_token=github_token)
    return retriever.retrieve_batch_data(url_data_list)


def retrieve_data_for_url(url_data: URLData, github_token: Optional[str] = None) -> RepositoryData:
    retriever = DataRetriever(github_token=github_token)
    return retriever.retrieve_data(url_data)


if __name__ == "__main__":
    # Example usage
    from url_handler import handle_url
    
    # Test with a GitHub repository
    github_url = "https://github.com/microsoft/typescript"
    url_data = handle_url(github_url)
    
    if url_data.is_valid:
        print(f"Processing URL: {github_url}")
        print(f"Extracted identifier: {url_data.unique_identifier}")
        
        repo_data = retrieve_data_for_url(url_data)
        
        if repo_data.success:
            print(f"Repository: {repo_data.name}")
            print(f"Description: {repo_data.description}")
            print(f"Stars: {repo_data.stars}")
            print(f"Language: {repo_data.language}")
        else:
            print(f"Error: {repo_data.error_message}")
