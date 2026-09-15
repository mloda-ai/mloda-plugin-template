from __future__ import annotations

import sys
from fnmatch import fnmatchcase
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10 has no stdlib tomllib; pytest already pulls in its tomli backport.
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parent.parent


def _find_config() -> dict[str, list[str]]:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools = config["tool"]["setuptools"]
    assert setuptools["include-package-data"] is False
    find: dict[str, list[str]] = setuptools["packages"]["find"]
    return find


def test_package_discovery_excludes_all_test_packages() -> None:
    find = _find_config()

    # Derive the package root from `include` so this keeps working after customize.sh
    # renames placeholder/ to the real package name.
    package_root = REPO_ROOT / find["include"][0].rstrip("*")
    test_packages = [
        ".".join(d.relative_to(REPO_ROOT).parts)
        for d in package_root.glob("*/*/tests")
        if (d / "__init__.py").is_file()
    ]
    assert test_packages, f"no tests packages found under {package_root}; this test would pass vacuously"

    # setuptools filters discovered package names with fnmatchcase, where `*` spans dots too.
    for package in test_packages:
        assert any(fnmatchcase(package, pattern) for pattern in find["include"]), package
        assert any(fnmatchcase(package, pattern) for pattern in find["exclude"]), package
