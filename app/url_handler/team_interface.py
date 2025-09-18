#!/usr/bin/env python3
"""
Team Interface Example

This file demonstrates how other team members (like metrics module) 
can import and use the URL handler functionality.
"""

from url_handler import (
    process_url_file, 
    get_processing_summary,
    get_valid_urls,
    get_urls_by_category,
    URLCategory,
    handle_url
)


def example_metrics_integration():
    """Example of how a metrics module might use the URL handler."""
    
    # Example: Process URLs from a file
    url_file = "sample_urls.txt"
    
    try:
        # Get all processed results
        results = process_url_file(url_file)
        
        # Get summary statistics
        summary = get_processing_summary(results)
        
        print("=== METRICS MODULE EXAMPLE ===")
        print(f"Total URLs processed: {summary['total_urls']}")
        print(f"Valid URLs: {summary['valid_count']}")
        print(f"Success rate: {summary['valid_count']/summary['total_urls']*100:.1f}%")
        
        # Get valid URLs only
        valid_urls = get_valid_urls(results)
        print(f"\nValid URLs found: {len(valid_urls)}")
        
        # Get URLs by category for specific processing
        github_repos = get_urls_by_category(results, URLCategory.GITHUB)
        npm_packages = get_urls_by_category(results, URLCategory.NPM)
        huggingface_models = get_urls_by_category(results, URLCategory.HUGGINGFACE)
        
        print(f"\nBreakdown by category:")
        print(f"  GitHub repositories: {len(github_repos)}")
        print(f"  NPM packages: {len(npm_packages)}")
        print(f"  Hugging Face models: {len(huggingface_models)}")
        
        # Example: Process each category differently
        print(f"\n=== GitHub Repositories ===")
        for repo in github_repos:
            print(f"  {repo.owner}/{repo.repository}")
            # Here metrics module could analyze GitHub-specific metrics
        
        print(f"\n=== NPM Packages ===")
        for package in npm_packages:
            print(f"  {package.package_name}")
            # Here metrics module could analyze NPM-specific metrics
        
        print(f"\n=== Hugging Face Models ===")
        for model in huggingface_models:
            if model.owner:
                print(f"  {model.owner}/{model.repository}")
            else:
                print(f"  {model.repository}")
            # Here metrics module could analyze Hugging Face-specific metrics
        
        # Return structured data for further processing
        return {
            'all_results': results,
            'summary': summary,
            'github_repos': github_repos,
            'npm_packages': npm_packages,
            'huggingface_models': huggingface_models
        }
        
    except (FileNotFoundError, IOError) as e:
        print(f"Error processing URL file: {e}")
        return None


def example_single_url_processing():
    """Example of processing individual URLs."""
    
    print("\n=== SINGLE URL PROCESSING ===")
    
    test_url = "https://github.com/torvalds/linux"
    result = handle_url(test_url)
    
    if result.is_valid:
        print(f"✓ Successfully processed: {test_url}")
        print(f"  Category: {result.category.value}")
        print(f"  Unique ID: {result.unique_identifier}")
        if result.owner and result.repository:
            print(f"  Owner: {result.owner}, Repository: {result.repository}")
    else:
        print(f"✗ Failed to process: {test_url}")
        print(f"  Error: {result.error_message}")
    
    return result


if __name__ == "__main__":
    # This shows how other modules would import and use your URL handler
    
    # Example 1: File processing (what metrics module might do)
    metrics_data = example_metrics_integration()
    
    # Example 2: Single URL processing
    single_result = example_single_url_processing()
    
    print("\n" + "="*50)
    print("TEAM INTEGRATION NOTES:")
    print("="*50)
    print("Other team members can import your functions like this:")
    print()
    print("from app.url_handler.url_handler import process_url_file, get_processing_summary")
    print()
    print("# Process all URLs from a file")
    print("results = process_url_file('urls.txt')")
    print("summary = get_processing_summary(results)")
    print()
    print("# Access the structured data")
    print("valid_urls = summary['valid_urls']")
    print("github_urls = summary['github_urls']")
    print("npm_urls = summary['npm_urls']")
    print("huggingface_urls = summary['huggingface_urls']")
