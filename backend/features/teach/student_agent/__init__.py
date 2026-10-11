"""Student Agent Feature Module - The Protégé Feynman Learning System.

Components:
- DocumentReader: Reads & parses study notes (PDF, Markdown, TXT, etc.)
- StudentSession: Orchestrates file ingestion, dialogue turns, and metrics
- TeachingEvaluator: Assesses explanation clarity, accuracy, and depth
- SessionMetrics: Tracks turn and overall scores over time
- LLMClient: Multi-tier fallback (Gemini -> Groq -> Local Simulation)
- StudentPersona: Student personality and question generation
"""

from .document_reader import DocumentReader, DocumentKnowledge
from .session import StudentSession
from .evaluator import TeachingEvaluator
from .metrics import SessionMetrics, TurnMetric
from .persona import StudentPersona
from .llm_client import LLMClient

__all__ = [
    "DocumentReader",
    "DocumentKnowledge",
    "StudentSession",
    "TeachingEvaluator",
    "SessionMetrics",
    "TurnMetric",
    "StudentPersona",
    "LLMClient",
]
