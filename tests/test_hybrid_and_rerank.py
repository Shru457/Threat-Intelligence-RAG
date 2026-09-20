import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import FAISS_INDEX_FILE, BM25_INDEX_FILE
from backend.retrieval.hybrid_search import _rrf_score, search as hybrid_search_fn
from backend.retrieval.reranker import rerank

_vectorstore_ready = FAISS_INDEX_FILE.exists() and BM25_INDEX_FILE.exists()


def test_rrf_score_favors_lower_rank():
    assert _rrf_score(1) > _rrf_score(5)


def test_rrf_fusion_on_controlled_example():
    """A tiny hand-built fusion check, independent of the real corpus."""
    from backend.retrieval import hybrid_search

    fake_semantic = [
        {"rank": 1, "chunk_id": "a", "score": 0.9, "document_id": "d", "document_title": "D",
         "source": "local_pdf", "page_number": 1, "chunk_index": 0, "text": "..."},
    ]
    fake_bm25 = [
        {"rank": 1, "chunk_id": "b", "score": 5.0, "document_id": "d", "document_title": "D",
         "source": "local_pdf", "page_number": 2, "chunk_index": 1, "text": "..."},
        {"rank": 2, "chunk_id": "a", "score": 3.0, "document_id": "d", "document_title": "D",
         "source": "local_pdf", "page_number": 1, "chunk_index": 0, "text": "..."},
    ]

    hybrid_search.semantic_search.search = lambda query, top_k=20: fake_semantic
    hybrid_search.bm25_search.search = lambda query, top_k=20: fake_bm25

    results = hybrid_search.search("fake query", top_k=2, candidate_k=20)

    # chunk "a" appears in BOTH lists (rank 1 semantic + rank 2 bm25),
    # so it should be fused higher than chunk "b" (rank 1 in bm25 only).
    assert results[0]["chunk_id"] == "a"
    ids = [r["chunk_id"] for r in results]
    assert len(ids) == len(set(ids))  # no duplicates


@pytest.mark.skipif(not _vectorstore_ready, reason="vectorstore/BM25 index not built yet")
def test_hybrid_search_against_real_index_has_no_duplicates():
    results = hybrid_search_fn("malware persistence", top_k=5)
    ids = [r["chunk_id"] for r in results]
    assert len(ids) == len(set(ids))


def test_reranker_handles_empty_candidates():
    assert rerank("some query", [], final_k=5) == []


@pytest.mark.skipif(not _vectorstore_ready, reason="vectorstore/BM25 index not built yet")
def test_reranker_sorts_by_score_descending():
    candidates = hybrid_search_fn("credential theft", top_k=10)
    if not candidates:
        pytest.skip("No candidates available to rerank.")
    reranked = rerank("credential theft", candidates, final_k=len(candidates))
    scores = [r["score"] for r in reranked]
    assert scores == sorted(scores, reverse=True)