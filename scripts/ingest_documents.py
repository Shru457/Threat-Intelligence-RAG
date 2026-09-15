"""
Entry point: run the full document ingestion pipeline.

Usage:
    python scripts/ingest_documents.py
"""

import json
import sys
from pathlib import Path

# Allow running this script directly (adds project root to the import path)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.ingestion.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    PROCESSED_OUTPUT_FILE,
)
from backend.ingestion.pdf_loader import load_pdf_pages
from backend.ingestion.text_cleaner import clean_text
from backend.ingestion.chunker import chunk_text
from backend.ingestion.metadata_builder import build_chunk_record


def make_document_id(pdf_path: Path) -> str:
    """Use the filename (without extension) as the document ID."""
    return pdf_path.stem


def make_document_title(document_id: str) -> str:
    """Turn a filename-style ID into a slightly more readable title."""
    return document_id.replace("_", " ").title()


def process_pdf(pdf_path: Path) -> list[dict]:
    """Run the full pipeline for a single PDF and return its chunk records."""
    document_id = make_document_id(pdf_path)
    document_title = make_document_title(document_id)

    print(f"\nProcessing: {pdf_path.name}")
    pages = load_pdf_pages(pdf_path)
    print(f"  Pages found: {len(pages)}")

    if not pages:
        print(f"  [WARNING] No pages extracted from {pdf_path.name}. Skipping.")
        return []

    records: list[dict] = []
    for page in pages:
        cleaned = clean_text(page.text)
        page_chunks = chunk_text(cleaned)

        for chunk_index, chunk_str in enumerate(page_chunks):
            record = build_chunk_record(
                document_id=document_id,
                document_title=document_title,
                page_number=page.page_number,
                chunk_index=chunk_index,
                text=chunk_str,
            )
            records.append(record)

    print(f"  Chunks generated: {len(records)}")
    return records


def main():
    print("=" * 60)
    print("Threat Intelligence RAG — Document Ingestion Pipeline")
    print("=" * 60)

    if not RAW_DATA_DIR.exists():
        print(f"[ERROR] Raw data directory not found: {RAW_DATA_DIR}")
        return

    pdf_files = sorted(RAW_DATA_DIR.glob("*.pdf"))
    print(f"\nPDF files found in {RAW_DATA_DIR}: {len(pdf_files)}")

    if not pdf_files:
        print("[ERROR] No PDF files found. Add reports to data/raw/ and rerun.")
        return

    all_records: list[dict] = []
    for pdf_path in pdf_files:
        try:
            records = process_pdf(pdf_path)
            all_records.extend(records)
        except Exception as exc:
            print(f"[ERROR] Failed to process {pdf_path.name}: {exc}")

    if not all_records:
        print("\n[ERROR] No chunks were generated from any document. Aborting save.")
        return

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\n" + "=" * 60)
    print(f"Done. Total chunks written: {len(all_records)}")
    print(f"Output file: {PROCESSED_OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()