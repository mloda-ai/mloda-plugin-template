"""End-to-end tests for the template customization script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUE_TEMPLATE = Path(".github/ISSUE_TEMPLATE/issue.yml")

# A minimal stand-in for .github/ISSUE_TEMPLATE/issue.yml, not a copy of the
# real file. The CI "scaffold" job runs bin/customize.sh for real against a
# full copy of this repo before running the test suite against the result,
# so by the time these tests run, REPO_ROOT's own issue template may already
# have had its 'placeholder/' paths rewritten. A fixture copied from
# REPO_ROOT at test time would silently stop exercising the rewrite in that
# case; a fixed fixture always contains 'placeholder/' to rewrite.
_ISSUE_TEMPLATE_FIXTURE = """\
name: Issue
body:
  - type: textarea
    id: pointers
    attributes:
      label: Code pointers (optional)
      placeholder: e.g. placeholder/feature_groups/my_plugin/my_feature_group.py:42
  - type: textarea
    id: dod
    attributes:
      label: Definition of done (optional)
      placeholder: Behavior, tests, docs.
  - type: input
    id: environment
    attributes:
      label: Environment (optional, bugs only)
      placeholder: Python 3.12, Linux, mloda 0.10.0
  - type: textarea
    id: summary
    attributes:
      label: Summary
      placeholder: One-sentence description.
  - type: textarea
    id: details
    attributes:
      label: Reproduction or motivation
      placeholder: Steps to reproduce.
"""


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
    (root / ISSUE_TEMPLATE).write_text(_ISSUE_TEMPLATE_FIXTURE, encoding="utf-8")
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


def _read_template() -> str:
    """The fixture issue form content installed by ``_make_scaffold``."""
    return _ISSUE_TEMPLATE_FIXTURE


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


def _assert_rejected(result: subprocess.CompletedProcess[str], root: Path, fragment: str) -> None:
    """A rejected run exits 2, explains itself, and leaves the tree untouched."""
    assert result.returncode == 2, result.stdout + result.stderr
    assert fragment in result.stdout + result.stderr
    assert (root / "placeholder").is_dir(), "a rejected run must not half-rename the scaffold"


def test_no_arguments_prints_usage(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root)

    _assert_rejected(result, root, "Usage: bin/customize.sh <package-name>")


def test_help_exits_zero_without_touching_the_tree(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: bin/customize.sh <package-name>" in result.stdout
    assert (root / "placeholder").is_dir()


def test_missing_package_name_is_rejected(tmp_path: Path) -> None:
    """Options without a positional package name do not reach the rename."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "--author", "Your Name")

    _assert_rejected(result, root, "<package-name> is required")


def test_placeholder_as_package_name_is_rejected(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "placeholder")

    _assert_rejected(result, root, "package name cannot be 'placeholder'")


@pytest.mark.parametrize("reserved", ["mloda", "mloda_plugins"])
def test_reserved_namespace_names_are_rejected(tmp_path: Path, reserved: str) -> None:
    """The safety-critical guard: shipping mloda/__init__.py breaks the namespace.

    See tests/test_reserved_namespace.py for why these two names matter.
    """
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, reserved)

    _assert_rejected(result, root, f"package name '{reserved}' is reserved by the mloda namespace")


@pytest.mark.parametrize(
    "name",
    ["9acme", "Acme", "my-plugin", "_acme", "acme.plugin", "acme plugin"],
    ids=["leading-digit", "uppercase", "hyphen", "leading-underscore", "dot", "space"],
)
def test_malformed_package_names_are_rejected(tmp_path: Path, name: str) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, name)

    _assert_rejected(result, root, "lowercase letters/digits/underscores")


def test_unknown_option_is_rejected(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--nope")

    _assert_rejected(result, root, "unknown option: --nope")


def test_second_positional_argument_is_rejected(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "extra")

    _assert_rejected(result, root, "unexpected positional argument: extra")


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
