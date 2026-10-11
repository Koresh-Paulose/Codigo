from pathlib import Path
from models import Material, Chunk
from .chunker import chunk_text

def save_material(db, title, file_type, file_path, text, user_id="demo"):
    m = Material(user_id=user_id, title=title, file_type=file_type,
                 file_path=str(file_path), content=text, word_count=len(text.split()))
    m.chunks = [Chunk(position=i, text=c) for i, c in enumerate(chunk_text(text))]
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def get_chunks(db, material_id):
    return db.query(Chunk).filter_by(material_id=material_id).order_by(Chunk.position).all()

def get_material_text(db, material_id) -> str:
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return ""
    if m.content and m.content.strip():
        return m.content
    chunks = get_chunks(db, material_id)
    if chunks:
        return "\n\n".join(c.text for c in chunks)
    if m.file_path and Path(m.file_path).exists():
        from .parser import extract_text
        try:
            return extract_text(Path(m.file_path))
        except Exception:
            pass
    return ""