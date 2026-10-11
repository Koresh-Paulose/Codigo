"""Comprehensive test suite for the Student Agent module."""
import unittest
from pathlib import Path
from backend.features.teach.student_agent.document_reader import DocumentReader
from backend.features.teach.student_agent.metrics import SessionMetrics, TurnMetric
from backend.features.teach.student_agent.session import StudentSession
from backend.features.teach.student_agent.llm_client import LLMClient

class TestStudentAgent(unittest.TestCase):
    def setUp(self):
        self.sample_file = Path(__file__).parent / "sample_notes.md"

    def test_document_reader(self):
        doc = DocumentReader.read_file(str(self.sample_file))
        self.assertEqual(doc.file_name, "sample_notes.md")
        self.assertGreater(doc.word_count, 100)
        self.assertGreater(len(doc.concepts), 0)
        self.assertIn("Self-Attention Mechanism", doc.concepts)

    def test_metrics_accumulation(self):
        metrics = SessionMetrics(all_concepts=["Concept A", "Concept B", "Concept C"], pending_concepts=["Concept A", "Concept B", "Concept C"])
        turn1 = TurnMetric(
            turn_index=1,
            concept_evaluated="Concept A",
            clarity_score=8.0,
            accuracy_score=9.0,
            depth_score=7.0,
            relevance_score=9.0,
            turn_score=83.0,
        )
        metrics.record_turn(turn1, newly_mastered="Concept A")
        self.assertEqual(metrics.total_turns, 1)
        self.assertEqual(metrics.average_accuracy, 9.0)
        self.assertIn("Concept A", metrics.mastered_concepts)
        self.assertNotIn("Concept A", metrics.pending_concepts)
        self.assertAlmostEqual(metrics.concept_coverage_percentage, 33.3, places=1)

    def test_session_flow(self):
        session = StudentSession(file_path=str(self.sample_file), persona_type="novice")
        initial_q = session.start()
        self.assertTrue(len(initial_q) > 10)

        # Step 1: Explain concept
        step_result = session.step("Self-attention compares every word with every other word using Q, K, and V vectors.")
        self.assertIn("turn_metric", step_result)
        self.assertIn("student_reply", step_result)
        self.assertEqual(session.metrics.total_turns, 1)
        self.assertGreater(session.metrics.overall_teaching_score, 0)

        summary = session.get_summary()
        self.assertIn("FINAL TEACHING PERFORMANCE REPORT", summary)

    def test_retest_and_early_exit(self):
        session = StudentSession(file_path=str(self.sample_file), persona_type="novice")
        session.start()
        session.step("A quick partial answer to question 1.")
        # Mid-session report
        mid_report = session.get_final_report()
        self.assertIn("FINAL TEACHING PERFORMANCE REPORT", mid_report)
        self.assertIn("Questions Answered:        1 / 5", mid_report)

        # Trigger retest
        new_q = session.retest()
        self.assertTrue(len(new_q) > 10)
        self.assertEqual(session.metrics.total_turns, 0)
        self.assertEqual(session.current_concept_idx, 0)

    def test_idk_and_natural_responses(self):
        session = StudentSession(file_path=str(self.sample_file), persona_type="novice")
        session.start()
        step1 = session.step("advancement in technology")
        self.assertNotIn("So idk", step1["student_reply"])
        self.assertNotIn("helpful way to frame it! So", step1["student_reply"])

        step2 = session.step("idk")
        reply2 = step2["student_reply"]
        self.assertNotIn("So idk", reply2)
        self.assertNotIn("helpful way to frame it", reply2)
        # Should be supportive
        self.assertTrue(any(w in reply2.lower() for w in ["no worries", "no problem", "totally fine", "fine", "review"]))

        report = session.get_final_report()
        self.assertIn("FINAL TEACHING PERFORMANCE REPORT", report)
        self.assertIn("Did not attempt an explanation", report)

    def test_dynamic_question_count(self):
        session = StudentSession(file_path=str(self.sample_file), persona_type="novice")
        session.set_total_questions(3)
        self.assertEqual(session.total_questions, 3)
        self.assertEqual(session.metrics.target_questions, 3)

        opening = session.start()
        self.assertIn("Student question #1 of 3", opening)

        res1 = session.step("Answer 1")
        self.assertFalse(res1["is_series_complete"])

        res2 = session.step("Answer 2")
        self.assertFalse(res2["is_series_complete"])

        res3 = session.step("Answer 3")
        self.assertTrue(res3["is_series_complete"])

        final_rep = session.get_final_report()
        self.assertIn("Questions Answered:        3 / 3", final_rep)

    def test_autonomous_topic_research_mode(self):
        # Test preset topic without files
        session = StudentSession(topic="Photosynthesis", max_questions=3)
        self.assertTrue(session.doc.file_name.startswith("Topic:"))
        self.assertGreaterEqual(len(session.doc.concepts), 3)

        opening = session.start()
        self.assertIn("Student question #1 of 3", opening)
        self.assertTrue(len(opening) > 50)

        step_res = session.step("Chlorophyll in chloroplasts absorbs light energy.")
        self.assertIn("student_reply", step_res)
        self.assertEqual(session.metrics.total_turns, 1)

        # Test arbitrary custom topic
        custom_session = StudentSession(topic="Cybersecurity & Encryption", max_questions=2)
        self.assertTrue(custom_session.doc.file_name.startswith("Topic:"))
        self.assertGreaterEqual(len(custom_session.doc.concepts), 2)

if __name__ == "__main__":
    unittest.main()
