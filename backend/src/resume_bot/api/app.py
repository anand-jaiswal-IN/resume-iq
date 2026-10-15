"""
Main FastAPI Application for AI Resume Bot.
Includes CORS configuration, REST routes mounting, WebSocket streaming, and startup verification.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resume_bot.config import APP_NAME, APP_VERSION, DATA_DIR
from resume_bot.vectorstore.store import collection_is_populated, get_collection_stats
from resume_bot.rag.extractor import get_current_profile
from resume_bot.api.schemas import HealthResponse, StatsResponse
from resume_bot.api.routes.resume import router as resume_router
from resume_bot.api.routes.evaluation import router as evaluation_router
from resume_bot.api.routes.chat import router as chat_router
from resume_bot.api.websocket.chat_ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management."""
    # On startup: verify directories and load existing profile if present
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profile = get_current_profile()
    if profile:
        print(f"[API Startup] Loaded profile for candidate: {profile.full_name}")
    else:
        print("[API Startup] No candidate profile currently loaded.")
    yield
    print("[API Shutdown] AI Resume Bot server stopping.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=f"{APP_NAME} Backend API",
        version=APP_VERSION,
        description=(
            "Production-ready backend API for Interactive Context-Aware AI Resume Bot.\n\n"
            "Features:\n"
            "- **REST Endpoints**: Resume PDF upload, candidate profile, executive summaries, links extraction, and JD matching.\n"
            "- **WebSocket Streaming**: Token-by-token real-time streaming chat (`/ws/chat`).\n"
            "- **Modern RAG**: LCEL chains, Gemini LLM & embeddings, Qdrant, and Pydantic structured output."
        ),
        lifespan=lifespan,
    )

    # Configure CORS for future Frontend UI integration (Next.js / React / Vite)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount REST and WebSocket routers
    app.include_router(resume_router)
    app.include_router(evaluation_router)
    app.include_router(chat_router)
    app.include_router(ws_router)

    # Root & Health Endpoints
    @app.get("/", tags=["General"])
    async def root():
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "docs": "/docs",
            "health": "/api/health",
            "websocket": "/ws/chat",
        }

    @app.get("/api/health", response_model=HealthResponse, tags=["General"])
    async def health():
        return HealthResponse(
            status="ok",
            version=APP_VERSION,
            message="AI Resume Bot API is operational",
        )

    @app.get("/api/stats", response_model=StatsResponse, tags=["General"])
    async def stats():
        vstats = get_collection_stats()
        profile = get_current_profile()
        return StatsResponse(
            collection_name=vstats["collection"],
            document_count=vstats["document_count"],
            has_profile=profile is not None,
            candidate_name=profile.full_name if profile else None,
        )

    return app


app = create_app()
