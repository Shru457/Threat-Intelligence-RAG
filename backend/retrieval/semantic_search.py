"""
Semantic search over the FAISS vector index.

This is the SemanticRetriever baseline referenced in the project's
roadmap. Its search() function is the integration point Day 4's
BM25Retriever/HybridRetriever and Day 5's RAG generation will call.
"""

import numpy as np

from .config import DEFAULT_TOP_K
from .embeddings import embed_single_text
from .vector_store import load_index, normalize_vectors

_index_cache = None
_metadata_cache = None


def _get_index_and_metadata():
    """Load the FAISS index and metadata once per process, then reuse them."""
    global _index_cache, _metadata_cache
    if _index_cache is None or _metadata_cache is None:
        _index_cache, _metadata_cache = load_index()
    return _index_cache, _metadata_cache


def search(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Embed a natural-language query and return the top_k most semantically
    similar chunks, ranked by descending similarity score.

    Each result dict contains: rank, score, chunk_id, document_id,
    document_title, source, page_number, chunk_index, text.
    """
    index, metadata = _get_index_and_metadata()

    if index.ntotal == 0:
        return []

    query_vector = embed_single_text(query).reshape(1, -1)
    query_vector = normalize_vectors(query_vector)

    k = min(top_k, index.ntotal)  # never ask FAISS for more than exists
    scores, ids = index.search(query_vector, k)

    results = []
    for rank, (vector_id, score) in enumerate(zip(ids[0], scores[0]), start=1):
        if vector_id == -1:
            continue  # FAISS pads with -1 if fewer than k matches exist
        chunk = metadata[vector_id]
        results.append({
            "rank": rank,
            "score": float(score),
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "source": chunk["source"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
        })

    return results