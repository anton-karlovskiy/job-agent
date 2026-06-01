from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ApplicantData:
    """Applicant profile and resume data consumed by all other modules."""

    profile_yaml: dict[str, Any]
    resume_text: str


def load_applicant_data(profile_path: str, resume_path: str) -> ApplicantData:
    """Load profile.yaml and the resume file into an ApplicantData instance.

    Args:
        profile_path: Absolute or relative path to profile.yaml.
        resume_path: Path to the resume — .md (preferred) or .pdf.

    Returns:
        An ApplicantData instance with profile_yaml and resume_text populated.

    Raises:
        FileNotFoundError: If either file does not exist.
    """
    profile_file = Path(profile_path)
    resume_file = Path(resume_path)

    if not profile_file.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    if not resume_file.exists():
        raise FileNotFoundError(
            f"Resume not found: {resume_path}  (Tip: .md format is preferred; .pdf is the fallback.)"
        )

    with profile_file.open(encoding="utf-8") as f:
        raw: Any = yaml.safe_load(f)
    profile_yaml: dict[str, Any] = raw if isinstance(raw, dict) else {}

    if resume_file.suffix.lower() == ".pdf":
        resume_text = _extract_pdf_text(resume_file)
    else:
        resume_text = resume_file.read_text(encoding="utf-8")

    return ApplicantData(profile_yaml=profile_yaml, resume_text=resume_text)


def _extract_pdf_text(path: Path) -> str:
    """Extract plain text from a PDF resume using PyPDF2.

    Args:
        path: Path to the PDF file.

    Returns:
        Concatenated text of all pages.
    """
    import PyPDF2  # imported lazily — only needed for PDF fallback

    with path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)
