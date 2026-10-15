"""
Resume management endpoints: upload, multi-resume registry, activation,
deletion, sessions, profile, summary, and links.
"""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, status

from resume_bot.config import DATA_DIR, QDRANT_COLLECTION_NAME, CHROMA_COLLECTION_NAME
from resume_bot.ingestion.loader import load_resume, extract_links
from resume_bot.ingestion.chunker import chunk_documents, get_chunk_summary
from resume_bot.vectorstore.store import (
    index_documents,
    collection_is_populated,
    get_collection_stats,
    delete_collection,
)
from resume_bot.rag.extractor import (
    extract_candidate_profile,
    get_current_profile,
    set_current_profile,
)
from resume_bot.rag.chain import reset_conversational_chain
from resume_bot.rag.enhancer import generate_candidate_summary
from resume_bot.rag.models import CandidateProfile
from resume_bot.rag.registry import (
    ResumeMetadata,
    list_resumes,
    get_resume,
    get_active_resume,
    set_active_resume as registry_set_active,
    add_or_update_resume,
    delete_resume as registry_delete_resume,
)
from resume_bot.rag.session_manager import (
    list_sessions,
    create_session,
    get_session,
    delete_session,
    delete_all_sessions_for_resume,
)
from resume_bot.api.schemas import (
    UploadResumeResponse,
    ResumeStatusResponse,
    ResumeItem,
    ResumeListResponse,
    ActivateResumeResponse,
    LinksResponse,
    SummaryResponse,
    ChatSessionSummarySchema,
    ChatSessionDetailSchema,
    CreateSessionRequest,
)

router = APIRouter(tags=["Resume"])


# ── Multi-Resume Registry Endpoints ───────────────────────────────────────────

@router.get("/api/resumes", response_model=ResumeListResponse)
async def get_all_resumes():
    """
    Fetch all resumes that are currently indexed and present in the backend.
    Includes metadata like date/time uploaded, assigned ID, chunk stats, and active state.
    """
    all_resumes = list_resumes()
    active = get_active_resume()
    items = [
        ResumeItem(
            id=r.id,
            file_name=r.file_name,
            file_size=r.file_size,
            uploaded_at=r.uploaded_at,
            candidate_name=r.candidate_name,
            headline=r.headline,
            total_pages=r.total_pages,
            total_chunks=r.total_chunks,
            links_count=r.links_count,
            is_active=r.is_active,
        )
        for r in all_resumes
    ]
    return ResumeListResponse(
        resumes=items,
        active_resume_id=active.id if active else None,
        total=len(items),
    )


@router.post("/api/resumes/{resume_id}/activate", response_model=ActivateResumeResponse)
async def activate_resume(resume_id: str):
    """
    Set a specific indexed resume as the active resume context for RAG and evaluations.
    """
    updated = registry_set_active(resume_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' not found.",
        )

    # Load its profile into memory
    profile = get_current_profile(resume_id=resume_id)
    if profile:
        set_current_profile(profile, resume_id=resume_id)

    reset_conversational_chain()

    active_item = ResumeItem(
        id=updated.id,
        file_name=updated.file_name,
        file_size=updated.file_size,
        uploaded_at=updated.uploaded_at,
        candidate_name=updated.candidate_name,
        headline=updated.headline,
        total_pages=updated.total_pages,
        total_chunks=updated.total_chunks,
        links_count=updated.links_count,
        is_active=True,
    )
    return ActivateResumeResponse(
        success=True,
        message=f"Resume '{updated.candidate_name or updated.file_name}' activated.",
        active_resume=active_item,
    )


@router.delete("/api/resumes/{resume_id}")
async def delete_resume_endpoint(resume_id: str):
    """
    Delete a resume from the backend, its Chroma vector collection, and its chat sessions.
    """
    target = get_resume(resume_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' not found.",
        )

    # Delete Qdrant collections
    delete_collection(target.collection_name)
    delete_all_sessions_for_resume(resume_id)

    success = registry_delete_resume(resume_id)
    reset_conversational_chain()

    # Re-activate remaining if any
    active = get_active_resume()
    if active:
        prof = get_current_profile(resume_id=active.id)
        if prof:
            set_current_profile(prof, resume_id=active.id)

    return {
        "success": success,
        "message": f"Resume '{target.file_name}' and its vector indexes deleted.",
        "active_resume_id": active.id if active else None,
    }


# ── Upload Endpoint ───────────────────────────────────────────────────────────

@router.post("/api/resume/upload", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF, parse text & links, index into Qdrant with assigned ID & metadata,
    and initialize an active chat session.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique resume ID
    resume_id = f"res_{uuid.uuid4().hex[:8]}"
    upload_time = datetime.now(timezone.utc).isoformat()

    # Store file with clean path
    safe_filename = file.filename
    destination = DATA_DIR / safe_filename

    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = destination.stat().st_size
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e}",
        )

    # Ingestion pipeline: load -> chunk -> embed -> extract profile
    try:
        documents, meta = load_resume(destination)
        chunks = chunk_documents(documents)
        chunk_summary = get_chunk_summary(chunks)

        # Index into Qdrant collection for this resume and shared collection
        collection_name = f"resume_{resume_id}"
        index_documents(chunks, collection_name=collection_name, reset=True)
        index_documents(chunks, collection_name=QDRANT_COLLECTION_NAME, reset=True)

        # Extract structured candidate profile
        profile = extract_candidate_profile(
            documents, destination.name, resume_id=resume_id, force_refresh=True
        )
        set_current_profile(profile, resume_id=resume_id)
        reset_conversational_chain()

        # Save metadata to registry
        resume_meta = ResumeMetadata(
            id=resume_id,
            file_name=safe_filename,
            file_path=str(destination),
            file_size=file_size,
            uploaded_at=upload_time,
            candidate_name=profile.full_name,
            headline=profile.headline_or_role,
            total_pages=meta.total_pages,
            total_chunks=chunk_summary["total_chunks"],
            links_count=len(meta.links),
            collection_name=collection_name,
            is_active=True,
        )
        add_or_update_resume(resume_meta, set_active=True)

        # Initialize default chat session for this resume
        create_session(resume_id=resume_id, title="General Q&A")

        return UploadResumeResponse(
            success=True,
            message=f"Resume '{safe_filename}' indexed and registered successfully.",
            id=resume_id,
            file_name=safe_filename,
            file_size=file_size,
            uploaded_at=upload_time,
            total_pages=meta.total_pages,
            total_chunks=chunk_summary["total_chunks"],
            links_count=len(meta.links),
            candidate_name=profile.full_name,
            headline=profile.headline_or_role,
            is_active=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {e}",
        )


