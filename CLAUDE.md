# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies and set up browser
uv sync
uv run playwright install chromium

# Run the CLI
uv run job-agent apply <url> [--dry-run] [--headless]
uv run job-agent log [--limit N]
uv run job-agent profile check

# Type-check (must pass with zero errors)
uv run mypy src/

# Lint and format
uv run ruff check --fix .
uv run ruff format .
```

Always use `uv run` — never invoke `python` or `pip` directly.

## Architecture

The data flow for a single `apply` run:

```
main.py (typer CLI)
  → profile.py          loads profile.yaml + resume (.md preferred, .pdf fallback)
  → prompt.py           builds the task string sent to browser-use Agent
  → agent.py            instantiates ChatOpenAI + Browser + Agent, calls Agent.run()
      ↕ tools.py        custom browser-use actions (ask_human, upload_resume, confirm_submit)
  → logger.py           writes SQLAlchemy Application row to applications.db
```

**`profile.py`** returns a `ProfileContext` dataclass with `.yaml_data` (dict) and `.resume_text` (str). All other modules consume this type — it is the canonical profile representation.

**`prompt.py`** is the single source of all prompt text. No prompt strings belong in `agent.py` or elsewhere. The prompt embeds the full profile context and explicit autonomy/style rules (no em-dashes, no AI buzzwords, autonomous answers for open-ended fields, `ask_human` only for hard blockers).

**`tools.py`** registers custom actions on a `browser-use` `Tools()` object. `ask_human` is intentionally narrow — it must only fire for CAPTCHAs, login walls, MFA, or fields with no inferable answer. Everything else the agent should answer autonomously.

**`agent.py`** is async throughout. `run_application()` is the sole public entry point; `main.py` calls it via `asyncio.run()`.

**`logger.py`** uses SQLAlchemy 2.0 declarative ORM (`DeclarativeBase`, `Mapped`, `mapped_column`). Engine is created from `LOG_DB_PATH` env var; `Base.metadata.create_all(engine)` runs on startup.

## Key constraints

- Every source file starts with `from __future__ import annotations`.
- All public function signatures are fully annotated; `uv run mypy src/` with `strict = true` must pass clean.
- `profile/` is `.gitignore`d — it contains personal data. Never commit it.
- Default resume format is `.md`; use `pypdf2` only when the file extension is `.pdf`.
- Always test new form automation with `--dry-run` before enabling submission.
- The `browser-use` `Agent.run()` call is async — the entry point wraps it with `asyncio.run()`.
- Use `ruff` (not black/flake8) for formatting and linting; target line length 120.
- Google-style docstrings on all public APIs.
- Absolute imports only.

## Environment

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Key variables:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
BROWSER_HEADLESS=false
LOG_DB_PATH=./applications.db
```
