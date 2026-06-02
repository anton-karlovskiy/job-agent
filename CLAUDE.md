# CLAUDE.md

We're building the app described in @SPEC.md. Read that file for general architectural tasks or to double-check the exact database structure, tech stack or application architecture.

For browser-use API usage and development rules, see @AGENTS.md.

Keep your replies extremely concise and focus on conveying the key information. No unnecessary fluff, no long code snippets.

Whenever working with any third-party library or something similar, you MUST look up the official documentation to ensure that you're working with up-to-date information.
Use the DocsExplorer subagent for efficient documentation lookup.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies and set up browser
uv sync
uvx browser-use install

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
  → applicant.py        loads profile.yaml + resume (.md preferred, .pdf fallback)
  → prompt.py           builds the task string sent to browser-use Agent
  → agent.py            instantiates LLM via make_llm(provider, model) + Browser + Agent, calls Agent.run()
      ↕ tools.py        custom browser-use actions (ask_human, confirm_submit)
  → logger.py           writes SQLAlchemy Application row to applications.db
```

**`applicant.py`** returns an `Applicant` dataclass with `.profile_yaml` (dict) and `.resume_text` (str). All other modules consume this type — it is the canonical applicant representation.

**`prompt.py`** is the single source of all prompt text. No prompt strings belong in `agent.py` or elsewhere. The prompt embeds the full profile context and explicit autonomy/style rules (no em-dashes, no AI buzzwords, autonomous answers for open-ended fields, `ask_human` only for hard blockers).

**`tools.py`** registers custom actions on a `browser-use` `Tools()` object. `ask_human` is intentionally narrow — it must only fire for CAPTCHAs, login walls, MFA, or fields with no inferable answer. Everything else the agent should answer autonomously.

**`agent.py`** is async throughout. `run_application()` is the sole public entry point; `main.py` calls it via `asyncio.run()`.

**`logger.py`** uses SQLAlchemy 2.0 declarative ORM (`DeclarativeBase`, `Mapped`, `mapped_column`). Engine is created from `LOG_DB_PATH` env var; `Base.metadata.create_all(engine)` runs on startup.

## Key constraints

- Every source file starts with `from __future__ import annotations`.
- All public function signatures are fully annotated; `uv run mypy src/` with `strict = true` must pass clean.
- `applicant/` is `.gitignore`d — it contains personal data. Never commit it.
- Default resume format is `.md`; use `pypdf2` only when the file extension is `.pdf`.
- Always test new form automation with `--dry-run` before enabling submission.
- The `browser-use` `Agent.run()` call is async — the entry point wraps it with `asyncio.run()`.
- Use `ruff` (not black/flake8) for formatting and linting; target line length 120.
- Google-style docstrings on all public APIs.
- Absolute imports only.

## Environment

Copy `.env.example` to `.env` and set the API key matching the provider configured in `main.py`. Key variables:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
BROWSER_HEADLESS=false
LOG_DB_PATH=./applications.db
```

To switch provider/model, edit `_LLM_PROVIDER` / `_LLM_MODEL` at the top of `src/job_agent/main.py`.

To install non-OpenAI provider packages: `uv sync --extra anthropic` / `--extra google` / `--extra all-providers`
