#!/usr/bin/env python3
"""
Integration Demo: URL Processing + Data Retrieval

This demo shows the complete flow from URL processing to data retrieval,
demonstrating how the URL handler and data retrieval modules work together.
"""

import time
from typing import List, Dict, Any
from url_handler import process_url_file, handle_url, URLCategory
from data_retrieval import DataRetriever, RepositoryData


def demo_single_url_flow():
    """Demonstrate the complete flow for a single URL."""
    print("🔄 SINGLE URL PROCESSING + DATA RETRIEVAL")
    print("=" * 60)
    
    # Example URLs from different platforms
    test_urls = [
        "https://github.com/microsoft/typescript",
        "https://www.npmjs.com/package/express", 
        "https://huggingface.co/microsoft/DialoGPT-medium"
    ]
    
    retriever = DataRetriever(rate_limit_delay=0.5)  # Add delay to be respectful to APIs
    
    for url in test_urls:
        print(f"\n📍 Processing: {url}")
        print("-" * 40)
        
        # Step 1: Process URL
        print("Step 1: URL Processing...")
        url_data = handle_url(url)
        
        if not url_data.is_valid:
            print(f"❌ URL processing failed: {url_data.error_message}")
            continue
        
        print(f"✅ URL processed successfully")
        print(f"   Category: {url_data.category.value}")
        print(f"   Identifier: {url_data.unique_identifier}")
        
        # Step 2: Retrieve data
        print("Step 2: Data Retrieval...")
        repo_data = retriever.retrieve_data(url_data)
        
        if not repo_data.success:
            print(f"❌ Data retrieval failed: {repo_data.error_message}")
            continue
        
        print(f"✅ Data retrieved successfully")
        print(f"   Name: {repo_data.name}")
        print(f"   Description: {repo_data.description[:100]}..." if repo_data.description else "   Description: None")
        
        # Show platform-specific metrics
        if repo_data.platform == "github":
            print(f"   ⭐ Stars: {repo_data.stars}")
            print(f"   🔧 Language: {repo_data.language}")
            print(f"   👥 Contributors: {repo_data.contributors_count}")
        elif repo_data.platform == "npm":
            print(f"   📦 Version: {repo_data.version}")
            print(f"   📈 Downloads (last month): {repo_data.downloads_last_month}")
            print(f"   🔗 Dependencies: {len(repo_data.dependencies or [])}")
        elif repo_data.platform == "huggingface":
            print(f"   📈 Downloads: {repo_data.downloads_last_month}")
            print(f"   🏷️ Pipeline: {repo_data.language}")


def demo_batch_processing():
    """Demonstrate batch processing of URLs from a file."""
    print("\n\n📦 BATCH PROCESSING DEMO")
    print("=" * 60)
    
    # Create a sample URLs file
    sample_urls = [
        "https://github.com/facebook/react",
        "https://www.npmjs.com/package/lodash",
        "https://huggingface.co/bert-base-uncased",
        "https://github.com/nodejs/node",
        "https://www.npmjs.com/package/@types/node"
    ]
    
    sample_file = "demo_urls.txt"
    with open(sample_file, 'w') as f:
        for url in sample_urls:
            f.write(f"{url}\n")
    
    print(f"📄 Created sample file: {sample_file}")
    print(f"📊 Processing {len(sample_urls)} URLs...")
    
    # Step 1: Process all URLs
    print("\nStep 1: Batch URL Processing...")
    url_results = process_url_file(sample_file)
    
    valid_urls = [result for result in url_results if result.is_valid]
    print(f"✅ Successfully processed {len(valid_urls)}/{len(url_results)} URLs")
    
    # Step 2: Retrieve data for all valid URLs
    print("\nStep 2: Batch Data Retrieval...")
    retriever = DataRetriever(rate_limit_delay=0.3)
    repo_data_list = retriever.retrieve_batch_data(valid_urls)
    
    successful_retrievals = [data for data in repo_data_list if data.success]
    print(f"✅ Successfully retrieved data for {len(successful_retrievals)}/{len(valid_urls)} URLs")
    
    # Step 3: Generate summary report
    print("\nStep 3: Summary Report...")
    generate_summary_report(repo_data_list)
    
    # Clean up
    import os
    os.remove(sample_file)
    print(f"\n🧹 Cleaned up {sample_file}")


