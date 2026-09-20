"""
Entry point: run the evaluation query set against every retrieval
method and compute Recall@k / Precision@k / MRR / nDCG@k for each.

Usage:
    python scripts/evaluate_retrieval.py
"""

import csv
import json
import sys
import time
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import (
    EVALUATION_QUERIES_FILE,
    EVALUATION_RESULTS_DIR,
    EVALUATION_TOP_K_VALUES,
    NDCG_K,
)
from backend.retrieval.retriever_factory import retrieve, VALID_METHODS
from evaluation.metrics import recall_at_k, precision_at_k, reciprocal_rank, ndcg_at_k


def load_queries() -> list[dict]:
    if not EVALUATION_QUERIES_FILE.exists():
        print(f"[ERROR] Evaluation query file not found: {EVALUATION_QUERIES_FILE}")
        sys.exit(1)

    with open(EVALUATION_QUERIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    queries = data.get("queries", [])

    usable = [q for q in queries if q.get("relevant_chunk_ids")]
    skipped = len(queries) - len(usable)
    if skipped:
        print(
            f"[WARNING] {skipped} quer(ies) have empty 'relevant_chunk_ids' "
            f"and will be skipped. Fill these in manually before evaluation "
            f"is meaningful (see Day 4 manual Part 13/14)."
        )
    if not usable:
        print("[ERROR] No queries with relevance judgments found. Nothing to evaluate.")
        sys.exit(1)

    return usable


def evaluate_method(method: str, queries: list[dict]) -> dict:
    """Run one retrieval method against every query, computing all metrics."""
    per_query_metrics = []
    latencies = []

    max_k = max(EVALUATION_TOP_K_VALUES)

    for q in queries:
        relevant_ids = set(q["relevant_chunk_ids"])
        relevance_grades = q.get("relevance_grades") or {cid: 1 for cid in relevant_ids}

        start = time.perf_counter()
        results = retrieve(q["query"], method=method, top_k=max_k)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

        retrieved_ids = [r["chunk_id"] for r in results]

        metrics = {"query_id": q["query_id"]}
        for k in EVALUATION_TOP_K_VALUES:
            metrics[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
            metrics[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        metrics["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
        metrics[f"ndcg@{NDCG_K}"] = ndcg_at_k(retrieved_ids, relevance_grades, NDCG_K)

        per_query_metrics.append(metrics)

    aggregated = {
        "method": method,
        "query_count": len(queries),
        "avg_latency_seconds": mean(latencies),
    }
    metric_keys = [k for k in per_query_metrics[0].keys() if k != "query_id"]
    for key in metric_keys:
        aggregated[key] = mean(m[key] for m in per_query_metrics)

    return aggregated


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — Retrieval Evaluation")
    print("=" * 60)

    queries = load_queries()
    print(f"\nEvaluating using {len(queries)} quer(ies) with relevance judgments.")

    all_results = []
    for method in VALID_METHODS:
        print(f"\nRunning method: {method} ...")
        result = evaluate_method(method, queries)
        all_results.append(result)
        print(f"  Recall@5: {result['recall@5']:.3f}  MRR: {result['mrr']:.3f}  "
              f"nDCG@{NDCG_K}: {result[f'ndcg@{NDCG_K}']:.3f}  "
              f"Avg latency: {result['avg_latency_seconds']*1000:.1f} ms")

    EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = EVALUATION_RESULTS_DIR / "retrieval_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    csv_path = EVALUATION_RESULTS_DIR / "retrieval_results.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
        writer.writeheader()
        writer.writerows(all_results)

    print("\n" + "=" * 60)
    print("Done. Results saved to:")
    print(f"  {json_path}")
    print(f"  {csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()