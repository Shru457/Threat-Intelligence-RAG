import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.metrics import (
    compute_token_f1,
    compute_evidence_grounding,
    compute_citation_metrics,
    evaluate_abstention,
)


def test_token_f1_exact_and_partial():
    # Exact match
    assert compute_token_f1("TheHatman stolen credentials", "TheHatman stolen credentials") == 1.0

    # Disjoint
    assert compute_token_f1("completely unrelated words", "something else entirely") == 0.0

    # Partial match
    f1 = compute_token_f1("TheHatman stole credentials in August 2026", "TheHatman credential theft 2026")
    assert 0.35 <= f1 < 1.0


def test_evidence_grounding():
    evidence_chunks = [
        {"text": "The ChainDrop npm worm infected over 400 packages that were downloaded millions of times."}
    ]

    # Grounded answer
    grounded_answer = "The ChainDrop npm worm infected over 400 packages [1]."
    assert compute_evidence_grounding(grounded_answer, evidence_chunks) == 1.0

    # Ungrounded / Hallucinated answer
    hallucinated = "The malware was written in Haskell by Russian state actors from GRU unit 74455."
    assert compute_evidence_grounding(hallucinated, evidence_chunks) == 0.0


def test_citation_metrics():
    relevant_cids = {"doc_p1_c0", "doc_p2_c1"}

    # Perfect citations
    good_citations = [
        {"citation_id": 1, "chunk_id": "doc_p1_c0", "is_valid": True},
        {"citation_id": 2, "chunk_id": "doc_p2_c1", "is_valid": True},
    ]
    res = compute_citation_metrics(good_citations, relevant_cids)
    assert res["citation_validity"] == 1.0
    assert res["citation_precision"] == 1.0
    assert res["citation_recall"] == 1.0

    # Citations with phantom / invalid reference
    bad_citations = [
        {"citation_id": 1, "chunk_id": "doc_p1_c0", "is_valid": True},
        {"citation_id": 2, "chunk_id": "UNKNOWN", "is_valid": False},
    ]
    res_bad = compute_citation_metrics(bad_citations, relevant_cids)
    assert res_bad["citation_validity"] == 0.5
    assert res_bad["citation_precision"] == 1.0  # 1 true positive out of 1 valid cited cid
    assert res_bad["citation_recall"] == 0.5     # 1 out of 2 relevant cids found


def test_abstention_evaluation():
    # Correct rejection (unanswerable query, system abstained)
    eval_cr = evaluate_abstention(is_abstention=True, expected_abstention=True)
    assert eval_cr["correct_decision"] is True
    assert eval_cr["is_false_positive"] is False

    # Correct answering (answerable query, system answered)
    eval_ca = evaluate_abstention(is_abstention=False, expected_abstention=False)
    assert eval_ca["correct_decision"] is True

    # False positive (unanswerable query, but system hallucinated an answer)
    eval_fp = evaluate_abstention(is_abstention=False, expected_abstention=True)
    assert eval_fp["correct_decision"] is False
    assert eval_fp["is_false_positive"] is True

    # False negative (answerable query, but system erroneously abstained)
    eval_fn = evaluate_abstention(is_abstention=True, expected_abstention=False)
    assert eval_fn["correct_decision"] is False
    assert eval_fn["is_false_negative"] is True
