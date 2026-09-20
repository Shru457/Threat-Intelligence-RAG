"""
BM25 sparse (keyword) retrieval over Day 2's processed chunks.

Uses rank_bm25's BM25Okapi implementation with a custom,
cybersecurity-aware tokenizer that keeps technical identifiers
(CVE IDs, MITRE ATT&CK IDs, hashes, IPs, domains, filenames) intact
as single tokens instead of shattering them on punctuation.
"""

import json
import pickle
import re

from rank_bm25 import BM25Okapi

from .config import PROCESSED_CHUNKS_FILE, BM25_INDEX_FILE, VECTORSTORE_DIR, BM25_TOP_K

# Matches a run of letters/digits that may contain internal dots,
# hyphens, or underscores. This is what keeps "CVE-2026-1234",
# "T1059.001", "10.10.10.10", "example-domain.com", and
# "powershell.exe" each as ONE token, instead of a naive
# whitespace/punctuation tokenizer shattering them apart.
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def tokenize(text: str) -> list[str]:
    """
    Cybersecurity-aware tokenizer.

    Lowercases text (so "CVE-2026-1234" and "cve-2026-1234" match the
    same token) and extracts alphanumeric runs that may include
    internal '.', '-', '_' — preserving technical identifiers whole.
    Standalone punctuation (commas, parentheses, quotes) is dropped,
    since it carries no retrieval-relevant meaning; punctuation
    INSIDE an identifier is preserved because it IS part of the
    identifier.
    """
    return _TOKEN_PATTERN.findall(text.lower())


def _load_chunks() -> list[dict]:
    """Read chunks.jsonl in file order — the same order Day 3 used for FAISS."""
    chunks = []
    with open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_bm25_index() -> tuple[BM25Okapi, list[dict]]:
    """
    Build a BM25 index from the same chunks.jsonl used by Day 3.

    Returns the BM25Okapi object and the metadata list, in matching
    order — metadata[i] describes the chunk BM25 refers to as
    document i, for the same reason Day 3's FAISS metadata alignment
    works: both are built by iterating chunks.jsonl in file order.
    """
    chunks = _load_chunks()
    tokenized_corpus = [tokenize(chunk["text"]) for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, chunks


def save_bm25_index(bm25: BM25Okapi, metadata: list[dict]) -> None:
    """Persist the BM25 index + its aligned metadata to vectorstore/."""
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    with open(BM25_INDEX_FILE, "wb") as f:
        pickle.dump({"bm25": bm25, "metadata": metadata}, f)


_bm25_cache = None
_bm25_metadata_cache = None


def load_bm25_index() -> tuple[BM25Okapi, list[dict]]:
    """Load the persisted BM25 index, caching it for the process lifetime."""
    global _bm25_cache, _bm25_metadata_cache
    if _bm25_cache is None:
        if not BM25_INDEX_FILE.exists():
            raise FileNotFoundError(
                f"BM25 index not found at {BM25_INDEX_FILE}. "
                f"Run 'python scripts/build_bm25_index.py' first."
            )
        with open(BM25_INDEX_FILE, "rb") as f:
            data = pickle.load(f)
        _bm25_cache = data["bm25"]
        _bm25_metadata_cache = data["metadata"]
    return _bm25_cache, _bm25_metadata_cache


def search(query: str, top_k: int = BM25_TOP_K) -> list[dict]:
    """
    Run a BM25 keyword search and return structured, ranked results in
    the SAME shape Day 3's semantic search() returns, so both can be
    used interchangeably by hybrid_search.py and the retriever factory.
    """
    bm25, metadata = load_bm25_index()

    if not metadata:
        return []

    tokenized_query = tokenize(query)
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top_indices = ranked_indices[:top_k]

    results = []
    for rank, idx in enumerate(top_indices, start=1):
        if scores[idx] <= 0:
            continue  # a zero/negative BM25 score means no real keyword match
        chunk = metadata[idx]
        results.append({
            "rank": rank,
            "score": float(scores[idx]),
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "source": chunk["source"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
        })

    return results