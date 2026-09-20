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