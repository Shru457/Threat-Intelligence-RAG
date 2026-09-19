"""
Embedding generation using Sentence Transformers.

Loads the model once (module-level cache) so repeated calls within the
same process don't reload it from disk each time.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL_NAME, EMBEDDING_BATCH_SIZE

_model_cache: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it across calls."""
    global _model_cache
    if _model_cache is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        print("(First run downloads the model from the internet — this is normal.)")
        _model_cache = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model_cache


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts into an (N, D) numpy array of float32 vectors.

    Used for BOTH document chunks (at index-build time) and user
    queries (at search time) — using the same model for both is
    required, since a query and a document embedded by different
    models would not be comparable in the same vector space.
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")


def embed_single_text(text: str) -> np.ndarray:
    """Embed one piece of text (e.g. a user question) and return a 1D vector."""
    return embed_texts([text])[0]