def generate_summary_report(repo_data_list: List[RepositoryData]):
    """Generate a comprehensive summary report."""
    print("\n📊 COMPREHENSIVE SUMMARY REPORT")
    print("=" * 50)
    
    # Platform breakdown
    platforms = {}
    successful_data = [data for data in repo_data_list if data.success]
    
    for data in successful_data:
        if data.platform not in platforms:
            platforms[data.platform] = []
        platforms[data.platform].append(data)
    
    print(f"📈 Successfully retrieved data for {len(successful_data)} repositories")
    print(f"📋 Platform breakdown:")
    for platform, repos in platforms.items():
        print(f"   • {platform.title()}: {len(repos)} repositories")
    
    # Platform-specific insights
    for platform, repos in platforms.items():
        print(f"\n🔍 {platform.title()} Insights:")
        
        if platform == "github":
            total_stars = sum(repo.stars or 0 for repo in repos)
            avg_stars = total_stars / len(repos) if repos else 0
            most_starred = max(repos, key=lambda x: x.stars or 0)
            
            print(f"   ⭐ Total stars: {total_stars:,}")
            print(f"   📊 Average stars: {avg_stars:.1f}")
            print(f"   🏆 Most starred: {most_starred.name} ({most_starred.stars:,} stars)")
            
        elif platform == "npm":
            total_downloads = sum(repo.downloads_last_month or 0 for repo in repos)
            most_downloaded = max(repos, key=lambda x: x.downloads_last_month or 0)
            
            print(f"   📈 Total downloads (last month): {total_downloads:,}")
            print(f"   🏆 Most downloaded: {most_downloaded.name} ({most_downloaded.downloads_last_month:,} downloads)")
            
        elif platform == "huggingface":
            total_downloads = sum(repo.downloads_last_month or 0 for repo in repos)
            print(f"   📈 Total downloads: {total_downloads:,}")
    
    # Error summary
    failed_data = [data for data in repo_data_list if not data.success]
    if failed_data:
        print(f"\n⚠️  Failed retrievals: {len(failed_data)}")
        for data in failed_data:
            print(f"   • {data.identifier}: {data.error_message}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n\n🛡️ ERROR HANDLING DEMO")
    print("=" * 60)
    
    # Test various error scenarios
    error_test_cases = [
        ("https://github.com/nonexistent/repository", "Non-existent GitHub repository"),
        ("https://www.npmjs.com/package/definitely-does-not-exist-package", "Non-existent NPM package"),
        ("https://huggingface.co/nonexistent/model", "Non-existent Hugging Face model"),
        ("invalid-url-format", "Invalid URL format"),
    ]
    
    retriever = DataRetriever(rate_limit_delay=0.2)
    
    for url, description in error_test_cases:
        print(f"\n🧪 Testing: {description}")
        print(f"📍 URL: {url}")
        
        # Process URL
        url_data = handle_url(url)
        
        if not url_data.is_valid:
            print(f"❌ URL processing failed: {url_data.error_message}")
            continue
        
        # Try to retrieve data
        repo_data = retriever.retrieve_data(url_data)
        
        if repo_data.success:
            print(f"✅ Unexpectedly successful: {repo_data.name}")
        else:
            print(f"❌ Expected failure: {repo_data.error_message}")


def demo_performance_metrics():
    """Demonstrate performance measurement."""
    print("\n\n⚡ PERFORMANCE METRICS DEMO")
    print("=" * 60)
    
    # Test URLs for performance measurement
    test_urls = [
        "https://github.com/microsoft/vscode",
        "https://www.npmjs.com/package/react",
        "https://huggingface.co/gpt2"
    ]
    
    retriever = DataRetriever(rate_limit_delay=0.1)
    
    total_start_time = time.time()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n⏱️  Processing {i}/{len(test_urls)}: {url.split('/')[-1]}")
        
        # Measure URL processing time
        url_start = time.time()
        url_data = handle_url(url)
        url_time = time.time() - url_start
        
        if url_data.is_valid:
            # Measure data retrieval time
            retrieval_start = time.time()
            repo_data = retriever.retrieve_data(url_data)
            retrieval_time = time.time() - retrieval_start
            
            print(f"   📊 URL processing: {url_time:.3f}s")
            print(f"   🌐 Data retrieval: {retrieval_time:.3f}s")
            print(f"   ✅ Total: {url_time + retrieval_time:.3f}s")
            print(f"   📈 Status: {'Success' if repo_data.success else 'Failed'}")
        else:
            print(f"   ❌ URL processing failed: {url_time:.3f}s")
    
    total_time = time.time() - total_start_time
    print(f"\n🏁 Total processing time: {total_time:.3f}s")
    print(f"📊 Average time per URL: {total_time/len(test_urls):.3f}s")


def main():
    """Run the complete integration demonstration."""
    print("🚀 URL PROCESSING + DATA RETRIEVAL INTEGRATION DEMO")
    print("=" * 70)
    print("This demo shows the complete flow from URL processing to data retrieval")
    print("across GitHub, NPM, and Hugging Face platforms.")
    print("=" * 70)
    
    try:
        demo_single_url_flow()
        demo_batch_processing()
        demo_error_handling()
        demo_performance_metrics()
        
        print("\n\n🎉 INTEGRATION DEMO COMPLETED SUCCESSFULLY!")
        print("\n📚 Key Integration Points:")
        print("   1. URL Handler processes and validates URLs")
        print("   2. Data Retriever uses URL identifiers for API calls")
        print("   3. Error handling works across both modules")
        print("   4. Batch processing combines both efficiently")
        print("   5. Performance monitoring tracks end-to-end timing")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {str(e)}")


if __name__ == "__main__":
    main()
