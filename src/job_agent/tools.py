from __future__ import annotations

from typing import Any

from browser_use import ActionResult, Tools
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
