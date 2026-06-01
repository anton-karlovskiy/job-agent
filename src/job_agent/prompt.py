from __future__ import annotations

import yaml

from job_agent.profile import ApplicantData

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


def build_task_prompt(applicantData: ApplicantData, job_url: str, dry_run: bool) -> str:
    """Build the task prompt string sent to the browser-use Agent.

    Args:
        applicantData: Loaded applicant data containing profile yaml and resume text.
        job_url: URL of the job application form.
        dry_run: If True, instruct the agent not to click submit.

    Returns:
        A complete task prompt string.
    """
    profile_text = yaml.dump(applicantData.profile_yaml, default_flow_style=False, allow_unicode=True)

    preferences: dict[str, str] = applicantData.profile_yaml.get("preferences", {})
    cover_letter_tone: str = preferences.get("cover_letter_tone", "professional")
    writing_style: str = preferences.get("writing_style", "natural-human")

    style_rule = _NATURAL_HUMAN_STYLE if writing_style == "natural-human" else _FORMAL_STYLE

    dry_run_notice = (
        "\n\n> DRY RUN: Do NOT click submit. Stop just before the final submission step and report what you would have submitted."
        if dry_run
        else ""
    )

    return f"""You are a job application assistant. Fill out and submit the job application at: {job_url}{dry_run_notice}

---

## APPLICANT PROFILE
{profile_text}
## APPLICANT RESUME
{applicantData.resume_text}

---

## INSTRUCTIONS

**1. Navigate**
Go to the job application URL.

**2. Survey before filling**
Scroll the entire form first. Before touching any field, note:
- Which fields are required vs. optional
- Whether a cover letter / motivation textarea is present
- What file-upload inputs exist

**3. Required fields — fill without exception**
- If an answer isn't in the profile, infer the best one from the job description, company context on the page, and the applicant's background.
- Do NOT call `ask_human` for essay questions, motivation questions, or ambiguous options — make a confident, tailored choice.
- Writing style: {style_rule}

**4. Substantive optional fields — always fill**
These include: cover letters, personal statements, "Why this company?", motivation or essay questions.
- They directly affect the hiring decision; treat them as required.
- Generate a confident, tailored answer even when not explicitly covered by the profile.

**5. Low-signal optional fields — leave blank**
Skip: demographic questions, referral codes, internal platform usernames, promo codes, "How did you hear about us?" (when no clear answer is in the profile).
- Do not invent values for fields tracking a specific referral, internal ID, or optional demographic data.

**6. Cover letter fields**
Distinguish between two types:
- **Free-text textarea** — write a full prose cover letter (tone: {cover_letter_tone}). Use paragraphs, not bullets.
- **File upload input** — skip entirely; do NOT upload the resume as a substitute. Only upload a dedicated cover letter file if one is explicitly available in your file list (separate from the resume).
- If no cover letter field exists on the form, skip this step entirely.

**7. File upload fields (resume / CV)**
Use the built-in `upload_file` action. The resume path is already in your file list — pass its path and the DOM index of the file input.

**8. Dropdowns and autocomplete fields (`role=combobox`)**
- Click the field → type to filter → wait for the suggestion list → click the correct option.
- Never leave a combobox after typing without confirming a selection.
- If no option matches the profile AND the field is required → call `ask_human`.

**9. When to call `ask_human` (hard blockers only)**
Call `ask_human` only when you are genuinely stuck:
- CAPTCHA or bot-check
- Unexpected login wall or MFA prompt
- Required field with no inferable answer (e.g. internal employee ID, referral code)
- Required dropdown whose available options don't match the applicant's profile (e.g. US-state selector when applicant has no US address)

Describe exactly what you encountered and what the user must do to unblock.

**10. Finish**
Call the `done` action with a human-readable summary covering:
- Every field filled and the value used
- Any fields skipped and why
- Any blockers encountered
"""
