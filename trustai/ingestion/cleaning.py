"""Text cleaning.

PDF text extraction is messy: ligatures ("ﬁ"), words split across lines
("infor-\\nmation"), and runs of spaces. Clean text gives better embeddings and
cleaner citations later. We keep cleaning conservative: we never rewrite
meaning, only normalise formatting.
"""

from __future__ import annotations

import re
import unicodedata

_NULL_AND_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HYPHEN_LINEBREAK = re.compile(r"(?<=[A-Za-z])-\n(?=[a-z])")
_SPACES = re.compile(r"[ \t ]+")
_MANY_BLANK_LINES = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Normalise extracted text.

    Steps:
      1. Unicode NFKC: turns ligatures like 'ﬁ' into 'fi' and non-breaking spaces into spaces.
      2. Remove NUL and control characters (keeps newline and tab).
      3. Normalise line endings to '\\n'.
      4. Re-join words hyphenated across a line break ('infor-\\nmation' -> 'information').
         Only when the next line starts lowercase, so 'COVID-\\n19' style cases are untouched.
      5. Collapse repeated spaces, trim each line, collapse 3+ blank lines to one blank line.
    """
    text = unicodedata.normalize("NFKC", text)
    text = _NULL_AND_CONTROL.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_LINEBREAK.sub("", text)
    text = _SPACES.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _MANY_BLANK_LINES.sub("\n\n", text)
    return text.strip()
