import os
import sys
import uuid
import json
import base64
import re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

# Ensure UTF-8 output encoding if supported by terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .session import StudentSession
from .persona import StudentPersona
from .document_reader import DocumentReader
from .config import get_active_llm_mode

ROOT_DIR = Path(__file__).resolve().parents[4]
sys.path.append(str(ROOT_DIR))
FRONTEND_DIR = ROOT_DIR / "frontend"
SAMPLE_NOTES = Path(__file__).resolve().parent / "sample_notes.md"
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory session store
sessions: Dict[str, StudentSession] = {}
active_exams = {}

class ProtegeRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        # API Routes
        
        if self.path == "/api/metrics":
            return self._send_json({
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
            })

        if self.path == "/api/materials":
            sys.path.append(str(ROOT_DIR / "backend"))
            from db import get_db
            from models import Material
            try:
                db = next(get_db())
                materials = db.query(Material).all()
                res = [
                    {"id": m.id, "title": m.title, "type": m.file_type, "words": m.word_count}
                    for m in materials
                ]
                return self._send_json(res)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=500)

        if self.path == "/api/status":
            return self._send_json({
                "status": "ok",
                "active_llm_mode": get_active_llm_mode(),
            })

        # Static assets routing
        if self.path == "/" or not self.path:
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        parsed_path = self.path.split("?")[0]

        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type", "")

        # 1. API: Upload Document or Research Topic

        if parsed_path == "/api/materials/upload":
            if "multipart/form-data" in content_type:
                boundary_match = re.search(r"boundary=([^;]+)", content_type)
                if boundary_match:
                    boundary = boundary_match.group(1).strip().strip('"').encode("ascii")
                    body = self.rfile.read(content_length)
                    parts = body.split(b"--" + boundary)
                    filename = "doc"
                    for part in parts:
                        if b'name="file"' in part:
                            header_end = part.find(b"\r\n\r\n")
                            if header_end != -1:
                                headers_part = part[:header_end].decode("utf-8", errors="ignore")
                                fn_match = re.search(r'filename="([^"]+)"', headers_part)
                                if fn_match:
                                    filename = fn_match.group(1)
                                file_bytes = part[header_end + 4 :].rstrip(b"\r\n")
                                
                                ext = Path(filename).suffix.lower()
                                save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
                                save_path.write_bytes(file_bytes)
                                
                                sys.path.append(str(ROOT_DIR / "backend"))
                                from db import get_db
                                from features.materials.parser import extract_text
                                from features.materials.store import save_material
                                
                                try:
                                    text = extract_text(save_path)
                                    db = next(get_db())
                                    m = save_material(db, filename, ext.lstrip("."), str(save_path), text)
                                    return self._send_json({"id": m.id, "title": m.title, "words": m.word_count})
                                except Exception as e:
                                    return self._send_json({"error": str(e)}, status=500)
            return self._send_json({"error": "Invalid upload"}, status=400)

        if parsed_path in ["/api/upload", "/api/research_topic"]:
            target_path = None
            filename = "document"

            if "application/json" in content_type:
                raw_body = self.rfile.read(content_length)
                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                except Exception as e:
                    return self._send_json({"error": f"Invalid JSON payload: {e}"}, status=400)

                if payload.get("topic"):
                    topic_name = payload["topic"].strip()
                    try:
                        session_id = uuid.uuid4().hex[:12]
                        session = StudentSession(topic=topic_name)
                        sessions[session_id] = session
                        doc = session.doc
                        return self._send_json({
                            "session_id": session_id,
                            "file_name": doc.file_name,
                            "word_count": doc.word_count,
                            "concepts": doc.concepts,
                            "total_available_topics": len(doc.concepts),
                            "active_llm_mode": get_active_llm_mode(),
                            "is_topic": True,
                            "topic": topic_name,
                        })
                    except Exception as e:
                        return self._send_json({"error": f"Failed to research topic: {e}"}, status=500)

                elif payload.get("material_id"):
                    sys.path.append(str(ROOT_DIR / "backend"))
                    from db import get_db
                    from models import Material
                    db = next(get_db())
                    material = db.query(Material).filter(Material.id == payload["material_id"]).first()
                    if material:
                        target_path = material.file_path
                        filename = Path(target_path).name
                elif payload.get("use_sample"):
                    target_path = str(SAMPLE_NOTES)
                    filename = SAMPLE_NOTES.name
                elif payload.get("file_path"):
                    target_path = DocumentReader.sanitize_path(payload["file_path"])
                    filename = Path(target_path).name
                elif payload.get("file_data_base64"):
                    filename = payload.get("file_name", f"upload_{uuid.uuid4().hex[:6]}.pdf")
                    b64_data = payload["file_data_base64"]
                    if "," in b64_data:
                        b64_data = b64_data.split(",", 1)[1]
                    file_bytes = base64.b64decode(b64_data)
                    save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
                    save_path.write_bytes(file_bytes)
                    target_path = str(save_path)
            elif "multipart/form-data" in content_type:
                # Parse boundary
                boundary_match = re.search(r"boundary=([^;]+)", content_type)
                if boundary_match:
                    boundary = boundary_match.group(1).strip().strip('"').encode("ascii")
                    body = self.rfile.read(content_length)
                    parts = body.split(b"--" + boundary)
                    for part in parts:
                        if b'name="file"' in part:
                            header_end = part.find(b"\r\n\r\n")
                            if header_end != -1:
                                headers_part = part[:header_end].decode("utf-8", errors="ignore")
                                fn_match = re.search(r'filename="([^"]+)"', headers_part)
                                if fn_match:
                                    filename = fn_match.group(1)
                                file_bytes = part[header_end + 4 :].rstrip(b"\r\n")
                                save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
                                save_path.write_bytes(file_bytes)
                                target_path = str(save_path)
                                break

            if not target_path or not Path(target_path).exists():
                return self._send_json({"error": "No valid document or sample provided."}, status=400)

            try:
                session_id = uuid.uuid4().hex[:12]
                session = StudentSession(file_path=target_path)
                sessions[session_id] = session

                doc = session.doc
                return self._send_json({
                    "session_id": session_id,
                    "file_name": doc.file_name,
                    "word_count": doc.word_count,
                    "concepts": doc.concepts,
                    "total_available_topics": len(doc.concepts),
                    "active_llm_mode": get_active_llm_mode(),
                })
            except Exception as e:
                return self._send_json({"error": f"Failed to parse document: {str(e)}"}, status=500)

        # Hint by Hint API
        if parsed_path == "/api/hint":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                return self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
            session_id = payload.get("session_id")

            concept_id = payload.get("concept_id")
            material_id = payload.get("material_id")
            source_chunk = ""
            if material_id:
                sys.path.append(str(ROOT_DIR / "backend"))
                from db import get_db
                from models import Material
                from features.materials.parser import extract_text
                try:
                    db = next(get_db())
                    material = db.query(Material).filter(Material.id == material_id).first()
                    if material:
                        source_chunk = extract_text(Path(material.file_path))
                except Exception as e:
                    print("Error getting material for hint:", e)

            user_last_answer = payload.get("user_last_answer", "")
            from backend.features.hint_by_hint.ladder import get_next_hint
            res = get_next_hint(session_id, concept_id, source_chunk=source_chunk, user_last_answer=user_last_answer)
            if "error" in res:
                return self._send_json({"hint": res["error"], "level": res["level"]}, status=400)
            return self._send_json({"hint": res["hint"], "level": res["level"]})

        # 2. API: Start Session (Configure questions & persona)
        if parsed_path == "/api/start":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                return self._send_json({"error": f"Invalid JSON: {e}"}, status=400)

            session_id = payload.get("session_id")
            session = sessions.get(session_id)
            if not session:
                return self._send_json({"error": "Session not found. Please upload a document first."}, status=404)

            num_questions = int(payload.get("num_questions", 5))
            persona_type = payload.get("persona", "novice")

            session.set_total_questions(max(1, num_questions))
            session.persona = StudentPersona(persona_type=persona_type)
            session.metrics.target_questions = session.total_questions

            initial_opening = session.start()

            return self._send_json({
                "session_id": session_id,
                "total_questions": session.total_questions,
                "current_question_idx": 1,
                "current_concept": session.current_concept,
                "concepts": session.doc.concepts[:session.total_questions],
                "student_name": session.persona.name,
                "student_opening": initial_opening,
            })

        # 3. API: Step / Chat Answer
        if parsed_path == "/api/step" or parsed_path == "/api/chat":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                return self._send_json({"error": f"Invalid JSON: {e}"}, status=400)

            session_id = payload.get("session_id")
            message = payload.get("message", "").strip()

            session = sessions.get(session_id)
            if not session:
                return self._send_json({"error": "Session not found."}, status=404)

            # Early quit command
            if message.lower() in ["/done", "/finish", "/quit", "/exit", "/stop", "quit", "exit", "done"]:
                final_rep = session.get_final_report()
                return self._send_json({
                    "is_series_complete": True,
                    "concluded_early": True,
                    "student_reply": "Study session wrapped up early as requested! Here is your performance report.",
                    "final_report": final_rep,
                    "overall_score": session.metrics.overall_teaching_score,
                    "grade": session.metrics.grade,
                    "questions_completed": session.metrics.total_turns,
                    "total_questions": session.total_questions,
                })

            result = session.step(message)
            turn_metric_dict = result["turn_metric"].dict() if result.get("turn_metric") else None

            response_data = {
                "student_reply": result["student_reply"],
                "is_series_complete": result["is_series_complete"],
                "question_number": result.get("question_number", session.metrics.total_turns),
                "total_questions": session.total_questions,
                "current_concept": session.current_concept,
                "mastered_concepts": session.metrics.mastered_concepts,
                "pending_concepts": session.metrics.pending_concepts,
                "turn_metric": turn_metric_dict,
                "overall_score": session.metrics.overall_teaching_score,
                "grade": session.metrics.grade,
                "final_report": session.get_final_report() if result["is_series_complete"] else None,
            }
            return self._send_json(response_data)

        # 4. API: Retest Session
        if parsed_path == "/api/retest":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                payload = {}

            session_id = payload.get("session_id")
            session = sessions.get(session_id)
            if not session:
                return self._send_json({"error": "Session not found."}, status=404)

            new_q = session.retest()
            return self._send_json({
                "student_opening": new_q,
                "total_questions": session.total_questions,
                "current_question_idx": 1,
                "current_concept": session.current_concept,
            })

        # 5. API: Final Report
        if parsed_path == "/api/report":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                payload = {}

            session_id = payload.get("session_id")
            session = sessions.get(session_id)
            if not session:
                return self._send_json({"error": "Session not found."}, status=404)

            return self._send_json({
                "final_report": session.get_final_report(),
                "overall_score": session.metrics.overall_teaching_score,
                "grade": session.metrics.grade,
                "total_turns": session.metrics.total_turns,
                "target_questions": session.metrics.target_questions,
                "turn_history": [t.dict() for t in session.metrics.turn_history],
            })

        # 6. API: Assessment Exam (Generate)
        if parsed_path == "/api/exam" or parsed_path == "/api/exam/generate":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                payload = {}

            topic = payload.get("topic", "").strip()
            material_id = payload.get("material_id")
            num_questions = int(payload.get("num_questions", 3))

            source_text = ""
            if topic:
                from features.teach.student_agent.topic_researcher import TopicResearcher
                try:
                    doc = TopicResearcher.research_topic(topic)
                    source_text = doc.content
                except Exception as e:
                    print(f"Error researching topic: {e}")
                    source_text = f"Topic: {topic}\nGeneral overview of {topic}."
            elif material_id:
                sys.path.append(str(ROOT_DIR / "backend"))
                from db import get_db
                from models import Material
                from features.materials.parser import extract_text
                try:
                    db = next(get_db())
                    material = db.query(Material).filter(Material.id == material_id).first()
                    if material:
                        source_text = extract_text(Path(material.file_path))
                except Exception as e:
                    print(f"Error reading material: {e}")

            if not source_text:
                return self._send_json({"error": "No content found for the selected topic or material."}, status=400)

            from features.assessment.direct import generate_exam_from_text
            try:
                exam_data = generate_exam_from_text(source_text, num_questions=num_questions)
                exam_id = uuid.uuid4().hex[:12]
                active_exams[exam_id] = exam_data
                
                # Return only public question info to the client
                client_questions = [{"id": q["id"], "question": q["question"]} for q in exam_data.get("questions", [])]
                return self._send_json({
                    "exam_id": exam_id,
                    "questions": client_questions
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json({"error": f"Failed to generate exam: {e}"}, status=500)

        # 7. API: Assessment Finish (Grade)
        if parsed_path == "/api/finish" or parsed_path == "/api/exam/grade":
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                payload = {}

            exam_id = payload.get("exam_id")
            answers = payload.get("answers", {})

            exam_data = active_exams.get(exam_id)
            if not exam_data:
                return self._send_json({"error": "Exam session expired or not found."}, status=404)

            from features.assessment.direct import grade_exam
            try:
                grade_report = grade_exam(exam_data, answers)
                return self._send_json(grade_report)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json({"error": f"Failed to grade exam: {e}"}, status=500)

        self.send_error(404, "Endpoint not found")

def run_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ProtegeRequestHandler)
    print("\n" + "="*70)
    print(" [PROTEGE]: AI STUDENT TEACHING PLATFORM")
    print(f" Web Interface live at: http://localhost:{port}")
    print(" Press Ctrl+C to stop the server.")
    print("="*70 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Protege Web Server...")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