# ── Chat Session Endpoints per Resume ─────────────────────────────────────────

@router.get("/api/resumes/{resume_id}/sessions", response_model=list[ChatSessionSummarySchema])
async def get_resume_sessions(resume_id: str):
    """
    List all chat sessions associated with a specific resume.
    """
    sessions = list_sessions(resume_id)
    return [
        ChatSessionSummarySchema(
            id=s.id,
            resume_id=s.resume_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=s.message_count,
            last_message=s.last_message,
        )
        for s in sessions
    ]


@router.post("/api/resumes/{resume_id}/sessions", response_model=ChatSessionDetailSchema)
async def create_resume_session(resume_id: str, payload: CreateSessionRequest | None = None):
    """
    Create a new chat session for a resume.
    """
    title = payload.title if payload else None
    session_data = create_session(resume_id, title=title)
    return ChatSessionDetailSchema(
        id=session_data.id,
        resume_id=session_data.resume_id,
        title=session_data.title,
        created_at=session_data.created_at,
        updated_at=session_data.updated_at,
        messages=[],
    )


@router.get("/api/resumes/{resume_id}/sessions/{session_id}", response_model=ChatSessionDetailSchema)
async def get_session_detail(resume_id: str, session_id: str):
    """
    Retrieve session details and full conversation history for a session.
    """
    session_data = get_session(resume_id, session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found for resume '{resume_id}'.",
        )

    return ChatSessionDetailSchema(
        id=session_data.id,
        resume_id=session_data.resume_id,
        title=session_data.title,
        created_at=session_data.created_at,
        updated_at=session_data.updated_at,
        messages=[m.model_dump() for m in session_data.messages],
    )


@router.delete("/api/resumes/{resume_id}/sessions/{session_id}")
async def delete_resume_session(resume_id: str, session_id: str):
    """
    Delete a specific chat session for a resume.
    """
    success = delete_session(resume_id, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return {"success": True, "message": f"Session '{session_id}' deleted."}


# ── Status, Profile, Summary, Links ───────────────────────────────────────────

@router.get("/api/resume/status", response_model=ResumeStatusResponse)
async def get_resume_status():
    """
    Check active resume metrics and backend population.
    """
    all_res = list_resumes()
    active = get_active_resume()
    profile = get_current_profile(resume_id=active.id if active else None)
    stats = get_collection_stats(collection_name=active.collection_name if active else CHROMA_COLLECTION_NAME)

    links_count = active.links_count if active else 0
    if not links_count and active:
        pdf_path = Path(active.file_path)
        if pdf_path.exists():
            try:
                links_count = len(extract_links(pdf_path))
            except Exception:
                pass

    return ResumeStatusResponse(
        is_loaded=bool(active and (profile or stats["document_count"] > 0)),
        file_name=active.file_name if active else None,
        candidate_name=profile.full_name if profile else (active.candidate_name if active else None),
        headline=profile.headline_or_role if profile else (active.headline if active else None),
        total_chunks=active.total_chunks if active else stats["document_count"],
        total_links=links_count,
        active_resume_id=active.id if active else None,
        total_resumes=len(all_res),
    )


@router.get("/api/resume/profile", response_model=CandidateProfile)
async def get_profile(resume_id: str | None = Query(None)):
    """
    Get structured candidate profile for a specific resume or active resume.
    """
    profile = get_current_profile(resume_id=resume_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidate profile found. Please upload a resume PDF first.",
        )
    return profile


@router.get("/api/resume/summary", response_model=SummaryResponse)
async def get_summary(resume_id: str | None = Query(None)):
    """
    Generate an executive career summary of the candidate.
    """
    profile = get_current_profile(resume_id=resume_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume loaded to summarize. Please upload a resume first.",
        )

    summary_text = generate_candidate_summary(profile)
    return SummaryResponse(
        candidate_name=profile.full_name,
        summary=summary_text,
    )


@router.get("/api/resume/links", response_model=LinksResponse)
async def get_resume_links(resume_id: str | None = Query(None)):
    """
    Get all extracted hyperlinks from the active or specified resume.
    """
    target = get_resume(resume_id) if resume_id else get_active_resume()
    if not target:
        return LinksResponse(file_name=None, total_links=0, links=[])

    file_path = Path(target.file_path)
    if not file_path.exists():
        file_path = DATA_DIR / target.file_name

    if not file_path.exists():
        return LinksResponse(file_name=target.file_name, total_links=0, links=[])

    try:
        links = extract_links(file_path)
        return LinksResponse(
            file_name=target.file_name,
            total_links=len(links),
            links=links,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract links: {e}",
        )
