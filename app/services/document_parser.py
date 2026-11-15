"""Extract raw text from uploaded files."""
import pymupdf


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text(filename: str, content: bytes) -> str:
    """Return text from a .pdf or .txt file."""
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            return "\n\n".join(page.get_text() for page in pdf)
    if lowered.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    raise UnsupportedFileTypeError("Only .pdf and .txt files are supported")
