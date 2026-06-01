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

    dry_run_line = (
        "\n\nDO NOT click the submit button — this is a dry run. "
        "Stop just before the final submission step and report what you would have submitted."
        if dry_run
        else ""
    )

    url_line = (
        f"You are a job application assistant. Your goal is to fill out and submit the job application at: {job_url}"
    )
    return f"""{url_line}

APPLICANT PROFILE:
{profile_text}
APPLICANT RESUME:
{applicantData.resume_text}

INSTRUCTIONS:
1. Navigate to the job application URL.
2. Scroll through the entire form first to understand its structure before filling anything. Note which field types are present, in particular whether a cover letter or free-text motivation textarea exists.
3. Required fields: fill every required field without exception. If the answer is not in the profile, generate the best possible answer from the job description, company context visible on the page, and the applicant's background. Do NOT call `ask_human` for essay questions, motivation questions, or ambiguous options — make a confident, tailored choice. {style_rule}
4. Substantive optional fields — cover letters, personal statements, "Why this company?", motivation or essay questions: always fill these. They directly affect the hiring decision. Generate a confident, tailored answer even when not explicitly covered by the profile.
5. Low-signal optional fields — demographic questions, referral codes, internal platform usernames, promo codes, "How'd you hear about us?" when no clear answer exists in the profile: leave blank. Do not invent values for fields that track a specific referral, internal ID, or collect optional demographic data.
6. Cover letter fields: distinguish between two types: (a) Free-text textarea — write a full prose cover letter using the profile and any job description text visible on the page. Tone: {cover_letter_tone}. Prose paragraphs, not bullets. (b) File upload input — skip it entirely; do NOT upload the resume or any other file as a cover letter substitute. Only upload a cover letter if a dedicated cover letter file is explicitly available in your file list (separate from the resume). If no cover letter field of either type exists on the form, skip this step entirely.
7. For file upload fields (resume/CV): use the built-in `upload_file` action. The resume path is already available in your file list — pass its path and the DOM index of the file input.
8. For dropdown / autocomplete fields (role=combobox): click the field, type to filter, wait for the suggestion list to appear, then click the correct option from the list. Never leave a combobox after typing without confirming a selection from the dropdown. If the suggestion list appears but contains no option that matches the profile data AND the field is required, call `ask_human` to surface it.
9. Call `ask_human` ONLY for hard blockers you cannot bypass: a CAPTCHA, an unexpected login wall, an MFA prompt, a required field with absolutely no inferable answer (e.g. an internal employee ID or a referral code), or a required dropdown whose available options don't match the applicant's profile (e.g. a US-state selector when the applicant has no US address). Describe exactly what you encountered and what the user needs to do.
10. After completing the form (or reaching the dry-run stopping point), use the `done` action with a human-readable summary of every field filled and any blockers encountered.{dry_run_line}
"""
