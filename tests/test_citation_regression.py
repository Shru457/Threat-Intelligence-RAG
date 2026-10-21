"""
Regression tests for Citation Traceability, Metadata Preservation, and PyArrow DataFrame Rendering.

Verifies:
1. Citation-to-evidence mapping against real PDF text.
2. Handling of duplicate citation tags.
3. Handling of missing or partial metadata without fabricating.
4. Marking phantom/invalid citation IDs as invalid.
5. PyArrow / Pandas DataFrame conversion for the citation table (ensuring no NumPy 2.0 / PyArrow conflict).
6. Abstention on unsupported queries producing zero citations.
"""

import sys
from pathlib import Path
import torch
import pytest
import pandas as pd
import pyarrow as pa
import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.generation.context_builder import (
    build_evidence_context,
    extract_citations,
)
from backend.generation.llm import OfflineExtractiveLLMProvider
from backend.generation.rag_pipeline import RAGPipeline
from backend.generation.config import INSUFFICIENT_EVIDENCE_MESSAGE


def test_citation_traceability_from_real_pdf_to_answer():
    """Verify that an answer citing ChainDrop traces back to the actual text on page 1 of the real PDF."""
    pdf_path = PROJECT_ROOT / "data" / "raw" / "unit42_chaindrop_npm_worm_2026.pdf"
    assert pdf_path.exists(), "Source PDF must exist"

    # 1. Open original PDF with PyMuPDF
    doc = fitz.open(pdf_path)
    page_1_text = doc[0].get_text("text")
    assert "ChainDrop" in page_1_text
    assert "400" in page_1_text

    # 2. Run query through the pipeline
    pipeline = RAGPipeline(provider=OfflineExtractiveLLMProvider())
    result = pipeline.answer(
        "How many packages were infected by the ChainDrop npm worm?",
        retrieval_method="hybrid_rerank",
        top_k=3,
    )

    assert result["is_abstention"] is False
    assert len(result["citations"]) > 0

    # 3. Check the first citation maps to page 1 of the ChainDrop document
    c1 = result["citations"][0]
    assert c1["is_valid"] is True
    assert "chaindrop" in c1["document_id"].lower()
    assert c1["page_number"] == 1
    assert "400" in c1["snippet"] or "ChainDrop" in c1["snippet"]


def test_citation_duplicate_and_ordering():
    """Verify duplicate citation references [1] ... [1] are deduplicated preserving order."""
    citation_map = {
        1: {
            "chunk_id": "doc1_p1_c0",
            "document_id": "doc1",
            "document_title": "Report One",
            "page_number": 1,
            "score": 0.9,
            "text": "Initial intrusion via phish.",
        },
        2: {
            "chunk_id": "doc2_p3_c0",
            "document_id": "doc2",
            "document_title": "Report Two",
            "page_number": 3,
            "score": 0.8,
            "text": "Subsequent lateral movement.",
        },
    }

    answer = "The attacker used phishing [1]. Then movement was observed [2], followed by more activity [1]."
    citations = extract_citations(answer, citation_map)

    assert len(citations) == 2
    assert [c["citation_id"] for c in citations] == [1, 2]
    assert citations[0]["chunk_id"] == "doc1_p1_c0"
    assert citations[1]["chunk_id"] == "doc2_p3_c0"


def test_citation_missing_or_corrupt_metadata_handling():
    """Verify missing optional fields do not crash the citation builder or fabricate false data."""
    incomplete_chunk = {
        "text": "Some isolated threat evidence without complete metadata.",
        # Missing chunk_id, document_title, page_number, score
    }
    context_str, citation_map = build_evidence_context([incomplete_chunk])
    assert "[1]" in context_str
    assert "Unknown Report" in context_str

    citations = extract_citations("Evidence was observed [1].", citation_map)
    assert len(citations) == 1
    c = citations[0]
    assert c["is_valid"] is True
    assert c["document_title"] == "Unknown Report" or c["document_title"] == ""
    assert c["page_number"] == 0 or c["page_number"] == "?"


def test_citation_invalid_references_marked_invalid():
    """Verify that hallucinated citation IDs like [99] are marked as invalid without crashing."""
    citation_map = {
        1: {
            "chunk_id": "doc1_p1_c0",
            "document_id": "doc1",
            "document_title": "Real Doc",
            "page_number": 1,
            "score": 0.95,
            "text": "Real evidence.",
        }
    }

    answer = "Real fact [1] and unsupported hallucinated claim [99]."
    citations = extract_citations(answer, citation_map)

    assert len(citations) == 2
    valid_c = [c for c in citations if c["is_valid"]]
    invalid_c = [c for c in citations if not c["is_valid"]]

    assert len(valid_c) == 1
    assert valid_c[0]["citation_id"] == 1
    assert len(invalid_c) == 1
    assert invalid_c[0]["citation_id"] == 99
    assert invalid_c[0]["chunk_id"] == "UNKNOWN"


def test_pyarrow_dataframe_citation_table_conversion():
    """Verify that the citation rows rendered in the UI convert into DataFrame and PyArrow Table without NumPy 2.0 error."""
    citation_rows = [
        {
            "Citation": "[1]",
            "Document Title": "Unit 42 ChainDrop Worm",
            "Document ID": "unit42_chaindrop_npm_worm_2026",
            "Page": 1,
            "Chunk ID": "unit42_chaindrop_npm_worm_2026_p1_c0",
            "Rerank Score": "0.9124",
            "Evidence Snippet": "A self-propagating npm worm nicknamed ChainDrop...",
        },
        {
            "Citation": "[2]",
            "Document Title": "Unit 42 Credential Attacks",
            "Document ID": "unit42_large_scale_credential_attacks_2026",
            "Page": 4,
            "Chunk ID": "unit42_large_scale_credential_attacks_2026_p4_c1",
            "Rerank Score": "0.7850",
            "Evidence Snippet": "Threat actors deployed spray attacks across...",
        },
    ]

    df = pd.DataFrame(citation_rows)
    assert not df.empty
    assert len(df) == 2

    # Converting to PyArrow table must succeed without NumPy 2.0 / PyArrow conflict
    pa_table = pa.Table.from_pandas(df)
    assert pa_table.num_rows == 2
    assert "Citation" in pa_table.column_names
    assert "Document Title" in pa_table.column_names


def test_unsupported_query_abstention_no_hallucinated_citations():
    """Verify that on an unanswerable query, the system abstains and returns 0 citations."""
    pipeline = RAGPipeline(provider=OfflineExtractiveLLMProvider())
    result = pipeline.answer(
        "What was the zero-day exploit used against iOS 19 in the 2029 Stuxnet reboot?",
        retrieval_method="hybrid_rerank",
        top_k=3,
    )
    assert result["is_abstention"] is True
    assert result["answer"] == INSUFFICIENT_EVIDENCE_MESSAGE
    assert len(result["citations"]) == 0
