"""
Centralized configuration for the ingestion pipeline.

Keeping these values in one place means chunk size/overlap (a key
research variable) can be changed and re-run without touching any
pipeline logic.
"""

from pathlib import Path

# --- Directories ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_OUTPUT_FILE = PROCESSED_DATA_DIR / "chunks.jsonl"

# --- Extraction ---
MIN_CHARS_PER_PAGE = 20  # below this, a page is flagged as likely scanned/empty

# --- Chunking (experimental variables) ---
CHUNK_SIZE_WORDS = 200
CHUNK_OVERLAP_WORDS = 40

# --- Validation ---
MIN_CHUNK_WORDS = 10  # chunks shorter than this are dropped as noise