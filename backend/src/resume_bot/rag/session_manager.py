"""
Session and chat history manager per resume.
Persists sessions and conversation logs to data/chat_sessions.json.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

from resume_bot.config import DATA_DIR

SESSIONS_FILE = DATA_DIR.parent / "chat_sessions.json"


class ChatMessageRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:10]}")
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Message body text")
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%I:%M %p"))
    intent: str | None = None
    jd_result: dict | None = None


class ChatSessionData(BaseModel):
    id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    resume_id: str
    title: str = "New Chat"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: list[ChatMessageRecord] = []


class ChatSessionSummary(BaseModel):
    id: str
    resume_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: str | None = None


def _load_all_sessions() -> dict[str, list[ChatSessionData]]:
    """Load sessions dictionary mapping resume_id -> list[ChatSessionData]."""
    if not SESSIONS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            result = {}
            for res_id, s_list in raw.items():
                result[res_id] = [ChatSessionData.model_validate(s) for s in s_list]
            return result
    except Exception:
        return {}


def _save_all_sessions(data: dict[str, list[ChatSessionData]]) -> None:
    """Save sessions dictionary to disk atomically."""
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = SESSIONS_FILE.with_suffix(".tmp")
    serialized = {
        res_id: [s.model_dump() for s in s_list] for res_id, s_list in data.items()
    }
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)
    temp_file.replace(SESSIONS_FILE)


def list_sessions(resume_id: str) -> list[ChatSessionSummary]:
    """List all sessions for a specific resume, sorted by updated_at descending."""
    all_sessions = _load_all_sessions()
    sessions = all_sessions.get(resume_id, [])

    if not sessions:
        # Create an initial default session for this resume
        default_session = ChatSessionData(
            resume_id=resume_id,
            title="General Conversation",
        )
        sessions = [default_session]
        all_sessions[resume_id] = sessions
        _save_all_sessions(all_sessions)

    summaries: list[ChatSessionSummary] = []
    for s in sessions:
        last_msg = s.messages[-1].content if s.messages else None
        if last_msg and len(last_msg) > 60:
            last_msg = last_msg[:60] + "..."
        summaries.append(
            ChatSessionSummary(
                id=s.id,
                resume_id=s.resume_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages),
                last_message=last_msg,
            )
        )

    # Sort newest updated first
    summaries.sort(key=lambda x: x.updated_at, reverse=True)
    return summaries


def create_session(resume_id: str, title: str | None = None) -> ChatSessionData:
    """Create a new chat session for a resume."""
    all_sessions = _load_all_sessions()
    if resume_id not in all_sessions:
        all_sessions[resume_id] = []

    session_title = title or f"Chat #{len(all_sessions[resume_id]) + 1}"
    new_session = ChatSessionData(
        resume_id=resume_id,
        title=session_title,
    )
    all_sessions[resume_id].insert(0, new_session)
    _save_all_sessions(all_sessions)
    return new_session


def get_session(resume_id: str, session_id: str) -> ChatSessionData | None:
    """Retrieve full session data including messages."""
    all_sessions = _load_all_sessions()
    sessions = all_sessions.get(resume_id, [])
    for s in sessions:
        if s.id == session_id:
            return s
    return None


def delete_session(resume_id: str, session_id: str) -> bool:
    """Delete a specific session."""
    all_sessions = _load_all_sessions()
    if resume_id not in all_sessions:
        return False

    initial_len = len(all_sessions[resume_id])
    all_sessions[resume_id] = [s for s in all_sessions[resume_id] if s.id != session_id]

    if len(all_sessions[resume_id]) < initial_len:
        _save_all_sessions(all_sessions)
        return True
    return False


def delete_all_sessions_for_resume(resume_id: str) -> None:
    """Delete all sessions when a resume is deleted."""
    all_sessions = _load_all_sessions()
    if resume_id in all_sessions:
        del all_sessions[resume_id]
        _save_all_sessions(all_sessions)


def add_message(
    resume_id: str,
    session_id: str,
    role: str,
    content: str,
    intent: str | None = None,
    jd_result: dict | None = None,
) -> ChatMessageRecord:
    """Append a message to a session and persist."""
    all_sessions = _load_all_sessions()
    sessions = all_sessions.get(resume_id, [])

    target_session = next((s for s in sessions if s.id == session_id), None)
    if not target_session:
        # Create session if it doesn't exist
        target_session = ChatSessionData(
            id=session_id,
            resume_id=resume_id,
            title="General Conversation",
        )
        if resume_id not in all_sessions:
            all_sessions[resume_id] = []
        all_sessions[resume_id].append(target_session)

    # Auto-generate a descriptive session title from first user message if still default
    if role == "user" and len(target_session.messages) <= 1:
        if target_session.title in ("New Chat", "General Conversation") or target_session.title.startswith("Chat #"):
            snippet = content.strip().replace("\n", " ")
            if len(snippet) > 36:
                snippet = snippet[:33] + "..."
            target_session.title = snippet

    new_msg = ChatMessageRecord(
        role=role,
        content=content,
        timestamp=datetime.now().strftime("%I:%M %p"),
        intent=intent,
        jd_result=jd_result,
    )

    target_session.messages.append(new_msg)
    target_session.updated_at = datetime.now(timezone.utc).isoformat()
    _save_all_sessions(all_sessions)
    return new_msg
