#!/usr/bin/env python3
"""Test script to validate all features work correctly."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from researcher.database import db
from researcher.paper_cataloguer import paper_cataloguer
from researcher.repo_cataloguer import repo_cataloguer
from researcher.models import Paper, Repository
from datetime import datetime

def test_database():
    """Test database operations."""
    print("Testing database operations...")
    
    # Create a test paper
    test_paper = Paper(
        id="test_paper_1",
        title="Test Paper: Machine Learning Advances",
        authors=["John Doe", "Jane Smith"],
        abstract="This is a test paper about machine learning.",
        url="https://arxiv.org/abs/test123",
        summary="A test paper",
        tags=["machine-learning", "ai", "test"],
        questions_answered=["What is ML?"],
        key_findings=["ML is useful"],
        relevancy_score=8.5,
        interesting_score=7.0
    )
    
    # Add paper
    try:
        db.add_paper(test_paper)
        print("✓ Paper added successfully")
    except Exception as e:
        print(f"✗ Error adding paper: {e}")
        return False
    
    # Retrieve paper
    try:
        retrieved = db.get_paper("test_paper_1")
        if retrieved and retrieved.title == test_paper.title:
            print("✓ Paper retrieved successfully")
        else:
            print("✗ Paper retrieval failed")
            return False
    except Exception as e:
        print(f"✗ Error retrieving paper: {e}")
        return False
    
    # Search papers
    try:
        results = db.search_papers("machine learning")
        if len(results) > 0:
            print(f"✓ Search found {len(results)} papers")
        else:
            print("✗ Search returned no results")
            return False
    except Exception as e:
        print(f"✗ Error searching papers: {e}")
        return False
    
    # Create a test repository
    test_repo = Repository(
        id="test_repo_1",
        name="test-ml-library",
        owner="testuser",
        description="A test machine learning library",
        url="https://github.com/testuser/test-ml-library",
        summary="A test repository",
        tags=["machine-learning", "python", "test"],
        questions_answered=["How to use ML?"],
        key_findings=["Easy to use"],
        relevancy_score=7.5,
        interesting_score=6.5
    )
    
    # Add repository
    try:
        db.add_repository(test_repo)
        print("✓ Repository added successfully")
    except Exception as e:
        print(f"✗ Error adding repository: {e}")
        return False
    
    # Find similar
    try:
        similar = db.find_similar("test_paper_1")
        print(f"✓ Found {len(similar['papers'])} similar papers, {len(similar['repositories'])} similar repos")
    except Exception as e:
        print(f"✗ Error finding similar items: {e}")
        return False
    
    # Get stats
    try:
        stats = db.get_stats()
        print(f"✓ Stats: {stats['total_papers']} papers, {stats['total_repositories']} repos")
    except Exception as e:
        print(f"✗ Error getting stats: {e}")
        return False
    
    # Get graph data
    try:
        graph_data = db.get_graph_data()
        print(f"✓ Graph data: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    except Exception as e:
        print(f"✗ Error getting graph data: {e}")
        return False
    
    return True

async def test_cataloguing():
    """Test cataloguing features."""
    print("\nTesting cataloguing features...")
    
    # Test processing a real arXiv URL
    try:
        print("Testing paper URL processing...")
        paper = await paper_cataloguer.process_url("https://arxiv.org/abs/1706.03762")
        if paper:
            print(f"✓ Successfully processed paper: {paper.title[:50]}...")
        else:
            print("✗ Failed to process paper URL")
            return False
    except Exception as e:
        print(f"✗ Error processing paper URL: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Research Catalog Features")
    print("=" * 60)
    
    # Test database
    if not test_database():
        print("\n✗ Database tests failed!")
        return 1
    
    # Test cataloguing
    if not asyncio.run(test_cataloguing()):
        print("\n✗ Cataloguing tests failed!")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())

