"""
Module 4: AI Career Mentor (RAG).
Retrieves relevant career-notes chunks for a question, then asks Gemini to
answer using ONLY those chunks. If the retrieved chunks don't contain a
real answer, the mentor is instructed to say so rather than guess —
this "grounding" behavior is what Section 8 of the brief evaluates.

Build the career-notes index once (or whenever you edit data/career_notes/):
    python -m src.mentor.rag_chain
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai

from src.config import (
    GOOGLE_API_KEY,
    EMBEDDING_MODEL,
    GEMINI_MODEL,
    CAREER_NOTES_DIR,
    CAREER_INDEX_PATH,
    CAREER_CHUNK_SIZE,
    CAREER_CHUNK_OVERLAP,
    require_api_key,
)

MENTOR_SYSTEM_PROMPT = """You are the AI Career Mentor for SmartHire GenAI. Answer the
candidate's question using ONLY the context documents provided below.

Rules:
- If the answer is not contained in the context, say clearly that you don't have
  information on that in your career notes — do NOT guess or use outside knowledge.
- Be specific and practical, not generic.
- Keep answers concise (3-6 sentences) unless the question needs a list.
- Do not mention "the context" or "the documents" explicitly in your answer — just
  answer naturally, as a mentor who happens to know this.

CONTEXT:
---
{context}
---

QUESTION: {question}
"""

_vectorstore = None


def build_career_index():
    """Chunk and embed every file in data/career_notes/, save FAISS index to disk."""
    require_api_key()
    loader = DirectoryLoader(str(CAREER_NOTES_DIR), glob="*.md", loader_cls=TextLoader)
    raw_docs = loader.load()
    if not raw_docs:
        raise FileNotFoundError(f"No .md files found in {CAREER_NOTES_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CAREER_CHUNK_SIZE, chunk_overlap=CAREER_CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(raw_docs)
    print(f"Loaded {len(raw_docs)} career-note files -> {len(chunks)} chunks")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
    vectorstore = FAISS.from_documents(chunks, embeddings)

    CAREER_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(CAREER_INDEX_PATH))
    print(f"Saved career-notes index to {CAREER_INDEX_PATH}")
    return vectorstore


def _get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        if not CAREER_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"No career-notes index at {CAREER_INDEX_PATH}. "
                f"Run `python -m src.mentor.rag_chain` first to build it."
            )
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
        _vectorstore = FAISS.load_local(
            str(CAREER_INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )
    return _vectorstore


def ask_mentor(question: str, k: int = 4) -> dict:
    """
    Runs the RAG pipeline: retrieve top-k relevant chunks, then ask Gemini
    to answer grounded in them. Returns {"answer": str, "sources": [str, ...]}
    so the UI can optionally show which career notes were used.
    """
    require_api_key()
    vectorstore = _get_vectorstore()
    docs = vectorstore.similarity_search(question, k=k)

    context = "\n\n---\n\n".join(d.page_content for d in docs)
    sources = sorted(set(d.metadata.get("source", "unknown") for d in docs))

    prompt = MENTOR_SYSTEM_PROMPT.format(context=context, question=question)
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)

    return {"answer": response.text.strip(), "sources": sources}


if __name__ == "__main__":
    build_career_index()