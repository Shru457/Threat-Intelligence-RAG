"""
Interactive CLI for testing semantic search.

Usage:
    python scripts/test_semantic_search.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.semantic_search import search
from backend.retrieval.config import DEFAULT_TOP_K


def print_results(query: str, results: list[dict]) -> None:
    print(f"\nQuery:\n{query}\n")

    if not results:
        print("No results found.")
        return

    print(f"Top {len(results)} Results:\n")
    for r in results:
        print(f"[{r['rank']}]")
        print(f"Score: {r['score']:.4f}")
        print(f"Document: {r['document_title']} ({r['document_id']})")
        print(f"Page: {r['page_number']}")
        print(f"Chunk ID: {r['chunk_id']}")
        print("Text:")
        print(r['text'])
        print()


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — Semantic Search Test")
    print("=" * 60)
    print("Type a cybersecurity question and press Enter.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Question: ").strip()
        if query.lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        if not query:
            continue

        results = search(query, top_k=DEFAULT_TOP_K)
        print_results(query, results)


if __name__ == "__main__":
    main()