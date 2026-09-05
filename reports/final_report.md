# Final Report — SmartHire GenAI

## What this project does
SmartHire GenAI is a career portal where a student uploads a resume and gets four things back: 
a structured profile, semantically matched jobs, tailored CV improvement suggestions, and a chatbot that answers career questions
grounded in a small knowledge base I wrote — rather than just answering from the model's general training.

## Design choices

**LLM: Google Gemini.** I used Gemini for both text generation and
embeddings, via the `google-genai` SDK. Partway through the project Google deprecated the older `google-generativeai` package, so I migrated to the current SDK mid-build — a good reminder that fast-moving AI APIs need code that's easy to swap models/SDKs in, not hardcoded assumptions.

**Structured output with Pydantic.** Both the resume parser (Module 1) and the CV suggestion generator (Module 3) ask Gemini for JSON in a strict shape, then validate it with Pydantic models before trusting it. If the JSON is malformed, the code retries once with the validation error fed back into the prompt so the model can self-correct. I did this instead of trusting raw
model output directly, since LLMs occasionally return slightly malformed JSON (extra text, markdown fences, etc.) and I wanted the app to fail loudly and retry rather than silently use garbage data.

**FAISS for both job search and the mentor's knowledge base.** I used the same embed-and-search pattern twice: once over job postings (Module 2), once over career-advice documents I wrote myself (Module 4). Keeping these as two separate FAISS indexes (`jobs_index`, `career_index`) rather than one
combined index kept the two very different kinds of content (job listings vs. advice articles) from polluting each other's search results.

**Guardrails as a separate, fast layer before the LLM call.** Rather than relying only on the mentor's grounding behavior to reject bad  input, Module 5 adds a lightweight regex-based check that runs before any Gemini call in either the mentor chat or the CV suggestions tab. This is intentionally simple (pattern matching, not another LLM call) so it doesn't add latency or burn API quota just to decide whether to even make the real call.

## What worked well
The RAG mentor's grounding behavior held up under real testing — it correctly refused an out-of-scope question ("what's the capital of France?") instead of hallucinating an answer, and gave accurate,specific answers (traceable back to the actual career-notes files) for four different in-scope questions.

Job matching returned a 100% relevant hit rate (5/5) for the one     resume tested, even with a small (60-job) index — suggesting the embedding approach generalizes well even with limited data.

Testing deliberately, rather than only checking the happy path, actually caught a real bug: my guardrail regex only blocked the plural "instructions," missing the singular "instruction" — a genuine prompt-injection gap that I found and fixed (full before/after in `answer_quality.md`).

## Limitations
- **Job index size.** The FAISS job index currently holds only a 60-row
  sample of the full 22,000-row Naukri dataset, kept small during
  development to control API usage and iteration speed. This should be
  increased before treating the matching results as representative of the
  full dataset.
- **Small evaluation sample.** I tested 1 resume for job matching and 4
  questions for the mentor. This is enough to demonstrate the pipeline
  works correctly, but not enough to make strong claims about accuracy
  across a wide variety of resumes/questions.
- **Guardrails are pattern-based, not exhaustive.** The regex-based
  guardrail catches known phrasings I specifically wrote patterns for
  (and one gap I found and fixed), but it isn't a general-purpose contentclassifier — a differently-worded unsafe request could still slip through. A more robust version would likely use a small LLM-based classifier as a second layer, at the cost of extra latency/API calls.
- **Free-tier API limits.** Development was repeatedly interrupted by
  Gemini's free-tier rate limits (both per-minute and per-day caps),
  which shaped some design decisions — e.g. embedding in small batches
  with pauses, and switching to a lighter model (`gemini-flash-lite-latest`)
  for day-to-day testing to preserve quota.

## A note on how this was built
I used Claude (an AI coding assistant) heavily throughout this project —
for writing the initial code structure, debugging environment issues
(a Python 3.14 compatibility problem, an SDK deprecation, a Windows
PowerShell/venv mixup), and reviewing/fixing bugs I found during testing (the guardrail regex gap above). My own role was directing what to build, running and testing everything on my actual machine, catching real issues through hands-on testing, and deciding what to fix and how. I think this is worth stating plainly rather than leaving ambiguous — the brief's own tools (LangChain, structured output, RAG) assume AI-assisted development is part of how this kind of project gets built today.