from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from job_agent.profile import ProfileContext, load_profile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadProfileYaml:
    def test_basic_yaml_loaded(self, tmp_path: Path) -> None:
        profile_file = _write(
            tmp_path,
            "profile.yaml",
            """\
            personal:
              first_name: Jane
              last_name: Doe
              email: jane@example.com
        """,
        )
        resume_file = _write(tmp_path, "resume.md", "# Jane Doe\n\nSenior Dev.")

        ctx = load_profile(str(profile_file), str(resume_file))

        assert isinstance(ctx, ProfileContext)
        assert ctx.yaml_data["personal"]["first_name"] == "Jane"
        assert ctx.yaml_data["personal"]["email"] == "jane@example.com"

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path) -> None:
        profile_file = _write(tmp_path, "profile.yaml", "")
        resume_file = _write(tmp_path, "resume.md", "resume content")

        ctx = load_profile(str(profile_file), str(resume_file))
        assert ctx.yaml_data == {}


class TestLoadProfileMarkdownResume:
    def test_md_resume_read_as_text(self, tmp_path: Path) -> None:
        profile_file = _write(tmp_path, "profile.yaml", "personal:\n  name: Jane")
        resume_file = _write(tmp_path, "resume.md", "# Jane\n\nPython developer.")

        ctx = load_profile(str(profile_file), str(resume_file))
        assert "Python developer" in ctx.resume_text

    def test_txt_resume_also_accepted(self, tmp_path: Path) -> None:
        profile_file = _write(tmp_path, "profile.yaml", "personal:\n  name: Jane")
        resume_file = _write(tmp_path, "resume.txt", "Plain text resume.")

        ctx = load_profile(str(profile_file), str(resume_file))
        assert "Plain text resume" in ctx.resume_text


class TestLoadProfileMissingFiles:
    def test_missing_profile_raises(self, tmp_path: Path) -> None:
        resume_file = _write(tmp_path, "resume.md", "resume")
        with pytest.raises(FileNotFoundError, match="Profile not found"):
            load_profile(str(tmp_path / "nonexistent.yaml"), str(resume_file))

    def test_missing_resume_raises(self, tmp_path: Path) -> None:
        profile_file = _write(tmp_path, "profile.yaml", "personal:\n  name: Jane")
        with pytest.raises(FileNotFoundError, match="Resume not found"):
            load_profile(str(profile_file), str(tmp_path / "nonexistent.md"))
