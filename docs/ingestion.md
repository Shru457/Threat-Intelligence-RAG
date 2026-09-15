# Document Ingestion Pipeline

## What document ingestion means
Converting raw threat intelligence PDF reports into structured, chunked
text with metadata, ready for embedding and retrieval.

## Supported input format
PDF files only, placed in `data/raw/`.

## Dataset organization
Filenames follow `<vendor>_<topic>_<year>.pdf` and become each
document's `document_id`.

## Extraction method
PyMuPDF (`fitz`), page-by-page, preserving 1-indexed page numbers.
Pages with fewer than 20 extracted characters are flagged as likely
scanned/image-only (OCR is not implemented yet).

## Cleaning method
Whitespace-only normalization: joins line-wrapped words, collapses
excess blank lines and repeated spaces. Never alters technical content
(CVE IDs, hashes, domains, IPs are preserved exactly).

## Chunking strategy
Fixed-size, word-count-based chunking, applied per page:
- Chunk size: 200 words
- Overlap: 40 words (20%)
Chosen as a standard, easily-tunable RAG baseline (see `backend/ingestion/config.py`).

## Metadata structure
Required fields: `chunk_id`, `document_id`, `document_title`, `source`,
`page_number`, `chunk_index`, `text`. `report_type` is included as a
best-effort placeholder. Threat-actor/malware/CVE-specific metadata
fields are future work, not yet implemented.

## Output format
JSONL, one chunk record per line, at `data/processed/chunks.jsonl`.

## How to run ingestion
`python scripts/ingest_documents.py`

## Known limitations
- No OCR: scanned/image-only PDFs will produce little/no text.
- No cross-page chunking: a chunk never spans two pages.
- No automatic entity extraction (threat actors, malware, CVEs are
  present in the text but not yet tagged as separate metadata fields).
- No header/footer/table-specific handling beyond PyMuPDF's default
  text-extraction mode.