"""
Unified retrieval interface.

Day 5's RAG generation (and Day 4's own evaluation script) should be
able to ask "give me the top relevant evidence for this question"
without caring which retrieval strategy produced it. get_retriever()
is the single point where a method name is turned into a callable.
"""

from . import semantic_search, bm25_search, hybrid_search, reranker
from .config import DEFAULT_TOP_K, RERANK_CANDIDATE_K, RERANK_FINAL_K, HYBRID_CANDIDATE_K

VALID_METHODS = ("semantic", "bm25", "hybrid", "hybrid_rerank")


def retrieve(query: str, method: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Run retrieval using the named method.

    method must be one of: "semantic", "bm25", "hybrid", "hybrid_rerank".
    """
    if method not in VALID_METHODS:
        raise ValueError(
            f"Unknown retrieval method '{method}'. "
            f"Valid options are: {', '.join(VALID_METHODS)}"
        )

    if method == "semantic":
        return semantic_search.search(query, top_k=top_k)

    if method == "bm25":
        return bm25_search.search(query, top_k=top_k)

    if method == "hybrid":
        return hybrid_search.search(query, top_k=top_k, candidate_k=HYBRID_CANDIDATE_K)

    # method == "hybrid_rerank"
    candidates = hybrid_search.search(
        query, top_k=RERANK_CANDIDATE_K, candidate_k=RERANK_CANDIDATE_K
    )
    return reranker.rerank(query, candidates, final_k=RERANK_FINAL_K)


def get_retriever(method: str):
    """
    Return a retriever callable for the given method, e.g.:

        retriever = get_retriever("hybrid_rerank")
        results = retriever("How did the malware maintain persistence?", top_k=5)
    """
    if method not in VALID_METHODS:
        raise ValueError(
            f"Unknown retrieval method '{method}'. "
            f"Valid options are: {', '.join(VALID_METHODS)}"
        )

    def _retriever(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        return retrieve(query, method=method, top_k=top_k)

    return _retriever