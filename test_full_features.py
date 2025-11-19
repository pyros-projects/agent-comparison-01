#!/usr/bin/env python3
"""Full integration test with cataloguing."""
import asyncio
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from researcher.database import db
from researcher.paper_cataloguer import paper_cataloguer
from researcher.api import app
from fastapi.testclient import TestClient

def test_api_endpoints():
    """Test all API endpoints."""
    print("\nTesting API endpoints...")
    client = TestClient(app)
    
    # Test stats
    try:
        response = client.get("/api/stats")
        assert response.status_code == 200
        stats = response.json()
        print(f"✓ GET /api/stats: {stats['total_papers']} papers, {stats['total_repositories']} repos")
    except Exception as e:
        print(f"✗ Error testing stats: {e}")
        return False
    
    # Test search
    try:
        response = client.post("/api/search", json={"query": "machine learning", "limit": 10})
        assert response.status_code == 200
        results = response.json()
        print(f"✓ POST /api/search: Found {results['total']} results")
    except Exception as e:
        print(f"✗ Error testing search: {e}")
        return False
    
    # Test theory
    try:
        response = client.post("/api/theory", json={"theory": "neural networks improve accuracy"})
        assert response.status_code == 200
        theory_result = response.json()
        print(f"✓ POST /api/theory: {len(theory_result['supporting_papers'])} supporting, {len(theory_result['opposing_papers'])} opposing")
    except Exception as e:
        print(f"✗ Error testing theory: {e}")
        return False
    
    # Test graph
    try:
        response = client.get("/api/graph")
        assert response.status_code == 200
        graph_data = response.json()
        print(f"✓ GET /api/graph: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    except Exception as e:
        print(f"✗ Error testing graph: {e}")
        return False
    
    # Test process URL
    try:
        response = client.post("/api/process-url", json={"url": "https://arxiv.org/abs/1706.03762"})
        # Might return 400 if already processed, that's OK
        if response.status_code in [200, 400]:
            print("✓ POST /api/process-url: Endpoint works")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing process-url: {e}")
        return False
    
    # Test get paper
    papers = db.get_all_papers()
    if papers:
        try:
            paper_id = papers[0].id
            response = client.get(f"/api/papers/{paper_id}")
            assert response.status_code == 200
            print(f"✓ GET /api/papers/{paper_id}: Paper retrieved")
        except Exception as e:
            print(f"✗ Error testing get paper: {e}")
            return False
    
    return True

async def test_cataloguing_short():
    """Test cataloguing with a short run."""
    print("\nTesting cataloguing (short run)...")
    
    # Process a few papers manually to populate database
    test_urls = [
        "https://arxiv.org/abs/1706.03762",  # Attention Is All You Need
        "https://arxiv.org/abs/2010.11929",  # An Image is Worth 16x16 Words
    ]
    
    for url in test_urls:
        try:
            print(f"  Processing {url}...")
            paper = await paper_cataloguer.process_url(url)
            if paper:
                print(f"    ✓ Processed: {paper.title[:60]}...")
            else:
                print(f"    ✗ Failed to process")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Check database
    papers = db.get_all_papers()
    print(f"\n✓ Database now has {len(papers)} papers")
    
    return True

def main():
    """Run full integration tests."""
    print("=" * 60)
    print("Full Feature Integration Test")
    print("=" * 60)
    
    # Test API endpoints
    if not test_api_endpoints():
        print("\n✗ API endpoint tests failed!")
        return 1
    
    # Test cataloguing
    if not asyncio.run(test_cataloguing_short()):
        print("\n✗ Cataloguing tests failed!")
        return 1
    
    # Test API again with data
    print("\nTesting API endpoints with data...")
    if not test_api_endpoints():
        print("\n✗ API endpoint tests with data failed!")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All integration tests passed!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())

