from models import Material, Chunk
from .chunker import chunk_text

def save_material(db, title, file_type, file_path, text, user_id="demo"):
    m = Material(user_id=user_id, title=title, file_type=file_type,
                 file_path=file_path, word_count=len(text.split()))
    m.chunks = [Chunk(position=i, text=c) for i, c in enumerate(chunk_text(text))]
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def get_chunks(db, material_id):
    return db.query(Chunk).filter_by(material_id=material_id).order_by(Chunk.position).all()