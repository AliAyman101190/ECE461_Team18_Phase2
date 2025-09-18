#!/usr/bin/env python3
"""
Quick Example: URL Processing + Data Retrieval

A simple example showing how to use both modules together.
"""

from url_handler import handle_url
from data_retrieval import retrieve_data_for_url


def main():
    """Quick example of the complete flow."""
    
    # Example URL
    url = "https://github.com/microsoft/typescript"
    
    print(f"🔄 Processing: {url}")
    
    # Step 1: Process the URL
    print("\n1️⃣ URL Processing...")
    url_data = handle_url(url)
    
    if not url_data.is_valid:
        print(f"❌ Error: {url_data.error_message}")
        return
    
    print(f"✅ Success!")
    print(f"   Category: {url_data.category.value}")
    print(f"   Owner: {url_data.owner}")
    print(f"   Repository: {url_data.repository}")
    print(f"   Identifier: {url_data.unique_identifier}")
    
    # Step 2: Retrieve data
    print("\n2️⃣ Data Retrieval...")
    repo_data = retrieve_data_for_url(url_data)
    
    if not repo_data.success:
        print(f"❌ Error: {repo_data.error_message}")
        return
    
    print(f"✅ Success!")
    print(f"   Name: {repo_data.name}")
    print(f"   Description: {repo_data.description}")
    print(f"   Stars: ⭐ {repo_data.stars:,}")
    print(f"   Language: {repo_data.language}")
    print(f"   License: {repo_data.license}")
    print(f"   Contributors: 👥 {repo_data.contributors_count}")
    print(f"   Created: {repo_data.created_at.strftime('%Y-%m-%d') if repo_data.created_at else 'Unknown'}")
    
    print("\n✅ Complete! You now have both URL metadata and repository data.")


if __name__ == "__main__":
    main()
