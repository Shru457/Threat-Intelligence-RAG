"""
Generate a research-paper-friendly bar chart comparing retrieval
methods, from the ACTUAL results in
data/evaluation/results/retrieval_results.json.

Usage:
    python scripts/generate_evaluation_chart.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import EVALUATION_RESULTS_DIR


def main():
    results_path = EVALUATION_RESULTS_DIR / "retrieval_results.json"
    if not results_path.exists():
        print(f"[ERROR] {results_path} not found. Run scripts/evaluate_retrieval.py first.")
        sys.exit(1)

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    methods = [r["method"] for r in results]
    metrics_to_plot = ["recall@5", "mrr", "ndcg@5"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bar_width = 0.25
    x_positions = range(len(methods))

    for i, metric in enumerate(metrics_to_plot):
        values = [r.get(metric, 0.0) for r in results]
        offsets = [x + i * bar_width for x in x_positions]
        ax.bar(offsets, values, width=bar_width, label=metric)

    ax.set_xticks([x + bar_width for x in x_positions])
    ax.set_xticklabels(methods)
    ax.set_ylabel("Score")
    ax.set_title("Retrieval Method Comparison (actual measured results)")
    ax.legend()
    ax.set_ylim(0, 1.0)

    output_path = EVALUATION_RESULTS_DIR / "evaluation_summary.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    print(f"Chart saved to {output_path}")


if __name__ == "__main__":
    main()