import json
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

try:
    import config
    OPENAI_API_KEY = getattr(config, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = getattr(config, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY = getattr(config, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = getattr(config, "GROQ_MODEL", None) or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

def _call_openai(prompt: str, json_mode: bool = False) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=OPENAI_API_KEY)
    kwargs = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()

def _call_groq(prompt: str, json_mode: bool = False) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    kwargs = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()

def _call_llm(prompt: str, json_mode: bool = False) -> str:
    errors = []

    if OPENAI_API_KEY:
        try:
            res = _call_openai(prompt, json_mode=json_mode)
            if res:
                return res
        except Exception as e:
            errors.append(f"OpenAI: {e}")

    if GROQ_API_KEY:
        try:
            res = _call_groq(prompt, json_mode=json_mode)
            if res:
                return res
        except Exception as e:
            errors.append(f"Groq: {e}")

    raise RuntimeError("All LLM providers failed -> " + " | ".join(errors))

def ask(prompt: str) -> str:
    return _call_llm(prompt, json_mode=False)

def ask_json(prompt: str) -> dict:
    raw = _call_llm(prompt, json_mode=True).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)