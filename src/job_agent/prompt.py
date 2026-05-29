from __future__ import annotations

import yaml

from job_agent.profile import ProfileContext

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


def build_task_prompt(profile: ProfileContext, job_url: str, dry_run: bool) -> str:
    """Build the task prompt string sent to the browser-use Agent.

    Args:
        profile: Loaded profile context containing YAML data and resume text.
        job_url: URL of the job application form.
        dry_run: If True, instruct the agent not to click submit.

    Returns:
        A complete task prompt string.
    """
    yaml_text = yaml.dump(profile.yaml_data, default_flow_style=False, allow_unicode=True)

    preferences: dict[str, str] = profile.yaml_data.get("preferences", {})
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
{yaml_text}
RESUME TEXT:
{profile.resume_text}

INSTRUCTIONS:
1. Navigate to the job application URL.
2. Scroll through the entire form first to understand its structure before filling anything.
3. Fill out every field — do not skip optional fields.
4. If a field is not explicitly covered by the profile, generate the best possible answer \
using the job description, company context visible on the page, and the applicant's background. \
Do NOT call `ask_human` for open-ended essay questions, motivation questions, or ambiguous options — \
make a confident, tailored choice. {style_rule}
5. For cover letter fields: write a tailored cover letter using the profile and any job description \
text visible on the page. Tone: {cover_letter_tone}. Use prose paragraphs, not bullets.
6. For file upload fields (resume/CV): use the built-in `upload_file` action. \
The resume path is already available in your file list — pass its path and the DOM index of the file input.
7. Call `ask_human` ONLY for hard blockers you cannot bypass: a CAPTCHA, an unexpected login wall, \
an MFA prompt, or a required field with absolutely no inferable answer (e.g. an internal employee ID \
or a referral code). Describe exactly what you encountered and what the user needs to do.
8. After completing the form (or reaching the dry-run stopping point), use the `done` action with \
a human-readable summary of every field filled and any blockers encountered.{dry_run_line}"""
