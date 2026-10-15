# 🤖 AI Resume Bot

Interactive Context-Aware AI Resume Bot — talk to your PDF resume using RAG.

Built with **LangChain + Gemini + ChromaDB** for the CLI phase.

---

## Features

- 📄 **PDF ingestion** — PyMuPDF for rich text + hyperlink extraction
- 🧩 **Section-aware chunking** — understands Skills, Experience, Education, etc.
- 🔍 **MMR retrieval** — diverse, non-redundant context for the LLM
- 💬 **Multi-turn chat** — remembers conversation history per session
- ⚡ **Streaming** — token-by-token live output
- 🗃️ **ChromaDB** — persistent local vector store (SQLite-backed)

---

## Quick Start

### 1. Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Gemini API key

### 2. Setup

```bash
# Clone the repo
git clone <repo-url>
cd ai-resume-bot

# Install dependencies
uv sync

# Set up your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run

```bash
# Load a resume and start chatting
uv run main.py data/resumes/your_resume.pdf

# Or start without a resume and load via CLI command
uv run main.py
```

---

## CLI Commands

| Command | Description |
|---|---|
| `/load <path>` | Load a new resume PDF |
| `/clear` | Clear conversation history |
| `/history` | Show chat history |
| `/links` | Show extracted hyperlinks |
| `/stats` | Show vector store stats |
| `/help` | Show all commands |
| `/exit` | Exit the app |

---

## Architecture

```
Resume PDF
    ↓ PyMuPDFLoader (text + links)
Section-Aware Chunking (chunk_size=500, overlap=75)
    ↓ Metadata injection (section labels)
Google text-embedding-004 (768 dimensions)
    ↓ ChromaDB (persistent SQLite)
MMR Retriever (k=5, fetch_k=10, λ=0.6)
    ↓ LCEL RAG Chain
Gemini 2.0 Flash (temp=0.1)
    ↓ Streaming output
Rich CLI
```

---

## RAG Parameters

| Parameter | Value | Reason |
|---|---|---|
| `chunk_size` | 500 | Full job entry or skill block |
| `chunk_overlap` | 75 | 15% overlap, prevents boundary loss |
| `embedding_model` | `text-embedding-004` | 768-dim Google native embedding |
| `retriever_k` | 5 | Optimal for 1-2 page resume |
| `search_type` | MMR | Avoids redundant skill chunks |
| `temperature` | 0.1 | Near-deterministic factual accuracy |

---


---

## 🚀 Running the FastAPI Backend Server (Phase 3)

Start the production FastAPI server:
`ash
# Starts API server on http://localhost:8000
uv run server.py

# Or with custom port and hot-reload
uv run server.py --port 8000 --reload
`

- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **WebSocket Streaming URL**: ws://localhost:8000/ws/chat

### REST API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/resume/upload | Upload resume PDF, parse text/links, index vector DB, and extract profile |
| GET | /api/resume/status | Check if a resume is currently indexed and active |
| GET | /api/resume/profile | Retrieve structured candidate profile (skills, projects, experience) |
| GET | /api/resume/summary | Generate an executive career overview |
| GET | /api/resume/links | Retrieve all extracted hyperlinks |
| POST | /api/evaluate-jd | Evaluate candidate fit against any Job Description (0-100% score) |
| POST | /api/chat | Non-streaming conversational RAG endpoint |
| GET | /api/chat/history | Get conversation history messages |
| DELETE | /api/chat/history | Clear session conversation history |
| GET | /api/health | Health check endpoint |
| GET | /api/stats | Vector store statistics |
| WS | /ws/chat | **Real-time token streaming WebSocket** |


---

## 🎨 Running the Web Frontend (Phase 4 / Bento Box UI)

The frontend is a modern **Bento Box Grid** design built with **React Router 7, MUI (Material UI), Tailwind CSS, Axios, and Zod**.

`ash
# Navigate to the frontend directory
cd frontend

# Start the development server
npm run dev
# Or with Bun:
bun run dev
`

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Key Web UI Features:
- 🍱 **Bento Box Grid Layout**: Modular, card-based interface with subtle gradient borders and glassmorphism.
- 🌓 **Light / Dark Mode**: Full theme toggle with localStorage persistence and synchronized Tailwind dark variants.
- ⚡ **Real-Time WebSocket Streaming**: Instant token streaming chat with automatic intent badge detection.
- 🎯 **Recruiter Scorecard & JD Matcher**: Paste any Job Description and get an instant 0–100% quantitative fit score, matched skills, skill gaps, proof projects, and interview questions.
- 👤 **Structured Candidate Profile**: Visual categorized technical skills, experience timeline, and project gallery with live links.
- 📄 **Drag-and-Drop Resume Ingestion**: PDF uploader with Zod validation and multi-step progress indicator.

## Roadmap

- [x] **Phase 1** — CLI App (LangChain + Gemini + ChromaDB + PyMuPDF)
- [x] **Phase 2** — Enhanced RAG (Intent Router, JD Matcher, Profile Extraction, Query Rewriter)
- [x] **Phase 3** — FastAPI Backend (REST Endpoints + WebSockets Streaming)
- [x] **Phase 4** — Web UI (React Router 7 + MUI + Tailwind + Bento Grid + Light/Dark Mode)
- [ ] **Phase 5** — Production Cloud Deployment (Docker, Pinecone/FAISS)

- [x] **Phase 1** — CLI app (current)
- [ ] **Phase 2** — Enhanced RAG (contextual compression, HyDE)
- [ ] **Phase 3** — Frontend UI (FastAPI + Next.js/React)
- [ ] **Phase 4** — Production (FAISS/Pinecone, Docker, auth)

---

## Tech Stack

- **LLM**: `gemini-2.0-flash` via `langchain-google-genai`
- **Embeddings**: `text-embedding-004`
- **Vector DB**: ChromaDB → FAISS (production)
- **Framework**: LangChain LCEL
- **PDF**: PyMuPDF
- **CLI**: Rich
