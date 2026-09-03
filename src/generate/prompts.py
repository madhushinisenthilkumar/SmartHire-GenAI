"""
Module 3: Prompt library.
Centralizes the prompts used to generate CV improvement suggestions.
Keeping prompts here (instead of inline in cv_suggestions.py) makes it easy
to compare versions for the evaluation report's "before/after prompt" section.
"""

# v1: baseline prompt
CV_SUGGESTION_PROMPT_V1 = """You are a career coach. Given a candidate's resume profile and a
target job, suggest improvements.

Candidate profile:
{profile_text}

Target job:
{job_text}

Give suggestions.
"""

# v2: improved — strict structure, grounded, asks for specifics not generic advice
CV_SUGGESTION_PROMPT_V2 = """You are an expert career coach and resume writer. Compare the
candidate's profile against the target job below, and return ONLY a valid JSON object
(no markdown fences, no commentary) with this exact shape:

{{
  "missing_skills": [string, ...],       // skills the job wants that the candidate's profile doesn't show
  "weak_bullet_points": [string, ...],   // specific existing experience lines that are vague or underselling — quote or paraphrase them
  "rewritten_summary": string            // a 2-3 sentence professional summary tailored to this target job, using ONLY facts present in the candidate's profile
}}

Rules:
- Base every suggestion on the actual candidate profile and job text given below — do not invent skills or experience the candidate doesn't have.
- Be specific, not generic ("add more detail" is not acceptable; name the actual gap).
- rewritten_summary must not claim skills or experience absent from the profile.

CANDIDATE PROFILE:
---
{profile_text}
---

TARGET JOB:
---
{job_text}
---

Return only the JSON object.
"""