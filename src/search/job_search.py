"""
Module 2 (part 2): Semantic job search.
Loads the FAISS index built by embed.py, embeds a query (e.g. the parsed
resume profile), and returns the top-N most similar job listings with
similarity scores.
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import GOOGLE_API_KEY, EMBEDDING_MODEL, JOBS_INDEX_PATH, TOP_N_JOBS
from src.parsing.resume_parser import ResumeProfile

_vectorstore = None  # cached after first load so repeated searches don't reload from disk


def _get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        if not JOBS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"No job index found at {JOBS_INDEX_PATH}. "
                f"Run `python -m src.search.embed` first to build it."
            )
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
        _vectorstore = FAISS.load_local(
            str(JOBS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )
    return _vectorstore


def profile_to_query(profile: ResumeProfile) -> str:
    """Turn a structured resume profile into a single text query for embedding."""
    parts = []
    if profile.target_role:
        parts.append(f"Target role: {profile.target_role}")
    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")
    if profile.experience_summary:
        parts.append(f"Experience: {'; '.join(profile.experience_summary)}")
    return "\n".join(parts) or "General candidate profile"


def search_jobs(query: str, top_n: int = TOP_N_JOBS) -> list[dict]:
    """
    Runs semantic search over the job index. Returns a list of dicts:
    { "title": str, "location": str, "content": str, "score": float }
    """
    vectorstore = _get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=top_n)

    output = []
    for doc, distance in results:
        relevance = 1 / (1 + distance)
        output.append({
            "title": doc.metadata.get("title", "Unknown"),
            "location": doc.metadata.get("location", ""),
            "content": doc.page_content,
            "relevance": round(relevance, 3),
        })
    return output


def search_jobs_for_profile(profile: ResumeProfile, top_n: int = TOP_N_JOBS) -> list[dict]:
    query = profile_to_query(profile)
    return search_jobs(query, top_n=top_n)