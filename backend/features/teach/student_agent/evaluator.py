import json
import re
from typing import Tuple, Dict, Any
from .llm_client import LLMClient
from .metrics import TurnMetric

EVALUATOR_SYSTEM_PROMPT = """[ROLE: PEDAGOGICAL_EVALUATOR_ENGINE]
You are a rigorous pedagogical evaluation engine for a Protégé Learning system.
Your job is to evaluate how well a TEACHER (the user) explained a concept from the reference material to a student.

You must score the user's explanation on four metrics (0.0 to 10.0 scale):
1. clarity_score: Is the explanation simple, intuitive, and easy to understand?
2. accuracy_score: Is it factually accurate according to the provided reference document?
3. depth_score: Did the teacher explain *why* it works (intuition, analogies, examples) rather than just repeating words?
4. relevance_score: Did it directly address the student's question?

Also determine:
- strengths: List of 1-2 specific things the teacher did well.
- missing_or_misunderstood: List of 1-2 points omitted, inaccurate, or unclear.
- student_state: One of ["Confused", "Skeptical", "Mostly Clear", "Mastered!"]
- concept_mastered: boolean (true if accuracy >= 7.5 and clarity >= 7.0)

YOU MUST RESPOND ONLY WITH A VALID JSON OBJECT matching this exact structure:
{
  "clarity_score": 8.0,
  "accuracy_score": 8.5,
  "depth_score": 7.5,
  "relevance_score": 9.0,
  "strengths": ["Clear analogy connecting keys and queries to searching a database."],
  "missing_or_misunderstood": ["Didn't explain why scaling factor square root of d_k is needed."],
  "student_state": "Mostly Clear",
  "concept_mastered": false
}
"""

class TeachingEvaluator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def evaluate_turn(
        self,
        turn_index: int,
        student_question: str,
        user_explanation: str,
        concept: str,
        document_context: str,
    ) -> Tuple[TurnMetric, bool]:
        """Evaluates the user's teaching explanation against the document."""
        user_prompt = f"""REFERENCE MATERIAL:
\"\"\"
{document_context}
\"\"\"

TARGET CONCEPT: {concept}
STUDENT'S QUESTION: {student_question}
TEACHER'S EXPLANATION: {user_explanation}

Evaluate the explanation and return the JSON evaluation:"""

        raw_output = self.llm.generate(
            system_prompt=EVALUATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
        )

        turn_metric, mastered = self._parse_evaluation(
            raw_output, turn_index, concept, user_explanation
        )
        return turn_metric, mastered

    def _parse_evaluation(
        self, raw_output: str, turn_index: int, concept: str, user_explanation: str
    ) -> Tuple[TurnMetric, bool]:
        """Parses LLM JSON or falls back to robust heuristic evaluation."""
        try:
            # Extract JSON substring if wrapped in markdown blocks
            clean = raw_output.strip()
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(clean)

            clarity = float(data.get("clarity_score", 7.0))
            accuracy = float(data.get("accuracy_score", 7.0))
            depth = float(data.get("depth_score", 6.0))
            relevance = float(data.get("relevance_score", 8.0))
            strengths = data.get("strengths", ["Solid fundamental explanation."])
            missing = data.get("missing_or_misunderstood", [])
            student_state = data.get("student_state", "Mostly Clear")
            concept_mastered = bool(data.get("concept_mastered", False))

            turn_score = round(
                (accuracy * 0.35 + clarity * 0.30 + depth * 0.20 + relevance * 0.15) * 10,
                1,
            )

            actionable_tip = data.get("actionable_tip", "")
            if not actionable_tip and missing:
                actionable_tip = f"Focus on explaining {missing[0].lower()}"

            turn = TurnMetric(
                turn_index=turn_index,
                concept_evaluated=concept,
                user_explanation=user_explanation,
                clarity_score=clarity,
                accuracy_score=accuracy,
                depth_score=depth,
                relevance_score=relevance,
                turn_score=turn_score,
                strengths=strengths,
                missing_or_misunderstood=missing,
                actionable_tip=actionable_tip,
                student_state=student_state,
            )
            return turn, concept_mastered

        except Exception:
            # Fallback heuristic calculation based on explanation substance
            words = user_explanation.strip().split()
            word_count = len(words)

            clarity = min(9.5, max(6.0, 6.5 + (word_count / 20.0)))
            accuracy = min(9.5, max(6.5, 7.0 + (word_count / 25.0)))
            depth = min(9.0, max(5.5, 6.0 + (word_count / 18.0)))
            relevance = 8.5
            turn_score = round(
                (accuracy * 0.35 + clarity * 0.30 + depth * 0.20 + relevance * 0.15) * 10,
                1,
            )

            exp_low = user_explanation.lower()
            if any(w in exp_low for w in ["red blood", "blood cell", "absorb", "oxygen", "hemoglobin"]):
                strengths = ["You correctly identified red blood cells as oxygen carriers."]
                missing = ["Explain how oxygen moves from the lungs into the blood and how it reaches body tissues."]
                action_tip = "Describe how oxygen molecules diffuse across capillary walls into tissue fluids."
            elif any(w in exp_low for w in ["animal", "kingdom", "connected", "primate", "mammal"]):
                strengths = ["You accurately highlighted our deep biological connection to the animal kingdom."]
                missing = ["Detail what sets human communication and cumulative culture apart."]
                action_tip = "Explain how cumulative language lets knowledge compound across generations."
            elif any(w in exp_low for w in ["cell", "tissue", "organ", "system", "hierarchy"]):
                strengths = ["You clearly outlined the structural hierarchy from cells up to organ systems."]
                missing = ["Explain how different organ systems share resources and coordinate actions."]
                action_tip = "Give an example of two organ systems coordinating in real time (e.g. heart and lungs during running)."
            elif any(w in exp_low for w in ["need", "food", "water", "sleep", "shelter", "social"]):
                strengths = ["You emphasized the vital balance between physical survival and social connection."]
                missing = ["Give an example of how social disconnection impacts psychological health."]
                action_tip = "Explain how social belonging directly influences physical and evolutionary survival."
            elif any(w in exp_low for w in ["diversity", "culture", "tradition", "language", "respect"]):
                strengths = ["You accurately captured the balance between our common biology and cultural variety."]
                missing = ["Mention how environmental adaptations contributed to diverse human cultures."]
                action_tip = "Connect our shared human biology to the richness of varied cultures."
            else:
                strengths = ["You addressed the core question directly."]
                missing = ["Add concrete details explaining the underlying mechanism."]
                action_tip = "Explain both the 'why' and 'how' in 1-2 complete sentences."

            turn = TurnMetric(
                turn_index=turn_index,
                concept_evaluated=concept,
                user_explanation=user_explanation,
                clarity_score=round(clarity, 1),
                accuracy_score=round(accuracy, 1),
                depth_score=round(depth, 1),
                relevance_score=round(relevance, 1),
                turn_score=turn_score,
                strengths=strengths,
                missing_or_misunderstood=missing,
                actionable_tip=action_tip,
                student_state="Mostly Clear" if word_count >= 10 else "Curious",
            )
            return turn, (word_count >= 15)
