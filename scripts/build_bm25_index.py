"""
Entry point: build and persist the BM25 index from Day 2's processed
chunks (the same chunks.jsonl Day 3's FAISS index was built from).

Usage:
    python scripts/build_bm25_index.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import PROCESSED_CHUNKS_FILE, BM25_INDEX_FILE
from backend.retrieval.bm25_search import build_bm25_index, save_bm25_index


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — BM25 Index Build")
    print("=" * 60)

    if not PROCESSED_CHUNKS_FILE.exists():
        print(f"[ERROR] Processed chunks file not found: {PROCESSED_CHUNKS_FILE}")
        print("Run Day 2's 'python scripts/ingest_documents.py' first.")
        sys.exit(1)

    print(f"\nBuilding BM25 index from {PROCESSED_CHUNKS_FILE}...")
    bm25, metadata = build_bm25_index()
    print(f"Indexed {len(metadata)} chunks.")

    save_bm25_index(bm25, metadata)

    print(f"\nSaved BM25 index to {BM25_INDEX_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()