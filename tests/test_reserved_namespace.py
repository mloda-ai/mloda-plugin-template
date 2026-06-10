"""Guard: a plugin built from this template must never occupy the reserved mloda namespace.

The core ``mloda`` package is a PEP 420 namespace package shared across distributions
(mloda core plus the mloda-registry packages under ``mloda.community`` /
``mloda.enterprise``). Namespace merging only works while no participating distribution
ships an ``mloda/__init__.py``. A template user who renames the ``placeholder/`` package
root to ``mloda`` (or ``mloda_plugins``) would ship exactly that file and shadow
``mloda.*`` for everyone who installs the plugin, making the core framework unimportable.

See https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
"""

from pathlib import Path

# Directory names a plugin must not use for its package root. ``mloda`` is the shared
# namespace root; ``mloda_plugins`` is reserved by the ecosystem to avoid collisions.
RESERVED_NAMESPACE_ROOTS = ("mloda", "mloda_plugins")

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_reserved_namespace_violations(root: Path) -> list[str]:
    """Return human-readable violations for reserved namespace roots under ``root``.

    setuptools discovers top-level packages directly under the project root
    (``tool.setuptools.packages.find.where = ["."]``), so a shipped ``mloda`` package can
    only come from a top-level ``mloda/`` directory here.
    """
    violations: list[str] = []
    for name in RESERVED_NAMESPACE_ROOTS:
        candidate = root / name
        if not candidate.is_dir():
            continue
        violations.append(
            f"package root directory '{name}/' uses the reserved mloda namespace; "
            "rename it (see README 'Setup Your Plugin')"
        )
        if (candidate / "__init__.py").is_file():
            violations.append(
                f"'{name}/__init__.py' would ship in the built distribution and collapse "
                "the PEP 420 'mloda' namespace package, making mloda unimportable for "
                "anyone who installs this plugin"
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

    assert len(violations) == 2
    assert any("__init__.py" in v for v in violations)


def test_detects_reserved_root_without_init(tmp_path: Path) -> None:
    # A reserved name is rejected even as a PEP 420 namespace dir (no __init__.py).
    (tmp_path / "mloda_plugins").mkdir()

    violations = find_reserved_namespace_violations(tmp_path)

    assert len(violations) == 1
    assert "mloda_plugins/" in violations[0]


def test_clean_tree_has_no_violations(tmp_path: Path) -> None:
    pkg = tmp_path / "acme"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    assert find_reserved_namespace_violations(tmp_path) == []
