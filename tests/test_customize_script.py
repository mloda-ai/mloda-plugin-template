"""End-to-end tests for the template customization script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


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
    if extra_pyproject:
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + extra_pyproject,
            encoding="utf-8",
        )
    return root


def _line_starting_with(path: Path, prefix: str) -> str:
    """The single line of ``path`` starting with ``prefix``, stripped."""
    matches = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"expected exactly one {prefix!r} line in {path.name}, got {matches}"
    return matches[0]


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


@pytest.mark.parametrize(
    "author",
    ["Ben & Jerry", "A|B", r"Back\slash", "Ampersand & pipe | together"],
    ids=["ampersand", "pipe", "backslash", "both"],
)
def test_author_survives_sed_metacharacters(tmp_path: Path, author: str) -> None:
    """A value containing sed replacement metacharacters lands literally."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--author", author, "--email", "you@example.com")

    assert result.returncode == 0, result.stdout + result.stderr
    authors = _line_starting_with(root / "pyproject.toml", "authors = ")
    assert authors == f'authors = [{{ name = "{author}", email = "you@example.com" }}]'


def test_email_survives_sed_metacharacters(tmp_path: Path) -> None:
    """--email goes through the same replacement and needs the same escaping."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--email", "a&b|c@example.com")

    assert result.returncode == 0, result.stdout + result.stderr
    authors = _line_starting_with(root / "pyproject.toml", "authors = ")
    assert 'email = "a&b|c@example.com"' in authors


@pytest.mark.parametrize(
    "description",
    ["Reads A & B", "Reads A|B", r"Escapes \n literally"],
    ids=["ampersand", "pipe", "backslash"],
)
def test_description_survives_sed_metacharacters(tmp_path: Path, description: str) -> None:
    """--description no longer rejects '|', and neither character is expanded."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--description", description)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _line_starting_with(root / "pyproject.toml", "description = ") == f'description = "{description}"'


@pytest.mark.parametrize(
    "url",
    ["https://example.com/repo?a=1&b=2", "https://example.com/a|b"],
    ids=["ampersand", "pipe"],
)
def test_repository_url_survives_sed_metacharacters(tmp_path: Path, url: str) -> None:
    """--repository-url lands literally in .releaserc.yaml."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--repository-url", url)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _line_starting_with(root / ".releaserc.yaml", "repositoryUrl: ") == f'repositoryUrl: "{url}"'


def test_sed_metacharacters_do_not_abort_after_the_rename(tmp_path: Path) -> None:
    """A '|' used to break the sed expression itself, after placeholder/ was gone."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--author", "A|B", "--description", "X|Y")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "acme").is_dir()
    assert not (root / "placeholder").exists()


def test_unexpected_entry_point_placeholder_still_fails(tmp_path: Path) -> None:
    """The stale-reference check still rejects a missed entry-point rename."""
    root = _make_scaffold(
        tmp_path,
        '\n[project.entry-points."mloda.feature_groups.extra"]\nleftover = "placeholder.unrelated:FEATURE_GROUPS"\n',
    )

    result = _run_customize(root, "acme")

    assert result.returncode == 1
    assert "stale 'placeholder' references" in result.stderr
