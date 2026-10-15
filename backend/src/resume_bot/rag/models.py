"""
Structured Pydantic models for Enhanced RAG.
Includes candidate profile extraction, job description evaluation, and query intent classification.
"""

from typing import Literal
from pydantic import BaseModel, Field


# ── Query Intent Classification ───────────────────────────────────────────────

class QueryIntent(BaseModel):
    """Classifies the user's intent to route to the appropriate pipeline."""

    intent: Literal["FACTUAL_QA", "JD_EVALUATION", "RESUME_SUMMARY", "GENERAL_CONVERSATION"] = Field(
        description=(
            "The detected intent of the user message:\n"
            "- 'JD_EVALUATION': User provides a job description or asks to evaluate/rate/match candidate for a role.\n"
            "- 'GENERAL_CONVERSATION': Greetings, meta-questions about bot capabilities ('can you evaluate JDs?', 'what can you do?'), polite chatter.\n"
            "- 'RESUME_SUMMARY': User asks for a complete overview, elevator pitch, or summary of the candidate.\n"
            "- 'FACTUAL_QA': Specific questions asking for facts from the resume (skills, experience, college, projects, links)."
        )
    )
    explanation: str = Field(
        description="Brief 1-sentence reason for this classification."
    )
    extracted_jd: str | None = Field(
        default=None,
        description="If the user provided a job description in their message, extract it here. Otherwise null."
    )


# ── Full Structured Candidate Profile ─────────────────────────────────────────

class WorkExperienceItem(BaseModel):
    company: str = Field(description="Company or organization name")
    role: str = Field(description="Job title or role")
    duration: str = Field(description="Duration or dates of employment")
    responsibilities: list[str] = Field(default_factory=list, description="Key duties and achievements")


class ProjectItem(BaseModel):
    title: str = Field(description="Project title")
    technologies: list[str] = Field(default_factory=list, description="Technologies and frameworks used")
    description: str = Field(description="Description of what was built and its impact")
    link: str | None = Field(default=None, description="Project demo or repo URL if present")


class EducationItem(BaseModel):
    institution: str = Field(description="University, college or school name")
    degree: str = Field(description="Degree or qualification name")
    duration: str = Field(description="Dates or graduation year")
    score: str | None = Field(default=None, description="CGPA, percentage or grade if present")


class CategorizedSkills(BaseModel):
    languages: list[str] = Field(default_factory=list, description="Programming languages (e.g. Python, TypeScript)")
    frontend: list[str] = Field(default_factory=list, description="Frontend frameworks and libraries (e.g. React, Next.js, Tailwind)")
    backend: list[str] = Field(default_factory=list, description="Backend frameworks & runtimes (e.g. Node, Express, FastAPI, Django)")
    databases: list[str] = Field(default_factory=list, description="Databases & caches (e.g. PostgreSQL, Redis, ChromaDB)")
    cloud_and_devops: list[str] = Field(default_factory=list, description="Cloud, CI/CD, containerization (e.g. Docker, Kubernetes, AWS)")
    ai_and_ml: list[str] = Field(default_factory=list, description="AI, GenAI, LangChain, vector DBs, LLM tools")
    tools: list[str] = Field(default_factory=list, description="Other developer tools (e.g. Git, Postman, Linux)")


class CandidateProfile(BaseModel):
    """Complete, structured representation of a candidate's resume."""

    full_name: str = Field(description="Candidate's full name")
    headline_or_role: str = Field(description="Current professional headline or role")
    summary: str | None = Field(default=None, description="Professional summary or bio if provided")
    contact_email: str | None = Field(default=None, description="Email address")
    contact_phone: str | None = Field(default=None, description="Phone number")
    location: str | None = Field(default=None, description="City, state, country")
    links: list[str] = Field(default_factory=list, description="URLs such as LinkedIn, GitHub, portfolio")
    skills: CategorizedSkills = Field(default_factory=CategorizedSkills, description="Categorized technical skills")
    work_experience: list[WorkExperienceItem] = Field(default_factory=list, description="List of work experiences")
    projects: list[ProjectItem] = Field(default_factory=list, description="Key projects built")
    education: list[EducationItem] = Field(default_factory=list, description="Education history")
    certifications: list[str] = Field(default_factory=list, description="Licenses and certifications")


# ── Job Fit / JD Evaluation Result ────────────────────────────────────────────

class JobFitEvaluation(BaseModel):
    """Detailed evaluation of how well the candidate matches a given Job Description."""

    candidate_name: str = Field(description="Name of the candidate evaluated")
    target_role: str = Field(description="Role or title derived from the Job Description")
    fit_score: int = Field(
        description="Quantitative fit rating from 0 to 100 based on skill overlap, experience depth, and relevance."
    )
    verdict: Literal["Strong Match", "Good Match", "Moderate Fit", "Low Fit / Significant Upskilling Needed"] = Field(
        description="Overall hiring recommendation verdict"
    )
    strengths: list[str] = Field(
        description="Top 3 to 5 areas where the candidate strongly matches or exceeds JD requirements"
    )
    matched_skills: list[str] = Field(
        description="List of skills explicitly required in the JD that the candidate possesses"
    )
    missing_skills_or_gaps: list[str] = Field(
        description="Skills or qualifications required in the JD that are NOT evident in the resume"
    )
    relevant_projects: list[str] = Field(
        description="Candidate projects that provide direct proof of competency for this JD"
    )
    recommendation_summary: str = Field(
        description="Recruiter summary: A 2-3 sentence balanced executive takeaway on hiring this candidate for this role."
    )
    suggested_interview_questions: list[str] = Field(
        default_factory=list,
        description="3 tailored technical questions to validate the candidate's gaps or deepest skills during an interview"
    )
