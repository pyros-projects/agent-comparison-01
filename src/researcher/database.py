import os
import numpy as np
from typing import List, Optional, Dict, Tuple
from tinydb import TinyDB, Query
from sklearn.metrics.pairwise import cosine_similarity
from .models import ResearchItem, Relationship, ItemType

class ResearchDatabase:
    def __init__(self, db_path: str = "research_data.json"):
        self.db = TinyDB(db_path)
        self.items_table = self.db.table("items")
        self.edges_table = self.db.table("edges")
        # Cache embeddings in memory for speed
        self._embedding_cache = {}
        self._refresh_embedding_cache()

    def _refresh_embedding_cache(self):
        self._embedding_cache = {}
        for item in self.items_table.all():
            if item.get('embedding'):
                self._embedding_cache[item['id']] = np.array(item['embedding'])

    def add_item(self, item: ResearchItem):
        Item = Query()
        item_dict = item.model_dump(mode="json")
        if not self.items_table.contains(Item.id == item.id):
            self.items_table.insert(item_dict)
        else:
            self.items_table.update(item_dict, Item.id == item.id)
        
        # Update cache
        if item.embedding:
            self._embedding_cache[item.id] = np.array(item.embedding)

    def get_item(self, item_id: str) -> Optional[ResearchItem]:
        Item = Query()
        result = self.items_table.search(Item.id == item_id)
        if result:
            return ResearchItem(**result[0])
        return None

    def get_all_items(self) -> List[ResearchItem]:
        return [ResearchItem(**item) for item in self.items_table.all()]

    def get_items_by_type(self, item_type: ItemType) -> List[ResearchItem]:
        Item = Query()
        return [ResearchItem(**item) for item in self.items_table.search(Item.type == item_type.value)]

    def add_relationship(self, relationship: Relationship):
        Edge = Query()
        # Check if exists
        exists = self.edges_table.contains(
            (Edge.source_id == relationship.source_id) & 
            (Edge.target_id == relationship.target_id) & 
            (Edge.type == relationship.type)
        )
        if not exists:
            self.edges_table.insert(relationship.model_dump(mode="json"))

    def get_relationships(self) -> List[Relationship]:
        return [Relationship(**edge) for edge in self.edges_table.all()]

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_items": len(self.items_table),
            "total_papers": self.items_table.count(Query().type == "paper"),
            "total_repos": self.items_table.count(Query().type == "repository"),
            "total_relationships": len(self.edges_table)
        }

    def search_similar(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.7) -> List[Tuple[ResearchItem, float]]:
        if not query_embedding or not self._embedding_cache:
            return []

        query_vec = np.array(query_embedding).reshape(1, -1)
        results = []

        # Calculate similarity with all cached items
        # Optimization: Could use Faiss or similar for large datasets, but numpy is fine for <10k items
        
        ids = list(self._embedding_cache.keys())
        vectors = np.array([self._embedding_cache[i] for i in ids])
        
        if len(vectors) == 0:
            return []

        similarities = cosine_similarity(query_vec, vectors)[0]
        
        # Zip and sort
        scored_items = sorted(zip(ids, similarities), key=lambda x: x[1], reverse=True)
        
        # Fetch full items for top k
        top_items = []
        for item_id, score in scored_items:
            if score < threshold: break
            if len(top_items) >= top_k: break
            
            item = self.get_item(item_id)
            if item:
                top_items.append((item, float(score)))
                
        return top_items

    def search(self, query_text: str, embedding: Optional[List[float]] = None) -> List[ResearchItem]:
        # Hybrid search: Text match OR Semantic match if embedding provided
        results_map = {}
        
        # 1. Text Search
        query_text_lower = query_text.lower()
        for item in self.items_table.all():
            if (query_text_lower in item.get('title', '').lower() or 
                query_text_lower in item.get('summary', '').lower() or
                any(query_text_lower in tag.lower() for tag in item.get('tags', []))):
                results_map[item['id']] = ResearchItem(**item)

        # 2. Semantic Search
        if embedding:
            similar = self.search_similar(embedding, top_k=10, threshold=0.6)
            for item, score in similar:
                results_map[item.id] = item

        return list(results_map.values())