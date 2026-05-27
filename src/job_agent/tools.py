from __future__ import annotations

import os
from typing import Any

from browser_use import ActionResult, BrowserSession, Tools
from browser_use.browser.events import UploadFileEvent
from rich.console import Console
from rich.prompt import Prompt

console = Console()
tools: Tools[Any] = Tools()


@tools.action(  # type: ignore[untyped-decorator]
    description=(
        "Interrupt the user ONLY for hard blockers you cannot bypass yourself: "
        "CAPTCHAs, login walls, MFA prompts, or required fields with absolutely no inferable answer "
        "(e.g. an internal employee ID or referral code). "
        "Do NOT call this for open-ended questions, missing profile fields, or ambiguous options — "
        "generate a best-effort answer instead."
    )
)
async def ask_human(message: str) -> ActionResult:
    """Pause and ask the human for input when hitting a hard blocker.

    Args:
        message: Description of the blocker and what the user must do.

    Returns:
        ActionResult containing the human's response.
    """
    console.rule("[yellow]Agent needs your input[/yellow]")
    console.print(f"[bold]{message}[/bold]")
    answer = Prompt.ask("[dim]Your response (or press Enter when done)[/dim]")
    return ActionResult(
        extracted_content=f"Human responded: {answer}",
        long_term_memory=f"User was asked: {message!r}. They responded: {answer!r}",
    )


@tools.action(  # type: ignore[untyped-decorator]
    description=(
        "Upload the applicant's resume file to a file upload field. "
        "Call this when you encounter a resume / CV file input. "
        "Pass the DOM element index of the file input field."
    )
)
async def upload_resume(
    index: int,
    browser_session: BrowserSession,
    resume_path: str,  # injected from Agent's custom_context
) -> ActionResult:
    """Upload the resume to the file input at the given DOM element index.

    Args:
        index: DOM element index of the file input (as shown in the page state).
        browser_session: Injected by browser-use framework.
        resume_path: Injected from custom_context; absolute path to the resume file.

    Returns:
        ActionResult indicating success or describing the error.
    """
    if not os.path.exists(resume_path):
        return ActionResult(error=f"Resume file not found: {resume_path}")

    node = await browser_session.get_dom_element_by_index(index)
    if node is None:
        return ActionResult(error=f"No DOM element found at index {index}.")

    if not browser_session.is_file_input(node):
        return ActionResult(error=f"Element at index {index} is not a file input.")

    upload_event = browser_session.event_bus.dispatch(UploadFileEvent(node=node, file_path=resume_path))
    await upload_event

    console.print(f"[green]Uploaded resume:[/green] {resume_path}")
    return ActionResult(
        extracted_content=f"Successfully uploaded resume: {resume_path}",
        long_term_memory=f"Resume uploaded from {resume_path} to element index {index}.",
    )
