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
    result = ask_json(prompt)
    
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
        kps = ", ".join(q["keypoints"])
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
    result = ask_json(prompt)
    
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
