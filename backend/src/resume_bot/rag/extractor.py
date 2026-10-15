"""
Structured resume extractor using Gemini with Pydantic structured output.
Extracts and caches a complete CandidateProfile from raw resume documents.
"""

import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from resume_bot.config import DATA_DIR
from resume_bot.rag.chain import get_llm
from resume_bot.rag.models import CandidateProfile


PROFILE_EXTRACTION_SYSTEM = """You are an expert HR data specialist and resume parser.
Extract the candidate's complete, comprehensive profile from the resume text provided below.
Ensure all skills, dates, companies, project descriptions, educational details, and hyperlinks are accurately populated.
If any field is missing from the resume, leave it as null or an empty list. Do not fabricate information.
"""

PROFILE_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", PROFILE_EXTRACTION_SYSTEM),
        ("human", "Resume text:\n\n{text}"),
    ]
)

_cached_profile: CandidateProfile | None = None
_cached_profile_id: str | None = None


def extract_candidate_profile(
    documents: list[Document],
    source_filename: str,
    resume_id: str | None = None,
    force_refresh: bool = False,
) -> CandidateProfile:
    """
    Extract a full structured CandidateProfile from resume documents.
    Caches the parsed result to JSON on disk for instant future evaluations.
    """
    global _cached_profile, _cached_profile_id

    stem = Path(source_filename).stem
    cache_path = DATA_DIR / f"{stem}.profile.json"
    id_cache_path = (DATA_DIR / f"{resume_id}.profile.json") if resume_id else None

    # Try reading from cache
    if not force_refresh:
        for p in (id_cache_path, cache_path):
            if p and p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profile = CandidateProfile.model_validate(data)
                        _cached_profile = profile
                        _cached_profile_id = resume_id
                        return profile
                except Exception:
                    pass

    # Combine all pages into full resume text
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(doc.page_content for doc in documents)

    # Use Gemini with Pydantic structured output
    llm = get_llm()
    structured_llm = llm.with_structured_output(CandidateProfile)

    extractor_chain = PROFILE_EXTRACTION_PROMPT | structured_llm
    profile: CandidateProfile = extractor_chain.invoke({"text": full_text})

    # Cache to disk
    for p in (id_cache_path, cache_path):
        if p:
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(profile.model_dump_json(indent=2))
            except Exception:
                pass

    _cached_profile = profile
    _cached_profile_id = resume_id
    return profile


def get_current_profile(resume_id: str | None = None) -> CandidateProfile | None:
    """
    Return the candidate profile.
    If resume_id is specified, loads the profile for that specific resume.
    Otherwise loads the active resume's profile.
    """
    global _cached_profile, _cached_profile_id

    if resume_id:
        if _cached_profile_id == resume_id and _cached_profile is not None:
            return _cached_profile
        # Look for {resume_id}.profile.json
        p_path = DATA_DIR / f"{resume_id}.profile.json"
        if p_path.exists():
            try:
                with open(p_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profile = CandidateProfile.model_validate(data)
                    _cached_profile = profile
                    _cached_profile_id = resume_id
                    return profile
            except Exception:
                pass

    # Import registry here to avoid circular imports
    try:
        from resume_bot.rag.registry import get_active_resume
        active = get_active_resume()
        if active:
            # Check ID profile
            id_p = DATA_DIR / f"{active.id}.profile.json"
            stem_p = DATA_DIR / f"{Path(active.file_name).stem}.profile.json"
            for p in (id_p, stem_p):
                if p.exists():
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            profile = CandidateProfile.model_validate(data)
                            _cached_profile = profile
                            _cached_profile_id = active.id
                            return profile
                    except Exception:
                        pass
    except Exception:
        pass

    if _cached_profile is not None:
        return _cached_profile

    # Look for any .profile.json in DATA_DIR
    json_files = list(DATA_DIR.glob("*.profile.json"))
    if json_files:
        try:
            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                _cached_profile = CandidateProfile.model_validate(data)
                return _cached_profile
        except Exception:
            pass

    return None


def set_current_profile(profile: CandidateProfile, resume_id: str | None = None) -> None:
    """Explicitly set the in-memory profile."""
    global _cached_profile, _cached_profile_id
    _cached_profile = profile
    _cached_profile_id = resume_id
