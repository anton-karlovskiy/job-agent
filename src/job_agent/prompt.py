from __future__ import annotations

import yaml

from job_agent.applicant import Applicant

_NATURAL_HUMAN_STYLE = (
    "Write all free-text so it sounds naturally composed by the applicant: "
    "no em-dashes, no AI buzzwords (leverage, spearhead, synergy, passionate about, thrilled to, delve, "
    "it is worth noting), no bullet-heavy cover letters. "
    "Vary sentence length — mix short punchy sentences with longer ones. "
    "Use concrete specifics over vague claims. "
    "Occasional contractions (I've, I'd, wasn't) are fine where the tone allows."
)

_FORMAL_STYLE = (
    "Write in clear, structured prose appropriate for a formal professional context "
    "(law, finance, academia). Contractions and casual phrasing should be avoided."
)


def build_task_prompt(applicant: Applicant, job_url: str, dry_run: bool) -> str:
    """Build the task prompt string sent to the browser-use Agent.

    Args:
        applicant: Loaded applicant containing profile yaml and resume text.
        job_url: URL of the job application form.
        dry_run: If True, instruct the agent not to click submit.

    Returns:
        A complete task prompt string.
    """
    profile_text = yaml.dump(applicant.profile_yaml, default_flow_style=False, allow_unicode=True)

    preferences: dict[str, str] = applicant.profile_yaml.get("preferences", {})
    cover_letter_tone: str = preferences.get("cover_letter_tone", "professional")
    writing_style: str = preferences.get("writing_style", "natural-human")

    style_rule = _NATURAL_HUMAN_STYLE if writing_style == "natural-human" else _FORMAL_STYLE

    submission_step = (
        "**9. DRY RUN — stop before submitting**\n"
        "Do NOT click submit. Report the full summary of what you would have submitted."
        if dry_run
        else (
            "**9. Before submitting — call `confirm_submit`**\n"
            "Before clicking the final submit/apply/send button:\n"
            "- Compile a two-column table: field name | value filled.\n"
            "- Call `confirm_submit` with that table as the `summary` argument.\n"
            "- If the user confirms → click submit.\n"
            "- If the user declines → call `done` with success=False and note the reason."
        )
    )

    return f"""You are a job application assistant. Fill out and submit the job application at: {job_url}

---

## APPLICANT PROFILE
{profile_text}
## APPLICANT RESUME
{applicant.resume_text}

---

## INSTRUCTIONS

**1. Navigate**
Use the `navigate` action to go to the job application URL.

**2. Survey the form before filling anything**
Use `scroll` to reach the bottom of the page, then call `extract` with the query
"list every visible form field: label, type (text/dropdown/checkbox/file/textarea), and whether it is required".
Study the result before touching any field.

**3. Required fields — fill without exception**
- If an answer isn't in the profile, infer the best one from the job description, company context, and the applicant's background.
- Use the `input` action for text fields. For checkboxes and radio buttons use `click`.
- Do NOT call `ask_human` for essay questions, motivation questions, or ambiguous options — make a confident, tailored choice.
- Writing style: {style_rule}

**4. Substantive optional fields — always fill**
Cover letters, personal statements, "Why this company?", motivation or essay questions directly affect hiring.
Treat them as required. Generate a confident, tailored answer even when not explicitly covered by the profile.

**5. Low-signal optional fields — leave blank**
Skip: demographic questions, referral codes, internal platform usernames, promo codes,
"How did you hear about us?" (when no clear answer is in the profile).

**6. Cover letter fields**
Distinguish between two types:
- **Free-text textarea** — write a full prose cover letter (tone: {cover_letter_tone}). Use paragraphs, not bullets.
- **File upload input** — skip entirely; do NOT upload the resume as a substitute.
  Only upload a dedicated cover letter file if one is explicitly in your available file list.
- If no cover letter field exists, skip this step entirely.

**7. File upload fields (resume / CV)**
Use the `upload_file` action: pass the file path from your available file list and the DOM index of the file input.

**8. Dropdowns and autocomplete fields (`role=combobox`)**
- Use `click` on the field → `input` to type and filter → wait for the suggestion list → `click` the correct option.
- Never leave a combobox after typing without confirming a selection via `click`.
- If the field is required and no option matches → call `ask_human`.
- If a button or field is unclickable, use `send_keys` with "Tab Tab Enter" or "ArrowDown Enter" to navigate around it.

**9. When to call `ask_human` (hard blockers only)**
Call `ask_human` only when you are genuinely stuck:
- CAPTCHA or bot-check
- Unexpected login wall or MFA prompt
- Required field with no inferable answer (e.g. internal employee ID, referral code)
- Required dropdown whose options don't match the applicant at all

Describe exactly what you encountered and what the user must do to unblock.

{submission_step}

**10. Finish — call `done`**
Call the `done` action with a human-readable summary covering:
- Every field filled and the value used
- Any fields skipped and why
- Any blockers encountered
- Whether submission was confirmed/completed, declined, or skipped (dry run)
"""
