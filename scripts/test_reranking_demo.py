"""
One-off demo: show hybrid retrieval results before and after reranking,
for a single query.

Usage:
    python scripts/test_reranking_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.hybrid_search import search
from backend.retrieval.reranker import rerank


def main():
    query = "How did the malware maintain persistence?"
    candidates = search(query, top_k=20, candidate_k=20)

    print("BEFORE RERANKING (hybrid order):")
    for r in candidates[:10]:
        print(f"  rank={r['rank']}  chunk_id={r['chunk_id']}  score={round(r['score'], 4)}")

    reranked = rerank(query, candidates, final_k=5)
    print()
    print("AFTER RERANKING (final order):")
    for r in reranked:
        print(f"  rank={r['rank']}  chunk_id={r['chunk_id']}  score={round(r['score'], 4)}")


if __name__ == "__main__":
    main()