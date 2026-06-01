from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from browser_use import Agent, Browser, ChatOpenAI

from job_agent.profile import ApplicantData
from job_agent.prompt import build_task_prompt
from job_agent.tools import tools


@dataclass
class AgentResult:
    """Result returned by run_application."""

    success: bool
    message: str
    error: str | None = field(default=None)


async def run_application(
    job_url: str,
    applicant: ApplicantData,
    available_file_paths: list[str],
    model: str,
    headless: bool,
    dry_run: bool,
    auto_confirm: bool,
) -> AgentResult:
    """
    Run the job application agent for the given URL.

    Args:
        job_url: URL of the job application form.
        applicant: Loaded applicant data.
        available_file_paths: Absolute paths to files the agent may upload (e.g. resume).
        model: OpenAI model name (e.g. "gpt-4o").
        headless: Whether to run the browser in headless mode.
        dry_run: If True, fill the form but do not submit.
        auto_confirm: If True, skip submission confirmation (Phase 2 flag).

    Returns:
        AgentResult with success flag, message, and optional error string.
    """
    task = build_task_prompt(applicant=applicant, job_url=job_url, dry_run=dry_run)
    llm: Any = ChatOpenAI(model=model)
    browser: Any = Browser(headless=headless, keep_alive=dry_run)

    agent: Any = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=tools,
        available_file_paths=available_file_paths,
        max_failures=3,
    )

    try:
        history: Any = await agent.run()
        succeeded: bool = bool(history.is_successful())
        if dry_run:
            try:
                msg = (
                    "\n[dry-run] Form filled. Review the browser, then press Enter to close it..."
                    if succeeded
                    else "\n[dry-run] Agent did not complete successfully. Review the browser, then press Enter to close it..."
                )
                await asyncio.to_thread(input, msg)
            except EOFError:
                pass
        raw = history.final_result()
        final: str = raw if raw is not None else str(history)
        return AgentResult(success=succeeded, message=final)
    except TimeoutError as exc:
        return AgentResult(success=False, message="Agent timed out.", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return AgentResult(success=False, message="Agent encountered an error.", error=str(exc))
    finally:
        await browser.kill()
