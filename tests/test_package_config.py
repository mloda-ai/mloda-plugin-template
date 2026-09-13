from __future__ import annotations

import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_package_discovery_excludes_all_test_packages() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools = config["tool"]["setuptools"]
    excluded = setuptools["packages"]["find"]["exclude"]

    assert setuptools["include-package-data"] is False
    assert excluded == ["*.tests", "*.tests.*"]
    for tests_dir in (REPO_ROOT / "placeholder").glob("*/my_plugin/tests"):
        package = ".".join(tests_dir.relative_to(REPO_ROOT).parts)
        assert package.endswith(".tests")
