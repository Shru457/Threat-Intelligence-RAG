# BM25, Hybrid Retrieval, Reranking & Evaluation (Day 4)

## BM25 retrieval
Implemented via `rank_bm25.BM25Okapi`, using a cybersecurity-aware
tokenizer (`backend/retrieval/bm25_search.py`) that preserves technical
identifiers (CVE IDs, MITRE ATT&CK IDs, hashes, IPs, domains,
filenames) as single tokens rather than splitting on punctuation.

## Semantic retrieval
Unchanged from Day 3 (`backend/retrieval/semantic_search.py`) — reused
directly by hybrid retrieval and the unified retriever interface.

## Hybrid retrieval
Combines semantic + BM25 candidates via Reciprocal Rank Fusion (RRF):
`score = sum(1 / (k + rank))` across every retriever that returned a
given chunk, with `k = 60`. Chosen over raw score addition because
BM25 and FAISS cosine-similarity scores are on incompatible scales.

## Reranking
A cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`, via
`sentence_transformers.CrossEncoder`) reorders the top `RERANK_CANDIDATE_K`
(default 20) hybrid candidates down to a final `RERANK_FINAL_K`
(default 5). This model is a general-domain relevance model (trained
on MS MARCO web-search data), NOT a cybersecurity-specific model —
this project evaluates its behavior when applied to CTI text.

## Retrieval evaluation
20 hand-labeled queries (`data/evaluation/retrieval_queries.json`)
spanning exact-identifier, behavioral, conceptual/paraphrased, and
report-specific query types. Relevance judgments (relevant chunk IDs,
optionally graded 0/1/2) were manually verified against the actual
processed chunks — never invented. The same query set and judgments
are run against all four methods (semantic, bm25, hybrid,
hybrid_rerank) in one evaluation pass (`scripts/evaluate_retrieval.py`)
for a fair, identical-protocol comparison.

## Configuration
All Day 4 settings centralized in `backend/retrieval/config.py`
alongside Day 3's settings: BM25 top-k, hybrid candidate-k, RRF
constant, reranker model/candidate-k/final-k, evaluation top-k values.

## Commands to run
- `python scripts/build_bm25_index.py` — build the BM25 index
- `python scripts/test_retrieval.py` — compare all 4 methods interactively
- `python scripts/evaluate_retrieval.py` — compute Recall/Precision/MRR/nDCG
- `python scripts/generate_evaluation_chart.py` — generate the comparison chart

## Evaluation methodology
Recall@{1,3,5,10}, Precision@{1,3,5,10}, MRR, and nDCG@5, computed
directly (see `evaluation/metrics.py`) against manually-verified
relevance judgments. Latency measured per method via wall-clock timing
around each retrieval call, averaged across all evaluation queries.

## Research experiment design
Four configurations compared under identical conditions (same corpus,
same 20 queries, same relevance judgments, same evaluation code):
A = semantic only, B = BM25 only, C = hybrid (A+B via RRF),
D = hybrid + reranking. This is the basis for an ablation-style
comparison — no configuration is assumed superior in advance; results
come only from actually running the experiment on this dataset.

## Limitations
- Only 20 evaluation queries — a small research-scale set, not a
  large-scale IR benchmark; results describe behavior on THIS corpus
  and query set, not general claims about BM25/semantic/hybrid
  retrieval overall.
- Relevance judgments were labeled manually by one person (project
  author) — no inter-annotator agreement was measured.
- The reranker is a general-domain (MS MARCO) model, not
  cybersecurity-specific.
- Latency numbers reflect one specific development machine, not a
  standardized benchmark environment.

## Reproducibility information
- BM25: rank_bm25 BM25Okapi, custom tokenizer (see bm25_search.py)
- Semantic: sentence-transformers/all-MiniLM-L6-v2, 384-dim, cosine via
  normalized inner product (Day 3)
- Hybrid: RRF, k=60, candidate_k=20 per retriever
- Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2, candidate_k=20, final_k=5
- Evaluation query file: data/evaluation/retrieval_queries.json
  (version-controlled; any future edits to relevance judgments should
  be noted in commit messages for traceability)