from pathlib import Path
from pypdf import PdfReader
from docx import Document

MAX_PAGES = 50

def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:MAX_PAGES])
    if ext == ".docx":
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {ext}")