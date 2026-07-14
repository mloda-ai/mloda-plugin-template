"""End-to-end tests for the template customization script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


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


def test_unexpected_entry_point_placeholder_still_fails(tmp_path: Path) -> None:
    """The stale-reference check still rejects a missed entry-point rename."""
    root = _make_scaffold(
        tmp_path,
        '\n[project.entry-points."mloda.feature_groups.extra"]\nleftover = "placeholder.unrelated:FEATURE_GROUPS"\n',
    )

    result = _run_customize(root, "acme")

    assert result.returncode == 1
    assert "stale 'placeholder' references" in result.stderr
