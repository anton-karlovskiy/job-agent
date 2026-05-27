# job-agent — specification

## Overview

`job-agent` is a CLI tool that automates filling out and submitting online job application forms. It uses `browser-use` for AI-driven browser automation and OpenAI as the LLM brain. Given a job posting URL and the user's profile/resume, it navigates to the form, fills it out intelligently, writes cover letters and screening answers, and pauses to ask the user when it encounters questions it cannot confidently answer.

---

## Goals

- Eliminate repetitive manual work when applying to jobs online
- Support any job application form (Greenhouse, Lever, Workday, custom sites, etc.)
- Generate tailored cover letters and screening question answers using profile context
- Pause and ask the user interactively when the agent is uncertain
- Log every application for tracking

---

## Non-goals (v1)

- No GUI — CLI only
- No parallel/batch application runs
- No LinkedIn Easy Apply integration (deferred to later)
- No autonomous submission without user confirmation

---

## Tech stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Ecosystem fit |
| Package manager | `uv` | Fast, modern, replaces pip |
| Browser automation | `browser-use` | AI-native agent loop built on Playwright |
| LLM | OpenAI (`gpt-4o` default, `o3` optional) | User has premium key; `browser-use` supports `ChatOpenAI` natively |
| CLI | `typer` + `rich` | Clean CLI with pretty output |
| Config/profile | YAML + PDF resume | Human-editable, easy to version |
| Storage | SQLite via `sqlite-utils` | Zero-setup application log |
| Env management | `python-dotenv` | Standard `.env` pattern |

---

## Project structure

```
job-agent/
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── README.md
├── SPEC.md
├── profile/
│   ├── resume.pdf            # User's resume (PDF)
│   └── profile.yaml          # Structured personal/professional info
├── src/
│   └── job_agent/
│       ├── __init__.py
│       ├── main.py           # CLI entry point (typer app)
│       ├── agent.py          # browser-use Agent setup and run loop
│       ├── profile.py        # Load and merge resume + profile.yaml
│       ├── prompt.py         # Build task prompt string for the agent
│       ├── tools.py          # Custom browser-use tool actions
│       ├── logger.py         # SQLite application log
│       └── utils.py          # Shared helpers
└── tests/
    └── test_profile.py
```

---

## Dependencies (`pyproject.toml`)

```toml
[project]
name = "job-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "browser-use>=0.12",
    "langchain-openai",
    "typer[all]",
    "rich",
    "pyyaml",
    "pypdf2",
    "python-dotenv",
    "sqlite-utils",
]

[project.scripts]
job-agent = "job_agent.main:app"
```

Install and run:
```bash
uv sync
uv run playwright install chromium
uv run job-agent --help
```

---

## Profile schema (`profile/profile.yaml`)

This file is the single source of truth for the agent. All fields are optional but the more complete it is, the fewer questions the agent needs to ask.

```yaml
personal:
  first_name: Jane
  last_name: Doe
  email: jane@example.com
  phone: "+1-555-555-5555"
  address: "123 Main St"
  city: Stockholm
  postal_code: "11122"
  country: Sweden
  linkedin: https://linkedin.com/in/janedoe
  github: https://github.com/janedoe
  website: https://janedoe.dev

work_authorization:
  authorized: true          # legally authorized to work
  sponsorship_needed: false

professional:
  title: "Senior Software Developer"
  years_experience: 7
  summary: >
    Full-stack software developer with 7 years of experience across
    web, mobile, and backend systems. Strong in Python, TypeScript,
    and cloud infrastructure.
  skills:
    - Python
    - TypeScript
    - React
    - Node.js
    - PostgreSQL
    - Docker
    - AWS
  desired_salary: "120000 USD"
  notice_period: "4 weeks"
  open_to_remote: true
  open_to_relocation: false

education:
  - degree: "B.Sc. Computer Science"
    institution: "Uppsala University"
    year: 2017

preferences:
  cover_letter_tone: professional   # professional | casual | enthusiastic
  cover_letter_length: medium       # short | medium | long
  writing_style: natural-human      # natural-human (default) | formal
```

---

## Environment variables (`.env`)

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o          # or o3
BROWSER_HEADLESS=false        # set true for headless runs
LOG_DB_PATH=./applications.db
```

---

## CLI interface

### `job-agent apply`

Main command. Navigates to the job URL and runs the application agent.

```bash
job-agent apply <url> [options]

Options:
  --profile PATH     Path to profile.yaml (default: ./profile/profile.yaml)
  --resume PATH      Path to resume PDF (default: ./profile/resume.pdf)
  --model TEXT       OpenAI model override (default: from .env)
  --headless         Run browser in headless mode
  --dry-run          Fill the form but do not submit
  --yes              Skip the final submission confirmation prompt
