"""
Module 3: CV Improvement Generator.
Given the candidate's parsed profile and a target job's text, asks Gemini
for missing skills, weak bullet points, and a rewritten summary — validated
with Pydantic, same pattern as Module 1's resume parser.
"""
import json
from google import genai
from pydantic import BaseModel, ValidationError, Field
from typing import List

from src.config import GOOGLE_API_KEY, GEMINI_MODEL, require_api_key
from src.parsing.resume_parser import ResumeProfile
from src.generate.prompts import CV_SUGGESTION_PROMPT_V2


class CVSuggestions(BaseModel):
    missing_skills: List[str] = Field(default_factory=list)
    weak_bullet_points: List[str] = Field(default_factory=list)
    rewritten_summary: str = Field(default="")


def _profile_to_text(profile: ResumeProfile) -> str:
    return (
        f"Name: {profile.name}\n"
        f"Target role: {profile.target_role}\n"
        f"Skills: {', '.join(profile.skills)}\n"
        f"Experience: {'; '.join(profile.experience_summary)}\n"
        f"Education: {'; '.join(profile.education)}"
    )


def _extract_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    return json.loads(cleaned)


def generate_cv_suggestions(profile: ResumeProfile, job_text: str, retries: int = 1) -> CVSuggestions:
    require_api_key()
    client = genai.Client(api_key=GOOGLE_API_KEY)
    profile_text = _profile_to_text(profile)
    prompt = CV_SUGGESTION_PROMPT_V2.format(profile_text=profile_text, job_text=job_text)

    last_error = None
    for attempt in range(retries + 1):
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        try:
            data = _extract_json(response.text)
            return CVSuggestions(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            prompt = CV_SUGGESTION_PROMPT_V2.format(profile_text=profile_text, job_text=job_text) + (
                f"\n\nYour previous output was invalid: {e}. Return corrected valid JSON only."
            )
    raise RuntimeError(f"Failed to get valid CV suggestions after retries: {last_error}")