"""
Comprehensive RAG Evaluation Runner.

Executes actual measured evaluations across:
1. BM25 Keyword Retrieval
2. Semantic Vector Retrieval
3. Hybrid Retrieval (RRF)
4. Hybrid + Cross-Encoder Reranking
5. Final Grounded RAG Pipeline (Retrieve + Rerank + Generation)

Measures:
- Retrieval: Recall@1, Recall@3, Recall@5, Recall@10, MRR, nDCG@5
- Generation: Answer Correctness (Token F1), Evidence Grounding / Faithfulness,
  Citation Precision & Validity, Abstention Accuracy on unanswerable queries
- Latency: Measured wall-clock latency per query in milliseconds

Saves actual results to data/evaluation/results/ as JSON and CSV.
"""

import csv
import json
import sys
import time
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.config import EVALUATION_RESULTS_DIR, EVALUATION_TOP_K_VALUES, NDCG_K
from backend.retrieval.retriever_factory import retrieve
from backend.generation.rag_pipeline import RAGPipeline
from evaluation.metrics import (
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
    compute_token_f1,
    compute_evidence_grounding,
    compute_citation_metrics,
    evaluate_abstention,
)

DATASET_FILE = PROJECT_ROOT / "data" / "evaluation" / "rag_evaluation_dataset.json"


