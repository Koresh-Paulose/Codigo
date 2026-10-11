import json
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
for env_name in [".env.local", ".env"]:
    for d in [ROOT_DIR, ROOT_DIR / "backend", Path.cwd()]:
        env_f = d / env_name
        if env_f.exists():
            load_dotenv(env_f, override=False)

try:
    import config
    GEMINI_API_KEY = getattr(config, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = getattr(config, "GEMINI_MODEL", None) or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    OPENAI_API_KEY = getattr(config, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = getattr(config, "OPENAI_MODEL", None) or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY = getattr(config, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = getattr(config, "GROQ_MODEL", None) or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def _call_gemini(prompt: str, json_mode: bool = False) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    models_to_try = [GEMINI_MODEL]
    for alt in ["gemini-3.5-flash-lite", "gemini-3.8-flash"]:
        if alt not in models_to_try:
            models_to_try.append(alt)
    
    last_err = None
    for model_name in models_to_try:
        try:
            kwargs = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str or "no longer available" in err_str or "429" in err_str or "quota" in err_str:
                continue
            raise e
    raise last_err or RuntimeError("Gemini model call failed")

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

    if GEMINI_API_KEY:
        try:
            res = _call_gemini(prompt, json_mode=json_mode)
            if res:
                return res
        except Exception as e:
            errors.append(f"Gemini: {e}")

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

    raise RuntimeError("All LLM providers failed -> " + (" | ".join(errors) if errors else "No LLM API keys configured (set GEMINI_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY in environment variables)."))

def ask(prompt: str) -> str:
    return _call_llm(prompt, json_mode=False)

def ask_json(prompt: str) -> dict:
    raw = _call_llm(prompt, json_mode=True).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)