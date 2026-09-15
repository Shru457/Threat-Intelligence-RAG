"""
Basic tests for the ingestion pipeline's core logic
(cleaning, chunking, chunk IDs, metadata).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.ingestion.text_cleaner import clean_text
from backend.ingestion.chunker import chunk_text
from backend.ingestion.metadata_builder import build_chunk_record


def test_clean_text_joins_wrapped_words():
    raw = "Cobalt\nStrike is a malware\nframework."
    cleaned = clean_text(raw)
    assert "Cobalt Strike" in cleaned
    assert "malware framework" in cleaned


def test_clean_text_collapses_blank_lines():
    raw = "Paragraph one.\n\n\n\n\nParagraph two."
    cleaned = clean_text(raw)
    assert "\n\n\n" not in cleaned


def test_clean_text_preserves_cve_ids():
    raw = "The flaw is tracked as CVE-2023-12345 and remains unpatched."
    cleaned = clean_text(raw)
    assert "CVE-2023-12345" in cleaned


def test_chunk_text_respects_overlap():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()
    overlap = set(first_chunk_words) & set(second_chunk_words)
    assert len(overlap) > 0


def test_chunk_text_empty_input():
    assert chunk_text("") == []


def test_build_chunk_record_id_format():
    record = build_chunk_record(
        document_id="testdoc",
        document_title="Test Doc",
        page_number=3,
        chunk_index=1,
        text="some sample chunk text",
    )
    assert record["chunk_id"] == "testdoc_p3_c1"
    assert record["page_number"] == 3
    assert record["text"] == "some sample chunk text"