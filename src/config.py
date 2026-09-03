"""
Central config: loads environment variables and defines shared paths/constants.
Every other module should import from here instead of hardcoding paths or model names.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root

# --- API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
RESUMES_DIR = DATA_DIR / "resumes"
CAREER_NOTES_DIR = DATA_DIR / "career_notes"
VECTORSTORE_DIR = ROOT_DIR / "vectorstore"
JOBS_INDEX_PATH = VECTORSTORE_DIR / "jobs_index"
CAREER_INDEX_PATH = VECTORSTORE_DIR / "career_index"

# --- App params ---
TOP_N_JOBS = 5

# --- Job CSV column names ---
# The Naukri Kaggle dataset's exact headers vary slightly by upload.
# job_search.py auto-detects from these candidate lists, so you usually
# don't need to touch this — but if detection fails, hardcode the exact
# column names here after checking your CSV in Excel.
JOB_TITLE_COL_CANDIDATES = ["jobtitle", "Job Title", "job_title", "Title"]
JOB_SKILLS_COL_CANDIDATES = ["skills", "Key Skills", "Skills"]
JOB_DESC_COL_CANDIDATES = ["jobdescription", "Job Description", "Role", "job_description", "description"]
JOB_LOCATION_COL_CANDIDATES = ["joblocation_address", "Location", "location"]
CAREER_CHUNK_SIZE = 500
CAREER_CHUNK_OVERLAP = 50


def require_api_key():
    """Call this before making any LLM call — fails fast with a clear message."""
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your Gemini API key."
        )