```

Example:
```bash
job-agent apply https://jobs.example.com/apply/12345 --dry-run
```

### `job-agent log`

Show past applications from the SQLite log.

```bash
job-agent log [--limit N] [--status STATUS]
```

### `job-agent profile check`

Validate that `profile.yaml` and `resume.pdf` exist and are parseable.

```bash
job-agent profile check
```

---

## Core modules

### `profile.py`

Responsibilities:
- Load and validate `profile.yaml`
- Extract text from `resume.pdf` using `pypdf2`
- Return a merged context string + structured dict used in prompts

Key function:
```python
def load_profile(profile_path: str, resume_path: str) -> ProfileContext:
    """Returns a ProfileContext with .yaml_data (dict) and .resume_text (str)"""
```

### `prompt.py`

Responsibilities:
- Build the task prompt string sent to `browser-use` Agent
- Incorporate profile context, job URL, and any instructions
- Prompt structure: role + objective + profile data + step-by-step instructions + uncertainty rule
- Inject writing-style constraints (no em-dashes, no AI buzzwords, varied sentence rhythm) so generated text passes human review

Key function:
```python
def build_task_prompt(profile: ProfileContext, job_url: str, dry_run: bool) -> str:
```

The prompt must include an explicit instruction like:
> "Generate a best-effort answer for any field not covered by the profile — do not pause to ask the user for open-ended questions or ambiguous options. Call the `ask_human` tool only for hard blockers you cannot resolve yourself: CAPTCHAs, login walls, MFA prompts, or required fields with no inferable answer."

### `tools.py`

Custom `browser-use` tool actions registered on the `Tools()` object:

| Tool name | Description |
|---|---|
| `ask_human` | Pauses agent for hard blockers the AI cannot resolve (CAPTCHAs, login walls, MFA); prints a message describing what the user must do and waits for confirmation before continuing |
| `upload_resume` | Handles resume file upload to detected file input elements |
| `confirm_submit` | Prints a summary (including all AI-generated answers) and asks user to confirm before the agent clicks submit (unless `--yes` flag is set) |

```python
from browser_use import Tools
from rich.prompt import Prompt

tools = Tools()

@tools.action(description="Interrupt the user only for hard blockers you cannot bypass yourself: CAPTCHAs, login walls, MFA prompts, or required fields with no inferable answer. Do NOT call this for open-ended questions or missing profile fields — generate a best answer instead.")
def ask_human(message: str) -> str:
    return Prompt.ask(f"[yellow]Agent needs your input[/yellow]\n{message}")
```

### `agent.py`

Responsibilities:
- Instantiate `ChatOpenAI` with the configured model
- Instantiate `Browser` with headless/headful setting
- Instantiate `browser-use` `Agent` with task prompt, LLM, browser, and custom tools
- Run the agent and return the result
- Handle errors and timeouts gracefully

```python
async def run_application(
    job_url: str,
    profile: ProfileContext,
    resume_path: str,
    model: str,
    headless: bool,
    dry_run: bool,
    auto_confirm: bool,
) -> AgentResult:
```

### `logger.py`

Responsibilities:
- Create and manage `applications.db` SQLite database
- Insert a record after each run (success or failure)
- Support listing past applications

Schema:
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    job_title TEXT,
    company TEXT,
    status TEXT,           -- 'submitted' | 'dry_run' | 'failed' | 'abandoned'
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT             -- agent's final_result summary
);
```

### `main.py`

Typer CLI app wiring the commands above together. Uses `rich` for formatted output (status spinners, confirmation prompts, log tables).

---

## Agent task prompt structure

The prompt passed to `browser-use` should follow this structure:

```
You are a job application assistant. Your goal is to fill out and submit the job application at: {url}

APPLICANT PROFILE:
{yaml_data as formatted text}

RESUME TEXT:
{resume_text}

INSTRUCTIONS:
1. Navigate to the job application URL.
2. Scroll through the entire form first to understand its structure.
3. Fill out every field — do not skip optional fields.
4. If a field is not explicitly covered by the profile, generate the best possible answer using the job description, company context visible on the page, and the applicant's background. Do NOT call `ask_human` for open-ended essay questions, motivation questions, or ambiguous options — make a confident, tailored choice. Write in natural, varied prose. Avoid em-dashes, AI-associated buzzwords ("leverage", "spearhead", "delve", "I am thrilled to"), and bullet-heavy structure. Vary sentence length. Contractions are fine where the tone allows.
5. For cover letter fields: write a tailored cover letter using the profile and any job description text visible on the page. Tone: {cover_letter_tone}. Use prose paragraphs, not bullets. Avoid em-dashes and overused opener phrases. Every sentence should sound like it was typed by the applicant, not generated.
6. For file upload fields: use the `upload_resume` tool.
7. Before clicking submit: call the `confirm_submit` tool to show the user a full summary of all filled fields (including AI-generated answers) so they can review and confirm. [omit if --yes flag]
8. Call `ask_human` only when you hit a hard blocker you cannot bypass: a CAPTCHA, an unexpected login wall, an MFA prompt, or a required field with no inferable answer (e.g. an internal employee ID). Describe exactly what you encountered and what the user needs to do.
9. After successful submission, use the `done` action with a human-readable summary of all fields filled and any blockers encountered.

{"DO NOT click the submit button — this is a dry run." if dry_run else ""}
```

---

## Human-in-the-loop flow

