"""
Centralized configuration for the retrieval subsystem: Day 3 semantic
retrieval settings plus Day 4 BM25 / hybrid / reranking / evaluation
settings, all in one place.
"""

from pathlib import Path

# --- Directories ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
FAISS_INDEX_FILE = VECTORSTORE_DIR / "index.faiss"
METADATA_FILE = VECTORSTORE_DIR / "metadata.json"
BM25_INDEX_FILE = VECTORSTORE_DIR / "bm25_index.pkl"  # NEW (Day 4)

EVALUATION_DIR = PROJECT_ROOT / "data" / "evaluation"
EVALUATION_QUERIES_FILE = EVALUATION_DIR / "retrieval_queries.json"  # NEW (Day 4)
EVALUATION_RESULTS_DIR = EVALUATION_DIR / "results"  # NEW (Day 4)

# --- Embedding model (Day 3) ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# --- Semantic retrieval (Day 3) ---
DEFAULT_TOP_K = 5
SIMILARITY_METRIC = "cosine_via_normalized_inner_product"
EMBEDDING_BATCH_SIZE = 32

# --- BM25 (Day 4, new) ---
BM25_TOP_K = 5

# --- Hybrid retrieval / RRF (Day 4, new) ---
HYBRID_CANDIDATE_K = 20   # candidates each of BM25/semantic contributes before fusion
RRF_K_CONSTANT = 60       # standard smoothing constant; see hybrid_search.py

# --- Reranking (Day 4, new) ---
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_CANDIDATE_K = 20   # candidates fed INTO the reranker
RERANK_FINAL_K = 5        # results kept AFTER reranking

# --- Evaluation (Day 4, new) ---
EVALUATION_TOP_K_VALUES = [1, 3, 5, 10]
NDCG_K = 5