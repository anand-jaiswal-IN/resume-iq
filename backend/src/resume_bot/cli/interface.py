"""
Rich CLI interface for the AI Resume Bot (Phase 2: Enhanced RAG).

Enhanced Features:
  - Intent Routing: Auto-detects general conversation, capability questions, JD evaluation, summaries, and factual Q&A.
  - Job Fit Evaluation (/match): Evaluates candidate fit against any Job Description with 0-100% score, skill gap analysis, and tailored interview questions.
  - Structured Candidate Profile (/profile): Deep view of skills, experience, and projects.
  - Executive Summaries (/summary): High-level career overview.
  - Query Rewriter: Semantic query expansion for improved retrieval accuracy.
  - Streaming output with live status indicators.
"""

import sys
from pathlib import Path
from typing import Callable, Iterator

from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.status import Status
from rich.table import Table
from rich.text import Text

from resume_bot.config import APP_NAME
from resume_bot.ingestion.loader import load_resume, resolve_resume_path, ResumeMetadata
from resume_bot.ingestion.chunker import chunk_documents, get_chunk_summary
from resume_bot.vectorstore.store import (
    index_documents,
    get_retriever,
    collection_is_populated,
    get_collection_stats,
)
from resume_bot.rag.chain import (
    build_conversational_chain,
    stream_conversational_answer,
    clear_session,
    get_session_history_messages,
)
from resume_bot.rag.models import CandidateProfile, JobFitEvaluation
from resume_bot.rag.extractor import (
    extract_candidate_profile,
    get_current_profile,
    set_current_profile,
)
from resume_bot.rag.router import classify_intent
from resume_bot.rag.evaluator import evaluate_job_fit
from resume_bot.rag.enhancer import (
    rewrite_query,
    generate_candidate_summary,
    respond_conversationally,
)

console = Console()

# ── CLI Commands ──────────────────────────────────────────────────────────────
COMMANDS: dict[str, str] = {
    "/help":    "Show this help table",
    "/match":   "Evaluate candidate fit against a Job Description (JD)",
    "/profile": "Display structured candidate profile (skills, experience, projects)",
    "/summary": "Generate an executive career summary of the candidate",
    "/links":   "Show all links extracted from the resume",
    "/load":    "Load a new resume PDF (e.g. /load data/resumes/resume.pdf)",
    "/clear":   "Clear conversation chat history",
    "/history": "Show recent conversation history",
    "/stats":   "Show vector store statistics",
    "/exit":    "Exit the application",
    "/quit":    "Exit the application",
}


# ── Display Helpers ───────────────────────────────────────────────────────────

def print_welcome() -> None:
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]{APP_NAME}[/bold cyan] [dim]-- Phase 2: Enhanced RAG[/dim]\n"
            "[dim]Powered by Gemini 3.8 Flash + LangChain + Qdrant + Pydantic[/dim]\n\n"
            "[green]* Talk directly to the resume with context-aware semantic search[/green]\n"
            "[green]* Paste any Job Description (JD) to evaluate candidate fit & get match score[/green]\n"
            "[dim]Type [bold]/help[/bold] to see all available commands.[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def print_help() -> None:
    table = Table(title="Available Commands", border_style="dim", show_header=True)
    table.add_column("Command", style="bold yellow")
    table.add_column("Description", style="white")
    for cmd, desc in COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)
    console.print()


def print_metadata(meta: ResumeMetadata, chunk_summary: dict, profile: CandidateProfile | None = None) -> None:
    name = profile.full_name if profile else "Candidate"
    role = profile.headline_or_role if profile else "Extracted from Resume"

    table = Table(title=f"📄 Resume Indexed: [bold green]{name}[/bold green] ({role})", border_style="green", show_header=False)
    table.add_column("Field", style="bold green")
    table.add_column("Value", style="white")

    table.add_row("File", meta.file_name)
    table.add_row("Pages", str(meta.total_pages))
    table.add_row("Hyperlinks", str(len(meta.links)))
    table.add_row("Chunks Created", str(chunk_summary["total_chunks"]))
    table.add_row("Avg Chunk Size", f"{chunk_summary['avg_chunk_size']} chars")

    for section, count in chunk_summary["section_distribution"].items():
        table.add_row(f"  [{section}]", f"{count} chunk(s)")

    console.print(table)
    console.print()


def print_links(links: list[str]) -> None:
    if not links:
        console.print("[dim]No links found in the resume.[/dim]\n")
        return

    console.print(Panel(
        "\n".join(f"[link={url}]{url}[/link]" for url in links),
        title="🔗 Resume Hyperlinks",
        border_style="blue",
    ))
    console.print()


