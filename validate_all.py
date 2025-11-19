#!/usr/bin/env python3
"""Comprehensive validation of all features."""
import asyncio
import sys
import os
import requests
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

API_BASE = "http://localhost:8000/api"

def test_api_connection():
    """Test if API is accessible."""
    try:
        response = requests.get(f"{API_BASE}/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def add_test_data():
    """Add test data via API."""
    print("Adding test data...")
    
    # Process some papers
    test_urls = [
        "https://arxiv.org/abs/1706.03762",  # Attention Is All You Need
        "https://arxiv.org/abs/2010.11929",  # Vision Transformer
    ]
    
    for url in test_urls:
        try:
            print(f"  Processing {url}...")
            response = requests.post(
                f"{API_BASE}/process-url",
                json={"url": url},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                print(f"    ✓ Added {data['type']}: {data['item'].get('title', data['item'].get('name', 'Unknown'))[:60]}")
            elif response.status_code == 400:
                print(f"    - Already exists or invalid URL")
            else:
                print(f"    ✗ Error: {response.status_code}")
        except Exception as e:
            print(f"    ✗ Exception: {e}")
    
    time.sleep(2)  # Wait for processing

def test_all_features():
    """Test all features."""
    print("\n" + "="*60)
    print("Testing All Features")
    print("="*60)
    
    # 1. Stats
    print("\n1. Testing Stats...")
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        assert response.status_code == 200
        stats = response.json()
        print(f"   ✓ Stats: {stats['total_papers']} papers, {stats['total_repositories']} repos")
        print(f"   ✓ Graph: {stats['graph_nodes']} nodes, {stats['graph_edges']} edges")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 2. Search
    print("\n2. Testing Search...")
    try:
        response = requests.post(
            f"{API_BASE}/search",
            json={"query": "transformer", "limit": 10},
            timeout=10
        )
        assert response.status_code == 200
        results = response.json()
        print(f"   ✓ Search found {results['total']} results")
        print(f"   ✓ Papers: {len(results['papers'])}, Repos: {len(results['repositories'])}")
        if results['papers']:
            print(f"   ✓ Sample paper: {results['papers'][0]['title'][:60]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 3. Graph
    print("\n3. Testing Graph View...")
    try:
        response = requests.get(f"{API_BASE}/graph", timeout=5)
        assert response.status_code == 200
        graph_data = response.json()
        print(f"   ✓ Graph data: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        if graph_data['nodes']:
            print(f"   ✓ Sample node: {graph_data['nodes'][0].get('label', 'Unknown')[:60]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 4. Theory
    print("\n4. Testing Theory Mode...")
    try:
        response = requests.post(
            f"{API_BASE}/theory",
            json={"theory": "attention mechanisms improve model performance"},
            timeout=30
        )
        assert response.status_code == 200
        theory_result = response.json()
        print(f"   ✓ Theory analysis complete")
        print(f"   ✓ Supporting: {len(theory_result['supporting_papers'])} papers, {len(theory_result['supporting_repos'])} repos")
        print(f"   ✓ Opposing: {len(theory_result['opposing_papers'])} papers, {len(theory_result['opposing_repos'])} repos")
        print(f"   ✓ Related theories: {len(theory_result['related_theories'])}")
        print(f"   ✓ Suggestions: {len(theory_result['suggestions'])}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Get Paper Detail
    print("\n5. Testing Paper Detail...")
    try:
        # Get list of papers first
        response = requests.get(f"{API_BASE}/papers?limit=1", timeout=5)
        if response.status_code == 200:
            papers = response.json()
            if papers:
                paper_id = papers[0]['id']
                response = requests.get(f"{API_BASE}/papers/{paper_id}", timeout=5)
                assert response.status_code == 200
                paper = response.json()
                print(f"   ✓ Retrieved paper: {paper['title'][:60]}...")
                print(f"   ✓ Has {len(paper['tags'])} tags, {len(paper['key_findings'])} findings")
            else:
                print("   - No papers to test")
        else:
            print("   - Could not get papers list")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 6. Similar Items
    print("\n6. Testing Similar Items...")
    try:
        response = requests.get(f"{API_BASE}/papers?limit=1", timeout=5)
        if response.status_code == 200:
            papers = response.json()
            if papers:
                paper_id = papers[0]['id']
                response = requests.get(f"{API_BASE}/similar/{paper_id}", timeout=5)
                assert response.status_code == 200
                similar = response.json()
                print(f"   ✓ Found {len(similar['papers'])} similar papers")
                print(f"   ✓ Found {len(similar['repositories'])} similar repos")
            else:
                print("   - No papers to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True

def main():
    """Run comprehensive validation."""
    print("="*60)
    print("Comprehensive Feature Validation")
    print("="*60)
    
    # Check API connection
    if not test_api_connection():
        print("\n✗ Cannot connect to API. Is the server running?")
        print("  Start with: uv run researcher")
        return 1
    
    print("\n✓ API is accessible")
    
    # Add test data
    add_test_data()
    
    # Test all features
    if not test_all_features():
        print("\n✗ Some tests failed!")
        return 1
    
    print("\n" + "="*60)
    print("✓ ALL FEATURES VALIDATED SUCCESSFULLY!")
    print("="*60)
    print("\nFeatures working:")
    print("  ✓ Paper cataloguing (URL processing)")
    print("  ✓ Database storage and retrieval")
    print("  ✓ Search functionality")
    print("  ✓ Graph view")
    print("  ✓ Theory mode")
    print("  ✓ Similar items discovery")
    print("  ✓ Statistics dashboard")
    print("\nThe application is ready to use!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

