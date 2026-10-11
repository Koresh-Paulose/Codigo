from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TurnMetric(BaseModel):
    turn_index: int
    concept_evaluated: str = "General Topic"
    user_explanation: str = ""
    clarity_score: float = Field(ge=0.0, le=10.0, default=7.0)
    accuracy_score: float = Field(ge=0.0, le=10.0, default=7.0)
    depth_score: float = Field(ge=0.0, le=10.0, default=6.0)
    relevance_score: float = Field(ge=0.0, le=10.0, default=8.0)
    turn_score: float = Field(ge=0.0, le=100.0, default=70.0)
    strengths: List[str] = Field(default_factory=list)
    missing_or_misunderstood: List[str] = Field(default_factory=list)
    actionable_tip: str = ""
    student_state: str = "Pondering"  # Confused, Skeptical, Getting It, Mastered!

class SessionMetrics(BaseModel):
    total_turns: int = 0
    target_questions: int = 5
    average_clarity: float = 0.0
    average_accuracy: float = 0.0
    average_depth: float = 0.0
    average_relevance: float = 0.0
    overall_teaching_score: float = 0.0
    concept_coverage_percentage: float = 0.0
    all_concepts: List[str] = Field(default_factory=list)
    mastered_concepts: List[str] = Field(default_factory=list)
    pending_concepts: List[str] = Field(default_factory=list)
    turn_history: List[TurnMetric] = Field(default_factory=list)

    def record_turn(self, turn: TurnMetric, newly_mastered: Optional[str] = None):
        self.turn_history.append(turn)
        self.total_turns = len(self.turn_history)

        self.average_clarity = round(sum(t.clarity_score for t in self.turn_history) / self.total_turns, 1)
        self.average_accuracy = round(sum(t.accuracy_score for t in self.turn_history) / self.total_turns, 1)
        self.average_depth = round(sum(t.depth_score for t in self.turn_history) / self.total_turns, 1)
        self.average_relevance = round(sum(t.relevance_score for t in self.turn_history) / self.total_turns, 1)

        raw_weighted = (
            self.average_accuracy * 0.35 +
            self.average_clarity * 0.30 +
            self.average_depth * 0.20 +
            self.average_relevance * 0.15
        ) * 10
        self.overall_teaching_score = round(min(100.0, max(0.0, raw_weighted)), 1)

        if newly_mastered and newly_mastered not in self.mastered_concepts:
            self.mastered_concepts.append(newly_mastered)
            if newly_mastered in self.pending_concepts:
                self.pending_concepts.remove(newly_mastered)

        if self.all_concepts:
            self.concept_coverage_percentage = round((len(self.mastered_concepts) / len(self.all_concepts)) * 100, 1)

    @property
    def grade(self) -> str:
        if self.overall_teaching_score >= 90:
            return "A+ (Master Teacher)"
        elif self.overall_teaching_score >= 80:
            return "A (Clear & Engaging)"
        elif self.overall_teaching_score >= 70:
            return "B (Solid Explanations)"
        elif self.overall_teaching_score >= 60:
            return "C (Basic Understanding)"
        elif self.overall_teaching_score >= 50:
            return "D (Needs Better Grounding)"
        return "Needs Retest (< 50%)"

    def generate_final_report(self, student_name: str = "Alex") -> str:
        """Generates a clean, to-the-point performance report centered on weak points and improvements."""
        if not self.turn_history:
            return "\n[Notice]: No questions answered yet. Study session concluded.\n"

        lines = [
            "",
            "+==========================================================================+",
            "|               FINAL TEACHING PERFORMANCE REPORT                          |",
            "|             Protege Feynman Active Learning System                       |",
            "+==========================================================================+",
            f"  Overall Teaching Mastery:  {self.overall_teaching_score:.1f}%  (Grade: {self.grade})",
            f"  Questions Answered:        {self.total_turns} / {self.target_questions}",
            f"  Mastered Topics:           {len(self.mastered_concepts)} of {max(len(self.all_concepts), self.total_turns)} topics with solid depth",
            "",
            "----------------------------------------------------------------------------",
            "📊 SCORE BREAKDOWN (Scale 0 - 10)",
            f"  • Scientific Accuracy:     {self.average_accuracy:>4.1f} / 10  (Factual precision based on notes)",
            f"  • Clarity & Simplicity:    {self.average_clarity:>4.1f} / 10  (Clear, accessible explanation)",
            f"  • Explanation Depth:       {self.average_depth:>4.1f} / 10  (Explaining *why* and mechanisms)",
            f"  • Responsiveness:          {self.average_relevance:>4.1f} / 10  (Directly answering student curiosity)",
            "",
            "----------------------------------------------------------------------------",
            "📋 QUESTION-BY-QUESTION PROGRESSION",
        ]

        for t in self.turn_history:
            rating_label = "Strong" if t.turn_score >= 80 else ("Satisfactory" if t.turn_score >= 70 else ("Basic" if t.turn_score >= 60 else "Needs Work"))
            lines.append(f"  [Q{t.turn_index}] {t.concept_evaluated:<28} : {t.turn_score:>5.1f}%  [{rating_label}]")

        # Weak points section: target questions below 80% or where explanation was lacking
        weak_turns = [t for t in self.turn_history if t.turn_score < 78.0]
        if not weak_turns and self.turn_history:
            weak_turns = sorted(self.turn_history, key=lambda x: x.turn_score)[:1]

        lines.extend([
            "",
            "----------------------------------------------------------------------------",
            "🎯 CRITICAL WEAK POINTS & HOW TO IMPROVE",
        ])

        if weak_turns:
            for idx, wt in enumerate(weak_turns, 1):
                ans_snippet = f'"{wt.user_explanation}"' if wt.user_explanation else "Brief answer"
                gap_text = wt.missing_or_misunderstood[0] if wt.missing_or_misunderstood else "Lacked core mechanism details or depth."
                tip_text = wt.actionable_tip if wt.actionable_tip else "Explain the underlying 'why' in full sentences rather than short fragments."
                lines.extend([
                    f"  {idx}. Question #{wt.turn_index}: {wt.concept_evaluated} (Score: {wt.turn_score:.1f}%)",
                    f"     • What you said: {ans_snippet}",
                    f"     • What was missing: {gap_text}",
                    f"     • Next time: {tip_text}",
                    "",
                ])
        else:
            lines.append("  • None! All explanations demonstrated thorough understanding and depth.")

        # Key strengths
        unique_strengths = []
        for t in self.turn_history:
            for s in t.strengths:
                if s not in unique_strengths:
                    unique_strengths.append(s)

        lines.extend([
            "----------------------------------------------------------------------------",
            "🌟 WHAT YOU DID WELL",
        ])
        if unique_strengths:
            for s in unique_strengths[:3]:
                lines.append(f"  + {s}")
        else:
            lines.append("  + Engaged directly with all student questions.")

        # Overall summary guidance
        lines.extend([
            "",
            "----------------------------------------------------------------------------",
            "💡 SUMMARY FOR TEACHING MASTERY",
        ])

        if self.average_depth < 6.8:
            lines.append("  Your biggest area for growth is EXPLANATION DEPTH. Avoid short fragments")
            lines.append("  (2-5 words); provide at least 1-2 full sentences explaining HOW and WHY")
            lines.append("  the mechanism works so a student gets the full picture.")
        else:
            lines.append("  Great teaching session! You communicated clearly and accurately.")
            lines.append("  To reach master level, continue using vivid real-world analogies.")

        lines.extend([
            "+==========================================================================+",
            "",
        ])

        return "\n".join(lines)
