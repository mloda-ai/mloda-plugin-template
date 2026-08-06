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


def test_description_with_a_pipe_is_rejected(tmp_path: Path) -> None:
    """'|' is the delimiter the description substitution uses."""
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--description", "a|b")

    _assert_rejected(result, root, "--description must not contain the '|' character")


def test_unknown_option_is_rejected(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "--nope")

    _assert_rejected(result, root, "unknown option: --nope")


def test_second_positional_argument_is_rejected(tmp_path: Path) -> None:
    root = _make_scaffold(tmp_path)

    result = _run_customize(root, "acme", "extra")

    _assert_rejected(result, root, "unexpected positional argument: extra")


def test_unexpected_entry_point_placeholder_still_fails(tmp_path: Path) -> None:
    """The stale-reference check still rejects a missed entry-point rename."""
    root = _make_scaffold(
        tmp_path,
        '\n[project.entry-points."mloda.feature_groups.extra"]\nleftover = "placeholder.unrelated:FEATURE_GROUPS"\n',
    )

    result = _run_customize(root, "acme")

    assert result.returncode == 1
    assert "stale 'placeholder' references" in result.stderr
