"""
Module 1 (part 2): Structured output.
Sends raw resume text to Gemini with a strict prompt and returns a validated
ResumeProfile object. If the model's JSON doesn't validate, we retry once with
the validation error fed back to it.
"""
import json
from google import genai
from pydantic import BaseModel, ValidationError, Field
from typing import List

from src.config import GOOGLE_API_KEY, GEMINI_MODEL, require_api_key

from google import genai


class ResumeProfile(BaseModel):
    name: str = Field(default="")
    email: str = Field(default="")
    skills: List[str] = Field(default_factory=list)
    experience_years: float = Field(default=0)
    experience_summary: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    target_role: str = Field(default="")


PARSE_PROMPT = """You are a resume parser. Read the resume text below and extract
ONLY the following fields as a single valid JSON object, with no extra commentary,
no markdown code fences, and no explanation before or after the JSON:

{{
  "name": string,
  "email": string,
  "skills": [string, ...],
  "experience_years": number,
  "experience_summary": [string, ...],   // one short line per role held
  "education": [string, ...],
  "target_role": string                  // best guess at the role this person is targeting
}}

If a field is not present in the resume, use an empty string, empty list, or 0.
Do not invent information that is not in the resume.

RESUME TEXT:
---
{resume_text}
---

Return only the JSON object.
"""


def _extract_json(raw: str) -> dict:
    """Strip markdown fences if the model added them anyway, then parse."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    cleaned = cleaned.replace("json\n", "", 1) if cleaned.startswith("json\n") else cleaned
    return json.loads(cleaned)


def parse_resume(resume_text: str, retries: int = 1) -> ResumeProfile:
    require_api_key()
    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = PARSE_PROMPT.format(resume_text=resume_text)

    last_error = None
    for attempt in range(retries + 1):
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw_text = response.text
        try:
            data = _extract_json(raw_text)
            return ResumeProfile(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            # feed the error back so the model can self-correct on retry
            prompt = PARSE_PROMPT.format(resume_text=resume_text) + (
                f"\n\nYour previous output was invalid JSON or failed validation "
                f"with this error: {e}. Return corrected valid JSON only."
            )
    raise RuntimeError(f"Failed to get valid structured output after retries: {last_error}")
