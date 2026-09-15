from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF


@dataclass
class PageText:
    """Raw text extracted from a single PDF page."""
    page_number: int  # 1-indexed, matches how a human would read the PDF
    text: str


def load_pdf_pages(pdf_path: Path, min_chars_per_page: int = 20) -> list[PageText]:
    """
    Open a PDF and extract text page by page.

    Args:
        pdf_path: path to the PDF file.
        min_chars_per_page: pages with fewer characters than this are
            still returned, but a warning is printed (likely a scanned/
            image-only page with no real extractable text).

    Returns:
        A list of PageText objects, one per page, in page order.
    """
    pages: list[PageText] = []

    with fitz.open(pdf_path) as doc:
        if doc.page_count == 0:
            print(f"[WARNING] {pdf_path.name}: PDF has zero pages.")
            return pages

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            raw_text = page.get_text("text")
            page_number = page_index + 1  # convert 0-indexed to 1-indexed

            if len(raw_text.strip()) < min_chars_per_page:
                print(
                    f"[WARNING] {pdf_path.name} page {page_number}: "
                    f"only {len(raw_text.strip())} characters extracted. "
                    f"Likely a scanned/image-only page (OCR not implemented yet)."
                )

            pages.append(PageText(page_number=page_number, text=raw_text))

    return pages