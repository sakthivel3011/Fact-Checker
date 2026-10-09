"""
RAG Vector Store & Semantic Retrieval Engine.
Provides high-speed semantic retrieval over verified fact-checks and news documents.
"""

import json
import math
import os
import re
from typing import List, Dict, Any, Optional
import numpy as np

from config import settings


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean lower-cased word tokens."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    # Basic stop words filtering
    stop_words = {
        "the", "and", "is", "in", "it", "to", "of", "for", "with", "on", "at", 
        "from", "by", "about", "as", "into", "like", "through", "after", "over", 
        "between", "out", "against", "during", "without", "before", "under", "around"
    }
    return [w for w in words if w not in stop_words]


class SimpleVectorStore:
    """
    Lightweight vector database implementing TF-IDF vectorization and cosine similarity.
    Compatible with LangChain Document retrieval standards without heavyweight external services.
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: Optional[np.ndarray] = None
        self.kb_path = knowledge_base_path or settings.KNOWLEDGE_BASE_PATH
        self.load_default_knowledge_base()

    def load_default_knowledge_base(self):
        """Loads default verified facts from JSON file if available."""
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    formatted_docs = []
                    for item in items:
                        formatted_docs.append({
                            "id": item.get("id"),
                            "content": f"{item.get('claim', '')}. {item.get('explanation', '')}",
                            "claim": item.get("claim", ""),
                            "verdict": item.get("verdict", "UNVERIFIED"),
                            "category": item.get("category", "General"),
                            "credibility_score": item.get("credibility_score", 50.0),
                            "sources": item.get("sources", []),
                            "source_type": "rag_knowledge_base"
                        })
                    self.add_documents(formatted_docs)
            except Exception:
                pass

    def _build_index(self):
        """Computes TF-IDF index across current document corpus."""
        if not self.documents:
            self.vocabulary = {}
            self.idf = {}
            self.doc_vectors = None
            return

        # 1. Build vocabulary & document frequency
        doc_tokens = [tokenize(doc["content"]) for doc in self.documents]
        df: Dict[str, int] = {}
        vocab_set = set()

        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            vocab_set.update(unique_tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        self.vocabulary = {token: idx for idx, token in enumerate(sorted(vocab_set))}
        n_docs = len(self.documents)
        self.idf = {token: math.log((n_docs + 1) / (df[token] + 1)) + 1.0 for token in self.vocabulary}

        # 2. Build document TF-IDF vectors
        vectors = np.zeros((n_docs, len(self.vocabulary)), dtype=np.float32)
        for doc_idx, tokens in enumerate(doc_tokens):
            if not tokens:
                continue
            tf_counts: Dict[str, int] = {}
            for t in tokens:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            
            for token, count in tf_counts.items():
                if token in self.vocabulary:
                    dim = self.vocabulary[token]
                    tf = count / len(tokens)
                    vectors[doc_idx, dim] = tf * self.idf[token]

            # Normalize to unit length
            norm = np.linalg.norm(vectors[doc_idx])
            if norm > 0:
                vectors[doc_idx] /= norm

        self.doc_vectors = vectors

    def add_documents(self, new_docs: List[Dict[str, Any]]):
        """Add new documents (e.g. fresh news articles or fact-check records)."""
        self.documents.extend(new_docs)
        self._build_index()

    def _embed_query(self, query: str) -> np.ndarray:
        """Vectorize a query string using the current vocabulary and IDF."""
        query_vec = np.zeros(len(self.vocabulary), dtype=np.float32)
        tokens = tokenize(query)
        if not tokens or len(self.vocabulary) == 0:
            return query_vec

        tf_counts: Dict[str, int] = {}
        for t in tokens:
            tf_counts[t] = tf_counts.get(t, 0) + 1

        for token, count in tf_counts.items():
            if token in self.vocabulary:
                dim = self.vocabulary[token]
                tf = count / len(tokens)
                query_vec[dim] = tf * self.idf[token]

        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec /= norm
        return query_vec

    def similarity_search(self, query: str, top_k: int = 4, threshold: float = 0.05) -> List[Dict[str, Any]]:
        """
        Search for most relevant documents matching query.
        Returns list of matched documents enriched with 'similarity_score'.
        """
        if not self.documents or self.doc_vectors is None or len(self.vocabulary) == 0:
            return []

        q_vec = self._embed_query(query)
        if np.linalg.norm(q_vec) == 0:
            return []

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.doc_vectors, q_vec)
        top_indices = np.argsort(scores)[::-1]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= threshold:
                doc_copy = dict(self.documents[idx])
                doc_copy["similarity_score"] = round(score, 3)
                results.append(doc_copy)
            if len(results) >= top_k:
                break

        return results


# Global singleton instance
vector_store = SimpleVectorStore()
