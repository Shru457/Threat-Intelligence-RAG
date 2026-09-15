import re


def clean_text(raw_text: str) -> str:
    """
    Clean raw extracted PDF text.

    Operations (all whitespace-only, content-preserving):
      1. Join words broken across a line wrap ("Cobalt\\nStrike" -> "Cobalt Strike").
      2. Collapse 3+ blank lines down to a single blank line.
      3. Collapse repeated spaces/tabs into a single space.
      4. Strip leading/trailing whitespace from the whole text.
    """
    text = raw_text

    # 1. Join hyphen-less line-wrapped words: a lowercase/uppercase letter,
    #    newline, then another letter -> replace the newline with a space.
    #    This fixes PDF line-wrap breaks without touching intentional
    #    paragraph breaks (which are followed by blank lines, handled below).
    text = re.sub(r"(?<=[a-zA-Z0-9])\n(?=[a-zA-Z0-9])", " ", text)

    # 2. Collapse 3+ consecutive newlines into exactly 2 (one blank line).
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 3. Collapse repeated spaces/tabs (but not newlines) into one space.
    text = re.sub(r"[ \t]{2,}", " ", text)

    # 4. Trim outer whitespace.
    text = text.strip()

    return text