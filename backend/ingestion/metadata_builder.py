"""
Builds the final metadata-attached dict for a single chunk.
"""


def build_chunk_record(
    document_id: str,
    document_title: str,
    page_number: int,
    chunk_index: int,
    text: str,
) -> dict:
    """
    Assemble the final structured record for one chunk, matching the
    metadata design in Day 2 Part 6 (required fields only for now).
    """
    chunk_id = f"{document_id}_p{page_number}_c{chunk_index}"

    return {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "document_title": document_title,
        "source": "local_pdf",
        "report_type": "unknown",  # best-effort placeholder; see Day 2 Part 6
        "page_number": page_number,
        "chunk_index": chunk_index,
        "text": text,
    }