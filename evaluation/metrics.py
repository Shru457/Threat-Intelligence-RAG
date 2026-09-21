"""
Retrieval evaluation metrics: Recall@k, Precision@k, MRR, nDCG@k.

Implemented directly (no external IR-metrics library) so every
formula is visible, explainable, and citable in a research write-up.
"""

import math


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """
    Recall@k: of ALL relevant chunks for this query, what fraction did
    we find somewhere in the top k retrieved results?

    Example: 3 relevant chunks exist total; top-5 retrieved contains 2
    of them -> Recall@5 = 2/3 = 0.667.
    """
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    found = top_k & relevant_ids
    return len(found) / len(relevant_ids)


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """
    Precision@k: of the k results we actually retrieved, what fraction
    were relevant?

    Example: top-5 retrieved contains 2 relevant chunks -> Precision@5
    = 2/5 = 0.4.
    """
    if k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    found = sum(1 for cid in top_k if cid in relevant_ids)
    return found / len(top_k)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """
    Reciprocal Rank for ONE query: 1 / (rank of the FIRST relevant
    result), or 0 if no relevant result appears at all.

    Example: the first relevant chunk appears at rank 3 -> RR = 1/3.
    Averaged across many queries, this becomes MRR (Mean Reciprocal
    Rank) — a measure of "how far down do I typically have to look
    before finding something useful?"
    """
    for rank, cid in enumerate(retrieved_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def dcg_at_k(retrieved_ids: list[str], relevance_grades: dict, k: int) -> float:
    """Discounted Cumulative Gain at k, using graded relevance (0/1/2)."""
    dcg = 0.0
    for i, cid in enumerate(retrieved_ids[:k], start=1):
        grade = relevance_grades.get(cid, 0)
        if grade > 0:
            dcg += grade / math.log2(i + 1)  # rank 1 -> log2(2)=1, rank 2 -> log2(3), etc.
    return dcg


def ndcg_at_k(retrieved_ids: list[str], relevance_grades: dict, k: int) -> float:
    """
    Normalized DCG@k: DCG@k divided by the IDEAL DCG@k (the DCG you'd
    get if the k most relevant chunks were placed in perfect order).

    Why graded relevance (0/1/2) matters here: nDCG can reward
    retrieving a HIGHLY relevant chunk near the top more than a
    merely relevant one — something binary Recall/Precision can't
    express, since binary metrics treat every relevant chunk as
    equally valuable regardless of how central it is to the answer.

    Example: true relevance grades are {A:2, B:1}; if retrieved order
    is [A, B, ...] this is already ideal -> nDCG@k = 1.0. If retrieved
    order is [B, A, ...], DCG is lower than ideal -> nDCG@k < 1.0,
    reflecting that the MORE relevant chunk should have ranked first.
    """
    dcg = dcg_at_k(retrieved_ids, relevance_grades, k)

    ideal_order = sorted(relevance_grades.keys(), key=lambda cid: relevance_grades[cid], reverse=True)
    idcg = dcg_at_k(ideal_order, relevance_grades, k)

    if idcg == 0:
        return 0.0
    return dcg / idcg


# =====================================================================
# Generation & RAG Quality Metrics (Phase 2)
# =====================================================================

import re


def compute_token_f1(prediction: str, ground_truth: str) -> float:
    """
    Compute token-level F1 overlap between prediction and reference answer.
    Standard QA metric (SQuAD / RAG QA evaluation).
    """
    pred_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9._-]+", prediction)]
    gold_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9._-]+", ground_truth)]
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0

    common = set(pred_tokens) & set(gold_tokens)
    if not common:
        return 0.0

    prec = sum(min(pred_tokens.count(t), gold_tokens.count(t)) for t in common) / len(pred_tokens)
    rec = sum(min(pred_tokens.count(t), gold_tokens.count(t)) for t in common) / len(gold_tokens)

    if prec + rec == 0:
        return 0.0
    return 2.0 * (prec * rec) / (prec + rec)


def compute_evidence_grounding(answer: str, evidence_chunks: list[dict]) -> float:
    """
    Evidence Grounding / Faithfulness:
    Evaluates what fraction of sentences in the generated answer are grounded
    in (substantially supported by) the retrieved evidence passages.
    """
    # Remove citations before splitting
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if len(s.strip()) > 10]
    if not sentences:
        return 1.0

    combined_evidence = " ".join(c.get("text", "") for c in evidence_chunks).lower()
    if not combined_evidence:
        return 0.0

    grounded_count = 0
    for sent in sentences:
        # Strip citation markers like [1], [2] for content matching
        clean_sent = re.sub(r"\[\d+\]", "", sent).strip()
        words = [w.lower() for w in re.findall(r"[a-zA-Z0-9._-]+", clean_sent) if len(w) > 3]
        if not words:
            grounded_count += 1
            continue
        matched = sum(1 for w in words if w in combined_evidence)
        if matched / len(words) >= 0.5:
            grounded_count += 1

    return grounded_count / len(sentences)


def compute_citation_metrics(citations: list[dict], relevant_chunk_ids: set[str]) -> dict[str, float]:
    """
    Citation correctness:
    - citation_validity: fraction of citations pointing to valid retrieved chunks (no phantom citations)
    - citation_precision: fraction of citations pointing to ground-truth relevant chunks
    - citation_recall: fraction of relevant chunks that were cited in the answer
    """
    if not citations:
        return {"citation_validity": 1.0, "citation_precision": 0.0, "citation_recall": 0.0}

    valid_count = sum(1 for c in citations if c.get("is_valid", False))
    validity = valid_count / len(citations)

    if not relevant_chunk_ids:
        return {"citation_validity": validity, "citation_precision": 0.0, "citation_recall": 0.0}

    cited_cids = {c.get("chunk_id") for c in citations if c.get("is_valid", False)}
    true_positive_cids = cited_cids & relevant_chunk_ids
    precision = len(true_positive_cids) / len(cited_cids) if cited_cids else 0.0
    recall = len(true_positive_cids) / len(relevant_chunk_ids)

    return {
        "citation_validity": validity,
        "citation_precision": precision,
        "citation_recall": recall,
    }


def evaluate_abstention(is_abstention: bool, expected_abstention: bool) -> dict[str, bool]:
    """
    Evaluate abstention accuracy:
    - correct_decision: True if pipeline decision matched expectation
    - is_false_positive: answered when should have abstained
    - is_false_negative: abstained when should have answered
    """
    return {
        "correct_decision": (is_abstention == expected_abstention),
        "is_false_positive": (not is_abstention and expected_abstention),
        "is_false_negative": (is_abstention and not expected_abstention),
    }