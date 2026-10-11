import os
import sys
import uuid
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

# Setup python import paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from db import get_db, Base, engine, is_postgres
import models
from models import Material
from features.materials.store import save_material, get_material_text
from features.teach.student_agent.config import get_active_llm_mode

# Ensure tables are created in Neon Postgres / SQLite
try:
    Base.metadata.create_all(bind=engine)
    # Ensure content column exists on materials table for existing databases
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE materials ADD COLUMN content TEXT"))
        except Exception:
            pass
except Exception as e:
    print(f"Database initialization note: {e}")

app = FastAPI(title="Protégé Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (scoped to lambda instance)
sessions: Dict[str, Any] = {}
active_exams: Dict[str, Any] = {}

UPLOAD_DIR = Path("/tmp/uploads") if os.environ.get("VERCEL") else BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_NOTES = BACKEND_DIR / "features" / "teach" / "student_agent" / "sample_notes.md"


def _material_to_dict(m: Material) -> Dict[str, Any]:
    file_name = m.title or (Path(m.file_path).name if m.file_path else "Untitled Document")
    file_type = m.file_type or "doc"
    return {
        "id": m.id,
        "title": file_name,
        "file_name": file_name,
        "type": file_type,
        "file_type": file_type,
        "words": m.word_count or 0,
        "word_count": m.word_count or 0,
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
    }


def _ensure_material_file(db: Session, material_id: Any) -> Optional[Path]:
    """Ensures a material file is available locally in /tmp on serverless."""
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return None
    if m.file_path and Path(m.file_path).exists():
        return Path(m.file_path)

    # Recover text from database (content or chunks) and write to /tmp
    text_content = get_material_text(db, m.id)
    if not text_content:
        return None

    safe_title = "".join(c for c in (m.title or "material") if c.isalnum() or c in "._- ")
    target_path = UPLOAD_DIR / f"{m.id}_{safe_title}"
    if not target_path.suffix:
        target_path = target_path.with_suffix(".txt")
    target_path.write_text(text_content, encoding="utf-8")
    return target_path


# -----------------
# 1. Status & Metrics
# -----------------
@app.get("/status")
@app.get("/api/status")
def get_status():
    return {
        "status": "ok",
        "app": "Protege AI Platform",
        "active_llm_mode": get_active_llm_mode(),
        "database": "Neon PostgreSQL" if is_postgres else "SQLite",
    }


@app.get("/metrics")
@app.get("/api/metrics")
def get_metrics():
    return {
        "modes_distribution": {
            "Teacher Mode": 8,
            "Hint by Hint": 4
        },
        "mastery_scores": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "accuracy": [60, 65, 75, 70, 85, 90, 95],
            "clarity": [50, 55, 60, 75, 80, 85, 90]
        },
        "streak_days": 3,
        "total_sessions": 12
    }


# -----------------
# 2. Materials
# -----------------
@app.get("/api/materials")
def list_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).order_by(Material.created_at.desc()).all()
    # Return array directly so frontend forEach works, with properties for both schemas
    return [_material_to_dict(m) for m in materials]


@app.post("/api/materials/upload")
async def upload_material(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower()
    allowed = {".pdf", ".docx", ".txt", ".md"}
    if ext not in allowed:
        raise HTTPException(400, f"Allowed types: {', '.join(sorted(allowed))}")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 10 MB)")

    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file.filename}"
    saved_path.write_bytes(data)

    from features.materials.parser import extract_text
    try:
        text = extract_text(saved_path)
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(422, f"Could not read file: {e}")

    mat = save_material(db, file.filename or "Uploaded Note", ext.lstrip("."), str(saved_path), text)

    res = _material_to_dict(mat)
    res["status"] = "uploaded"
    return res


