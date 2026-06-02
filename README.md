# Job Agent

CLI tool that automates filling out online job application forms. Given a job posting URL and your profile/resume, it navigates the form, writes tailored cover letters and screening answers, and asks you only when it hits a genuine blocker (CAPTCHA, login wall, MFA).

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- An API key for your chosen LLM provider (Google Gemini by default)

## Setup

```bash
uv sync
uvx browser-use install
cp .env.example .env
# Edit .env — set the API key for your provider
```

Copy `applicant/profile.yaml.example` to `applicant/profile.yaml` and fill in your details. Add your resume as `applicant/resume.md` (Markdown preferred; `.pdf` also accepted).

To switch the LLM provider or model, edit `_LLM_PROVIDER` / `_LLM_MODEL` at the top of `src/job_agent/main.py`.

## Usage

```bash
# Fill a form (dry run — does not submit)
uv run job-agent apply https://jobs.example.com/apply/123 --dry-run

# Fill and submit
uv run job-agent apply https://jobs.example.com/apply/123

# Run browser headlessly
uv run job-agent apply <url> --headless

# View past applications
uv run job-agent log
uv run job-agent log --limit 20

# Validate your profile and resume files
uv run job-agent profile check
```

Always test with `--dry-run` before enabling submission on a new site.

## Profile (`applicant/profile.yaml`)

The agent reads this file to fill every form field. The more complete it is, the fewer questions it needs to ask. Key sections:

```yaml
personal:
  first_name: Jane
  last_name: Doe
  email: jane@example.com
  phone: "+1-555-555-5555"
  location: Stockholm, Sweden

target:
  roles: [Senior Software Developer]
  work_authorization: "US Citizen"

experience:
  years_total: 7
  current_title: "Senior Software Developer"

compensation:
  desired_salary_usd: 120000

preferences:
  cover_letter_tone: professional   # professional | casual | enthusiastic
  writing_style: natural-human      # natural-human | formal
```

For fields not in your profile, the agent generates a best-effort answer autonomously. It only pauses to ask you for hard blockers it cannot bypass.

## Environment variables

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Google Gemini (default provider) |
| `OPENAI_API_KEY` | OpenAI provider |
| `ANTHROPIC_API_KEY` | Anthropic provider |
| `GROQ_API_KEY` | Groq provider |
| `BROWSER_USE_API_KEY` | browseruse cloud provider |
| `BROWSER_HEADLESS` | `true`/`false` — headless mode |
| `LOG_DB_PATH` | SQLite log path (default: `./applications.db`) |

## Development

```bash
uv run mypy src/          # type-check (must pass clean)
uv run ruff check --fix . # lint
uv run ruff format .      # format
uv run pytest             # tests
```
