from __future__ import annotations

import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Applicant:
    """Applicant profile and resume data consumed by all other modules."""

    profile_yaml: dict[str, Any]
    resume_text: str


def load_applicant(profile_path: str, resume_path: str) -> Applicant:
    """Load profile.yaml and the resume file into an Applicant instance.

    Args:
        profile_path: Absolute or relative path to profile.yaml.
        resume_path: Path to the resume — .md (preferred) or .pdf.

    Returns:
        An Applicant instance with profile_yaml and resume_text populated.

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

    return Applicant(profile_yaml=profile_yaml, resume_text=resume_text)


@contextmanager
def resume_as_pdf(resume_path: Path) -> Generator[str, None, None]:
    """Yield an absolute path to a PDF version of the resume, cleaning up any temp file on exit.

    Args:
        resume_path: Path to the resume (.md or .pdf).

    Yields:
        Absolute path string to a PDF file ready for upload.
    """
    if resume_path.suffix.lower() == ".pdf":
        yield str(resume_path.resolve())
        return

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    tmp_path = Path(tmp.name)
    try:
        _md_to_pdf(resume_path, tmp_path)
        yield str(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _md_to_pdf(md_path: Path, pdf_path: Path) -> None:
    """Convert a Markdown resume to PDF using markdown + xhtml2pdf (no system dependencies).

    Args:
        md_path: Source .md file.
        pdf_path: Destination .pdf file (will be overwritten).

    Raises:
        RuntimeError: If xhtml2pdf reports conversion errors.
    """
    import markdown as md_lib  # lazy import — only needed for PDF export
    from xhtml2pdf import pisa  # lazy import — only needed for PDF export

    html_body = md_lib.markdown(md_path.read_text(encoding="utf-8"))
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        "<style>"
        "body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;margin:2cm}"
        "h1{font-size:18pt}h2{font-size:14pt}h3{font-size:12pt}"
        "ul,ol{margin-left:1.2em}"
        "</style></head><body>"
        f"{html_body}"
        "</body></html>"
    )
    with pdf_path.open("wb") as f:
        status = pisa.CreatePDF(html, dest=f)
    if status.err:
        raise RuntimeError(f"PDF conversion failed with {status.err} error(s)")


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
