"""
Unit tests for Phase 2: Enhanced RAG components.
Tests Pydantic models, Intent Router heuristics, and Job Fit Evaluation structure.
"""

import pytest
from resume_bot.rag.models import (
    CandidateProfile,
    CategorizedSkills,
    WorkExperienceItem,
    ProjectItem,
    EducationItem,
    JobFitEvaluation,
    QueryIntent,
)
from resume_bot.rag.router import classify_intent


def test_candidate_profile_model():
    profile = CandidateProfile(
        full_name="Anand Jaiswal",
        headline_or_role="Full Stack Engineer",
        skills=CategorizedSkills(
            languages=["Python", "TypeScript"],
            backend=["FastAPI", "Node.js"],
            databases=["PostgreSQL", "ChromaDB"],
        ),
        work_experience=[
            WorkExperienceItem(
                company="DevX Alpha",
                role="Full Stack Web Intern",
                duration="July 2025 – August 2025",
                responsibilities=["Developed backend APIs", "Integrated Redis"],
            )
        ],
        projects=[
            ProjectItem(
                title="LiveQuiz",
                technologies=["Next.js", "Socket.io"],
                description="Real-time quiz platform",
            )
        ],
        education=[
            EducationItem(
                institution="BIET Jhansi",
                degree="B.Tech ECE",
                duration="2023 - 2027",
                score="8.21",
            )
        ],
        certifications=["Oracle AI Associate"],
    )

    dumped = profile.model_dump()
    assert dumped["full_name"] == "Anand Jaiswal"
    assert "Python" in dumped["skills"]["languages"]
    assert len(dumped["work_experience"]) == 1
    assert dumped["work_experience"][0]["company"] == "DevX Alpha"


def test_job_fit_evaluation_model():
    eval_result = JobFitEvaluation(
        candidate_name="Anand Jaiswal",
        target_role="Full Stack AI Engineer",
        fit_score=92,
        verdict="Strong Match",
        strengths=["Strong Python & LangChain experience", "Full stack TypeScript/Next.js foundation"],
        matched_skills=["Python", "FastAPI", "Next.js", "LangChain", "PostgreSQL"],
        missing_skills_or_gaps=["GraphQL", "Terraform"],
        relevant_projects=["LiveQuiz", "AI Resume Bot"],
        recommendation_summary="High-potential engineer with outstanding foundation in modern GenAI stacks.",
        suggested_interview_questions=[
            "How did you implement low-latency WebSocket synchronization in LiveQuiz?",
            "How do you handle context window optimization and chunking in LangChain RAG?",
        ],
    )

    assert eval_result.fit_score == 92
    assert eval_result.verdict == "Strong Match"
    assert len(eval_result.matched_skills) == 5
    assert len(eval_result.missing_skills_or_gaps) == 2


def test_intent_router_greetings():
    greetings = ["hi", "hello", "hey", "help", "who are you", "what can you do"]
    for g in greetings:
        res = classify_intent(g)
        assert res.intent == "GENERAL_CONVERSATION", f"Failed for '{g}'"


def test_intent_router_jd_heuristics():
    jd_sample = """
    Job Description: Senior Full Stack Developer
    Requirements:
    - 3+ years experience with React, Next.js, and TypeScript
    - Strong knowledge of Node.js and PostgreSQL
    - Experience with Docker and CI/CD pipelines
    - Responsibilities: Design and implement high-scale microservices
    """
    res = classify_intent(jd_sample)
    assert res.intent == "JD_EVALUATION"
    assert res.extracted_jd is not None
