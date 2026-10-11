import re
from typing import List, Dict, Any, Optional
from .document_reader import DocumentReader, DocumentKnowledge, TopicFact
from .persona import StudentPersona
from .llm_client import LLMClient
from .evaluator import TeachingEvaluator
from .metrics import SessionMetrics, TurnMetric

class StudentSession:
    """Manages an interactive study session through a series of exactly 5 topical questions."""

    def __init__(
        self,
        file_path: Optional[str] = None,
        topic: Optional[str] = None,
        persona_type: str = "novice",
        llm_client: Optional[LLMClient] = None,
        max_questions: int = 5,
    ):
        self.llm = llm_client or LLMClient()
        self.persona = StudentPersona(persona_type=persona_type)
        self.evaluator = TeachingEvaluator(llm_client=self.llm)
        self.doc: Optional[DocumentKnowledge] = None
        self.total_questions: int = max_questions
        self.metrics = SessionMetrics(target_questions=max_questions)
        self.history: List[Dict[str, str]] = []
        self.current_concept_idx: int = 0
        self.last_student_question: str = ""
        self.is_series_complete: bool = False

        if file_path:
            self.load_document(file_path, max_questions=max_questions)
        elif topic:
            self.load_topic(topic, max_questions=max_questions)

    def load_document(self, file_path: str, max_questions: Optional[int] = None) -> DocumentKnowledge:
        """Parses and ingests a reference document into the student session."""
        self.doc = DocumentReader.read_file(file_path)
        self.metrics.all_concepts = list(self.doc.concepts)
        self.metrics.pending_concepts = list(self.doc.concepts)
        self.metrics.mastered_concepts = []
        self.current_concept_idx = 0
        self.is_series_complete = False
        if max_questions is not None:
            self.total_questions = max(1, max_questions)
        self.metrics.target_questions = self.total_questions

        return self.doc

    def load_topic(self, topic: str, max_questions: Optional[int] = None) -> DocumentKnowledge:
        """Autonomously researches a topic and constructs curriculum and knowledge grounding without requiring a file."""
        from .topic_researcher import TopicResearcher
        self.doc = TopicResearcher.research_topic(topic, llm_client=self.llm)
        self.metrics.all_concepts = list(self.doc.concepts)
        self.metrics.pending_concepts = list(self.doc.concepts)
        self.metrics.mastered_concepts = []
        self.current_concept_idx = 0
        self.is_series_complete = False
        if max_questions is not None:
            self.total_questions = max(1, max_questions)
        self.metrics.target_questions = self.total_questions

        return self.doc

    def set_total_questions(self, count: int):
        """Allows setting the total questions before starting the session."""
        self.total_questions = max(1, count)
        self.metrics.target_questions = self.total_questions

    @property
    def current_topic_fact(self) -> TopicFact:
        if self.doc and self.doc.topic_facts:
            idx = min(self.current_concept_idx, len(self.doc.topic_facts) - 1)
            return self.doc.topic_facts[idx]
        return TopicFact(title="General Topic", fact="Core principles of the document.")

    @property
    def current_concept(self) -> str:
        return self.current_topic_fact.title

    def retest(self) -> str:
        """Resets the metrics, dialogue history, and topic counter to restart a fresh study session."""
        if not self.doc:
            raise ValueError("No document loaded to retest. Call load_document() first.")
        self.metrics = SessionMetrics(
            target_questions=self.total_questions,
            all_concepts=list(self.doc.concepts),
            pending_concepts=list(self.doc.concepts),
        )
        self.history = []
        self.current_concept_idx = 0
        self.is_series_complete = False
        return self.start()

    def format_interim_card(self, turn_metric: TurnMetric, turn_index: int) -> str:
        acc_label = "Good" if turn_metric.accuracy_score >= 8.0 else ("Fair" if turn_metric.accuracy_score >= 6.5 else "Needs Attention")
        clar_label = "Good start" if turn_metric.clarity_score >= 7.5 else ("Clear" if turn_metric.clarity_score >= 6.5 else "Needs Simplification")

        strength_text = turn_metric.strengths[0] if turn_metric.strengths else "you accurately identified the core concept."
        tip_text = turn_metric.missing_or_misunderstood[0] if turn_metric.missing_or_misunderstood else "Explain how oxygen moves from the lungs into the blood and reaches body tissues."
        obs_title = "Initial observation" if turn_index == 1 else f"Observation #{turn_index}"

        return f"""------------------------------------------------------------------------
📊 Teaching performance — interim feedback
[{obs_title}]
• Accuracy: {acc_label} — {strength_text}
• Clarity: {clar_label} — your explanation was concise and easy to follow.
• To improve: {tip_text}

No overall score yet; I'll assess more evidence as our lesson continues.
------------------------------------------------------------------------"""

    def start(self) -> str:
        """Starts the session and produces the student's initial opening and Question 1."""
        if not self.doc:
            raise ValueError("No document loaded. Call load_document() first.")

        # Reorder to start with body systems only if this is specifically the human biology document
        if "human" in self.doc.content.lower() and "respiratory" in self.doc.content.lower():
            body_idx = next((i for i, tf in enumerate(self.doc.topic_facts) if "body" in tf.title.lower()), None)
            if body_idx is not None and body_idx != 0:
                item = self.doc.topic_facts.pop(body_idx)
                self.doc.topic_facts.insert(0, item)
                self.current_concept_idx = 0

        # Extract title from first line if descriptive
        lines = [l.strip() for l in self.doc.content.splitlines() if l.strip()]
        first_line = re.sub(r"^#+\s*", "", lines[0]).strip() if lines else ""
        if 3 <= len(first_line) <= 60 and not first_line.lower().startswith("http"):
            doc_display = first_line
        else:
            doc_display = self.doc.file_name

        takeaways = []
        for i, tf in enumerate(self.doc.topic_facts[:self.total_questions], 1):
            takeaways.append(f"  {i}. **{tf.title}**\n     {tf.fact}")
        takeaways_str = "\n".join(takeaways)

        is_topic_mode = self.doc.file_name.lower().startswith("topic:")
        if is_topic_mode:
            doc_type_str = "topic overview"
            doc_display = self.doc.file_name.replace("Topic: ", "").strip()
            intro_action = f"I've researched your topic, **{doc_display}**"
            learned_header = f"What I've researched on {doc_display} ({len(takeaways)} Study Topics)"
        else:
            doc_type_str = "PDF" if self.doc.file_name.lower().endswith(".pdf") else "document"
            intro_action = f"I've read your {doc_type_str}, {doc_display}"
            learned_header = f"What I've learned from your {doc_type_str} ({len(takeaways)} Study Topics)"

        tf = self.current_topic_fact
        system_prompt = self.persona.get_system_prompt(
            document_context=self.doc.content[:3500],
            current_concept=tf.title,
            concept_fact=tf.fact,
            question_num=1,
            total_questions=self.total_questions,
        )
        user_prompt = f"""OPENING QUESTION:
TARGET TOPIC: {tf.title}
FACT GROUNDING: {tf.fact}
SESSION PROGRESS: Question 1 of {self.total_questions}

TASK:
Please ask your opening curious student question about this topic based strictly on the provided fact."""

        q1_text = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        opening_text = f"""Alright, teacher! 😄 📚 {intro_action}. I'll act as a curious student, ask you {self.total_questions} questions based on your teaching material, respond to your explanations, and assess your teaching performance at the end.

📖 **{learned_header}:**
{takeaways_str}

🎓 **Classroom Rules:**
• Me — the student: I'll ask {self.total_questions} genuine questions, one on each topic, and follow up on your explanations.
• You — the teacher: Teach me naturally with simple explanations, analogies, and examples.
• Commands: Type '/quit' anytime to finish early and see your performance report | '/retest' to restart.

🧑‍🎓 **Let's begin, teacher!**

**Student question #1 of {self.total_questions}**
Topic: {tf.title}

{q1_text}

Your turn, teacher! 😊 (Answer naturally, or type /quit anytime to end early and see your report)"""

        self.last_student_question = q1_text
        self.history.append({"role": "student", "content": opening_text})
        return opening_text

    def step(self, user_explanation: str) -> Dict[str, Any]:
        """Processes teacher's explanation, quietly evaluates it, and produces the next question in the 5-question series."""
        if not self.doc:
            raise ValueError("No document loaded.")

        turn_index = self.metrics.total_turns + 1
        evaluated_concept = self.current_concept

        # 1. Check for "idk" / uncertain responses BEFORE evaluation - these should not be scored
        if self.llm._is_uncertain_or_idk(user_explanation):
            # Create a zero-score TurnMetric for "idk" responses - no evaluation needed
            turn_metric = TurnMetric(
                turn_index=turn_index,
                concept_evaluated=evaluated_concept,
                user_explanation=user_explanation,
                clarity_score=0.0,
                accuracy_score=0.0,
                depth_score=0.0,
                relevance_score=0.0,
                turn_score=0.0,
                strengths=["Honestly stated being unsure rather than guessing inaccurate facts."],
                missing_or_misunderstood=[f"Did not attempt an explanation ('{user_explanation}'). Review the notes for this topic."],
                actionable_tip="Review the notes on this topic and try explaining the intuition in 1-2 complete sentences.",
                student_state="Confused",
            )
            mastered = False
        else:
            # 2. Background Pedagogical Evaluation (only for actual explanations)
            turn_metric, mastered = self.evaluator.evaluate_turn(
                turn_index=turn_index,
                student_question=self.last_student_question,
                user_explanation=user_explanation,
                concept=evaluated_concept,
                document_context=self.doc.content[:3500],
            )

        newly_mastered = evaluated_concept if mastered else None
        self.metrics.record_turn(turn_metric, newly_mastered=newly_mastered)

        # 2. Record Teacher's Input into History
        self.history.append({"role": "teacher", "content": user_explanation})

        # 3. Check if all 5 questions have been answered
        if turn_index >= self.total_questions:
            self.is_series_complete = True
            student_closing = (
                f"Awesome, teacher! 😄 That thoroughly covers all {self.total_questions} questions for our study session!\n"
                f"Thank you for teaching me — your explanations really helped connect the dots.\n\n"
                f"Here is your final teaching performance report:"
            )
            full_reply = f"{student_closing}\n\n{self.get_final_report()}"
            self.history.append({"role": "student", "content": full_reply})
            return {
                "student_reply": full_reply,
                "is_series_complete": True,
                "turn_index": turn_index,
                "turn_metric": turn_metric,
                "session_metrics": self.metrics,
                "concept_mastered": mastered,
                "next_concept": None,
                "provider_used": self.llm.last_provider_used,
            }

        # 4. Advance to Next Topic in Series
        self.current_concept_idx += 1
        next_question_num = turn_index + 1
        next_tf = self.current_topic_fact

        # 5. Generate Next Natural Student Question in Series
        system_prompt = self.persona.get_system_prompt(
            document_context=self.doc.content[:3500],
            current_concept=next_tf.title,
            concept_fact=next_tf.fact,
            question_num=next_question_num,
            total_questions=self.total_questions,
        )

        recent_dialogue = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in self.history[-4:]]
        )

        user_prompt = f"""RECENT DIALOGUE:
{recent_dialogue}

TEACHER'S LATEST EXPLANATION:
\"{user_explanation}\"

TARGET TOPIC: {next_tf.title}
FACT GROUNDING: {next_tf.fact}
SESSION PROGRESS: Question {next_question_num} of {self.total_questions}

TASK:
1. Natural student reaction:
   - If the teacher was unsure or said 'idk' / 'not sure', respond supportively and naturally (e.g. "No worries at all! That's definitely a tricky one to explain on the spot—we can keep moving and circle back later.").
   - If the teacher provided an explanation, synthesize the core idea naturally without repeating robotic boilerplates or echoing typos.
2. Fluid transition to Question {next_question_num} on topic **{next_tf.title}**.
3. Ask a curious, intuitive student question probing '{next_tf.title}' grounded in: {next_tf.fact}."""

        student_reply = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        full_reply = student_reply
        self.last_student_question = student_reply
        self.history.append({"role": "student", "content": full_reply})

        return {
            "student_reply": full_reply,
            "is_series_complete": False,
            "turn_index": turn_index,
            "question_number": next_question_num,
            "total_questions": self.total_questions,
            "turn_metric": turn_metric,
            "session_metrics": self.metrics,
            "concept_mastered": mastered,
            "next_concept": next_tf.title,
            "provider_used": self.llm.last_provider_used,
        }

    def get_final_report(self) -> str:
        """Generates the full end-of-chat performance report."""
        return self.metrics.generate_final_report(student_name=self.persona.name)

    def get_summary(self) -> str:
        """Alias for get_final_report."""
        return self.get_final_report()
