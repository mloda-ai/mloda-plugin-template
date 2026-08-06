"""End-to-end tests for the template customization script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUE_TEMPLATE = Path(".github/ISSUE_TEMPLATE/issue.yml")


def _make_scaffold(tmp_path: Path, extra_pyproject: str = "") -> Path:
    root = tmp_path / "scaffold"
    (root / "bin").mkdir(parents=True)
    (root / "placeholder").mkdir()
    (root / "placeholder" / "module.py").write_text(
        "from placeholder.feature_groups import manifest\n", encoding="utf-8"
    )
    shutil.copy2(REPO_ROOT / "bin" / "customize.sh", root / "bin" / "customize.sh")
    shutil.copy2(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")
    shutil.copy2(REPO_ROOT / ".releaserc.yaml", root / ".releaserc.yaml")
    (root / ISSUE_TEMPLATE).parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / ISSUE_TEMPLATE, root / ISSUE_TEMPLATE)
    if extra_pyproject:
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + extra_pyproject,
            encoding="utf-8",
        )
    return root


def _read_template() -> str:
    """The template repository's own copy of the issue form."""
    return (REPO_ROOT / ISSUE_TEMPLATE).read_text(encoding="utf-8")


def _run_customize(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "bin/customize.sh", *args],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )


def test_optional_fields_can_be_left_for_manual_editing(tmp_path: Path) -> None:
    """Omitting optional flags does not make the scaffold command fail."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "acme").is_dir()


def test_issue_template_paths_are_repointed(tmp_path: Path) -> None:
    """The scaffolded issue form must not keep pointing at placeholder/."""
    root = _make_scaffold(tmp_path)
    before = (root / ISSUE_TEMPLATE).read_text(encoding="utf-8")
    assert "placeholder/" in before, "fixture no longer exercises the rewrite"

    result = _run_customize(root, "acme")

    assert result.returncode == 0, result.stdout + result.stderr
    after = (root / ISSUE_TEMPLATE).read_text(encoding="utf-8")
    assert "placeholder/" not in after
    assert "acme/feature_groups/my_plugin/my_feature_group.py:42" in after


def test_issue_template_field_keys_survive_the_rewrite(tmp_path: Path) -> None:
    """'placeholder:' is one of the form's own field keys and must be left alone.

    Both the rewrite and the stale-reference check are scoped to 'placeholder/'
    for this reason: a bare-word rewrite would rename every key and break the
    form, and a bare-word check would abort every single run.
    """
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme")

    assert result.returncode == 0, result.stdout + result.stderr
    after = (root / ISSUE_TEMPLATE).read_text(encoding="utf-8")
    assert after.count("placeholder:") == _read_template().count("placeholder:")
    for field_id in ("summary", "details", "pointers", "dod", "environment"):
        assert f"id: {field_id}" in after


def test_customize_runs_without_an_issue_template(tmp_path: Path) -> None:
    """A scaffold that has already dropped the form still customizes cleanly."""
    root = _make_scaffold(tmp_path)
    (root / ISSUE_TEMPLATE).unlink()

    result = _run_customize(root, "acme")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "acme").is_dir()


def test_unexpected_entry_point_placeholder_still_fails(tmp_path: Path) -> None:
    """The stale-reference check still rejects a missed entry-point rename."""
    root = _make_scaffold(
        tmp_path,
        '\n[project.entry-points."mloda.feature_groups.extra"]\nleftover = "placeholder.unrelated:FEATURE_GROUPS"\n',
    )

    result = _run_customize(root, "acme")

    assert result.returncode == 1
    assert "stale 'placeholder' references" in result.stderr
