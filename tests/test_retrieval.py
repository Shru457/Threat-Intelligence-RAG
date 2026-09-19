"""
Tests for the Day 3 semantic retrieval subsystem.

Note: these tests require the embedding model (downloaded on first use
and then cached locally) and, for the FAISS-dependent tests, a
pre-built vectorstore/ (run scripts/build_vector_index.py first).
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.config import EMBEDDING_DIMENSION, FAISS_INDEX_FILE, METADATA_FILE
from backend.retrieval.embeddings import embed_texts, embed_single_text
from backend.retrieval.vector_store import build_index, normalize_vectors, load_index
from backend.retrieval.semantic_search import search


def test_embedding_generation_works():
    vectors = embed_texts(["This is a test sentence about malware."])
    assert vectors.shape[0] == 1


def test_embedding_dimension_matches_config():
    vectors = embed_texts(["A short test sentence."])
    assert vectors.shape[1] == EMBEDDING_DIMENSION


def test_embedding_is_reasonably_stable():
    v1 = embed_single_text("The malware exfiltrated credentials.")
    v2 = embed_single_text("The malware exfiltrated credentials.")
    # Same input should produce (near-)identical output.
    assert np.allclose(v1, v2, atol=1e-5)


def test_embedding_count_matches_input_count():
    texts = ["one", "two", "three", "four"]
    vectors = embed_texts(texts)
    assert vectors.shape[0] == len(texts)


def test_faiss_index_contains_expected_vector_count():
    texts = ["alpha chunk", "beta chunk", "gamma chunk"]
    vectors = embed_texts(texts)
    index = build_index(vectors)
    assert index.ntotal == len(texts)


def test_normalize_vectors_produces_unit_length():
    vectors = embed_texts(["some sample text", "another sample text"])
    normalized = normalize_vectors(vectors)
    norms = np.linalg.norm(normalized, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


@pytest.mark.skipif(
    not FAISS_INDEX_FILE.exists() or not METADATA_FILE.exists(),
    reason="vectorstore/ not built yet — run scripts/build_vector_index.py first",
)
class TestBuiltVectorstore:
    """These tests run against your ACTUAL built vectorstore from Part 9."""

    def test_saved_index_can_be_loaded(self):
        index, metadata = load_index()
        assert index.ntotal > 0
        assert len(metadata) == index.ntotal

    def test_search_returns_exactly_k_results(self):
        results = search("malware persistence techniques", top_k=3)
        assert len(results) == 3

    def test_search_results_contain_required_fields(self):
        results = search("credential theft", top_k=1)
        required = {"rank", "score", "chunk_id", "document_id",
                    "document_title", "source", "page_number",
                    "chunk_index", "text"}
        assert required.issubset(results[0].keys())

    def test_search_results_are_ranked_by_descending_score(self):
        results = search("supply chain attack", top_k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_does_not_crash_on_short_query(self):
        results = search("CVE", top_k=2)
        assert isinstance(results, list)


def test_missing_vectorstore_raises_clear_error(tmp_path, monkeypatch):
    """Simulate a missing vectorstore and confirm a clear error, not a crash."""
    import backend.retrieval.vector_store as vs_module
    monkeypatch.setattr(vs_module, "FAISS_INDEX_FILE", tmp_path / "missing_index.faiss")
    monkeypatch.setattr(vs_module, "METADATA_FILE", tmp_path / "missing_meta.json")

    with pytest.raises(FileNotFoundError):
        vs_module.load_index()