def print_stats() -> None:
    stats = get_collection_stats()
    profile = get_current_profile()
    profile_status = f"[green]Loaded ({profile.full_name})[/green]" if profile else "[yellow]None[/yellow]"

    console.print(
        Panel(
            f"[bold]Collection:[/bold] {stats['collection']}\n"
            f"[bold]Indexed Chunks:[/bold] {stats['document_count']}\n"
            f"[bold]Structured Profile:[/bold] {profile_status}",
            title="📊 System & Vector Store Stats",
            border_style="magenta",
        )
    )
    console.print()


def print_profile(profile: CandidateProfile | None = None) -> None:
    if profile is None:
        profile = get_current_profile()

    if profile is None:
        console.print("[yellow]No candidate profile available. Please load a resume first.[/yellow]\n")
        return

    # Basic Info
    console.print(Panel(
        f"[bold cyan]{profile.full_name}[/bold cyan] -- [white]{profile.headline_or_role}[/white]\n"
        f"[dim]Email: {profile.contact_email or 'N/A'} | Phone: {profile.contact_phone or 'N/A'}[/dim]",
        title="👤 Candidate Profile",
        border_style="cyan"
    ))

    # Skills Table
    skills_table = Table(title="🛠 Technical Skills", border_style="cyan", show_header=True)
    skills_table.add_column("Category", style="bold yellow", width=20)
    skills_table.add_column("Technologies & Tools", style="white")

    s = profile.skills
    if s.languages:
        skills_table.add_row("Languages", ", ".join(s.languages))
    if s.frontend:
        skills_table.add_row("Frontend", ", ".join(s.frontend))
    if s.backend:
        skills_table.add_row("Backend", ", ".join(s.backend))
    if s.databases:
        skills_table.add_row("Databases", ", ".join(s.databases))
    if s.cloud_and_devops:
        skills_table.add_row("Cloud / DevOps", ", ".join(s.cloud_and_devops))
    if s.ai_and_ml:
        skills_table.add_row("AI & GenAI", ", ".join(s.ai_and_ml))
    if s.tools:
        skills_table.add_row("Developer Tools", ", ".join(s.tools))
    console.print(skills_table)
    console.print()

    # Experience Table
    if profile.work_experience:
        exp_table = Table(title="💼 Work Experience", border_style="green", show_header=True)
        exp_table.add_column("Company", style="bold green", width=22)
        exp_table.add_column("Role & Duration", style="bold white", width=28)
        exp_table.add_column("Responsibilities & Impact", style="dim white")

        for exp in profile.work_experience:
            resp_text = "\n".join(f"• {r}" for r in exp.responsibilities) if exp.responsibilities else "N/A"
            exp_table.add_row(exp.company, f"{exp.role}\n[dim]{exp.duration}[/dim]", resp_text)
        console.print(exp_table)
        console.print()

    # Projects Table
    if profile.projects:
        proj_table = Table(title="🚀 Key Projects", border_style="blue", show_header=True)
        proj_table.add_column("Project", style="bold blue", width=20)
        proj_table.add_column("Tech Stack", style="yellow", width=26)
        proj_table.add_column("Summary", style="white")

        for proj in profile.projects:
            tech_text = ", ".join(proj.technologies) if proj.technologies else "N/A"
            proj_table.add_row(proj.title, tech_text, proj.description)
        console.print(proj_table)
        console.print()


