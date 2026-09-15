"""
Fixed-size, word-count-based chunking with overlap.
Operates per-page so every chunk has an unambiguous single page number.
"""

from .config import CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS, MIN_CHUNK_WORDS


def chunk_text(text: str) -> list[str]:
    """
    Split a single page's cleaned text into overlapping word-count chunks.

    Returns a list of chunk strings (may be empty if the input has no
    words meeting the minimum length after chunking).
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
    if step <= 0:
        raise ValueError(
            "CHUNK_OVERLAP_WORDS must be smaller than CHUNK_SIZE_WORDS."
        )

    start = 0
    while start < len(words):
        window = words[start:start + CHUNK_SIZE_WORDS]
        if len(window) >= MIN_CHUNK_WORDS:
            chunks.append(" ".join(window))
        start += step

    return chunks