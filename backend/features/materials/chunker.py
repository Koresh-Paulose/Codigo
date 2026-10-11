def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = size - overlap
    chunks = []
    for i in range(0, len(words), step):
        chunks.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
    return chunks