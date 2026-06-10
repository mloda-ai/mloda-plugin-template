"""Guard: a template-born plugin must never ship ``mloda/__init__.py``.

``mloda`` is a shared PEP 420 namespace package; a distribution that ships
``mloda/__init__.py`` collapses it and makes mloda unimportable. See
https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
"""

import os
from pathlib import Path

# Names a plugin must not use for a package root (``mloda_plugins`` is reserved too).
RESERVED_NAMESPACE_ROOTS = ("mloda", "mloda_plugins")

# Dirs that never ship; pruned so an installed dep (e.g. mloda under .venv) is ignored.
EXCLUDED_DIRS = frozenset(
    {".git", ".venv", "venv", ".tox", ".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__", "build", "dist"}
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_reserved_namespace_violations(root: Path) -> list[str]:
    """Flag a reserved top-level package root, or a reserved ``<name>/__init__.py``
    anywhere in the tree (so ``src/``-style layouts are covered too)."""
    violations: list[str] = []

    for name in RESERVED_NAMESPACE_ROOTS:
        if (root / name).is_dir():
            violations.append(
                f"package root directory '{name}/' uses the reserved mloda namespace; "
                "rename it (see README 'Setup Your Plugin')"
            )

    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")]
        for name in RESERVED_NAMESPACE_ROOTS:
            init_file = Path(dirpath) / name / "__init__.py"
            if init_file.is_file():
                rel = init_file.relative_to(root).as_posix()
                violations.append(
                    f"'{rel}' would ship in the built distribution and collapse the PEP 420 "
                    "'mloda' namespace package, making mloda unimportable for anyone who "
                    "installs this plugin"
                )

    return violations


def test_repo_has_no_reserved_namespace_root() -> None:
    """Live guard: this repo must not ship into the mloda namespace."""
    violations = find_reserved_namespace_violations(REPO_ROOT)
    assert not violations, "Reserved namespace violation(s):\n" + "\n".join(violations)


def test_detects_reserved_root_with_init(tmp_path: Path) -> None:
    pkg = tmp_path / "mloda"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    violations = find_reserved_namespace_violations(tmp_path)

    # Root-name check and shipped-__init__.py check both fire.
    assert len(violations) == 2
    assert any("__init__.py" in v for v in violations)


def test_detects_reserved_root_without_init(tmp_path: Path) -> None:
    # Rejected even as a bare namespace dir (no __init__.py).
    (tmp_path / "mloda_plugins").mkdir()

    violations = find_reserved_namespace_violations(tmp_path)

    assert len(violations) == 1
    assert "mloda_plugins/" in violations[0]


def test_detects_reserved_namespace_in_src_layout(tmp_path: Path) -> None:
    # src/ layout shipping mloda/__init__.py is still caught.
    pkg = tmp_path / "src" / "mloda"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")

    violations = find_reserved_namespace_violations(tmp_path)

    assert len(violations) == 1
    assert "src/mloda/__init__.py" in violations[0]


def test_ignores_excluded_dirs(tmp_path: Path) -> None:
    # A dep installed under .venv must not trip the guard.
    pkg = tmp_path / ".venv" / "lib" / "mloda"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")

    assert find_reserved_namespace_violations(tmp_path) == []


def test_clean_tree_has_no_violations(tmp_path: Path) -> None:
    pkg = tmp_path / "acme"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    assert find_reserved_namespace_violations(tmp_path) == []
