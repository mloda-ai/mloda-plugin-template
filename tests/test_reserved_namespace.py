"""Guard: a plugin built from this template must never occupy the reserved mloda namespace.

The core ``mloda`` package is a PEP 420 namespace package shared across distributions
(mloda core plus the mloda-registry packages under ``mloda.community`` /
``mloda.enterprise``). Namespace merging only works while no participating distribution
ships an ``mloda/__init__.py``. A template user who renames the ``placeholder/`` package
root to ``mloda`` (or ``mloda_plugins``) would ship exactly that file and shadow
``mloda.*`` for everyone who installs the plugin, making the core framework unimportable.

See https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
"""

import os
from pathlib import Path

# Directory names a plugin must not use for a package root. ``mloda`` is the shared
# namespace root; ``mloda_plugins`` is reserved by the ecosystem to avoid collisions.
RESERVED_NAMESPACE_ROOTS = ("mloda", "mloda_plugins")

# Directories that never ship in the distribution: VCS, virtualenvs, caches, build
# outputs. Pruned from the recursive scan so an installed dependency (e.g. mloda under
# .venv) never trips the guard.
EXCLUDED_DIRS = frozenset(
    {".git", ".venv", "venv", ".tox", ".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__", "build", "dist"}
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_reserved_namespace_violations(root: Path) -> list[str]:
    """Return human-readable violations for reserved namespace usage under ``root``.

    Two checks:

    * a top-level directory named ``mloda`` / ``mloda_plugins`` (the package root a
      template user would create by renaming ``placeholder/`` to a reserved name); and
    * any ``mloda/__init__.py`` / ``mloda_plugins/__init__.py`` anywhere in the source
      tree (covers ``src/``-style layouts, not just the default ``where = ["."]``),
      which is the file that would ship and collapse the shared namespace.
    """
    violations: list[str] = []

    for name in RESERVED_NAMESPACE_ROOTS:
        if (root / name).is_dir():
            violations.append(
                f"package root directory '{name}/' uses the reserved mloda namespace; "
                "rename it (see README 'Setup Your Plugin')"
            )

    for dirpath, dirnames, _ in os.walk(root):
        # Prune excluded and egg-info directories in place so os.walk does not descend.
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
    """The live guard: fail if this repo would ship a package into the mloda namespace."""
    violations = find_reserved_namespace_violations(REPO_ROOT)
    assert not violations, "Reserved namespace violation(s):\n" + "\n".join(violations)


def test_detects_reserved_root_with_init(tmp_path: Path) -> None:
    pkg = tmp_path / "mloda"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    violations = find_reserved_namespace_violations(tmp_path)

    # Both the root-name check and the shipped-__init__.py check fire.
    assert len(violations) == 2
    assert any("__init__.py" in v for v in violations)


def test_detects_reserved_root_without_init(tmp_path: Path) -> None:
    # A reserved name is rejected even as a PEP 420 namespace dir (no __init__.py).
    (tmp_path / "mloda_plugins").mkdir()

    violations = find_reserved_namespace_violations(tmp_path)

    assert len(violations) == 1
    assert "mloda_plugins/" in violations[0]


def test_detects_reserved_namespace_in_src_layout(tmp_path: Path) -> None:
    # A non-default layout (src/) that ships mloda/__init__.py is still caught.
    pkg = tmp_path / "src" / "mloda"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")

    violations = find_reserved_namespace_violations(tmp_path)

    assert len(violations) == 1
    assert "src/mloda/__init__.py" in violations[0]


def test_ignores_excluded_dirs(tmp_path: Path) -> None:
    # An installed dependency inside a virtualenv must not trip the guard.
    pkg = tmp_path / ".venv" / "lib" / "mloda"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")

    assert find_reserved_namespace_violations(tmp_path) == []


def test_clean_tree_has_no_violations(tmp_path: Path) -> None:
    pkg = tmp_path / "acme"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    assert find_reserved_namespace_violations(tmp_path) == []
