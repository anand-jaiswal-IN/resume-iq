"""
WebSocket real-time streaming endpoint for the AI Resume Bot.
Persists messages to the multi-resume session store.

Endpoint: /ws/chat
Protocol:
  Client -> Server: {"message": "User query", "session_id": "sess_123", "resume_id": "res_abc"}
  Server -> Client:
    - {"type": "intent", "content": "FACTUAL_QA", "session_id": "...", "resume_id": "..."}
    - {"type": "token", "content": "partial token", "session_id": "...", "resume_id": "..."}
    - {"type": "done", "content": "full assembled response", "session_id": "...", "resume_id": "..."}
    - {"type": "jd_result", "content": { ...JobFitEvaluation dict... }, "session_id": "...", "resume_id": "..."}
    - {"type": "error", "content": "error message"}
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from resume_bot.rag.router import classify_intent
from resume_bot.rag.enhancer import (
    respond_conversationally,
    generate_candidate_summary,
    rewrite_query,
)
from resume_bot.rag.evaluator import evaluate_job_fit
from resume_bot.rag.chain import (
    get_shared_conversational_chain,
    stream_conversational_answer,
)
from resume_bot.rag.extractor import get_current_profile
from resume_bot.rag.registry import get_active_resume
from resume_bot.rag.session_manager import add_message as persist_message
from resume_bot.vectorstore.store import collection_is_populated

router = APIRouter(tags=["WebSocket Streaming"])


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    Bi-directional WebSocket streaming connection.
    Supports real-time token-by-token streaming of RAG answers and structured JD evaluation payloads.
    Persists conversations to the active session.
    """
    await websocket.accept()

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except Exception:
                await websocket.send_json({"type": "error", "content": "Invalid JSON payload."})
                continue

            message = payload.get("message", "").strip()
            session_id = payload.get("session_id", "default")
            active_res = get_active_resume()
            resume_id = payload.get("resume_id") or (active_res.id if active_res else "default")

            if not message:
                await websocket.send_json({"type": "error", "content": "Message cannot be empty."})
                continue

            # Persist user message immediately
            persist_message(resume_id=resume_id, session_id=session_id, role="user", content=message)

            # Step 1: Detect intent
            intent_info = await asyncio.to_thread(classify_intent, message)
            intent = intent_info.intent

            await websocket.send_json({
                "type": "intent",
                "content": intent,
                "session_id": session_id,
                "resume_id": resume_id,
            })

            # Step 2: Route and Stream
            if intent == "GENERAL_CONVERSATION":
                response_text = await asyncio.to_thread(respond_conversationally, message)
                # Stream the conversational response in word chunks
                words = response_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    await websocket.send_json({
                        "type": "token",
                        "content": chunk,
                        "session_id": session_id,
                        "resume_id": resume_id,
                    })
                    await asyncio.sleep(0.015)

                persist_message(
                    resume_id=resume_id,
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    intent=intent,
                )

                await websocket.send_json({
                    "type": "done",
                    "content": response_text,
                    "session_id": session_id,
                    "resume_id": resume_id,
                })

            elif intent == "JD_EVALUATION":
                jd_text = intent_info.extracted_jd or message
                evaluation = await asyncio.to_thread(
                    evaluate_job_fit, jd_text, get_current_profile(resume_id=resume_id)
                )

                persist_message(
                    resume_id=resume_id,
                    session_id=session_id,
                    role="assistant",
                    content=evaluation.recommendation_summary,
                    intent=intent,
                    jd_result=evaluation.model_dump(),
                )

                # Send structured evaluation payload
                await websocket.send_json({
                    "type": "jd_result",
                    "content": evaluation.model_dump(),
                    "session_id": session_id,
                    "resume_id": resume_id,
                })
                await websocket.send_json({
                    "type": "done",
                    "content": evaluation.recommendation_summary,
                    "session_id": session_id,
                    "resume_id": resume_id,
                })

            elif intent == "RESUME_SUMMARY":
                profile = get_current_profile(resume_id=resume_id)
                summary_text = await asyncio.to_thread(generate_candidate_summary, profile)
                paragraphs = summary_text.split("\n\n")
                for para in paragraphs:
                    words = para.split(" ")
                    for i, word in enumerate(words):
                        chunk = word + (" " if i < len(words) - 1 else "")
                        await websocket.send_json({
                            "type": "token",
                            "content": chunk,
                            "session_id": session_id,
                            "resume_id": resume_id,
                        })
                        await asyncio.sleep(0.01)
                    await websocket.send_json({
                        "type": "token",
                        "content": "\n\n",
                        "session_id": session_id,
                        "resume_id": resume_id,
                    })

                persist_message(
                    resume_id=resume_id,
                    session_id=session_id,
                    role="assistant",
                    content=summary_text,
                    intent=intent,
                )

                await websocket.send_json({
                    "type": "done",
                    "content": summary_text,
                    "session_id": session_id,
                    "resume_id": resume_id,
                })

            else:  # FACTUAL_QA
                optimized_query = await asyncio.to_thread(rewrite_query, message)
                chain = get_shared_conversational_chain()

                # Stream token-by-token live from Gemini LCEL chain
                full_assembled = ""

                def sync_stream_tokens(active_chain):
                    try:
                        return list(stream_conversational_answer(active_chain, optimized_query, session_id))
                    except Exception as err:
                        if "does not exist" in str(err).lower() or "notfounderror" in type(err).__name__.lower():
                            refreshed_chain = get_shared_conversational_chain(force_refresh=True)
                            return list(stream_conversational_answer(refreshed_chain, optimized_query, session_id))
                        raise

                # Stream tokens
                tokens = await asyncio.to_thread(sync_stream_tokens, chain)
                for token in tokens:
                    full_assembled += token
                    await websocket.send_json({
                        "type": "token",
                        "content": token,
                        "session_id": session_id,
                        "resume_id": resume_id,
                    })
                    await asyncio.sleep(0.005)

                persist_message(
                    resume_id=resume_id,
                    session_id=session_id,
                    role="assistant",
                    content=full_assembled,
                    intent=intent,
                )

                await websocket.send_json({
                    "type": "done",
                    "content": full_assembled,
                    "session_id": session_id,
                    "resume_id": resume_id,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
