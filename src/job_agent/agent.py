from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from browser_use import Agent, Browser, ChatOpenAI

from job_agent.profile import ProfileContext
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
    profile: ProfileContext,
    resume_path: str,
    model: str,
    headless: bool,
    dry_run: bool,
    auto_confirm: bool,
) -> AgentResult:
    """Run the job application agent for the given URL.

    Args:
        job_url: URL of the job application form.
        profile: Loaded profile context.
        resume_path: Absolute path to the resume file.
        model: OpenAI model name (e.g. "gpt-4o").
        headless: Whether to run the browser in headless mode.
        dry_run: If True, fill the form but do not submit.
        auto_confirm: If True, skip submission confirmation (Phase 2 flag).

    Returns:
        AgentResult with success flag, message, and optional error string.
    """
    task = build_task_prompt(profile=profile, job_url=job_url, dry_run=dry_run)
    llm: Any = ChatOpenAI(model=model)
    browser: Any = Browser(headless=headless)

    agent: Any = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=tools,
        custom_context={"resume_path": resume_path},
        max_failures=3,
    )

    try:
        history: Any = await agent.run()
        return AgentResult(success=True, message=str(history))
    except TimeoutError as exc:
        return AgentResult(success=False, message="Agent timed out.", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return AgentResult(success=False, message="Agent encountered an error.", error=str(exc))
    finally:
        await browser.kill()
