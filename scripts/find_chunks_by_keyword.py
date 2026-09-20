"""
Helper: search chunks.jsonl by a plain keyword to help you manually
identify chunk_ids for the evaluation query set (Part 13/14).

Usage:
    python scripts/find_chunks_by_keyword.py "credential"
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import PROCESSED_CHUNKS_FILE


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/find_chunks_by_keyword.py "some keyword"')
        sys.exit(1)

    keyword = sys.argv[1].lower()

    with open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        matches = 0
        for line in f:
            chunk = json.loads(line)
            if keyword in chunk["text"].lower():
                matches += 1
                print(f"\nchunk_id: {chunk['chunk_id']}")
                print(f"document: {chunk['document_title']}  (page {chunk['page_number']})")
                snippet = chunk["text"][:220].replace("\n", " ")
                print(f"snippet: {snippet}...")

    print(f"\n{matches} matching chunk(s) found for keyword '{keyword}'.")


if __name__ == "__main__":
    main()