# -----------------
# 3. Document / Topic Upload for Teaching Session
# -----------------
@app.post("/api/research_topic")
async def research_topic_endpoint(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    topic_name = (payload.get("topic") or "").strip()
    if not topic_name:
        raise HTTPException(400, "Topic name cannot be empty")

    from features.teach.student_agent.session import StudentSession
    try:
        session_id = uuid.uuid4().hex[:12]
        session = StudentSession(topic=topic_name)
        sessions[session_id] = session
        doc = session.doc
        return {
            "session_id": session_id,
            "file_name": doc.file_name,
            "word_count": doc.word_count,
            "concepts": doc.concepts,
            "total_available_topics": len(doc.concepts),
            "active_llm_mode": get_active_llm_mode(),
            "is_topic": True,
            "topic": topic_name,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to research topic: {e}")


@app.post("/api/upload")
async def general_upload_endpoint(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    target_path = None
    file_display_name = "document"

    from features.teach.student_agent.session import StudentSession

    # 1. Handle JSON Payloads
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(400, "Invalid JSON payload")

        # Case A: Topic Research
        if payload.get("topic"):
            topic_name = payload["topic"].strip()
            try:
                session_id = uuid.uuid4().hex[:12]
                session = StudentSession(topic=topic_name)
                sessions[session_id] = session
                doc = session.doc
                return {
                    "session_id": session_id,
                    "file_name": doc.file_name,
                    "word_count": doc.word_count,
                    "concepts": doc.concepts,
                    "total_available_topics": len(doc.concepts),
                    "active_llm_mode": get_active_llm_mode(),
                    "is_topic": True,
                    "topic": topic_name,
                }
            except Exception as e:
                raise HTTPException(500, f"Failed to research topic: {e}")

        # Case B: Sample Notes
        elif payload.get("use_sample"):
            if SAMPLE_NOTES.exists():
                target_path = SAMPLE_NOTES
                file_display_name = SAMPLE_NOTES.name
            else:
                # Create fallback sample note
                target_path = UPLOAD_DIR / "sample_notes.md"
                target_path.write_text("# Transformers & Self-Attention\n\nTransformers use self-attention to weigh the significance of each token relative to all other tokens.", encoding="utf-8")
                file_display_name = "sample_notes.md"

        # Case C: Material ID from Neon / SQLite Database
        elif payload.get("material_id"):
            recovered_path = _ensure_material_file(db, payload["material_id"])
            if not recovered_path or not recovered_path.exists():
                raise HTTPException(404, "Selected study material could not be loaded from database.")
            target_path = recovered_path
            file_display_name = recovered_path.name

        # Case D: Base64 Upload
        elif payload.get("file_data_base64"):
            file_display_name = payload.get("file_name", f"upload_{uuid.uuid4().hex[:6]}.txt")
            b64_data = payload["file_data_base64"]
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            try:
                file_bytes = base64.b64decode(b64_data)
            except Exception as e:
                raise HTTPException(400, f"Invalid base64 payload: {e}")

            save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file_display_name}"
            save_path.write_bytes(file_bytes)
            target_path = save_path

            # Also persist in database
            ext = save_path.suffix.lower()
            from features.materials.parser import extract_text
            try:
                parsed_text = extract_text(save_path)
                save_material(db, file_display_name, ext.lstrip("."), str(save_path), parsed_text)
            except Exception:
                pass

    # 2. Handle Multipart Form Data Upload
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file:
            raise HTTPException(400, "No file provided in form data")

        file_display_name = uploaded_file.filename or "upload.txt"
        file_bytes = await uploaded_file.read()
        save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file_display_name}"
        save_path.write_bytes(file_bytes)
        target_path = save_path

        # Persist to database
        ext = save_path.suffix.lower()
        from features.materials.parser import extract_text
        try:
            parsed_text = extract_text(save_path)
            save_material(db, file_display_name, ext.lstrip("."), str(save_path), parsed_text)
        except Exception:
            pass
    else:
        raise HTTPException(400, f"Unsupported Content-Type: {content_type}")

    if not target_path or not Path(target_path).exists():
        raise HTTPException(400, "No valid document or sample available.")

    try:
        session_id = uuid.uuid4().hex[:12]
        session = StudentSession(file_path=str(target_path))
        sessions[session_id] = session
        doc = session.doc
        return {
            "session_id": session_id,
            "file_name": doc.file_name,
            "word_count": doc.word_count,
            "concepts": doc.concepts,
            "total_available_topics": len(doc.concepts),
            "active_llm_mode": get_active_llm_mode(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to parse document: {e}")


# -----------------
# 4. Hint by Hint
# -----------------
class HintRequest(BaseModel):
    session_id: Optional[str] = "default_session"
    concept: Optional[str] = ""
    concept_id: Optional[str] = None
    user_answer: Optional[str] = ""
    material_id: Optional[Any] = None


@app.post("/api/hint")
def post_hint(req: HintRequest, db: Session = Depends(get_db)):
    concept_id = req.concept_id or req.concept or "General Concept"
    user_last_answer = req.user_answer or ""
    source_chunk = ""

    if req.material_id:
        try:
            source_chunk = get_material_text(db, req.material_id)
        except Exception as e:
            print(f"Error reading reference material for hint: {e}")

    from features.hint_by_hint.ladder import get_next_hint
    res = get_next_hint(req.session_id, concept_id, source_chunk=source_chunk, user_last_answer=user_last_answer)

    if "error" in res and not res.get("hint"):
        return JSONResponse(
            status_code=400,
            content={
                "error": res["error"],
                "detail": res["error"],
                "hint": res.get("hint", ""),
                "level": res.get("level", 0)
            }
        )
    return {
        "hint": res.get("hint", ""),
        "level": res.get("level", 1)
    }


# -----------------
# 5. Teacher Mode
# -----------------
class StartSessionRequest(BaseModel):
    session_id: Optional[str] = None
    topic: Optional[str] = None
    material_id: Optional[Any] = None
    num_questions: Optional[int] = 5
    persona: Optional[str] = None
    persona_type: Optional[str] = None


@app.post("/api/start")
def start_teaching_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    from features.teach.student_agent.session import StudentSession
    from features.teach.student_agent.persona import StudentPersona

    session_id = req.session_id or uuid.uuid4().hex[:12]
    session = sessions.get(session_id)

    if not session:
        if req.topic:
            session = StudentSession(topic=req.topic.strip())
        elif req.material_id:
            recovered_path = _ensure_material_file(db, req.material_id)
            if not recovered_path or not recovered_path.exists():
                raise HTTPException(404, "Material not found in database")
            session = StudentSession(file_path=str(recovered_path))
        else:
            session = StudentSession(topic="General Science")

    chosen_persona = req.persona or req.persona_type or "novice"
    session.set_total_questions(max(1, req.num_questions or 5))
    session.persona = StudentPersona(persona_type=chosen_persona)
    session.metrics.target_questions = session.total_questions

    opening = session.start()
    sessions[session_id] = session

    return {
        "session_id": session_id,
        "total_questions": session.total_questions,
        "current_question_idx": 1,
        "current_concept": session.current_concept,
        "concepts": session.doc.concepts[:session.total_questions] if session.doc else [],
        "student_name": session.persona.name,
        "student_opening": opening,
    }


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/api/chat")
@app.post("/api/step")
def chat_step(req: ChatRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Please start a session first.")

    msg = req.message.strip()
    if msg.lower() in ["/done", "/finish", "/quit", "/exit", "/stop", "quit", "exit", "done"]:
        final_rep = session.get_final_report()
        return {
            "is_series_complete": True,
            "concluded_early": True,
            "student_reply": "Study session wrapped up early as requested! Here is your performance report.",
            "final_report": final_rep,
            "overall_score": session.metrics.overall_teaching_score,
            "grade": session.metrics.grade,
            "questions_completed": session.metrics.total_turns,
            "total_questions": session.total_questions,
        }

    result = session.step(msg)
    turn_metric = result["turn_metric"].dict() if result.get("turn_metric") else None

    return {
        "student_reply": result["student_reply"],
        "is_series_complete": result["is_series_complete"],
        "question_number": result.get("question_number", session.metrics.total_turns),
        "total_questions": session.total_questions,
        "current_concept": session.current_concept,
        "mastered_concepts": session.metrics.mastered_concepts,
        "pending_concepts": session.metrics.pending_concepts,
        "turn_metric": turn_metric,
        "overall_score": session.metrics.overall_teaching_score,
        "grade": session.metrics.grade,
        "final_report": session.get_final_report() if result["is_series_complete"] else None,
    }


class SessionIdOnlyRequest(BaseModel):
    session_id: str


@app.post("/api/retest")
def session_retest(req: SessionIdOnlyRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    new_q = session.retest()
    return {
        "student_opening": new_q,
        "total_questions": session.total_questions,
        "current_question_idx": 1,
        "current_concept": session.current_concept,
    }


@app.post("/api/report")
def session_report(req: SessionIdOnlyRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    return {
        "final_report": session.get_final_report(),
        "overall_score": session.metrics.overall_teaching_score,
        "grade": session.metrics.grade,
        "total_turns": session.metrics.total_turns,
        "target_questions": session.metrics.target_questions,
        "turn_history": [t.dict() for t in session.metrics.turn_history],
    }


# -----------------
# 6. Assessment Mode
# -----------------
class ExamGenerateRequest(BaseModel):
    topic: Optional[str] = ""
    material_id: Optional[Any] = None
    num_questions: Optional[int] = 3


@app.post("/api/exam")
@app.post("/api/exam/generate")
def generate_exam(req: ExamGenerateRequest, db: Session = Depends(get_db)):
    source_text = ""

    if req.topic and req.topic.strip():
        from features.teach.student_agent.topic_researcher import TopicResearcher
        try:
            doc = TopicResearcher.research_topic(req.topic.strip())
            source_text = doc.content
        except Exception as e:
            print(f"Error researching topic for exam: {e}")
            source_text = f"Topic: {req.topic}\nGeneral overview of {req.topic}."
    elif req.material_id:
        source_text = get_material_text(db, req.material_id)

    if not source_text:
        raise HTTPException(400, "No content found for the selected topic or material.")

    from features.assessment.direct import generate_exam_from_text
    try:
        exam_data = generate_exam_from_text(source_text, num_questions=req.num_questions or 3)
        exam_id = uuid.uuid4().hex[:12]
        active_exams[exam_id] = exam_data

        client_questions = [{"id": q["id"], "question": q["question"]} for q in exam_data.get("questions", [])]
        return {
            "exam_id": exam_id,
            "questions": client_questions
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to generate exam: {e}")


class ExamGradeRequest(BaseModel):
    exam_id: str
    answers: Dict[str, str]


@app.post("/finish")
@app.post("/api/finish")
@app.post("/exam/grade")
@app.post("/api/exam/grade")
def grade_exam_route(req: ExamGradeRequest):
    exam_data = active_exams.get(req.exam_id)
    if not exam_data:
        raise HTTPException(404, "Exam session expired or not found. Please regenerate an exam.")

    from features.assessment.direct import grade_exam
    try:
        return grade_exam(exam_data, req.answers)
    except Exception as e:
        raise HTTPException(500, f"Failed to grade exam: {e}")


# Mount static frontend files for all other routes
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
