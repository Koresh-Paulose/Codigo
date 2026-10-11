import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Material
from .parser import extract_text
from .store import save_material

router = APIRouter(prefix="/materials", tags=["materials"])

import os
# Resolves to /tmp/uploads on Vercel, or local uploads
UPLOAD_DIR = Path("/tmp/uploads") if os.environ.get("VERCEL") else Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED = {".pdf", ".docx", ".txt", ".md"}
MAX_BYTES = 10 * 1024 * 1024
MIN_WORDS = 30

def _summary(m: Material):
    return {"id": m.id, "title": m.title, "type": m.file_type,
            "words": m.word_count, "chunks": len(m.chunks),
            "created_at": m.created_at.isoformat()}

@router.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Allowed types: {', '.join(sorted(ALLOWED))}")
    
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 10 MB)")

    # Save file locally
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    path.write_bytes(data)
    
    # Process text
    try:
        text = extract_text(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise HTTPException(422, "Could not read this file")
        
    if len(text.split()) < MIN_WORDS:
        path.unlink(missing_ok=True)
        raise HTTPException(422, "No readable text found (scanned PDF?)")

    # Save to database
    return _summary(save_material(db, file.filename, ext.lstrip("."), str(path), text))