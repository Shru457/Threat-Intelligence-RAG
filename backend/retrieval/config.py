"""
Centralized configuration for the semantic retrieval subsystem.

Mirrors the pattern used in backend/ingestion/config.py: every value
that might change between experiments (model choice, top_k, similarity
metric) lives here, not scattered through the pipeline code.
"""

from pathlib import Path

# --- Directories (relative to project root, same pattern as ingestion config) ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
FAISS_INDEX_FILE = VECTORSTORE_DIR / "index.faiss"
METADATA_FILE = VECTORSTORE_DIR / "metadata.json"

# --- Embedding model ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # output vector size for the model above

# --- Retrieval ---
DEFAULT_TOP_K = 5

# --- Similarity metric ---
# We use cosine similarity via normalized vectors + FAISS inner product
# (IndexFlatIP). See vector_store.py for the normalization step and
# docs/retrieval.md for the full explanation.
SIMILARITY_METRIC = "cosine_via_normalized_inner_product"

# --- Batching (for embedding generation) ---
EMBEDDING_BATCH_SIZE = 32