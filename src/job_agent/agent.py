from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from browser_use import Agent, Browser

from job_agent.applicant import Applicant
from job_agent.prompt import build_task_prompt
from job_agent.tools import make_tools

_PROVIDER_DEFAULTS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
    "google": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "browseruse": "",
}

SUPPORTED_PROVIDERS: list[str] = list(_PROVIDER_DEFAULTS)


def make_llm(provider: str, model: str | None) -> Any:
    """Instantiate a LangChain chat model for the given provider and model name.

    Args:
        provider: One of 'openai', 'anthropic', 'google', 'groq', 'browseruse'.
        model: Model name; uses a sensible default for the provider when None.

    Returns:
        A LangChain BaseChatModel instance.
    """
    resolved = model or _PROVIDER_DEFAULTS.get(provider, "")
    if provider == "openai":
        from browser_use import ChatOpenAI
        return ChatOpenAI(model=resolved)
    if provider == "anthropic":
        from browser_use import ChatAnthropic
        return ChatAnthropic(model=resolved, temperature=0.0)
    if provider == "google":
        from browser_use import ChatGoogle
        return ChatGoogle(model=resolved)
    if provider == "groq":
        from browser_use import ChatGroq
        return ChatGroq(model=resolved)
    if provider == "browseruse":
        from browser_use import ChatBrowserUse
        return ChatBrowserUse()
    raise ValueError(f"Unknown provider {provider!r}. Choose from: {', '.join(SUPPORTED_PROVIDERS)}")


@dataclass
class AgentResult:
    """Result returned by run_application."""

    success: bool
    message: str
    error: str | None = field(default=None)


async def run_application(
    job_url: str,
    applicant: Applicant,
    available_file_paths: list[str],
    llm: Any,
    headless: bool,
    dry_run: bool,
    auto_confirm: bool,
) -> AgentResult:
    """
    Run the job application agent for the given URL.

    Args:
        job_url: URL of the job application form.
        applicant: Loaded applicant.
        available_file_paths: Absolute paths to files the agent may upload (e.g. resume).
        llm: Instantiated LangChain chat model (created by make_llm in main.py).
        headless: Whether to run the browser in headless mode.
        dry_run: If True, fill the form but do not submit.
        auto_confirm: If True, skip submission confirmation (Phase 2 flag).

    Returns:
        AgentResult with success flag, message, and optional error string.
    """
    task = build_task_prompt(applicant=applicant, job_url=job_url, dry_run=dry_run)
    browser: Any = Browser(headless=headless, keep_alive=dry_run)

    agent: Any = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=make_tools(auto_confirm=auto_confirm),
        available_file_paths=available_file_paths,
        max_actions_per_step=5,
    )

    try:
        history: Any = await agent.run()
        succeeded: bool = bool(history.is_successful())
        raw = history.final_result()
        final: str = raw if raw is not None else str(history)
        return AgentResult(success=succeeded, message=final)
    except TimeoutError as exc:
        return AgentResult(success=False, message="Agent timed out.", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return AgentResult(success=False, message="Agent encountered an error.", error=str(exc))
    finally:
        if not dry_run:
            await browser.kill()
