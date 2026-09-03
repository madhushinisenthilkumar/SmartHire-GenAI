"""
SmartHire GenAI — Streamlit portal.
Week 1 scope: upload a resume, parse it into structured JSON, display it.
Later weeks will add job matching, CV suggestions, and the mentor chat as tabs.
"""
import sys
from pathlib import Path

# allow `import src...` when running `streamlit run app/streamlit_app.py` from project root
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.parsing.loader import load_resume_text
from src.parsing.resume_parser import parse_resume

st.set_page_config(page_title="SmartHire GenAI", page_icon="🎯", layout="centered")
st.title("🎯 SmartHire GenAI")
st.caption("Resume parsing · Job matching · CV suggestions · AI Career Mentor")

tab_parse, tab_jobs, tab_suggest, tab_mentor = st.tabs(
    ["1️⃣ Parse Resume", "2️⃣ Matched Jobs", "3️⃣ CV Suggestions", "4️⃣ Career Mentor"]
)

with tab_parse:
    st.subheader("Upload your resume")
    uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])

    if uploaded is not None:
        with st.spinner("Reading resume..."):
            try:
                text = load_resume_text(uploaded)
            except Exception as e:
                st.error(f"Could not read file: {e}")
                text = None

        if text:
            with st.spinner("Extracting structured profile with Gemini..."):
                try:
                    profile = parse_resume(text)
                    st.session_state["profile"] = profile
                except Exception as e:
                    st.error(f"Parsing failed: {e}")
                    profile = None

            if profile:
                st.success("Profile extracted")
                st.json(profile.model_dump())

with tab_jobs:
   with tab_jobs:
    st.subheader("Jobs matched to your profile")
    profile = st.session_state.get("profile")

    if not profile:
        st.info("Parse a resume in Tab 1 first — job matching uses your extracted profile.")
    else:
        if st.button("Find matching jobs"):
            with st.spinner("Searching the job index..."):
                try:
                    from src.search.job_search import search_jobs_for_profile
                    jobs = search_jobs_for_profile(profile)
                    st.session_state["matched_jobs"] = jobs
                except FileNotFoundError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Job search failed: {e}")

        jobs = st.session_state.get("matched_jobs")
        if jobs:
            for j in jobs:
                with st.container(border=True):
                    st.markdown(f"**{j['title']}**  ·  relevance: {j['relevance']}")
                    if j["location"]:
                        st.caption(j["location"])
                    st.text(j["content"])

with tab_suggest:
    st.info("Coming in Week 1 (Module 3): CV improvement suggestions for a target role.")

with tab_mentor:
    st.info("Coming in Week 2 (Module 4): AI Career Mentor chatbot with RAG.")
