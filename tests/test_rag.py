"""Unit tests for the RAG Vector Store and Semantic Retrieval Engine."""

import pytest
from rag.vector_store import SimpleVectorStore


def test_vector_store_initialization():
    store = SimpleVectorStore()
    assert len(store.documents) > 0
    assert store.doc_vectors is not None
    assert len(store.vocabulary) > 0


def test_similarity_search_exact_match():
    store = SimpleVectorStore()
    hits = store.similarity_search("5G cell towers cause coronavirus", top_k=2)
    assert len(hits) >= 1
    top_hit = hits[0]
    assert "5G" in top_hit["claim"] or "5g" in top_hit["content"].lower()
    assert top_hit["similarity_score"] > 0.1


def test_add_documents_dynamically():
    store = SimpleVectorStore()
    initial_count = len(store.documents)
    
    new_doc = {
        "id": "TEST-01",
        "claim": "Artificial photosynthesis achieves commercial solar-to-hydrogen efficiency record.",
        "content": "Artificial photosynthesis achieves commercial solar-to-hydrogen efficiency record in laboratory trial.",
        "verdict": "TRUE",
        "category": "Energy",
        "credibility_score": 90.0,
        "sources": []
    }
    store.add_documents([new_doc])
    assert len(store.documents) == initial_count + 1

    hits = store.similarity_search("photosynthesis hydrogen efficiency", top_k=1)
    assert len(hits) == 1
    assert hits[0]["id"] == "TEST-01"
