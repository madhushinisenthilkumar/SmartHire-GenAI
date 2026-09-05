# SmartHire GenAI — Resume Matching & AI Career Mentor

An end-to-end Generative AI career portal: upload a resume, get a structured profile,
find matching jobs by semantic search, get AI-generated CV improvement suggestions,
and chat with a RAG-based AI Career Mentor.

Built with: Google Gemini · Embeddings · FAISS · LangChain · Streamlit

## Status
- [x] Project scaffold
- [x] Module 1: Resume Parser (structured output)
- [x] Module 2: Semantic Job Search (FAISS)
- [x] Module 3: CV Improvement Generator
- [x] Module 4: AI Career Mentor (RAG)
- [x] Module 5: Guardrails
- [ ] Module 6: Deploy on Streamlit Community Cloud

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Gemini API key
   (get one free at https://aistudio.google.com/apikey):
   ```bash
   cp .env.example .env
   ```
4. Run the app:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Project structure
See `src/` for the pipeline code (parsing, search, generate, mentor, safety) and
`app/streamlit_app.py` for the UI. Full layout in the project brief.

## Demo
_Deployed link goes here once Module 6 is done._
