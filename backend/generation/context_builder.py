"""
Context Construction & Citation Mapping Module.

Constructs evidence-aware prompt contexts from retrieved/reranked chunks,
enforces [1], [2] citation conventions, preserves technical cybersecurity
identifiers (CVEs, MITRE ATT&CK IDs, hashes, IPs, domains), and maps
citations back to full source metadata.
"""

import re
from typing import Any

# Regex patterns for key cybersecurity identifiers
CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
MITRE_TECHNIQUE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
IPV4_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
MD5_PATTERN = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA256_PATTERN = re.compile(r"\b[a-fA-F0-9]{64}\b")
DOMAIN_PATTERN = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")


def extract_cybersecurity_identifiers(text: str) -> dict[str, list[str]]:
    """
    Extract technical cybersecurity identifiers from a text passage.
    Returns a dictionary grouped by identifier category.
    """
    return {
        "cves": list(set(CVE_PATTERN.findall(text))),
        "mitre_techniques": list(set(MITRE_TECHNIQUE_PATTERN.findall(text))),
        "ips": list(set(IPV4_PATTERN.findall(text))),
        "sha256": list(set(SHA256_PATTERN.findall(text))),
        "md5": list(set(MD5_PATTERN.findall(text))),
    }


def build_evidence_context(
    retrieved_chunks: list[dict[str, Any]]
) -> tuple[str, dict[int, dict[str, Any]]]:
    """
    Format retrieved chunks into numbered evidence blocks with complete source metadata.

    Returns:
        context_str: Formatted text containing all evidence blocks.
        citation_map: Mapping from citation index (e.g. 1, 2) to the original chunk dict.
    """
    if not retrieved_chunks:
        return "No relevant evidence found in the threat intelligence reports.", {}

    blocks = []
    citation_map: dict[int, dict[str, Any]] = {}

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        citation_map[idx] = chunk
        doc_title = chunk.get("document_title", "Unknown Report")
        doc_id = chunk.get("document_id", "unknown_id")
        page = chunk.get("page_number", "?")
        chunk_id = chunk.get("chunk_id", f"chunk_{idx}")
        source = chunk.get("source", "local_pdf")
        score = chunk.get("score", 0.0)
        rank = chunk.get("rank", idx)
        text = chunk.get("text", "").strip()

        block = (
            f"[{idx}] Source Document: {doc_title} (ID: {doc_id}) | "
            f"Page: {page} | Chunk ID: {chunk_id} | Rank: {rank} | Score: {score:.4f} | Origin: {source}\n"
            f"Content:\n{text}"
        )
        blocks.append(block)

    context_str = "\n\n".join(blocks)
    return context_str, citation_map


def extract_citations(
    answer_text: str, citation_map: dict[int, dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Extract all citation references (e.g. [1], [2]) from the generated answer text
    and resolve them against the citation map.

    Returns a list of structured citation records.
    """
    citation_numbers = [int(m) for m in re.findall(r"\[(\d+)\]", answer_text)]
    # Preserve order of appearance, eliminate duplicates
    seen = set()
    unique_citations = []
    for num in citation_numbers:
        if num not in seen:
            seen.add(num)
            unique_citations.append(num)

    resolved_citations = []
    for num in unique_citations:
        if num in citation_map:
            chunk = citation_map[num]
            text_snippet = chunk.get("text", "")
            if len(text_snippet) > 200:
                text_snippet = text_snippet[:200] + "..."

            resolved_citations.append({
                "citation_id": num,
                "chunk_id": chunk.get("chunk_id", ""),
                "document_id": chunk.get("document_id", ""),
                "document_title": chunk.get("document_title", ""),
                "page_number": chunk.get("page_number", 0),
                "source": chunk.get("source", "local_pdf"),
                "rank": chunk.get("rank", num),
                "score": chunk.get("score", 0.0),
                "snippet": text_snippet,
                "is_valid": True,
            })
        else:
            # Referenced citation number not in evidence!
            resolved_citations.append({
                "citation_id": num,
                "chunk_id": "UNKNOWN",
                "document_id": "UNKNOWN",
                "document_title": "UNKNOWN",
                "page_number": 0,
                "source": "UNKNOWN",
                "rank": -1,
                "score": 0.0,
                "snippet": "",
                "is_valid": False,
            })

    return resolved_citations


def preserve_cybersecurity_identifiers(query: str, retrieved_chunks: list[dict]) -> list[str]:
    """
    Collect all cybersecurity identifiers (CVEs, MITRE IDs, etc.) present
    across the query and retrieved evidence passages.
    """
    all_text = query + " " + " ".join(c.get("text", "") for c in retrieved_chunks)
    found = extract_cybersecurity_identifiers(all_text)
    combined = []
    for category, items in found.items():
        combined.extend(items)
    return sorted(set(combined))
