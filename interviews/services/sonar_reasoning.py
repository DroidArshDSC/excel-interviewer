# interviews/services/sonar_reasoning.py
"""
Sonar-only judge service.

Behavior:
- Calls the Sonar/Perplexity chat completions endpoint and expects the model
  to return a single valid JSON object containing:
    { "score": <0..100>, "verdict": "<short string>", "mistakes": [...],
      "improvements": [...], "citations": [...] }
- If the API call fails, or the response is not parseable as JSON, this
  function returns a clear "Sonar unavailable" result (score 0) and
  includes a short debug excerpt in the returned dict for local debugging.
"""

import time as _time
import os
import requests
import json
import re
from typing import Dict, Any, Optional
from django.conf import settings

SONAR_API_KEY = os.getenv("SONAR_REASONING_API_KEY") or os.getenv("PPLX_API_KEY")
API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-reasoning"


def _extract_candidate_text(resp: requests.Response) -> str:
    """
    Try common locations for model textual output in Perplexity-like responses.
    Falls back to resp.text.
    """
    try:
        data = resp.json()
    except Exception:
        return resp.text or ""

    # Perplexity / chat style: choices -> message -> content | text
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message") or {}
            content = message.get("content") or message.get("text")
            if content:
                return content
    # fallback to textual representation
    return json.dumps(data)


def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON directly; if fails return None."""
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        # attempt to extract last JSON block (conservative)
        last_open = text.rfind("{")
        if last_open != -1:
            candidate = text[last_open:]
            # quick balanced-brace parse
            depth = 0
            for i, ch in enumerate(candidate):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        block = candidate[: i + 1]
                        try:
                            return json.loads(block)
                        except Exception:
                            break
        return None


def judge_answer(question: Dict[str, Any], submission: Dict[str, Any], runner_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sonar-only judge.

    Returns a dict with keys:
      - score: float (0..100)
      - verdict: str
      - mistakes: list
      - improvements: list
      - citations: list
      - debug: dict (only for local debugging; contains http_status and a short raw_excerpt)
    """

    # Ensure we have an API key
    if not SONAR_API_KEY:
        return {
            "score": 0.0,
            "verdict": "Sonar unavailable (no API key)",
            "mistakes": [],
            "improvements": ["Sonar API key not configured on server."],
            "citations": [],
            "debug": {"reason": "no_api_key"}
        }

    headers = {"Authorization": f"Bearer {SONAR_API_KEY}", "Content-Type": "application/json"}

    # Strong system prompt requesting ONLY the JSON object
    system_prompt = (
        "You are Sonar-reasoning. RETURN ONLY a single valid JSON object and nothing else. "
        "The JSON must contain keys: score (number 0..100), verdict (string), mistakes (array), improvements (array), citations (array). "
        "Do not include any commentary, analysis, or text outside the JSON. "
        "If you cannot produce values for a key, return an empty array or empty string as appropriate."
    )

    user_prompt = (
        "Question:\n" + json.dumps(question) + "\n\n"
        "Submission:\n" + json.dumps(submission) + "\n\n"
        "Runner checks:\n" + json.dumps(runner_result) + "\n\n"
        "Return ONLY the JSON object with keys: score, verdict, mistakes, improvements, citations."
    )

    payload = {
        "model": MODEL,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    except Exception as e:
        # Network / connection error — Sonar unavailable
        return {
            "score": 0.0,
            "verdict": "Sonar unavailable (network error)",
            "mistakes": [],
            "improvements": [f"network_error: {str(e)}"],
            "citations": [],
            "debug": {"exception": str(e)}
        }

    status = getattr(resp, "status_code", None)
    raw_excerpt = None
    try:
        candidate_text = _extract_candidate_text(resp)
        raw_excerpt = (candidate_text[:400] + "...") if len(candidate_text) > 400 else candidate_text
    except Exception:
        raw_excerpt = (resp.text[:400] + "...") if resp.text else ""

    # Try strict parse
    parsed = _safe_parse_json(candidate_text)

    if not parsed:
        # No parseable JSON found — Sonar unable to provide judge in expected form
        return {
            "score": 0.0,
            "verdict": "Sonar unavailable (unparsable response)",
            "mistakes": [],
            "improvements": ["Sonar returned an unparsable response."],
            "citations": [],
            "debug": {"http_status": status, "raw_excerpt": raw_excerpt}
        }

    # Normalize parsed fields into expected types
    score = parsed.get("score", parsed.get("grade", 0))
    verdict = parsed.get("verdict", parsed.get("summary", "")) or ""
    mistakes = parsed.get("mistakes", parsed.get("errors", [])) or []
    improvements = parsed.get("improvements", parsed.get("advice", [])) or []
    citations = parsed.get("citations", []) or []

    # Ensure numeric score and clamp
    try:
        score = float(score)
    except Exception:
        score = 0.0
    score = max(0.0, min(100.0, score))

    # Ensure lists
    if not isinstance(mistakes, list):
        mistakes = [str(mistakes)]
    if not isinstance(improvements, list):
        improvements = [str(improvements)]
    if not isinstance(citations, list):
        citations = [str(citations)]

    # Limit debug size
    debug = {"http_status": status, "raw_excerpt": raw_excerpt}

    return {
        "score": score,
        "verdict": verdict,
        "mistakes": mistakes,
        "improvements": improvements,
        "citations": citations,
        "debug": debug
    }


#Check whether Sonar is Up or not 
def ping(timeout: int = 8) -> (bool, dict):
    """
    Lightweight Sonar health check.
    Returns (ok: bool, info: dict).
    info contains http_status, time_ms, and a short response excerpt if available.
    """

    if not settings.DEBUG:
        info.pop("raw_excerpt", None)

    if not SONAR_API_KEY:
        return False, {"error": "no_api_key"}

    headers = {"Authorization": f"Bearer {SONAR_API_KEY}", "Content-Type": "application/json"}
    # minimal prompt that should be harmless and return quickly
    system_prompt = "You are a diagnostic helper. Reply quickly with the single JSON: {\"ok\": true} (no extra text)."
    user_prompt = "health-check"

    payload = {
        "model": MODEL,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 8,
    }

    t0 = _time.time()
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=timeout)
        elapsed_ms = int((_time.time() - t0) * 1000)
        status = getattr(resp, "status_code", None)
        # try to extract text safely
        try:
            text = resp.text or ""
        except Exception:
            text = ""
        excerpt = (text[:400] + "...") if len(text) > 400 else text
        # try parse JSON if present
        parsed = None
        try:
            parsed = resp.json()
        except Exception:
            parsed = None

        ok = (200 <= status < 300) and parsed is not None
        info = {"http_status": status, "time_ms": elapsed_ms, "parsed": bool(parsed), "raw_excerpt": excerpt}
        return bool(ok), info
    except Exception as e:
        elapsed_ms = int((_time.time() - t0) * 1000)
        return False, {"exception": str(e), "time_ms": elapsed_ms}
