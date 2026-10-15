"""
Resume metadata registry for managing multiple indexed resumes.
Persists metadata to data/resumes_registry.json.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

from resume_bot.config import DATA_DIR

REGISTRY_FILE = DATA_DIR.parent / "resumes_registry.json"


class ResumeMetadata(BaseModel):
    id: str = Field(description="Unique identifier for the resume (e.g. res_abc123)")
    file_name: str = Field(description="Original uploaded filename")
    file_path: str = Field(description="Relative or absolute path on disk")
    file_size: int = Field(default=0, description="File size in bytes")
    uploaded_at: str = Field(description="ISO timestamp of upload")
    candidate_name: str | None = Field(default=None, description="Extracted candidate full name")
    headline: str | None = Field(default=None, description="Professional headline or title")
    total_pages: int = Field(default=1, description="Number of pages in PDF")
    total_chunks: int = Field(default=0, description="Total indexed text chunks")
    links_count: int = Field(default=0, description="Number of extracted hyperlinks")
    collection_name: str = Field(default="resume_collection", description="Qdrant collection name")
    is_active: bool = Field(default=False, description="Whether this is the currently active resume")


class RegistryData(BaseModel):
    active_resume_id: str | None = None
    resumes: list[ResumeMetadata] = []


def _load_registry_data() -> RegistryData:
    """Load registry JSON from disk or return default."""
    if not REGISTRY_FILE.exists():
        return RegistryData()
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RegistryData.model_validate(data)
    except Exception:
        return RegistryData()


def _save_registry_data(data: RegistryData) -> None:
    """Persist registry JSON to disk atomically."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = REGISTRY_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json(indent=2))
    temp_file.replace(REGISTRY_FILE)


def sync_registry_with_disk() -> RegistryData:
    """
    Ensure the registry matches actual files on disk.
    If physical files exist without registry records, registers them.
    If registered files no longer exist on disk, removes them.
    """
    reg = _load_registry_data()
    existing_pdfs = list(DATA_DIR.glob("*.pdf"))
    existing_pdf_names = {p.name for p in existing_pdfs}

    # Filter out records whose PDF no longer exists
    valid_resumes: list[ResumeMetadata] = []
    for r in reg.resumes:
        file_path = Path(r.file_path)
        if file_path.exists() or (DATA_DIR / r.file_name).exists():
            valid_resumes.append(r)

    registered_filenames = {r.file_name for r in valid_resumes}

    # Check for any PDFs on disk not yet in registry
    for pdf in existing_pdfs:
        if pdf.name not in registered_filenames:
            stem = pdf.stem
            # Check if there is a cached profile
            candidate_name = None
            headline = None
            profile_path = DATA_DIR / f"{stem}.profile.json"
            if profile_path.exists():
                try:
                    with open(profile_path, "r", encoding="utf-8") as pf:
                        pdata = json.load(pf)
                        candidate_name = pdata.get("full_name")
                        headline = pdata.get("headline_or_role")
                except Exception:
                    pass

            resume_id = f"res_{abs(hash(pdf.name)) % 1000000:06d}"
            new_meta = ResumeMetadata(
                id=resume_id,
                file_name=pdf.name,
                file_path=str(pdf),
                file_size=pdf.stat().st_size,
                uploaded_at=datetime.fromtimestamp(pdf.stat().st_mtime, timezone.utc).isoformat(),
                candidate_name=candidate_name or stem.replace("_", " "),
                headline=headline or "Imported Candidate",
                total_pages=1,
                total_chunks=0,
                links_count=0,
                collection_name=f"resume_{resume_id}",
                is_active=False,
            )
            valid_resumes.append(new_meta)

    # Ensure exactly one resume is active if any exist
    if valid_resumes:
        has_active = any(r.is_active for r in valid_resumes)
        if not has_active:
            # Check if previous active_resume_id matches
            match = next((r for r in valid_resumes if r.id == reg.active_resume_id), None)
            if match:
                match.is_active = True
            else:
                valid_resumes[0].is_active = True
                reg.active_resume_id = valid_resumes[0].id
        else:
            active_item = next(r for r in valid_resumes if r.is_active)
            reg.active_resume_id = active_item.id
    else:
        reg.active_resume_id = None

    reg.resumes = valid_resumes
    _save_registry_data(reg)
    return reg


def list_resumes() -> list[ResumeMetadata]:
    """Return all resumes currently present in the backend."""
    reg = sync_registry_with_disk()
    return reg.resumes


def get_resume(resume_id: str) -> ResumeMetadata | None:
    """Retrieve metadata for a specific resume by ID."""
    reg = sync_registry_with_disk()
    for r in reg.resumes:
        if r.id == resume_id:
            return r
    return None


def get_active_resume() -> ResumeMetadata | None:
    """Retrieve the currently active resume."""
    reg = sync_registry_with_disk()
    for r in reg.resumes:
        if r.is_active:
            return r
    return reg.resumes[0] if reg.resumes else None


def set_active_resume(resume_id: str) -> ResumeMetadata | None:
    """Set a specific resume as active and deactivate all others."""
    reg = sync_registry_with_disk()
    target: ResumeMetadata | None = None
    for r in reg.resumes:
        if r.id == resume_id:
            r.is_active = True
            target = r
        else:
            r.is_active = False

    if target:
        reg.active_resume_id = target.id
        _save_registry_data(reg)
    return target


def add_or_update_resume(meta: ResumeMetadata, set_active: bool = True) -> ResumeMetadata:
    """Add a new resume or update existing record."""
    reg = _load_registry_data()
    updated = False
    new_list: list[ResumeMetadata] = []

    for r in reg.resumes:
        if r.id == meta.id:
            if set_active:
                meta.is_active = True
            new_list.append(meta)
            updated = True
        else:
            if set_active:
                r.is_active = False
            new_list.append(r)

    if not updated:
        if set_active:
            for r in new_list:
                r.is_active = False
            meta.is_active = True
        new_list.insert(0, meta)

    reg.resumes = new_list
    if set_active:
        reg.active_resume_id = meta.id

    _save_registry_data(reg)
    return meta


def delete_resume(resume_id: str) -> bool:
    """Delete a resume record and remove associated files from disk."""
    reg = _load_registry_data()
    target = next((r for r in reg.resumes if r.id == resume_id), None)
    if not target:
        return False

    # Remove files on disk
    try:
        pdf_path = Path(target.file_path)
        if pdf_path.exists():
            pdf_path.unlink()
    except Exception:
        pass

    # Remove profile json if exists
    try:
        profile_path = DATA_DIR / f"{Path(target.file_name).stem}.profile.json"
        if profile_path.exists():
            profile_path.unlink()
        id_profile = DATA_DIR / f"{target.id}.profile.json"
        if id_profile.exists():
            id_profile.unlink()
    except Exception:
        pass

    # Update list
    reg.resumes = [r for r in reg.resumes if r.id != resume_id]

    if reg.active_resume_id == resume_id:
        if reg.resumes:
            reg.resumes[0].is_active = True
            reg.active_resume_id = reg.resumes[0].id
        else:
            reg.active_resume_id = None

    _save_registry_data(reg)
    return True
