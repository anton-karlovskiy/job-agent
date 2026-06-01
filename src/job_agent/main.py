from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

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
        Path("./profile/profile.yaml"),
        "--profile",
        help="Path to profile.yaml",
        show_default=True,
    ),
    resume_path: Path = typer.Option(
        Path("./profile/resume.md"),
        "--resume",
        help="Path to resume (.md preferred, .pdf also accepted)",
        show_default=True,
    ),
    model: str = typer.Option("gpt-4o", "--model", envvar="OPENAI_MODEL", help="OpenAI model to use"),
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

    console.rule("[bold]job-agent apply[/bold]")
    console.print(f"  URL    : {url}")
    console.print(f"  Model  : {model}")
    console.print(f"  Resume : {resume_path}")
    if dry_run:
        console.print("[yellow]  Mode   : DRY RUN — form will be filled but NOT submitted[/yellow]")
    console.rule()

    # Import here to keep startup fast (typer --help stays snappy)
    from job_agent.agent import run_application
    from job_agent.profile import load_profile_context

    try:
        profile = load_profile_context(str(profile_path), str(resume_path))
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    result = asyncio.run(
        run_application(
            job_url=url,
            profile=profile,
            resume_path=str(resume_path.resolve()),
            model=model,
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
