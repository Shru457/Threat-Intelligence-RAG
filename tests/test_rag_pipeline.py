"""
Unit tests for Phase 1 RAG Generation Layer.
Tests context builder, citation extraction, LLM provider abstraction,
and end-to-end RAG pipeline functionality.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.generation.config import INSUFFICIENT_EVIDENCE_MESSAGE
from backend.generation.context_builder import (
    build_evidence_context,
    extract_citations,
    extract_cybersecurity_identifiers,
    preserve_cybersecurity_identifiers,
)
from backend.generation.llm import (
    OfflineExtractiveLLMProvider,
    get_llm_provider,
    BaseLLMProvider,
)
from backend.generation.rag_pipeline import RAGPipeline


def test_provider_factory_defaults_to_offline():
    provider = get_llm_provider("offline")
    assert isinstance(provider, BaseLLMProvider)
    assert provider.name == "offline_extractive"


def test_provider_factory_fallback_on_missing_key():
    # When an external provider is requested without an API key, it should fallback safely
    provider = get_llm_provider("gemini")
    assert isinstance(provider, BaseLLMProvider)


def test_context_builder_formats_metadata_and_citations():
    mock_chunks = [
        {
            "chunk_id": "test_doc_p1_c0",
            "document_id": "test_doc",
            "document_title": "Test Security Report",
            "source": "local_pdf",
            "page_number": 1,
            "chunk_index": 0,
            "rank": 1,
            "score": 0.95,
            "text": "Adversaries exploited CVE-2023-24955 to execute arbitrary code.",
        },
        {
            "chunk_id": "test_doc_p2_c1",
            "document_id": "test_doc",
            "document_title": "Test Security Report",
            "source": "local_pdf",
            "page_number": 2,
            "chunk_index": 1,
            "rank": 2,
            "score": 0.88,
            "text": "The actor utilized T1003 for credential dumping.",
        },
    ]

    context_str, citation_map = build_evidence_context(mock_chunks)
    assert "[1]" in context_str
    assert "[2]" in context_str
    assert "Test Security Report" in context_str
    assert "CVE-2023-24955" in context_str
    assert "T1003" in context_str
    assert len(citation_map) == 2
    assert citation_map[1]["chunk_id"] == "test_doc_p1_c0"
    assert citation_map[2]["chunk_id"] == "test_doc_p2_c1"


def test_citation_extraction_and_resolution():
    citation_map = {
        1: {
            "chunk_id": "doc1_p1_c0",
            "document_id": "doc1",
            "document_title": "Doc One",
            "page_number": 1,
            "source": "local_pdf",
            "rank": 1,
            "score": 0.9,
            "text": "Snippet of doc one.",
        },
        2: {
            "chunk_id": "doc2_p5_c1",
            "document_id": "doc2",
            "document_title": "Doc Two",
            "page_number": 5,
            "source": "local_pdf",
            "rank": 2,
            "score": 0.8,
            "text": "Snippet of doc two.",
        },
    }

    answer = "The vulnerability was exploited [1]. Furthermore, lateral movement was observed [2]."
    citations = extract_citations(answer, citation_map)

    assert len(citations) == 2
    assert citations[0]["citation_id"] == 1
    assert citations[0]["chunk_id"] == "doc1_p1_c0"
    assert citations[0]["is_valid"] is True
    assert citations[1]["citation_id"] == 2
    assert citations[1]["chunk_id"] == "doc2_p5_c1"
    assert citations[1]["is_valid"] is True


def test_invalid_citation_resolution():
    citation_map = {1: {"chunk_id": "c1", "document_title": "D1", "text": "..."}}
    answer = "Unsupported claim citing phantom source [99]."
    citations = extract_citations(answer, citation_map)

    assert len(citations) == 1
    assert citations[0]["citation_id"] == 99
    assert citations[0]["is_valid"] is False


def test_cybersecurity_identifier_extraction():
    sample_text = (
        "Adversary exploited CVE-2023-24955 and CVE-2023-29357 using technique T1003.001. "
        "C2 IP 192.168.1.100 was communicated with."
    )
    extracted = extract_cybersecurity_identifiers(sample_text)
    assert "CVE-2023-24955" in extracted["cves"]
    assert "CVE-2023-29357" in extracted["cves"]
    assert "T1003.001" in extracted["mitre_techniques"]
    assert "192.168.1.100" in extracted["ips"]


def test_offline_provider_abstains_on_irrelevant_query():
    provider = OfflineExtractiveLLMProvider()
    mock_prompt = (
        "[1] Source Document: Report A | Page: 1 | Chunk ID: c1 | Rank: 1 | Score: 0.1\n"
        "Content:\nThe company reported quarterly profits and financial earnings.\n\n"
        "Question: Which zero-day exploit was used against iOS 19 in the 2029 Stuxnet reboot?"
    )
    answer = provider.generate(mock_prompt)
    assert answer == INSUFFICIENT_EVIDENCE_MESSAGE


def test_offline_provider_answers_and_cites_grounded_fact():
    provider = OfflineExtractiveLLMProvider()
    mock_prompt = (
        "[1] Source Document: Unit 42 ChainDrop | Page: 1 | Chunk ID: c1 | Rank: 1 | Score: 0.9\n"
        "Content:\nThe ChainDrop npm worm infected over 400 packages that are downloaded millions of times.\n\n"
        "Question: How many packages were infected by the ChainDrop npm worm?"
    )
    answer = provider.generate(mock_prompt)
    assert "[1]" in answer
    assert "400" in answer
    assert "ChainDrop" in answer


def test_rag_pipeline_end_to_end():
    pipeline = RAGPipeline(provider=OfflineExtractiveLLMProvider())
    result = pipeline.answer(
        "What is the ChainDrop npm worm?",
        retrieval_method="hybrid",
        top_k=3,
    )

    assert "query" in result
    assert "answer" in result
    assert "is_abstention" in result
    assert "citations" in result
    assert "retrieved_evidence" in result
    assert "latency_seconds" in result
    assert len(result["retrieved_evidence"]) <= 3
    assert result["latency_seconds"] > 0.0


def test_rag_pipeline_abstains_on_unanswerable_query():
    pipeline = RAGPipeline(provider=OfflineExtractiveLLMProvider())
    result = pipeline.answer(
        "What was the zero-day exploit used against iOS 19 in the 2029 Stuxnet reboot?",
        retrieval_method="hybrid_rerank",
        top_k=3,
    )
    assert result["is_abstention"] is True
    assert result["answer"] == INSUFFICIENT_EVIDENCE_MESSAGE
    assert len(result["citations"]) == 0
