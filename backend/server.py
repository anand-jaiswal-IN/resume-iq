"""
FastAPI Server Entry Point for AI Resume Bot.

Usage:
    uv run server.py
    uv run server.py --port 8000 --reload
"""

import argparse
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run AI Resume Bot FastAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload")
    args = parser.parse_args()

    print(f"Starting AI Resume Bot API on http://{args.host}:{args.port}")
    print(f"Swagger Documentation: http://localhost:{args.port}/docs")
    print(f"WebSocket Endpoint:    ws://localhost:{args.port}/ws/chat")

    uvicorn.run(
        "resume_bot.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
