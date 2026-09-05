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
    st.subheader("CV improvement suggestions")
    profile = st.session_state.get("profile")

    if not profile:
        st.info("Parse a resume in Tab 1 first.")
    else:
        matched_jobs = st.session_state.get("matched_jobs", [])
        job_options = ["(type my own target job below)"] + [j["title"] for j in matched_jobs]
        choice = st.selectbox("Target job", job_options)

        if choice == job_options[0]:
            job_text = st.text_area(
                "Paste or describe the target job",
                placeholder="e.g. Data Analyst role requiring SQL, Python, Tableau, 2+ years experience...",
            )
        else:
            job_text = next(j["content"] for j in matched_jobs if j["title"] == choice)
            st.text(job_text)

        if st.button("Generate suggestions"):
            if not job_text or not job_text.strip():
                st.warning("Enter or select a target job first.")
            else:
                from src.safety.guardrails import check_input
                check = check_input(job_text)
                if not check["allowed"]:
                    st.warning(check["reason"])
                else:
                    with st.spinner("Generating suggestions with Gemini..."):
                        try:
                            from src.generate.cv_suggestions import generate_cv_suggestions
                            suggestions = generate_cv_suggestions(profile, job_text)
                            st.session_state["suggestions"] = suggestions
                        except Exception as e:
                            st.error(f"Suggestion generation failed: {e}")

        suggestions = st.session_state.get("suggestions")
        if suggestions:
            st.markdown("**Missing skills**")
            st.write(suggestions.missing_skills or "None identified")
            st.markdown("**Weak bullet points**")
            st.write(suggestions.weak_bullet_points or "None identified")
            st.markdown("**Rewritten summary**")
            st.info(suggestions.rewritten_summary or "—")
            
with tab_mentor:
    st.subheader("AI Career Mentor")
    st.caption("Answers are grounded in the career notes knowledge base — it will say so if it doesn't know.")

    if "mentor_history" not in st.session_state:
        st.session_state["mentor_history"] = []

    for role, text in st.session_state["mentor_history"]:
        with st.chat_message(role):
            st.write(text)

    question = st.chat_input("Ask a career question...")
    if question:
        from src.safety.guardrails import check_input
        check = check_input(question)

        st.session_state["mentor_history"].append(("user", question))
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            if not check["allowed"]:
                st.warning(check["reason"])
                st.session_state["mentor_history"].append(("assistant", check["reason"]))
            else:
                with st.spinner("Thinking..."):
                    try:
                        from src.mentor.rag_chain import ask_mentor
                        result = ask_mentor(question)
                        st.write(result["answer"])
                        if result["sources"]:
                            st.caption("Sources: " + ", ".join(s.split("/")[-1] for s in result["sources"]))
                        st.session_state["mentor_history"].append(("assistant", result["answer"]))
                    except FileNotFoundError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Mentor failed: {e}")