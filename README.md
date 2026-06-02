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
  location: San Francisco, CA
  linkedin: https://linkedin.com/in/janedoe
  github: https://github.com/janedoe
  twitter: https://x.com/janedoe
  telegram: https://t.me/janedoe

target:
  roles:
    - Senior Software Engineer
    - Backend Engineer
  seniority: Senior
  industries:
    - fintech
    - developer tools
  preferred_locations:
    - San Francisco, CA
    - Remote
  open_to_relocation: false
  notice_period: "2 weeks"
  work_authorization:
    citizenship: US Citizen
    authorized: true
    sponsorship_needed: false

experience:
  years_total: 7
  current_title: Senior Software Engineer
  current_company: Acme Corp
  summary: >
    Backend-focused engineer with 7 years building distributed systems in Python and Go.

skills:
  languages:
    - Python
    - Go
    - TypeScript
  frameworks:
    - FastAPI
    - Django
    - React
  tools:
    - PostgreSQL
    - Redis
    - Kubernetes
    - Docker

education:
  - degree: B.S. Computer Science
    school: University of California, Berkeley
    year: 2018

compensation:
  desired_salary_usd: 180000
  open_to_equity: true

preferences:
  cover_letter_tone: professional   # professional | casual
  writing_style: natural-human      # natural-human | formal

answers:
  # Pre-baked answers used verbatim for common screening questions.
  why_this_company: >
    I'm drawn to the company's focus on developer experience and its track record
    of shipping pragmatic solutions to hard infrastructure problems.
  greatest_strength: >
    I break ambiguous problems into concrete pieces quickly.
  greatest_weakness: >
    I used to under-communicate blockers; I've since built a daily check-in habit.
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

## Related projects

Other open-source job-application tools, for comparison:

| Project | Stars | Approach | Notes |
|---|---|---|---|
| [AIHawk](https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk) | ~30k | LLM-driven, tailored answers | Most popular; **archived/unmaintained** |
| [Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn) | ~2.4k | Selenium, LinkedIn Easy Apply | Best actively-maintained option |
| [ApplyPilot](https://github.com/Pickle-Pixel/ApplyPilot) | ~1.1k | Agentic, "any site, any form" | Closest in ambition to this project |
| [EasyApplyJobsBot](https://github.com/wodsuz/EasyApplyJobsBot) | ~0.8k | Scripted, multi-board | LinkedIn, Glassdoor, Greenhouse, etc. |
| [career-ops](https://github.com/santifer/career-ops) | — | Claude Code-based | A–F scoring, ATS PDF gen, scans Greenhouse/Ashby/Lever |

Most popular tools are scripted Selenium bots targeting LinkedIn Easy Apply (which bans automation). This project is distinct in being **browser-use + LLM-agent-driven**, working on any form autonomously.

## Development

```bash
uv run mypy src/          # type-check (must pass clean)
uv run ruff check --fix . # lint
uv run ruff format .      # format
uv run pytest             # tests
```
