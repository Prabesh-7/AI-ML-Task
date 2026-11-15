"""Two selectable chunking strategies."""
from enum import Enum


class ChunkStrategy(str, Enum):
    FIXED = "fixed"          # sliding window of characters with overlap
    PARAGRAPH = "paragraph"  # groups whole paragraphs up to a max size


def fixed_size_chunks(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into equal windows; overlap keeps context between chunks."""
    step = size - overlap
    chunks = [text[i : i + size].strip() for i in range(0, len(text), step)]
    return [c for c in chunks if c]


def paragraph_chunks(text: str, max_chars: int = 800) -> list[str]:
    """Merge paragraphs into chunks; oversized paragraphs fall back to fixed windows."""
    chunks: list[str] = []
    current = ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(fixed_size_chunks(para, size=max_chars, overlap=100))
        elif len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def chunk_text(text: str, strategy: ChunkStrategy) -> list[str]:
    if strategy is ChunkStrategy.FIXED:
        return fixed_size_chunks(text)
    return paragraph_chunks(text)