def print_job_fit(evaluation: JobFitEvaluation) -> None:
    """Render the structured JobFitEvaluation in an attractive recruiter scorecard format."""
    score = evaluation.fit_score
    if score >= 80:
        score_color = "bold green"
        badge = "🌟 STRONG MATCH"
    elif score >= 65:
        score_color = "bold yellow"
        badge = "👍 GOOD MATCH"
    elif score >= 50:
        score_color = "bold dark_orange"
        badge = "⚖ MODERATE FIT"
    else:
        score_color = "bold red"
        badge = "⚠ LOW FIT / SIGNIFICANT GAPS"

    console.print()
    console.print(Rule(f"[{score_color}]JOB FIT EVALUATION: {badge}[/{score_color}]", style="dim"))
    console.print()

    # Score Card Header
    console.print(
        Panel(
            f"Candidate: [bold cyan]{evaluation.candidate_name}[/bold cyan]   |   Target Role: [bold white]{evaluation.target_role}[/bold white]\n"
            f"Fit Score: [{score_color}]{evaluation.fit_score} / 100[/{score_color}]   |   Verdict: [bold]{evaluation.verdict}[/bold]\n\n"
            f"[italic]{evaluation.recommendation_summary}[/italic]",
            title="🎯 Recruiter Scorecard",
            border_style=score_color.split()[-1],
            padding=(1, 2),
        )
    )
    console.print()

    # Strengths & Matched Skills
    col_table = Table(border_style="dim", show_header=True)
    col_table.add_column("✅ Matched Strengths & Key Skills", style="green", ratio=1)
    col_table.add_column("❌ Skill Gaps & Missing Requirements", style="red", ratio=1)

    matched_content = "\n".join(f"• {s}" for s in evaluation.matched_skills)
    strengths_content = "\n".join(f"★ {s}" for s in evaluation.strengths)
    left_side = f"[bold]Top Strengths:[/bold]\n{strengths_content}\n\n[bold]Matched Skills:[/bold]\n{matched_content}"

    missing_content = "\n".join(f"▲ {g}" for g in evaluation.missing_skills_or_gaps) if evaluation.missing_skills_or_gaps else "[green]None identified![/green]"
    right_side = f"[bold]Identified Gaps:[/bold]\n{missing_content}"

    col_table.add_row(left_side, right_side)
    console.print(col_table)
    console.print()

    # Relevant Proof Projects
    if evaluation.relevant_projects:
        proj_text = "\n".join(f"• {p}" for p in evaluation.relevant_projects)
        console.print(Panel(proj_text, title="📂 Projects Providing Direct Competency Proof", border_style="blue"))
        console.print()

    # Interview Questions
    if evaluation.suggested_interview_questions:
        q_text = "\n\n".join(f"[bold yellow]Q{i}:[/bold yellow] {q}" for i, q in enumerate(evaluation.suggested_interview_questions, 1))
        console.print(Panel(q_text, title="💡 Recommended Technical Interview Questions", border_style="yellow"))
        console.print()


def stream_and_print_answer(stream_fn: Callable[[], Iterator[str]]) -> str:
    console.print()
    console.print(Text("🤖 Assistant", style="bold green"))
    console.print(Rule(style="dim green"))

    full_answer = ""
    for token in stream_fn():
        console.print(token, end="", highlight=False)
        full_answer += token

    console.print()
    console.print(Rule(style="dim green"))
    console.print()
    return full_answer


# ── Ingestion Pipeline ────────────────────────────────────────────────────────

def ingest_resume(pdf_path: str | Path, reset: bool = True) -> ResumeMetadata:
    """
    Run the Enhanced RAG ingestion pipeline:
      1. Load PDF & hyperlinks
      2. Semantic section-aware chunking
      3. Index chunks into Qdrant
      4. Extract and cache full structured CandidateProfile
    """
    with Status("[cyan]1/3 Loading PDF & extracting hyperlinks...[/cyan]", console=console):
        documents, meta = load_resume(pdf_path)

    with Status("[cyan]2/3 Semantic chunking & indexing into Qdrant...[/cyan]", console=console):
        chunks = chunk_documents(documents)
        chunk_summary = get_chunk_summary(chunks)
        store = index_documents(chunks, reset=reset)

    with Status("[cyan]3/3 Extracting structured candidate profile with Gemini...[/cyan]", console=console):
        profile = extract_candidate_profile(documents, Path(pdf_path).name, force_refresh=reset)
        set_current_profile(profile)

    print_metadata(meta, chunk_summary, profile)
    return meta


# ── Interactive Job Description Flow ──────────────────────────────────────────

def handle_job_matching_flow(jd_text: str | None = None) -> None:
    """Guides the user through evaluating a Job Description."""
    if not jd_text:
        console.print(
            Panel(
                "[bold cyan]Job Description Evaluation Mode[/bold cyan]\n"
                "[dim]Paste your Job Description below. When finished, press Enter.\n"
                "(For multiline JDs, paste all text and press Enter)[/dim]",
                border_style="cyan"
            )
        )
        try:
            jd_text = Prompt.ask("\n[bold yellow]Paste JD here[/bold yellow]").strip()
        except (KeyboardInterrupt, EOFError):
            return

    if not jd_text or len(jd_text) < 15:
        console.print("[yellow]Job description is too short to evaluate. Please provide a more detailed JD.[/yellow]\n")
        return

    with Status("[cyan]Analyzing candidate profile and evaluating fit against JD...[/cyan]", console=console):
        try:
            evaluation = evaluate_job_fit(jd_text)
            print_job_fit(evaluation)
        except Exception as e:
            console.print(f"[red]❌ Error evaluating job fit: {e}[/red]\n")


# ── Main CLI Loop ─────────────────────────────────────────────────────────────

