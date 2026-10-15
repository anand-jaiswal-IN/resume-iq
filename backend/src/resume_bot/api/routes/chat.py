"""
REST Chat and conversation history endpoints.
Persists messages to resume session storage.
"""

from fastapi import APIRouter, Query, HTTPException, status
from resume_bot.rag.router import classify_intent
from resume_bot.rag.enhancer import (
    respond_conversationally,
    generate_candidate_summary,
    rewrite_query,
)
from resume_bot.rag.evaluator import evaluate_job_fit
from resume_bot.rag.chain import (
    get_shared_conversational_chain,
    clear_session,
    get_session_history_messages,
)
from resume_bot.rag.extractor import get_current_profile
from resume_bot.rag.registry import get_active_resume
from resume_bot.rag.session_manager import (
    add_message as persist_message,
    get_session as get_persisted_session,
)
from resume_bot.vectorstore.store import collection_is_populated
from resume_bot.api.schemas import (
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    HistoryMessage,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """
    Non-streaming REST chat endpoint with semantic intent routing:
      - GENERAL_CONVERSATION: Friendly capability/greeting answer
      - JD_EVALUATION: Automatically evaluates candidate fit if a JD is pasted
      - RESUME_SUMMARY: High-level career overview
      - FACTUAL_QA: Grounded RAG answer using query rewriting and MMR retrieval
    """
    active_resume = get_active_resume()
    resume_id = payload.resume_id or (active_resume.id if active_resume else "default")
    session_id = payload.session_id or "default"

    # Save user message to persistent session store
    persist_message(resume_id=resume_id, session_id=session_id, role="user", content=payload.message)

    # 1. Classify Intent
    intent_info = classify_intent(payload.message)
    intent = intent_info.intent

    # 2. Route accordingly
    if intent == "GENERAL_CONVERSATION":
        answer = respond_conversationally(payload.message)
        persist_message(resume_id=resume_id, session_id=session_id, role="assistant", content=answer, intent=intent)
        return ChatResponse(
            answer=answer,
            intent=intent,
            session_id=session_id,
            resume_id=resume_id,
        )

    elif intent == "JD_EVALUATION":
        jd_text = intent_info.extracted_jd or payload.message
        evaluation = evaluate_job_fit(jd_text, profile=get_current_profile(resume_id=resume_id))
        persist_message(
            resume_id=resume_id,
            session_id=session_id,
            role="assistant",
            content=evaluation.recommendation_summary,
            intent=intent,
            jd_result=evaluation.model_dump(),
        )
        return ChatResponse(
            answer=evaluation.recommendation_summary,
            intent=intent,
            session_id=session_id,
            resume_id=resume_id,
            jd_evaluation=evaluation,
        )

    elif intent == "RESUME_SUMMARY":
        profile = get_current_profile(resume_id=resume_id)
        summary = generate_candidate_summary(profile=profile)
        persist_message(resume_id=resume_id, session_id=session_id, role="assistant", content=summary, intent=intent)
        return ChatResponse(
            answer=summary,
            intent=intent,
            session_id=session_id,
            resume_id=resume_id,
        )

    else:  # FACTUAL_QA
        optimized = rewrite_query(payload.message)
        chain = get_shared_conversational_chain()
        try:
            res = chain.invoke(
                {"question": optimized},
                config={"configurable": {"session_id": session_id}},
            )
        except Exception as e:
            if "does not exist" in str(e).lower() or "notfounderror" in type(e).__name__.lower():
                chain = get_shared_conversational_chain(force_refresh=True)
                res = chain.invoke(
                    {"question": optimized},
                    config={"configurable": {"session_id": session_id}},
                )
            else:
                raise

        # Handle TextAccessor or str
        answer_text = res.text if hasattr(res, "text") else str(res)
        persist_message(resume_id=resume_id, session_id=session_id, role="assistant", content=answer_text, intent=intent)

        return ChatResponse(
            answer=answer_text,
            intent=intent,
            session_id=session_id,
            resume_id=resume_id,
        )


@router.get("/history", response_model=HistoryResponse)
async def get_history(session_id: str = Query("default"), resume_id: str | None = Query(None)):
    """
    Get conversation history for a given session ID.
    Checks persistent session store first, then fallback to in-memory LangChain history.
    """
    target_res_id = resume_id or (get_active_resume().id if get_active_resume() else "default")
    sess = get_persisted_session(target_res_id, session_id)
    if sess and sess.messages:
        history_items = [
            HistoryMessage(
                role="user" if m.role == "user" else "assistant",
                content=m.content,
            )
            for m in sess.messages
        ]
        return HistoryResponse(session_id=session_id, messages=history_items)

    messages = get_session_history_messages(session_id)
    history_items = [
        HistoryMessage(
            role="user" if m.type == "human" else "assistant",
            content=m.content if isinstance(m.content, str) else str(m.content),
        )
        for m in messages
    ]
    return HistoryResponse(session_id=session_id, messages=history_items)


@router.delete("/history")
async def clear_history(session_id: str = Query("default"), resume_id: str | None = Query(None)):
    """
    Clear conversation history for a given session ID.
    """
    clear_session(session_id)
    return {"success": True, "message": f"History for session '{session_id}' cleared."}
