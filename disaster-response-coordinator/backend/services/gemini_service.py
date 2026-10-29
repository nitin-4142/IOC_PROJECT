"""
Gemini AI service — thin wrapper around the google-genai SDK.
Handles authentication, timeouts, retries, and fallback signalling.
"""
from __future__ import annotations
import json
import logging
import time
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
            return None
        try:
            from google import genai
            _client = genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception as exc:
            logger.warning("Could not initialise Gemini client: %s", exc)
            return None
    return _client


def is_available() -> bool:
    """Return True when a Gemini API key is configured."""
    return bool(
        config.GEMINI_API_KEY
        and config.GEMINI_API_KEY != "your_gemini_api_key_here"
        and not config.DEMO_MODE
    )


def generate_structured(
    prompt: str,
    system_instruction: str = "",
    max_retries: int = 2,
) -> Optional[dict[str, Any]]:
    """
    Send a prompt to Gemini and parse the first JSON object from the response.
    Returns None on failure so callers can fall back gracefully.
    """
    if not is_available():
        return None

    client = _get_client()
    if client is None:
        return None

    from google.genai import types

    contents = prompt
    config_kwargs: dict[str, Any] = {
        "temperature": 0.1,
        "max_output_tokens": 2048,
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    candidate_models = [config.GEMINI_MODEL]
    for fallback_model in ("gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite"):
        if fallback_model not in candidate_models:
            candidate_models.append(fallback_model)

    for current_model in candidate_models:
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                text = response.text or ""
                parsed = _extract_json(text)
                if parsed:
                    logger.info("Successfully received structured response from Gemini using %s", current_model)
                    return parsed
            except Exception as exc:
                logger.warning("Gemini attempt %d with model %s failed: %s", attempt + 1, current_model, exc)
                if attempt < max_retries:
                    time.sleep(config.AGENT_RETRY_DELAY)
                else:
                    break  # Try next candidate model if available

    return None


def _extract_json(text: str) -> Optional[dict]:
    """Extract the first JSON object from a (possibly markdown-wrapped) string."""
    # Strip markdown code fences
    for marker in ("```json", "```JSON", "```"):
        text = text.replace(marker, "")
    text = text.strip().strip("`").strip()

    # Find first { … } block
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