def run_cli(pdf_path: str | None = None) -> None:
    print_welcome()

    current_links: list[str] = []
    SESSION_ID = "resume-chat"

    # Startup resume loading
    if pdf_path:
        try:
            resolved = resolve_resume_path(pdf_path)
            meta = ingest_resume(resolved, reset=False)
            current_links = meta.links
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[red]❌ {e}[/red]")
            console.print("[dim]Use /load <path> to load a resume.[/dim]")
    elif collection_is_populated():
        stats = get_collection_stats()
        profile = get_current_profile()
        name_str = f" for [bold green]{profile.full_name}[/bold green]" if profile else ""
        console.print(
            f"[green]✅ Loaded vector store ({stats['document_count']} chunks){name_str}.[/green]\n"
            "[dim]Type your question, paste a JD, or use /help.[/dim]\n"
        )
    else:
        console.print(
            "[yellow]⚠  No resume loaded. Use [bold]/load <path>[/bold] "
            "to upload a resume PDF.[/yellow]\n"
        )

    retriever = get_retriever()
    chain = build_conversational_chain(retriever)

    # Main interactive REPL
    while True:
        try:
            user_input = Prompt.ask("[bold blue]You[/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        # ── Commands ──────────────────────────────────────────────────────────
        if lower in ("/exit", "/quit"):
            console.print("[dim]Goodbye! 👋[/dim]")
            break

        elif lower == "/help":
            print_help()

        elif lower == "/clear":
            clear_session(SESSION_ID)
            console.print("[green]✅ Conversation history cleared.[/green]\n")

        elif lower == "/history":
            messages = get_session_history_messages(SESSION_ID)
            if not messages:
                console.print("[dim]No conversation history yet.[/dim]\n")
            else:
                for msg in messages:
                    role = "You" if msg.type == "human" else "Assistant"
                    style = "blue" if msg.type == "human" else "green"
                    console.print(f"[{style}][{role}][/{style}]: {msg.content}\n")

        elif lower == "/links":
            print_links(current_links)

        elif lower == "/stats":
            print_stats()

        elif lower == "/profile":
            print_profile()

        elif lower == "/summary":
            with Status("[cyan]Generating executive summary...[/cyan]", console=console):
                summary = generate_candidate_summary()
            console.print(Panel(summary, title="📋 Executive Candidate Summary", border_style="green"))
            console.print()

        elif lower == "/match" or lower == "/jd":
            handle_job_matching_flow()

        elif lower.startswith("/load"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[yellow]Usage: /load <path-to-resume.pdf>[/yellow]\n")
                continue
            try:
                resolved = resolve_resume_path(parts[1].strip())
                meta = ingest_resume(resolved, reset=True)
                current_links = meta.links
                retriever = get_retriever()
                chain = build_conversational_chain(retriever)
                clear_session(SESSION_ID)
                console.print("[green]✅ New resume loaded and structured profile extracted.[/green]\n")
            except (FileNotFoundError, ValueError) as e:
                console.print(f"[red]❌ {e}[/red]\n")

        elif lower.startswith("/"):
            console.print(f"[yellow]Unknown command: {user_input}. Type /help for available commands.[/yellow]\n")

        # ── Enhanced RAG Unified Intent Dispatcher ────────────────────────────
        else:
            if not collection_is_populated():
                console.print("[yellow]⚠  No resume loaded. Use [bold]/load <path>[/bold] first.[/yellow]\n")
                continue

            with Status("[cyan]Thinking...[/cyan]", console=console):
                intent_info = classify_intent(user_input)

            # Intent 1: General conversation or capability question
            if intent_info.intent == "GENERAL_CONVERSATION":
                response = respond_conversationally(user_input)
                console.print()
                console.print(Text("🤖 Assistant", style="bold green"))
                console.print(Rule(style="dim green"))
                console.print(response)
                console.print(Rule(style="dim green"))
                console.print()

            # Intent 2: User pasted or provided a Job Description
            elif intent_info.intent == "JD_EVALUATION":
                jd_text = intent_info.extracted_jd or user_input
                handle_job_matching_flow(jd_text)

            # Intent 3: High-level overview/summary
            elif intent_info.intent == "RESUME_SUMMARY":
                with Status("[cyan]Generating executive summary...[/cyan]", console=console):
                    summary = generate_candidate_summary()
                console.print(Panel(summary, title="📋 Executive Summary", border_style="green"))
                console.print()

            # Intent 4: Factual Q&A with Query Rewriting + MMR Retrieval
            else:
                try:
                    # Query rewriting for semantic expansion
                    optimized_query = rewrite_query(user_input)

                    stream_and_print_answer(
                        lambda: stream_conversational_answer(
                            chain, optimized_query, SESSION_ID
                        )
                    )
                except Exception as e:
                    console.print(f"[red]❌ Error: {e}[/red]\n")
