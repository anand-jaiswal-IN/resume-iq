"""
Job Description (JD) Matcher and Candidate Fit Evaluator.
Performs comprehensive multi-factor scoring against job descriptions using:
  1. Complete structured CandidateProfile
  2. Targeted vector retrieval for JD-specific technical competencies
  3. Structured Gemini output generating quantitative scores, skill gaps, and interview questions.
"""

from langchain_core.prompts import ChatPromptTemplate
from resume_bot.rag.chain import get_llm, safe_invoke_retriever
from resume_bot.rag.models import CandidateProfile, JobFitEvaluation
from resume_bot.rag.extractor import get_current_profile
from resume_bot.vectorstore.store import get_retriever


EVALUATOR_SYSTEM = """You are a Principal Technical Recruiter, Staff Engineer, and Talent Partner.
You are evaluating a candidate's resume against a specific Job Description (JD).

Scoring Guidelines:
- **85 - 100 (Strong Match)**: Candidate covers virtually all must-have technical skills, frameworks, and architectural experience, and has concrete project or professional proof.
- **70 - 84 (Good Match)**: Solid foundation with 70%+ core tech stack match; minor gaps in secondary tools that can be learned quickly on the job.
- **50 - 69 (Moderate Fit)**: Candidate has transferable skills (e.g. good Python/JS fundamentals), but lacks direct hands-on experience in several required stack components.
- **< 50 (Low Fit)**: Significant mismatch in role domain, language ecosystem, or seniority expectations.

Evaluation Rules:
1. Be objective, realistic, and rigorous. Do NOT artificially inflate scores.
2. Ground matched skills ONLY in concrete resume evidence.
3. Explicitly enumerate missing skills or experience gaps found in the JD.
4. Highlight which specific candidate projects provide real-world proof of capability.
5. Provide 3 high-signal technical interview questions designed to test the candidate on their matching areas or verify borderline gaps.
"""

EVALUATOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", EVALUATOR_SYSTEM),
        (
            "human",
            "CANDIDATE PROFILE:\n{profile_json}\n\n"
            "ADDITIONAL RETRIEVED RESUME CONTEXT:\n{retrieved_context}\n\n"
            "JOB DESCRIPTION TO EVALUATE AGAINST:\n{job_description}\n\n"
            "Perform a comprehensive fit analysis and return the structured JobFitEvaluation.",
        ),
    ]
)


def evaluate_job_fit(job_description: str, profile: CandidateProfile | None = None) -> JobFitEvaluation:
    """
    Evaluate candidate fit against a provided Job Description.

    Args:
        job_description: The full text of the job description or role requirements.
        profile: The structured candidate profile. If None, loaded from cache.

    Returns:
        Structured JobFitEvaluation with score, strengths, gaps, and interview questions.
    """
    if profile is None:
        profile = get_current_profile()

    if profile is None:
        raise ValueError("No candidate profile loaded. Please load a resume PDF first.")

    # Retrieve specific vector chunks matching the JD key phrases
    retriever = get_retriever()
    retrieved_docs = safe_invoke_retriever(retriever, job_description[:500])
    retrieved_context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    llm = get_llm()
    structured_llm = llm.with_structured_output(JobFitEvaluation)

    evaluator_chain = EVALUATOR_PROMPT | structured_llm

    result: JobFitEvaluation = evaluator_chain.invoke(
        {
            "profile_json": profile.model_dump_json(indent=2),
            "retrieved_context": retrieved_context,
            "job_description": job_description,
        }
    )

    return result
