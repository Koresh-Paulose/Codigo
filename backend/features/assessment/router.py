import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models import StudySession, Concept, Turn, Score
from core.llm_client import ask_json
from .evaluator import evaluate
from .scoring import build_parts, combine

router = APIRouter(prefix="/session", tags=["assessment"])
EXAM_SIZE = 5
TRANSCRIPT_CHARS = 6000


class ExamBody(BaseModel):
    session_id: int


class ExamAnswer(BaseModel):
    question_id: int
    answer: str = ""


class FinishBody(BaseModel):
    session_id: int
    answers: list[ExamAnswer]


def _get_session(db: Session, session_id):
    s = db.get(StudySession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


def _exam_questions(db: Session, session_id):
    return (
        db.query(Turn)
        .filter_by(session_id=session_id, is_exam=True, role="student")
        .order_by(Turn.id)
        .all()
    )


def _generate_questions(db: Session, session, concepts):
    picked = concepts[:EXAM_SIZE]
    valid = {c.id for c in picked}
    block = "\n".join(f"[{c.id}] {c.name}: {c.summary}" for c in picked)
    questions = {}
    try:
        data = ask_json(f"""You are a curious student. For EACH concept below, write ONE question you would ask
your teacher that needs a real explanation in their own words (not yes/no).
Do not reveal or hint at the answer.

{block}

Return ONLY JSON: {{"questions": [{{"concept_id": 0, "question": "..."}}]}}""")
        for q in data.get("questions", []):
            cid, text = q.get("concept_id"), (q.get("question") or "").strip()
            if cid in valid and text and cid not in questions:
                questions[cid] = text
    except Exception:
        pass

    turns = []
    for c in picked:
        text = questions.get(c.id) or f"Can you explain {c.name} to me? I don't get it yet."
        t = Turn(
            session_id=session.id,
            role="student",
            content=text,
            concept_id=c.id,
            is_exam=True,
        )
        db.add(t)
        turns.append(t)
    db.commit()
    return turns


def _card(score: Score):
    raw_details = str(score.details) if score.details is not None else "{}"
    d = json.loads(raw_details)
    return {
        "session_id": score.session_id,
        "total": score.total,
        "parts": {
            "coverage": score.coverage,
            "accuracy": score.accuracy,
            "clarity": score.clarity,
            "flaw": score.flaw,
            "independence": score.independence,
        },
        "feedback": d.get("feedback", ""),
        "errors": d.get("errors", []),
        "missed_concepts": d.get("missed_concepts", []),
    }


@router.post("/exam")
def start_exam(body: ExamBody, db: Session = Depends(get_db)):
    s = _get_session(db, body.session_id)
    turns = _exam_questions(db, s.id)
    if not turns:
        concepts = db.query(Concept).filter_by(session_id=s.id).order_by(Concept.id).all()
        if not concepts:
            raise HTTPException(400, "This session has no concepts yet")
        turns = _generate_questions(db, s, concepts)
    return {
        "session_id": s.id,
        "questions": [
            {
                "question_id": t.id,
                "concept_id": t.concept_id,
                "question": t.content,
            }
            for t in turns
        ],
    }


@router.post("/finish")
def finish(body: FinishBody, db: Session = Depends(get_db)):
    s = _get_session(db, body.session_id)

    existing = db.query(Score).filter_by(session_id=s.id).first()
    if existing:
        return _card(existing)

    q_turns = _exam_questions(db, s.id)
    if not q_turns:
        raise HTTPException(400, "Start the exam first (POST /session/exam)")

    by_id = {t.id: t for t in q_turns}
    given = {}
    for a in body.answers:
        if a.question_id not in by_id:
            raise HTTPException(400, f"Unknown question_id {a.question_id}")
        given[a.question_id] = a.answer

    concepts = db.query(Concept).filter_by(session_id=s.id).all()
    chat = (
        db.query(Turn)
        .filter_by(session_id=s.id, is_exam=False)
        .order_by(Turn.id)
        .all()
    )
    transcript = "\n".join(
        f"{'TEACHER' if str(t.role) == 'user' else 'STUDENT'}: {t.content}" for t in chat
    )[-TRANSCRIPT_CHARS:]
    qa = [
        {
            "question_id": t.id,
            "concept_id": t.concept_id,
            "question": str(t.content),
            "answer": given.get(t.id, ""),
        }
        for t in q_turns
    ]

    try:
        ev = evaluate(
            concepts,
            str(s.flaw_claim) if s.flaw_claim is not None else "",
            str(s.flaw_truth) if s.flaw_truth is not None else "",
            transcript,
            qa,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(502, f"Grader error: {str(e)}")

    parts = build_parts(db, s.id, concepts, ev)
    total = combine(parts)
    errors = [e for p in ev["per_question"].values() for e in p["errors"]][:8]

    covered_set = set(ev["covered"])
    missed = [str(c.name) for c in concepts if c.id not in covered_set]

    for t in q_turns:
        db.add(
            Turn(
                session_id=s.id,
                role="user",
                content=given.get(t.id, ""),
                concept_id=t.concept_id,
                is_exam=True,
                reply_to=t.id,
            )
        )

    score = Score(
        session_id=s.id,
        total=total,
        **parts,
        details=json.dumps(
            {
                "feedback": ev["feedback"],
                "errors": errors,
                "missed_concepts": missed,
            }
        ),
    )
    db.add(score)
    setattr(s, "status", "finished")
    setattr(s, "finished_at", datetime.utcnow())
    db.commit()
    db.refresh(score)
    return _card(score)