### AI-generated answers (no interruption)

For any field the profile does not explicitly cover, the agent generates the best possible answer autonomously:

- **Open-ended / motivational questions** (e.g. "Why do you want to work here?", "Describe a challenge you overcame") — agent writes a tailored response using the job description, visible company context, and the applicant's background.
- **Ambiguous options** (e.g. salary range, start date) — agent makes a reasonable choice informed by the job posting and profile defaults.

All AI-generated answers are surfaced in the pre-submission review (`confirm_submit`) so the user can read through everything and edit in the browser before confirming.

### `ask_human` — reserved for hard blockers only

The agent calls `ask_human` only when it hits something it cannot bypass:

- A **CAPTCHA** or bot-detection challenge
- An unexpected **login wall** or **MFA prompt**
- A required field with **no inferable answer** (e.g. an internal employee ID, a referral code)

The terminal pauses and shows:
```
╭─ Agent needs your input ─────────────────────────────────────────╮
│ I encountered a CAPTCHA on the application page. Please solve it │
│ in the browser window, then press Enter to continue.             │
╰──────────────────────────────────────────────────────────────────╯
Press Enter when done: █
```

The user resolves the blocker in the browser and presses Enter; the agent resumes from where it stopped.

---

## Text generation style

AI-generated text is increasingly recognised and rejected by application reviewers. The agent must write all free-text content so that it reads as naturally composed by the applicant.

### Rules the agent must follow

**Avoid these AI-writing markers:**
- Em-dashes (—): use a comma, semicolon, or restructure the sentence instead
- Overused AI vocabulary: "leverage", "spearhead", "synergy", "passionate about", "I am excited to", "I am thrilled to", "delve", "it is worth noting"
- Bullet-heavy cover letters: prose paragraphs read more human
- Unnaturally uniform sentence length: vary short and long sentences
- Starting consecutive sentences with the same word or structure

**Aim for:**
- Concrete, specific sentences ("I reduced deploy time from 45 min to 8 min by migrating to GitHub Actions") over vague claims ("I improved processes")
- Occasional contractions where the tone allows ("I've", "I'd", "wasn't")
- Natural paragraph transitions without signpost phrases like "Furthermore," or "In conclusion,"
- First-person voice that sounds like one person wrote it, not a template

### Where this applies

All free-text the agent fills autonomously:
- Cover letter fields
- "Why do you want to work here?" and similar motivation questions
- Competency / behavioural questions ("Describe a challenge you overcame")
- Any other open-ended text box

The `writing_style: natural-human` profile preference (default) enforces these rules. Setting it to `formal` relaxes them for industries where structured prose is conventional (law, finance, academia).

---

## Application log output

After each run, `job-agent log` displays:

```
 #   Company      Job URL                          Status      Applied
 1   Acme Corp    https://jobs.acme.com/apply/1    submitted   2026-05-27 10:32
 2   Beta Inc     https://beta.io/careers/42       dry_run     2026-05-27 11:01
```

---

## Error handling

| Scenario | Behaviour |
|---|---|
| Resume PDF not found | Exit with clear error before starting browser |
| Profile YAML missing required fields | Warn but continue; agent generates best-effort answers from context |
| Browser-use agent times out | Log as 'failed', print last agent step for debugging |
| Network error mid-form | Agent retries up to 3 times, then calls ask_human |
| CAPTCHA detected | Agent calls ask_human: "I encountered a CAPTCHA. Please solve it and press Enter." |

---

## Development phases

### Phase 1 — core (start here)
- [ ] Project scaffold with `uv`, `pyproject.toml`, folder structure
- [ ] `profile.py` — load YAML + parse PDF resume
- [ ] `tools.py` — `ask_human` and `upload_resume` tools
- [ ] `agent.py` — wire up `browser-use` Agent with OpenAI
- [ ] `prompt.py` — task prompt builder
- [ ] `main.py` — `job-agent apply` CLI command
- [ ] Manual test against a real job application URL

### Phase 2 — quality of life
- [ ] `logger.py` — SQLite application log
- [ ] `job-agent log` command
- [ ] `confirm_submit` tool + `--yes` / `--dry-run` flags
- [ ] `job-agent profile check` command
- [ ] `.env.example` and README

### Phase 3 — advanced features (future)
- [ ] Cover letter quality improvements (scrape job description for tailoring)
- [ ] Multi-step / multi-page form handling improvements
- [ ] Support for LinkedIn Easy Apply
- [ ] Batch mode: apply to a list of URLs from a file
- [ ] Application status tracking (follow-up reminders)
- [ ] Browser profile reuse for sites requiring login (e.g. Indeed, LinkedIn)

---

## Notes for Claude Code

- Use `uv sync` — never `pip install`
- All async code uses `asyncio`; entry point calls `asyncio.run(...)`
- `browser-use` `Agent.run()` is async — wrap appropriately in `main.py`
- Keep prompts in `prompt.py`, not scattered in `agent.py`
- The `profile/` directory should be in `.gitignore` (contains personal data)
- Test with `--dry-run` first on any real job URL before enabling submission
