"""
Entry point: build the FAISS vector index from Day 2's processed chunks.

Usage:
    python scripts/build_vector_index.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import PROCESSED_CHUNKS_FILE
from backend.retrieval.embeddings import embed_texts
from backend.retrieval.vector_store import build_index, save_index


def load_chunks() -> list[dict]:
    """Read every chunk record from Day 2's chunks.jsonl, in file order."""
    if not PROCESSED_CHUNKS_FILE.exists():
        print(f"[ERROR] Processed chunks file not found: {PROCESSED_CHUNKS_FILE}")
        print("Run Day 2's 'python scripts/ingest_documents.py' first.")
        sys.exit(1)

    chunks = []
    with open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[ERROR] Malformed JSON on line {line_number}: {exc}")
                sys.exit(1)

    return chunks


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — Vector Index Build")
    print("=" * 60)

    chunks = load_chunks()
    print(f"\nLoaded {len(chunks)} chunks from {PROCESSED_CHUNKS_FILE}")

    if not chunks:
        print("[ERROR] No chunks found. Nothing to index.")
        sys.exit(1)

    texts = [chunk["text"] for chunk in chunks]

    print(f"\nGenerating embeddings for {len(texts)} chunks...")
    embeddings = embed_texts(texts)
    print(f"Embeddings shape: {embeddings.shape}")  # (N, 384)

    print("\nBuilding FAISS index...")
    index = build_index(embeddings)
    print(f"FAISS index contains {index.ntotal} vectors")

    # metadata[i] corresponds exactly to FAISS vector ID i, since chunks
    # were embedded and added to the index in this same list order.
    metadata = chunks

    print("\nSaving index and metadata to vectorstore/...")
    save_index(index, metadata)

    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Vectors indexed:   {index.ntotal}")
    print(f"  Metadata entries:  {len(metadata)}")
    print("  Files written:")
    print("    vectorstore/index.faiss")
    print("    vectorstore/metadata.json")
    print("=" * 60)


if __name__ == "__main__":
    main()