def load_dataset() -> dict:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {DATASET_FILE}")
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval_method(method: str, queries: list[dict]) -> dict:
    """Evaluate a pure retrieval method across answerable queries."""
    max_k = max(EVALUATION_TOP_K_VALUES)
    per_query = []
    latencies = []

    for q in queries:
        if q.get("expected_abstention", False):
            continue  # Pure retrieval metrics are computed on queries with relevant targets

        relevant_ids = set(q["relevant_chunk_ids"])
        relevance_grades = q.get("relevance_grades") or {cid: 1 for cid in relevant_ids}

        start = time.perf_counter()
        results = retrieve(q["query"], method=method, top_k=max_k)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

        retrieved_ids = [r["chunk_id"] for r in results]

        row = {"query_id": q["query_id"]}
        for k in EVALUATION_TOP_K_VALUES:
            row[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
            row[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        row["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
        row[f"ndcg@{NDCG_K}"] = ndcg_at_k(retrieved_ids, relevance_grades, NDCG_K)
        per_query.append(row)

    metric_keys = [k for k in per_query[0].keys() if k != "query_id"]
    agg = {
        "system": method,
        "type": "retrieval_baseline",
        "evaluated_queries": len(per_query),
        "avg_latency_ms": round(mean(latencies) * 1000, 2),
    }
    for k in metric_keys:
        agg[k] = round(mean(p[k] for p in per_query), 4)

    # Placeholders for generation metrics
    agg["answer_correctness_f1"] = "N/A"
    agg["evidence_grounding"] = "N/A"
    agg["citation_precision"] = "N/A"
    agg["citation_validity"] = "N/A"
    agg["abstention_accuracy"] = "N/A"

    return agg


def evaluate_rag_pipeline(pipeline: RAGPipeline, queries: list[dict]) -> tuple[dict, list[dict]]:
    """Evaluate the end-to-end RAG pipeline across all queries (including unanswerables)."""
    max_k = max(EVALUATION_TOP_K_VALUES)
    per_query_records = []
    latencies = []
    retrieval_latencies = []
    generation_latencies = []

    retrieval_eval_rows = []
    correctness_scores = []
    grounding_scores = []
    citation_precisions = []
    citation_validities = []
    abstention_correct = []

    for q in queries:
        query_text = q["query"]
        expected_abstention = q.get("expected_abstention", False)
        relevant_ids = set(q.get("relevant_chunk_ids", []))
        relevance_grades = q.get("relevance_grades") or {cid: 1 for cid in relevant_ids}
        ground_truth = q.get("ground_truth_answer", "")

        rag_output = pipeline.answer(query_text, retrieval_method="hybrid_rerank", top_k=max_k)

        latencies.append(rag_output["latency_seconds"])
        retrieval_latencies.append(rag_output.get("retrieval_latency_seconds", 0.0))
        generation_latencies.append(rag_output.get("generation_latency_seconds", 0.0))

        is_abstention = rag_output["is_abstention"]
        answer_text = rag_output["answer"]
        citations = rag_output["citations"]
        evidence = rag_output["retrieved_evidence"]
        retrieved_ids = [e["chunk_id"] for e in evidence]

        # 1. Abstention check
        abs_eval = evaluate_abstention(is_abstention, expected_abstention)
        abstention_correct.append(1.0 if abs_eval["correct_decision"] else 0.0)

        record = {
            "query_id": q["query_id"],
            "category": q["category"],
            "query": query_text,
            "expected_abstention": expected_abstention,
            "is_abstention": is_abstention,
            "latency_ms": round(rag_output["latency_seconds"] * 1000, 2),
            "generated_answer": answer_text,
            "citation_count": len(citations),
            "citations": citations,
        }

        # 2. If answerable query, evaluate retrieval & generation
        if not expected_abstention:
            ret_row = {}
            for k in EVALUATION_TOP_K_VALUES:
                ret_row[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
                ret_row[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
            ret_row["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
            ret_row[f"ndcg@{NDCG_K}"] = ndcg_at_k(retrieved_ids, relevance_grades, NDCG_K)
            retrieval_eval_rows.append(ret_row)

            # Answer correctness (token F1)
            f1 = compute_token_f1(answer_text, ground_truth)
            correctness_scores.append(f1)
            record["correctness_f1"] = round(f1, 4)

            # Evidence grounding
            grounding = compute_evidence_grounding(answer_text, evidence)
            grounding_scores.append(grounding)
            record["evidence_grounding"] = round(grounding, 4)

            # Citations
            cite_metrics = compute_citation_metrics(citations, relevant_ids)
            citation_precisions.append(cite_metrics["citation_precision"])
            citation_validities.append(cite_metrics["citation_validity"])
            record["citation_precision"] = round(cite_metrics["citation_precision"], 4)
            record["citation_validity"] = round(cite_metrics["citation_validity"], 4)
        else:
            record["correctness_f1"] = 1.0 if is_abstention else 0.0
            record["evidence_grounding"] = 1.0 if is_abstention else 0.0
            record["citation_precision"] = 1.0 if not citations else 0.0
            record["citation_validity"] = 1.0

        per_query_records.append(record)

    agg = {
        "system": "final_rag_pipeline",
        "type": "end_to_end_rag",
        "evaluated_queries": len(queries),
        "avg_latency_ms": round(mean(latencies) * 1000, 2),
    }

    # Aggregate retrieval metrics from the RAG pipeline's first stage
    if retrieval_eval_rows:
        for k in retrieval_eval_rows[0].keys():
            agg[k] = round(mean(r[k] for r in retrieval_eval_rows), 4)

    agg["answer_correctness_f1"] = round(mean(correctness_scores), 4) if correctness_scores else 0.0
    agg["evidence_grounding"] = round(mean(grounding_scores), 4) if grounding_scores else 0.0
    agg["citation_precision"] = round(mean(citation_precisions), 4) if citation_precisions else 0.0
    agg["citation_validity"] = round(mean(citation_validities), 4) if citation_validities else 0.0
    agg["abstention_accuracy"] = round(mean(abstention_correct), 4)

    return agg, per_query_records


def main():
    print("=" * 70)
    print("CYBERSECURITY THREAT INTELLIGENCE RAG — COMPREHENSIVE EVALUATION")
    print("=" * 70)

    dataset_obj = load_dataset()
    queries = dataset_obj["queries"]
    print(f"\nLoaded {len(queries)} evaluation queries across {len(dataset_obj['categories'])} categories.")

    answerable_queries = [q for q in queries if not q.get("expected_abstention", False)]
    unanswerable_queries = [q for q in queries if q.get("expected_abstention", False)]
    print(f"  - Answerable queries: {len(answerable_queries)}")
    print(f"  - Unanswerable (abstention) queries: {len(unanswerable_queries)}")

    systems_to_evaluate = ["bm25", "semantic", "hybrid", "hybrid_rerank"]
    all_results = []

    # 1. Evaluate pure retrieval baselines
    for method in systems_to_evaluate:
        print(f"\nEvaluating retrieval system: {method.upper()} ...")
        res = evaluate_retrieval_method(method, queries)
        all_results.append(res)
        print(
            f"  Recall@5: {res['recall@5']:.4f} | MRR: {res['mrr']:.4f} | "
            f"nDCG@5: {res[f'ndcg@{NDCG_K}']:.4f} | Latency: {res['avg_latency_ms']} ms"
        )

    # 2. Evaluate final end-to-end RAG pipeline
    print("\nEvaluating complete FINAL RAG PIPELINE (Retrieval + Rerank + Generation) ...")
    pipeline = RAGPipeline()
    rag_res, per_query_records = evaluate_rag_pipeline(pipeline, queries)
    all_results.append(rag_res)

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY RESULTS")
    print("=" * 70)
    for r in all_results:
        sys_name = r["system"]
        rec5 = r.get("recall@5", "N/A")
        mrr = r.get("mrr", "N/A")
        ndcg = r.get("ndcg@5", "N/A")
        f1 = r.get("answer_correctness_f1", "N/A")
        faith = r.get("evidence_grounding", "N/A")
        cite_p = r.get("citation_precision", "N/A")
        abs_acc = r.get("abstention_accuracy", "N/A")
        lat = r["avg_latency_ms"]
        print(
            f"[{sys_name:<18}] Rec@5: {str(rec5):<6} | MRR: {str(mrr):<6} | "
            f"nDCG@5: {str(ndcg):<6} | F1: {str(f1):<6} | Grounding: {str(faith):<6} | "
            f"CitePrec: {str(cite_p):<6} | AbstainAcc: {str(abs_acc):<6} | Latency: {lat}ms"
        )

    # Persist results
    EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summary_json = EVALUATION_RESULTS_DIR / "rag_evaluation_results.json"
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    summary_csv = EVALUATION_RESULTS_DIR / "rag_evaluation_results.csv"
    keys = list(all_results[0].keys())
    # Ensure all keys across results are present in CSV header
    all_keys = list(dict.fromkeys(k for res in all_results for k in res.keys()))
    with open(summary_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(all_results)

    per_query_json = EVALUATION_RESULTS_DIR / "rag_per_query_results.json"
    with open(per_query_json, "w", encoding="utf-8") as f:
        json.dump(per_query_records, f, indent=2)

    print("\n" + "=" * 70)
    print("Saved Evaluation Results to:")
    print(f"  Summary JSON:   {summary_json}")
    print(f"  Summary CSV:    {summary_csv}")
    print(f"  Per-Query JSON: {per_query_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()
