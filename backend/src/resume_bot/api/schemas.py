"""
Pydantic schemas for the FastAPI REST and WebSocket endpoints.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field
from resume_bot.rag.models import CandidateProfile, JobFitEvaluation


# ── Health & Status ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    message: str = "AI Resume Bot API is running"


class ResumeStatusResponse(BaseModel):
    is_loaded: bool = Field(description="Whether a resume is currently loaded in the system")
    file_name: str | None = Field(default=None, description="Name of the active resume file")
    candidate_name: str | None = Field(default=None, description="Name of the candidate if extracted")
    headline: str | None = Field(default=None, description="Current title or headline of candidate")
    total_chunks: int = Field(default=0, description="Total indexed chunks in Qdrant")
    total_links: int = Field(default=0, description="Number of hyperlinks extracted")
    active_resume_id: str | None = Field(default=None, description="Active resume unique identifier")
    total_resumes: int = Field(default=0, description="Total count of resumes present in the backend")


class StatsResponse(BaseModel):
    collection_name: str
    document_count: int
    has_profile: bool
    candidate_name: str | None = None


# ── Multiple Resume Management ────────────────────────────────────────────────

class ResumeItem(BaseModel):
    id: str = Field(description="Unique ID for the resume")
    file_name: str = Field(description="Original filename of the resume PDF")
    file_size: int = Field(default=0, description="File size in bytes")
    uploaded_at: str = Field(description="ISO timestamp of when the resume was uploaded")
    candidate_name: str | None = Field(default=None, description="Extracted candidate name")
    headline: str | None = Field(default=None, description="Extracted headline or title")
    total_pages: int = Field(default=1, description="Number of pages")
    total_chunks: int = Field(default=0, description="Indexed semantic chunks")
    links_count: int = Field(default=0, description="Number of extracted hyperlinks")
    is_active: bool = Field(default=False, description="Whether this resume is currently active")


class ResumeListResponse(BaseModel):
    resumes: list[ResumeItem] = Field(default_factory=list, description="List of all indexed resumes")
    active_resume_id: str | None = Field(default=None, description="ID of the currently active resume")
    total: int = Field(default=0, description="Total number of resumes in the system")


class ActivateResumeResponse(BaseModel):
    success: bool
    message: str
    active_resume: ResumeItem | None = None


# ── Resume Ingestion & Profile ────────────────────────────────────────────────

class UploadResumeResponse(BaseModel):
    success: bool
    message: str
    id: str = Field(description="Unique ID assigned to the uploaded resume")
    file_name: str
    file_size: int = 0
    uploaded_at: str
    total_pages: int
    total_chunks: int
    links_count: int
    candidate_name: str
    headline: str
    is_active: bool = True


class LinksResponse(BaseModel):
    file_name: str | None
    total_links: int
    links: list[str]


class SummaryResponse(BaseModel):
    candidate_name: str
    summary: str


# ── Chat & Sessions ───────────────────────────────────────────────────────────

class ChatSessionSummarySchema(BaseModel):
    id: str
    resume_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: str | None = None


class ChatMessageSchema(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: str
    intent: str | None = None
    jd_result: JobFitEvaluation | None = None


class ChatSessionDetailSchema(BaseModel):
    id: str
    resume_id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ChatMessageSchema] = []


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, description="Optional custom session title")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's question, prompt, or message")
    session_id: str = Field(default="default", description="Conversation session ID for memory")
    resume_id: str | None = Field(default=None, description="Target resume ID to chat with")


class ChatResponse(BaseModel):
    answer: str = Field(description="Answer or response from the assistant")
    intent: str = Field(description="Detected query intent")
    session_id: str = Field(description="Session ID used for this interaction")
    resume_id: str | None = Field(default=None, description="Resume ID associated with this chat")
    jd_evaluation: JobFitEvaluation | None = Field(
        default=None,
        description="Populated if the query was a Job Description evaluation request"
    )


# ── Job Description Evaluation ────────────────────────────────────────────────

class JDEvalRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=20,
        description="Full text of the Job Description or role requirements to match against"
    )
    resume_id: str | None = Field(
        default=None,
        description="Optional resume ID to evaluate against. Defaults to active resume."
    )


# ── Chat History (Legacy / Compatibility) ─────────────────────────────────────

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]


# ── WebSocket Messages ────────────────────────────────────────────────────────

class WebSocketIncomingMessage(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default="default")
    resume_id: str | None = Field(default=None)


class WebSocketEvent(BaseModel):
    type: Literal["intent", "token", "done", "jd_result", "error"]
    content: Any = None
    session_id: str | None = None
    resume_id: str | None = None
