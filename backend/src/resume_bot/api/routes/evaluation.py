"""
Job Description (JD) matching and candidate fit evaluation endpoint.
"""

from fastapi import APIRouter, HTTPException, status
from resume_bot.rag.models import JobFitEvaluation
from resume_bot.rag.evaluator import evaluate_job_fit
from resume_bot.rag.extractor import get_current_profile
from resume_bot.api.schemas import JDEvalRequest

router = APIRouter(prefix="/api", tags=["Job Description Matching"])


@router.post("/evaluate-jd", response_model=JobFitEvaluation)
async def evaluate_jd(payload: JDEvalRequest):
    """
    Evaluate candidate fit against a provided Job Description (JD).
    Returns a comprehensive scorecard with 0-100 fit score, matched skills,
    missing skill gaps, proof projects, and tailored interview questions.
    """
    profile = get_current_profile(resume_id=payload.resume_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidate resume loaded. Please upload a resume first.",
        )

    try:
        evaluation = evaluate_job_fit(payload.job_description, profile=profile)
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating job fit: {e}",
        )
