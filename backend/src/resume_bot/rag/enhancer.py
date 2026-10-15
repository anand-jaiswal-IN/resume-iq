"""
Enhanced RAG techniques:
  1. Query Rewriter: Expands/rewrites conversational questions into keyword-rich retrieval queries.
  2. Candidate Summarizer: Generates high-level executive summaries using the structured profile.
  3. Conversational Responder: Generates helpful responses for greetings & capability queries.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from resume_bot.rag.chain import get_llm
from resume_bot.rag.extractor import get_current_profile
from resume_bot.rag.models import CandidateProfile


# ── Query Rewriter ────────────────────────────────────────────────────────────

REWRITER_SYSTEM = """You are a search query optimizer for resume retrieval.
Given a user question, generate a concise, keyword-dense search query optimized to retrieve
the exact relevant sections, tools, metrics, and bullet points from a candidate's resume.
Include synonyms and related technical keywords where relevant.
Output ONLY the optimized query string, nothing else.
"""

REWRITER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", REWRITER_SYSTEM),
        ("human", "Original user question: {question}\n\nOptimized search query:"),
    ]
)


def rewrite_query(question: str) -> str:
    """Rewrite a conversational question into a keyword-rich query for vector retrieval."""
    # If the question is already short and specific, keep it
    if len(question.split()) <= 4:
        return question

    llm = get_llm()
    chain = REWRITER_PROMPT | llm | StrOutputParser()
    try:
        rewritten = chain.invoke({"question": question})
        return str(rewritten).strip()
    except Exception:
        return question


# ── Candidate Summarizer ──────────────────────────────────────────────────────

SUMMARY_SYSTEM = """You are a senior executive recruiter.
Based on the candidate's structured profile, generate a compelling, factual 3-paragraph executive summary:
Paragraph 1: Core identity, current role, years of experience/education, and primary domain.
Paragraph 2: Deep technical competencies (languages, frameworks, databases, cloud, AI/ML tools).
Paragraph 3: Key standout projects and tangible achievements.
Maintain strict factual grounding from the profile.
"""

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SUMMARY_SYSTEM),
        ("human", "Candidate Profile:\n{profile_json}\n\nGenerate executive summary:"),
    ]
)


def generate_candidate_summary(profile: CandidateProfile | None = None) -> str:
    """Generate an executive summary of the candidate's profile."""
    if profile is None:
        profile = get_current_profile()

    if profile is None:
        return "No resume profile loaded. Please load a resume PDF first."

    llm = get_llm()
    chain = SUMMARY_PROMPT | llm | StrOutputParser()
    return str(chain.invoke({"profile_json": profile.model_dump_json(indent=2)}))


# ── Conversational Responder (Capabilities & Greetings) ───────────────────────

CONVERSATION_SYSTEM = """You are the AI Resume Bot assistant.
You help recruiters, hiring managers, and candidates analyze resumes, perform technical Q&A, and evaluate candidate fit against Job Descriptions (JDs).

Your capabilities:
1. **Factual Q&A**: Ask anything about the candidate's skills, work experience, projects, education, CGPA, and certifications.
2. **Hyperlinks**: Extract and display all portfolio, GitHub, LinkedIn, and demo links.
3. **Job Description (JD) Evaluation & Match Scoring**: The user can provide a Job Description (via chat or `/match`), and you will evaluate candidate fit with a 0-100% score, identify strengths, pinpoint missing skill gaps, match relevant projects, and suggest tailored technical interview questions.
4. **Executive Summary**: Generate high-level summaries of the candidate's background.

Respond politely and helpfully to the user. If they are asking if you can evaluate a JD or how to provide one, enthusiastically explain that you CAN, and invite them to paste the JD directly into chat or use the `/match` command!
"""

CONVERSATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CONVERSATION_SYSTEM),
        ("human", "{query}"),
    ]
)


def respond_conversationally(query: str) -> str:
    """Answer meta-questions, greetings, and capability inquiries."""
    llm = get_llm()
    chain = CONVERSATION_PROMPT | llm | StrOutputParser()
    return str(chain.invoke({"query": query}))
