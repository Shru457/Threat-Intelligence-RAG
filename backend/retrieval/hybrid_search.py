"""
Hybrid retrieval: combines Day 3's semantic retriever and Day 4's BM25
retriever using Reciprocal Rank Fusion (RRF).

RRF was chosen over raw weighted score fusion because BM25 scores
(unbounded, corpus-dependent) and FAISS cosine-similarity scores
(bounded -1..1) live on fundamentally incompatible scales. Adding them
directly would let whichever score happens to be larger in magnitude
dominate, for reasons that have nothing to do with actual relevance.
RRF sidesteps this entirely by using each retriever's RANK (1st, 2nd,
3rd...) instead of its raw score — ranks are always on the same,
comparable scale regardless of the underlying method.
"""

from . import semantic_search, bm25_search
from .config import HYBRID_CANDIDATE_K, RRF_K_CONSTANT, DEFAULT_TOP_K


def _rrf_score(rank: int, k: int = RRF_K_CONSTANT) -> float:
    """
    Reciprocal Rank Fusion score contribution for one rank.

    Formula: 1 / (k + rank)

    - rank starts at 1 (the top result), not 0.
    - k is a smoothing constant (commonly 60 in IR literature) that
      flattens the curve so the gap between rank 1 and rank 2 doesn't
      dominate too aggressively. Without it, rank 1 (1/1=1.0) vs rank
      2 (1/2=0.5) would swing wildly on raw rank alone; with k=60,
      rank 1 (1/61=0.0164) vs rank 2 (1/62=0.0161) contribute much
      more comparable amounts — letting a chunk that ranks moderately
      well in BOTH retrievers beat a chunk that ranks #1 in only one.
    """
    return 1.0 / (k + rank)


def search(query: str, top_k: int = DEFAULT_TOP_K,
           candidate_k: int = HYBRID_CANDIDATE_K) -> list[dict]:
    """
    Run semantic + BM25 retrieval, fuse their rankings via RRF, dedupe
    by chunk_id, and return the final top_k fused results.
    """
    semantic_results = semantic_search.search(query, top_k=candidate_k)
    bm25_results = bm25_search.search(query, top_k=candidate_k)

    # chunk_id -> {"fused_score": float, "record": dict}
    fused: dict[str, dict] = {}

    for result in semantic_results:
        cid = result["chunk_id"]
        fused.setdefault(cid, {"fused_score": 0.0, "record": result})
        fused[cid]["fused_score"] += _rrf_score(result["rank"])

    for result in bm25_results:
        cid = result["chunk_id"]
        fused.setdefault(cid, {"fused_score": 0.0, "record": result})
        fused[cid]["fused_score"] += _rrf_score(result["rank"])

    ranked = sorted(fused.values(), key=lambda x: x["fused_score"], reverse=True)
    top = ranked[:top_k]

    final_results = []
    for rank, entry in enumerate(top, start=1):
        record = dict(entry["record"])  # copy, so we don't mutate the cached original
        record["rank"] = rank
        record["score"] = entry["fused_score"]
        final_results.append(record)

    return final_results