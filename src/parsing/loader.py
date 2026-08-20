"""
Module 1 (part 1): Document loading.
Reads a PDF or DOCX resume from a file-like object or path and returns raw text.
"""
from pathlib import Path
from pypdf import PdfReader
from docx import Document


def load_resume_text(file) -> str:
    """
    Accepts either:
      - a path (str/Path) to a .pdf or .docx file, or
      - a file-like object with a .name attribute (e.g. Streamlit's UploadedFile)
    Returns the extracted raw text as a single string.
    """
    name = getattr(file, "name", str(file))
    suffix = Path(name).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(file)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    elif suffix == ".docx":
        doc = Document(file)
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf or .docx")

    text = text.strip()
    if not text:
        raise ValueError("No extractable text found in the resume file.")
    return text
