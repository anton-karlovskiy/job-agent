from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

# LLM configuration — edit here to switch provider or model.
# Providers: openai | anthropic | google | groq | browseruse
# Model: None uses the provider default (gpt-4o / claude-sonnet-4-6 / gemini-2.0-flash)
_LLM_PROVIDER = "google"
_LLM_MODEL: str | None = "gemini-2.5-flash"

app = typer.Typer(
    name="job-agent",
    help="AI-powered job application automation.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.callback()
def _root() -> None:
    """AI-powered job application automation."""


@app.command()
def apply(
    url: str = typer.Argument(..., help="Job application URL"),
    profile_path: Path = typer.Option(
        Path("./applicant/profile.yaml"),
        "--profile",
        help="Path to profile.yaml",
        show_default=True,
    ),
    resume_path: Path = typer.Option(
        Path("./applicant/resume.md"),
        "--resume",
        help="Path to resume (.md preferred, .pdf also accepted)",
        show_default=True,
    ),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fill the form but do not submit"),
    yes: bool = typer.Option(False, "--yes", help="Skip the final submission confirmation prompt"),
) -> None:
    """Navigate to a job application URL and fill out the form using your profile."""
    # Validate inputs early — before launching a browser
    if not profile_path.exists():
        console.print(f"[red]Profile not found:[/red] {profile_path}")
        raise typer.Exit(code=1)
    if not resume_path.exists():
        console.print(f"[red]Resume not found:[/red] {resume_path}")
        console.print("[dim]Tip: .md format is preferred. Use --resume to specify an alternate path.[/dim]")
        raise typer.Exit(code=1)

    # Import here to keep startup fast (typer --help stays snappy)
    from job_agent.agent import make_llm, run_application
    from job_agent.applicant import load_applicant, resume_as_pdf

    try:
        llm = make_llm(_LLM_PROVIDER, _LLM_MODEL)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.rule("[bold]job-agent apply[/bold]")
    console.print(f"  URL    : {url}")
    console.print(f"  LLM    : {_LLM_PROVIDER}/{_LLM_MODEL or '(default)'}")
    console.print(f"  Resume : {resume_path}")
    if dry_run:
        console.print("[yellow]  Mode   : DRY RUN — form will be filled but NOT submitted[/yellow]")
    console.rule()

    try:
        applicant = load_applicant(str(profile_path), str(resume_path))
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    with resume_as_pdf(resume_path) as pdf_path:
        result = asyncio.run(
            run_application(
                job_url=url,
                applicant=applicant,
                available_file_paths=[pdf_path],
                llm=llm,
                headless=headless,
                dry_run=dry_run,
                auto_confirm=yes,
            )
        )

    if result.success:
        console.rule("[green]Done[/green]")
        console.print(result.message)
    else:
        console.rule("[red]Failed[/red]")
        console.print(result.message)
        if result.error:
            console.print(f"[dim]{result.error}[/dim]")
        raise typer.Exit(code=1)
