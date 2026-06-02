from __future__ import annotations

import asyncio
import functools
from typing import Any

from browser_use import ActionResult, Tools
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def make_tools(auto_confirm: bool = False) -> Tools[Any]:
    """Create a configured Tools instance.

    Args:
        auto_confirm: If True, confirm_submit approves automatically (--yes flag).

    Returns:
        Tools instance with ask_human and confirm_submit registered.
    """
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
        try:
            answer = await asyncio.to_thread(
                functools.partial(Prompt.ask, "[dim]Your response (or press Enter when done)[/dim]")
            )
        except (EOFError, asyncio.CancelledError):
            answer = ""
        if not answer:
            return ActionResult(
                extracted_content=(
                    "No human input available. Call `done` with success=False and include "
                    "this blocker in your summary so the user can review it."
                ),
                long_term_memory=f"Hard blocker encountered (no human available): {message!r}",
            )
        return ActionResult(
            extracted_content=f"Human responded: {answer}",
            long_term_memory=f"User was asked: {message!r}. They responded: {answer!r}",
        )

    @tools.action(  # type: ignore[untyped-decorator]
        description=(
            "Call this BEFORE clicking the final submit/apply/send button. "
            "Pass a plain-text summary table of every field name and value you filled in. "
            "Wait for the user to confirm before proceeding to submit. "
            "If the user declines, call `done` with success=False."
        )
    )
    async def confirm_submit(summary: str) -> ActionResult:
        """Show the filled-form summary and ask the user whether to submit.

        Args:
            summary: Human-readable table of field → value pairs.

        Returns:
            ActionResult telling the agent whether to proceed or abort.
        """
        if auto_confirm:
            console.rule("[cyan]Submitting (--yes)[/cyan]")
            console.print(summary)
            return ActionResult(
                extracted_content="Auto-confirmed. Proceed with submission.",
                long_term_memory="Submission auto-confirmed via --yes flag.",
            )

        console.rule("[cyan]Ready to submit — please review[/cyan]")
        console.print(summary)
        try:
            answer = await asyncio.to_thread(
                functools.partial(Prompt.ask, "[bold]Submit the application? [y/N][/bold]", default="n")
            )
        except (EOFError, asyncio.CancelledError):
            answer = "n"

        if answer.strip().lower() in ("y", "yes"):
            return ActionResult(
                extracted_content="User confirmed. Proceed with submission.",
                long_term_memory="User confirmed submission.",
            )
        return ActionResult(
            extracted_content="User declined. Do NOT submit. Call `done` with success=False.",
            long_term_memory="User declined submission.",
            is_done=True,
            success=False,
        )

    return tools
