from __future__ import annotations

import re
import tomllib
from fnmatch import fnmatchcase
from importlib.metadata import metadata
from pathlib import Path
from typing import Any

from packaging.specifiers import SpecifierSet  # pytest already depends on packaging.

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_pyproject() -> dict[str, Any]:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _find_config() -> dict[str, list[str]]:
    setuptools = _load_pyproject()["tool"]["setuptools"]
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


def test_supported_pythons_match_ci_and_mloda() -> None:
    # A Python we allow but mloda rejects fails the install with an error that blames mloda; test.yml covers our range.
    supported = SpecifierSet(_load_pyproject()["project"]["requires-python"])
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    matrix = re.search(r"python-version: \[([^\]]+)\]", workflow)
    minors = sorted(int(minor) for minor in re.findall(r"\b3\.(\d+)\b", matrix.group(1))) if matrix else []
    assert minors, "no python-version matrix found in test.yml"
    assert minors == list(range(minors[0], minors[-1] + 1)), minors
    # No Requires-Python means any Python.
    runtime = {
        pkg: SpecifierSet(",".join(metadata(pkg).get_all("Requires-Python") or []))
        for pkg in ("mloda", "mloda-testing")
    }
    for minor in range(minors[0] - 1, minors[-1] + 2):
        version = f"3.{minor}"
        assert (version in supported) == (minors[0] <= minor <= minors[-1]), version
        for package, package_range in runtime.items():
            assert version not in supported or version in package_range, (package, version)
