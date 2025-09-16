# interviews/services/pplx.py
import os
import requests
import json
from typing import Dict, Any, Optional

PPLX_API_KEY = os.getenv("PPLX_API_KEY") or os.getenv("SONAR_REASONING_API_KEY")
API_URL = "https://api.perplexity.ai/chat/completions"  # confirm with Perplexity docs if different
MODEL = "sonar-pro"

def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Try parse JSON out of a string that may contain prose + JSON."""
    try:
        return json.loads(text)
    except Exception:
        # try to find a JSON block inside the text
        import re
        m = re.search(r"(\{[\\s\\S]*\})", text)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
    return None

def generate_question(admin_prompt: str) -> Dict[str, Any]:
    """
    Ask Sonar-pro to generate a question with strict JSON output.
    Returns dict matching your GeneratedQuestion schema:
    { type, title, spec(rubric/dataset/task), rubric, ideal_answer, version }
    """
    # Offline fallback stub (useful in dev without API key)
    if not PPLX_API_KEY:
        return {
            "type": "theory",
            "title": "VLOOKUP concept (stub)",
            "spec": {"prompt": admin_prompt},
            "rubric": {"key_points": ["lookup mechanics", "limitations", "alternatives"]},
            "ideal_answer": "VLOOKUP retrieves values vertically; INDEX/MATCH is more flexible.",
            "version": 1,
        }

    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json",
    }

    system = (
        "You are Sonar-pro, a question generator for Excel interviews. "
        "Return only valid JSON in the response body with these fields: "
        '{"type":"theory"|"practical","title":str,"spec":object,"rubric":object,"ideal_answer":str,"version":int}.'
        "If you cannot produce a dataset for practical Q, set spec.dataset to null."
    )

    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": admin_prompt},
        ],
        # optional: set token limits / other options if Perplexity supports them
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Common shape: data["choices"][0]["message"]["content"]
        content = None
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                message = choices[0].get("message") or {}
                content = message.get("content") or message.get("text") or None
        # defensively parse
        parsed = None
        if content:
            parsed = _safe_parse_json(content)
        if not parsed:
            # attempt to parse top-level if response already dict-like
            parsed = data.get("metadata") if isinstance(data, dict) else None

        # Safe defaults when parsing fails
        if not parsed:
            return {
                "type": "theory",
                "title": f"Generated: {admin_prompt[:40]}",
                "spec": {"prompt": admin_prompt},
                "rubric": {},
                "ideal_answer": "",
                "version": 1,
            }

        # Normalize fields
        return {
            "type": parsed.get("type", "theory"),
            "title": parsed.get("title", parsed.get("name", "Untitled Question")),
            "spec": parsed.get("spec", parsed.get("prompt", {"prompt": admin_prompt})),
            "rubric": parsed.get("rubric", {}),
            "ideal_answer": parsed.get("ideal_answer", parsed.get("answer", "")),
            "version": int(parsed.get("version", 1)),
        }
    except Exception as e:
        # network error or parse error -> fallback stub with helpful error note
        return {
            "type": "theory",
            "title": "VLOOKUP concept (fallback)",
            "spec": {"prompt": admin_prompt, "error": str(e)},
            "rubric": {"key_points": ["lookup mechanics", "limitations", "alternatives"]},
            "ideal_answer": "VLOOKUP retrieves values vertically; INDEX/MATCH is more flexible.",
            "version": 1,
        }
