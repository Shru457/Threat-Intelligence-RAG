# Semantic Retrieval (Day 3)

## Overview
Dense semantic retrieval baseline using sentence embeddings and FAISS,
built on top of Day 2's processed chunk output.

## Embedding model
- Name: sentence-transformers/all-MiniLM-L6-v2
- Output dimension: 384
- Runs locally on CPU, no API key required
- Chosen for speed, low RAM footprint, and status as a standard RAG baseline

## Similarity metric
Cosine similarity, implemented via L2-normalized vectors + FAISS
IndexFlatIP (inner product on unit vectors is mathematically equivalent
to cosine similarity).

## Index type
faiss.IndexFlatIP wrapped in faiss.IndexIDMap — exact (non-approximate)
search, with explicit sequential integer IDs assigned at build time.

## Metadata mapping design
metadata.json is a JSON array; array position i corresponds exactly to
FAISS vector ID i, by construction (chunks are embedded and indexed in
the same list order they are loaded from chunks.jsonl). This mapping is
regenerated every time scripts/build_vector_index.py runs — it is a
derived artifact, not a second source of truth. data/processed/chunks.jsonl
(from Day 2) remains the source of truth for chunk content and metadata.

## Persisted files
- vectorstore/index.faiss — the FAISS vector index (vectors + IDs only)
- vectorstore/metadata.json — full chunk records, aligned to FAISS IDs

## Configuration
All values centralized in backend/retrieval/config.py: model name,
embedding dimension, default top_k, batch size, and all file paths.

## How to build the index
`python scripts/build_vector_index.py`

## How to test retrieval interactively
`python scripts/test_semantic_search.py`

## Reproducibility notes
- Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- Similarity: cosine via L2-normalized inner product
- Index type: FAISS IndexFlatIP + IndexIDMap (exact search, no approximation)
- Chunk source: data/processed/chunks.jsonl (Day 2 output, 200-word
  chunks with 40-word overlap, per page)
- No random seeding is required: embedding inference for a frozen,
  pretrained model is deterministic given the same input text and model
  version; FAISS exact (Flat) search is likewise deterministic — there
  is no approximation or randomness in this baseline configuration.

## Known limitations
- Semantic-only retrieval: exact keyword/identifier matching (e.g. an
  exact CVE ID lookup) is not this component's strength — that is the
  motivation for Day 4's BM25/hybrid retrieval work.
- No reranking yet (Day 4/5).
- No relevance/quality evaluation yet (Day 6) — results are inspected
  manually for now.