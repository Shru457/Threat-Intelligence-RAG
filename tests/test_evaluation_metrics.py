import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.metrics import recall_at_k, precision_at_k, reciprocal_rank, ndcg_at_k


def test_recall_at_k_basic():
    retrieved = ["a", "b", "c", "d", "e"]
    relevant = {"c", "z"}  # only "c" is actually in the top 5
    assert recall_at_k(retrieved, relevant, k=5) == 0.5


def test_precision_at_k_basic():
    retrieved = ["a", "b", "c", "d", "e"]
    relevant = {"a", "c"}
    assert precision_at_k(retrieved, relevant, k=5) == 2 / 5


def test_reciprocal_rank_basic():
    retrieved = ["x", "y", "z"]
    relevant = {"y"}
    assert reciprocal_rank(retrieved, relevant) == 0.5  # y is at rank 2


def test_reciprocal_rank_no_match():
    assert reciprocal_rank(["x", "y"], {"z"}) == 0.0


def test_ndcg_perfect_order_is_one():
    retrieved = ["a", "b"]
    grades = {"a": 2, "b": 1}
    assert ndcg_at_k(retrieved, grades, k=2) == 1.0


def test_ndcg_worse_order_is_less_than_one():
    retrieved = ["b", "a"]  # reversed from ideal
    grades = {"a": 2, "b": 1}
    assert ndcg_at_k(retrieved, grades, k=2) < 1.0