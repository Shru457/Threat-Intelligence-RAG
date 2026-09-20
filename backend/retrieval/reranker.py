"""
Cross-encoder reranking stage.

A cross-encoder scores a (query, passage) pair JOINTLY through one
transformer forward pass, rather than comparing two independently
computed embeddings (Day 3's bi-encoder/FAISS approach). This is
typically more accurate because the model can directly attend between
the query and the passage's words — but it is much more expensive per
comparison, since a fresh forward pass is needed for EVERY (query,
passage) pair, with no reusable precomputed passage vectors. This is
exactly why we only rerank a small candidate set (RERANK_CANDIDATE_K,
e.g. 20) returned by a cheaper first-stage retriever, rather than
running it over the entire corpus.

MODEL DOMAIN NOTE: cross-encoder/ms-marco-MiniLM-L-6-v2 was trained on
MS MARCO, a general-domain web-search passage ranking dataset. It is
NOT trained specifically on cybersecurity or threat-intelligence text.
This project evaluates it as a general-purpose relevance model applied
to a cybersecurity domain — this distinction should be stated
explicitly in any research write-up, not glossed over.

MODEL SIZE / FEASIBILITY: ~80MB, comparable to Day 3's embedding
model. Reranking ~20 candidates for one query takes well under a
second on a normal CPU — the cost is per-candidate, not per-corpus,
which is exactly what keeps this practical on a student laptop.
"""

from sentence_transformers import CrossEncoder

from .config import RERANKER_MODEL_NAME, RERANK_FINAL_K

_reranker_cache: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    """Load the cross-encoder model once and reuse it (mirrors embeddings.py)."""
    global _reranker_cache
    if _reranker_cache is None:
        print(f"Loading reranker model: {RERANKER_MODEL_NAME}")
        print("(First run downloads the model from the internet — this is normal.)")
        try:
            _reranker_cache = CrossEncoder(RERANKER_MODEL_NAME)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load reranker model '{RERANKER_MODEL_NAME}'. "
                f"Check your internet connection (first run needs it) and "
                f"that 'sentence-transformers' is installed correctly. "
                f"Original error: {exc}"
            ) from exc
    return _reranker_cache


def rerank(query: str, candidates: list[dict],
           final_k: int = RERANK_FINAL_K) -> list[dict]:
    """
    Rerank a candidate list using the cross-encoder, returning the top
    final_k, re-ranked and re-scored.

    Each candidate dict must contain at least "text"; all other fields
    are preserved and passed through unchanged.
    """
    if not candidates:
        return []

    model = get_reranker()
    pairs = [(query, candidate["text"]) for candidate in candidates]
    scores = model.predict(pairs)

    scored_candidates = list(zip(candidates, scores))
    scored_candidates.sort(key=lambda pair: pair[1], reverse=True)

    top = scored_candidates[:final_k]

    final_results = []
    for rank, (candidate, score) in enumerate(top, start=1):
        record = dict(candidate)
        record["rank"] = rank
        record["score"] = float(score)
        final_results.append(record)

    return final_results