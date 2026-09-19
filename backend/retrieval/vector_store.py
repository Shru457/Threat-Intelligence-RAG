"""
FAISS vector index construction, persistence, and the metadata mapping
that turns a FAISS result ID back into a full chunk record.

Design decision (deliberate, not incidental):
  We use faiss.IndexIDMap wrapping an IndexFlatIP index. Every vector is
  added with an EXPLICIT integer ID equal to its position in the
  metadata list at build time. That same ID is what FAISS returns on
  search. This means "FAISS ID 42" and "metadata[42]" are guaranteed to
  refer to the same chunk by construction, not by a fragile assumption
  about insertion order being preserved forever.
"""

import json

import faiss
import numpy as np

from .config import FAISS_INDEX_FILE, METADATA_FILE, VECTORSTORE_DIR, EMBEDDING_DIMENSION


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """
    L2-normalize each vector to unit length.

    Required for cosine similarity via inner product: cosine_sim(a, b)
    equals the plain dot product of a and b ONLY when both are unit
    vectors. Without this step, IndexFlatIP would compute a similarity
    that is influenced by vector magnitude, not just direction —
    which is not what we want for text similarity (see Day 3 Part 2,
    question 6-7 in docs/retrieval.md).
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12  # avoid division by zero for a degenerate all-zero vector
    return vectors / norms


def build_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS index from an (N, D) embedding matrix.

    Uses IndexFlatIP (inner product) over L2-normalized vectors, which
    is mathematically equivalent to exact cosine similarity search.
    Wrapped in IndexIDMap so every vector has an explicit, stable
    integer ID (its row position) rather than relying on implicit
    ordering.
    """
    if embeddings.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension {embeddings.shape[1]} does not match "
            f"configured EMBEDDING_DIMENSION={EMBEDDING_DIMENSION}. "
            f"Did the embedding model change without updating config.py?"
        )

    normalized = normalize_vectors(embeddings)
    base_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
    index = faiss.IndexIDMap(base_index)

    ids = np.arange(len(normalized)).astype("int64")
    index.add_with_ids(normalized, ids)
    return index


def save_index(index: faiss.Index, metadata: list[dict]) -> None:
    """Persist the FAISS index and its aligned metadata list to vectorstore/."""
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_index() -> tuple[faiss.Index, list[dict]]:
    """
    Load the FAISS index and metadata list from vectorstore/.

    Raises a clear, actionable error if either file is missing, rather
    than letting a cryptic low-level exception surface.
    """
    if not FAISS_INDEX_FILE.exists() or not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Vectorstore files not found at {VECTORSTORE_DIR}. "
            f"Run 'python scripts/build_vector_index.py' first."
        )

    index = faiss.read_index(str(FAISS_INDEX_FILE))
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if index.ntotal != len(metadata):
        raise ValueError(
            f"Vectorstore is inconsistent: FAISS index has {index.ntotal} "
            f"vectors but metadata.json has {len(metadata)} entries. "
            f"Rebuild the index with 'python scripts/build_vector_index.py'."
        )

    return index, metadata