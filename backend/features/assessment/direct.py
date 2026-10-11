import json
from core.llm_client import ask_json

def generate_exam_from_text(text: str, num_questions: int = 5) -> dict:
    """Generate unique questions with expected keypoints from a text."""
    prompt = f"""You are an expert exam creator.
Based on the following text, create {num_questions} unique, insightful, and thought-provoking questions.
For each question, identify 3-5 specific 'keypoints' that must be mentioned in the answer for it to be considered fully correct.
The questions must test true understanding, not just memorization.

SOURCE TEXT:
{text[:15000]}

Return exactly this JSON format:
{{
    "questions": [
        {{
            "id": 1,
            "question": "What is...?",
            "keypoints": ["keypoint 1", "keypoint 2", "keypoint 3"]
        }}
    ]
}}
"""
    try:
        result = ask_json(prompt)
    except Exception as e:
        print(f"[generate_exam_from_text] LLM call failed ({e}). Generating fallback questions...")
        import re
        sentences = [s.strip() for s in re.split(r'[.\n]+', text) if len(s.strip()) > 25]
        questions = []
        for i in range(num_questions):
            s = sentences[i % len(sentences)] if sentences else "the core concepts in this study material"
            words = [w for w in re.findall(r'\b[A-Za-z]{4,}\b', s)]
            kps = words[:3] if len(words) >= 3 else ["understanding", "core mechanism", "application"]
            questions.append({
                "id": str(i + 1),
                "question": f"Based on the material, explain the mechanism and significance of: '{s[:80]}...'?",
                "keypoints": kps
            })
        result = {"questions": questions}
    
    # Assign unique string IDs to make UI binding easier
    import uuid
    for i, q in enumerate(result.get("questions", [])):
        q["id"] = uuid.uuid4().hex[:8]
    
    return result

def grade_exam(exam_data: dict, answers: dict) -> dict:
    """
    exam_data: {"questions": [{"id": "abc", "question": "...", "keypoints": [...]}]}
    answers: {"abc": "User's answer here"}
    """
    questions = exam_data.get("questions", [])
    
    qa_block = ""
    for q in questions:
        qid = q["id"]
        qtext = q["question"]
        kps = ", ".join(q.get("keypoints", []))
        ans = answers.get(qid, "").strip()
        
        qa_block += f"QUESTION ID: {qid}\n"
        qa_block += f"QUESTION: {qtext}\n"
        qa_block += f"REQUIRED KEYPOINTS: {kps}\n"
        qa_block += f"STUDENT ANSWER: {ans if ans else '(No answer provided)'}\n\n"

    prompt = f"""You are a strict but fair examiner grading a student's exam.
For each question, check if the student's answer captures the REQUIRED KEYPOINTS.
Assign a score from 0 to 10 for each question based on how many keypoints they hit and their overall understanding.
Also provide a 1-2 sentence constructive feedback for each question.

EXAM DATA:
{qa_block}

Return exactly this JSON format:
{{
    "results": [
        {{
            "id": "QUESTION_ID_HERE",
            "score": 8,
            "keypoints_hit": ["keypoint 1", "keypoint 2"],
            "keypoints_missed": ["keypoint 3"],
            "feedback": "Good answer, but you missed..."
        }}
    ],
    "overall_feedback": "Overall performance summary..."
}}
"""
    try:
        result = ask_json(prompt)
    except Exception as e:
        print(f"[grade_exam] LLM call failed ({e}). Using keypoint matching fallback...")
        results = []
        for q in questions:
            qid = q["id"]
            kps = q.get("keypoints", [])
            ans = answers.get(qid, "").lower()
            hit = [k for k in kps if k.lower() in ans]
            missed = [k for k in kps if k.lower() not in ans]
            score = int((len(hit) / max(1, len(kps))) * 10) if ans else 0
            results.append({
                "id": qid,
                "score": score,
                "keypoints_hit": hit,
                "keypoints_missed": missed,
                "feedback": f"Answer noted. Captured {len(hit)} of {len(kps)} required keypoints." if ans else "No answer provided."
            })
        result = {
            "results": results,
            "overall_feedback": "Evaluation completed based on keypoint mastery and core topic alignment."
        }
    
    # Calculate total score out of 100
    results = result.get("results", [])
    total_possible = len(questions) * 10
    total_earned = sum(r.get("score", 0) for r in results)
    
    percentage = int((total_earned / max(1, total_possible)) * 100)
    
    return {
        "percentage": percentage,
        "results": results,
        "overall_feedback": result.get("overall_feedback", "")
    }
