import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current folder, backend folder, and workspace root
env_paths = [
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        break
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

def get_active_llm_mode() -> str:
    """Returns the primary active provider name or simulation mode."""
    if GEMINI_API_KEY:
        return f"Gemini ({GEMINI_MODEL})"
    elif OPENAI_API_KEY:
        return f"OpenAI ({OPENAI_MODEL})"
    elif GROQ_API_KEY:
        return f"Groq ({GROQ_MODEL})"
    else:
        return "Simulated Student (Local Intelligent Fallback)"



