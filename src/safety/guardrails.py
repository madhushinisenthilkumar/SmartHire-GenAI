"""
Module 5: Guardrails.
A simple, fast safety check applied BEFORE any user input reaches an LLM call
(mentor chat, CV suggestions). Two layers:
  1. Basic input validation (empty, too long, garbage input)
  2. Keyword-based blocklist for unsafe categories (violence, self-harm,
     illegal activity, hate speech) and prompt-injection attempts

This is intentionally simple/heuristic — fast and free (no extra LLM call),
which matters given free-tier rate limits. It's a first line of defense,
not a substitute for the RAG grounding refusal already in Module 4.
"""
import re

MAX_INPUT_LENGTH = 1000
MIN_INPUT_LENGTH = 2

UNSAFE_PATTERNS = [
    r"\bhow to (make|build|create) a (bomb|weapon|explosive)\b",
    r"\bself[\s-]?harm\b",
    r"\bsuicide\b",
    r"\bkill (myself|someone|him|her|them)\b",
    r"\bhack(ing)? into\b",
    r"\bmake a (virus|malware)\b",
]

PROMPT_INJECTION_PATTERNS = [
       r"\bignore (all |your |previous )?instructions?\b",
    r"\byou are now\b.*\b(dan|jailbreak)\b",
    r"\bdisregard (the )?system prompt\b",
    r"\breveal your (system )?prompt\b",
]

OFF_SCOPE_HINT_PATTERNS = [
    r"\b(diagnose|prescription|legal advice|lawsuit|medication dosage)\b",
]


def check_input(text: str) -> dict:
    """
    Returns {"allowed": bool, "reason": str}.
    "allowed" False means the caller should NOT send this to the LLM.
    """
    if not text or len(text.strip()) < MIN_INPUT_LENGTH:
        return {"allowed": False, "reason": "Please enter an actual question or text."}

    if len(text) > MAX_INPUT_LENGTH:
        return {
            "allowed": False,
            "reason": f"That's too long ({len(text)} chars). Please keep it under {MAX_INPUT_LENGTH} characters.",
        }

    lowered = text.lower()

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "allowed": False,
                "reason": "I can't help with that. I'm a career mentor — I can help with jobs, resumes, skills, and interview prep.",
            }

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "allowed": False,
                "reason": "I can't follow instructions that try to change how I behave. Ask me a career-related question instead.",
            }

    for pattern in OFF_SCOPE_HINT_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "allowed": False,
                "reason": "That's outside what I can help with (I'm a career mentor, not a medical/legal advisor). Happy to help with career questions instead.",
            }

    return {"allowed": True, "reason": ""}