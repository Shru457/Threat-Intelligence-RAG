"""
Interactive CLI for testing all four retrieval methods side by side.

Usage:
    python scripts/test_retrieval.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.retriever_factory import retrieve, VALID_METHODS
from backend.retrieval.config import DEFAULT_TOP_K


def print_results(method: str, results: list[dict]) -> None:
    print(f"\n--- {method.upper()} ---")
    if not results:
        print("No results found.")
        return
    for r in results:
        print(f"[{r['rank']}] score={r['score']:.4f}  "
              f"{r['document_title']} (page {r['page_number']})  "
              f"chunk_id={r['chunk_id']}")
        print(f"    {r['text'][:150].strip()}...")


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — Unified Retrieval Test")
    print("=" * 60)
    print(f"Available methods: {', '.join(VALID_METHODS)}")
    print("Type a question, or 'exit' to quit.\n")

    while True:
        query = input("Question: ").strip()
        if query.lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        if not query:
            continue

        print(f"\nQuery:\n{query}")
        for method in VALID_METHODS:
            results = retrieve(query, method=method, top_k=DEFAULT_TOP_K)
            print_results(method, results)
        print()


if __name__ == "__main__":
    main()