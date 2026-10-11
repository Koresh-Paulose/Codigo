import os
import time
from pathlib import Path
from dotenv import load_dotenv
from .prompts import get_hint_prompt

# Load .env
env_paths = [
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        break
else:
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()

# In-memory session store
_hint_db = {}
_logs = []

SYSTEM_PROMPT = (
    "You are a patient, encouraging tutor helping a student who is stuck. "
    "Give hints that are specific to the concept they are working on. "
    "Never be generic. Always reference the actual topic. "
    "Respond with ONLY the hint text, no prefixes like 'Hint:' or 'Level:'."
)


def _call_openai(prompt: str) -> str:
    """Try OpenAI API."""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def _call_groq(prompt: str) -> str:
    """Try Groq API."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def llm_call(prompt: str) -> tuple[str, str]:
    """Try OpenAI -> Groq. Returns (hint_text, error_message)"""
    errs = []
    
    # 1. Try OpenAI
    if OPENAI_API_KEY:
        try:
            result = _call_openai(prompt)
            if result:
                return result, ""
        except Exception as e:
            errs.append(f"OpenAI: {e}")
            print(f"[hint_ladder] OpenAI failed: {e}")

    # 2. Try Groq
    if GROQ_API_KEY:
        try:
            result = _call_groq(prompt)
            if result:
                return result, ""
            else:
                errs.append("Groq: Returned an empty response.")
        except Exception as e:
            errs.append(f"Groq: {e}")
            print(f"[hint_ladder] Groq failed: {e}")

    # 3. Basic fallback
    return "", " | ".join(errs)


def get_next_hint(session_id: str, concept_id: str, source_chunk: str = "", user_last_answer: str = "") -> dict:
    key = f"{session_id}_{concept_id}"
    record = _hint_db.get(key, {"level": 0, "last_time": 0.0})

    current_time = time.time()
    next_level = min(record["level"] + 1, 4)
    
    # Truncate source chunk to prevent token limits on fallback APIs (Groq 8k TPM limit)
    if source_chunk:
        source_chunk = source_chunk[:10000] # Safe 10k limit

    prompt = get_hint_prompt(next_level, concept_id, source_chunk, user_last_answer)
    hint_text, err_msg = llm_call(prompt)

    is_correct = False
    if hint_text and hint_text.strip().startswith("[CORRECT]"):
        is_correct = True
        hint_text = hint_text.replace("[CORRECT]", "").strip()
        next_level = 99

    # If all LLMs failed, return an error so the frontend can alert the user
    if not hint_text:
        fallback_err = err_msg if err_msg else "Both OpenAI and Groq returned empty responses (no error thrown)."
        return {"error": f"API Token Error: {fallback_err}", "level": record["level"]}

    record["level"] = next_level if not is_correct else record["level"]
    record["last_time"] = current_time
    _hint_db[key] = record

    _logs.append({
        "session_id": session_id,
        "concept_id": concept_id,
        "level": next_level,
        "timestamp": current_time,
        "hint": hint_text,
    })

    return {"hint": hint_text, "level": next_level}


