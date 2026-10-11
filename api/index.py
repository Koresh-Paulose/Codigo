import os
import sys
import uuid
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi.staticfiles import StaticFiles

# Setup python import paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from db import get_db, Base, engine
import models
from models import Material

# Ensure tables are created
try:
    Base.metadata.create_all(bind=engine)
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

# -----------------
# 1. Status & Metrics
# -----------------
@app.get("/status")
@app.get("/api/status")
def get_status():
    return {"status": "ok", "app": "Protege AI Platform"}

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
    materials = db.query(Material).all()
    return {
        "materials": [
            {
                "id": m.id,
                "file_name": m.title or Path(m.file_path).name,
                "file_type": m.file_type,
                "word_count": m.word_count,
                "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at)
            }
            for m in materials
        ]
    }

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

    word_count = len(text.split())
    mat = Material(
        title=file.filename,
        file_type=ext.lstrip("."),
        file_path=str(saved_path),
        word_count=word_count
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)

    return {
        "id": mat.id,
        "file_name": mat.title,
        "word_count": mat.word_count,
        "status": "uploaded"
    }

# -----------------
# 3. Hint by Hint
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
            m = db.query(Material).filter(Material.id == req.material_id).first()
            if m:
                from features.materials.parser import extract_text
                source_chunk = extract_text(Path(m.file_path))
        except Exception as e:
            print(f"Error reading reference material: {e}")

    from features.hint_by_hint.ladder import get_next_hint
    res = get_next_hint(req.session_id, concept_id, source_chunk=source_chunk, user_last_answer=user_last_answer)
    if "error" in res:
        raise HTTPException(400, res["error"])
    return res

# -----------------
# 4. Teacher Mode
# -----------------
class StartSessionRequest(BaseModel):
    session_id: Optional[str] = None
    topic: Optional[str] = None
    material_id: Optional[Any] = None
    num_questions: Optional[int] = 5
    persona_type: Optional[str] = "novice"

@app.post("/api/start")
def start_teaching_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    from features.teach.student_agent.session import StudentSession
    from features.teach.student_agent.persona import StudentPersona

    session_id = req.session_id or uuid.uuid4().hex[:12]

    if req.topic:
        session = StudentSession(topic=req.topic.strip())
    elif req.material_id:
        m = db.query(Material).filter(Material.id == req.material_id).first()
        if not m:
            raise HTTPException(404, "Material not found")
        session = StudentSession(file_path=m.file_path)
    else:
        # Default topic if none provided
        session = StudentSession(topic="General Science")

    session.set_total_questions(max(1, req.num_questions or 5))
    session.persona = StudentPersona(persona_type=req.persona_type or "novice")
    session.metrics.target_questions = session.total_questions

    opening = session.start()
    sessions[session_id] = session

    return {
        "session_id": session_id,
        "total_questions": session.total_questions,
        "current_question_idx": 1,
        "current_concept": session.current_concept,
        "concepts": session.doc.concepts[:session.total_questions],
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
        raise HTTPException(404, "Session not found")

    msg = req.message.strip()
    if msg.lower() in ["/done", "/finish", "/quit", "/exit", "/stop", "quit", "exit", "done"]:
        final_rep = session.get_final_report()
        return {
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
# 5. Assessment
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
            print(f"Error researching topic: {e}")
            source_text = f"Topic: {req.topic}\nGeneral overview of {req.topic}."
    elif req.material_id:
        m = db.query(Material).filter(Material.id == req.material_id).first()
        if m:
            from features.materials.parser import extract_text
            try:
                source_text = extract_text(Path(m.file_path))
            except Exception as e:
                print(f"Error parsing file: {e}")

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
        raise HTTPException(404, "Exam session expired or not found.")

    from features.assessment.direct import grade_exam
    try:
        return grade_exam(exam_data, req.answers)
    except Exception as e:
        raise HTTPException(500, f"Failed to grade exam: {e}")

# Mount static frontend files for all other routes
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

