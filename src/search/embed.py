"""
Module 2 (part 1): Embeddings + vector database build.
Reads data/jobs/jobs.csv, turns each row into one text "document"
(title + skills + description), embeds every document with Gemini's
embedding model, and saves a FAISS index to disk so we don't have to
re-embed on every app run.

Run this file directly whenever jobs.csv changes:
    python -m src.search.embed
"""
import time
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.config import (
    GOOGLE_API_KEY,
    EMBEDDING_MODEL,
    JOBS_DIR,
    JOBS_INDEX_PATH,
    JOB_TITLE_COL_CANDIDATES,
    JOB_SKILLS_COL_CANDIDATES,
    JOB_DESC_COL_CANDIDATES,
    JOB_LOCATION_COL_CANDIDATES,
    require_api_key,
)


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _row_to_text(row, title_col, skills_col, desc_col, loc_col) -> str:
    parts = []
    if title_col and pd.notna(row.get(title_col)):
        parts.append(f"Job Title: {row[title_col]}")
    if skills_col and pd.notna(row.get(skills_col)):
        parts.append(f"Skills: {row[skills_col]}")
    if desc_col and pd.notna(row.get(desc_col)):
        parts.append(f"Description: {row[desc_col]}")
    if loc_col and pd.notna(row.get(loc_col)):
        parts.append(f"Location: {row[loc_col]}")
    return "\n".join(parts)


def build_job_index(csv_filename: str = "jobs.csv", sample_size: int | None = None):
    """
    Reads the job CSV, builds a FAISS index over it, saves to VECTORSTORE_DIR.
    sample_size: if set, only embeds the first N rows (useful for a quick
    test run before committing to embedding the whole dataset / API cost).
    """
    require_api_key()
    csv_path = JOBS_DIR / csv_filename
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No job CSV found at {csv_path}. Download a dataset from Kaggle "
            f"and place it there as '{csv_filename}'."
        )

    df = pd.read_csv(csv_path)
    print(f"CSV columns found: {list(df.columns)}")
    if sample_size:
        df = df.head(sample_size)

    title_col = _find_col(df, JOB_TITLE_COL_CANDIDATES)
    skills_col = _find_col(df, JOB_SKILLS_COL_CANDIDATES)
    desc_col = _find_col(df, JOB_DESC_COL_CANDIDATES)
    loc_col = _find_col(df, JOB_LOCATION_COL_CANDIDATES)

    if not title_col and not skills_col and not desc_col:
        raise ValueError(
            f"Could not detect job title/skills/description columns. "
            f"Your CSV has columns: {list(df.columns)}. "
            f"Update the *_COL_CANDIDATES lists in src/config.py to match."
        )

    docs = []
    for i, row in df.iterrows():
        text = _row_to_text(row, title_col, skills_col, desc_col, loc_col)
        if not text.strip():
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "row_id": int(i),
                    "title": str(row.get(title_col, "")) if title_col else "",
                    "location": str(row.get(loc_col, "")) if loc_col else "",
                },
            )
        )

    print(f"Embedding {len(docs)} job listings using columns: "
          f"title={title_col}, skills={skills_col}, desc={desc_col}, loc={loc_col}")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)

    # Embed in small batches with a pause between them to stay under the
    # free-tier requests-per-minute limit. If you still hit 429 errors,
    # lower BATCH_SIZE further or increase the sleep time.
    BATCH_SIZE = 20
    SLEEP_SECONDS = 20
    vectorstore = None
    for start in range(0, len(docs), BATCH_SIZE):
        batch = docs[start:start + BATCH_SIZE]
        print(f"  Embedding batch {start}-{start + len(batch)} of {len(docs)}...")
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vectorstore.add_documents(batch)
        if start + BATCH_SIZE < len(docs):
            time.sleep(SLEEP_SECONDS)

    JOBS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(JOBS_INDEX_PATH))
    print(f"Saved FAISS index to {JOBS_INDEX_PATH}")
    return vectorstore


if __name__ == "__main__":
    # Small first run: fast, and safely under free-tier rate limits.
    # Once this works end-to-end, increase sample_size (or remove it
    # entirely to embed the full CSV) — just expect it to take longer.
    build_job_index(sample_size=60)