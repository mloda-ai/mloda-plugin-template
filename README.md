[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/mloda-ai/mloda-plugin-template/blob/main/LICENSE)
[![mloda](https://img.shields.io/badge/built%20with-mloda-blue.svg)](https://github.com/mloda-ai/mloda)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/mloda-ai/mloda-plugin-template/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/mloda-ai/mloda-plugin-template/actions/workflows/test.yml?query=branch%3Amain)

# mloda-plugin-template

> **A GitHub template for creating standalone mloda plugins.** Part of the [mloda](https://github.com/mloda-ai/mloda) ecosystem for open data access. Visit [mloda.ai](https://mloda.ai) for an overview and business context, the [GitHub repository](https://github.com/mloda-ai/mloda) for technical context, or the [documentation](https://mloda-ai.github.io/mloda/) for detailed guides.

Create your own FeatureGroups, ComputeFrameworks, and Extenders as standalone packages. This repository serves two audiences:

- **Plugin authors**: click *Use this template* on GitHub to scaffold a new plugin repository, then follow the [Use this template](#use-this-template) section below.
- **Template contributors**: improving the scaffold itself? See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Contribute to this template](#contribute-to-this-template) section.

## Related Repositories

- **[mloda](https://github.com/mloda-ai/mloda)**: The core library for open data access. Declaratively define what data you need, not how to get it. mloda handles feature resolution, dependency management, and compute framework abstraction automatically.

- **[mloda-registry](https://github.com/mloda-ai/mloda-registry)**: The central hub for discovering and sharing mloda plugins. Browse community-contributed FeatureGroups, find integration guides, and publish your own plugins for others to use.

## Use this template

Click *Use this template* on GitHub to scaffold a new plugin repository. See [docs/getting-started.md](docs/getting-started.md) for the GitHub template-creation walkthrough; once your repository is in place, follow the steps below to customize the scaffold for your organization.

### Structure

```
placeholder/
├── feature_groups/
│   ├── manifest.py               # Entry-point manifest: FEATURE_GROUPS list
│   └── my_plugin/
│       ├── __init__.py           # Package exports
│       ├── my_feature_group.py   # Example FeatureGroup implementation
│       └── tests/
│           └── test_my_feature_group.py
├── compute_frameworks/
│   ├── manifest.py               # Entry-point manifest: COMPUTE_FRAMEWORKS list
│   └── my_plugin/
│       ├── __init__.py
│       ├── my_compute_framework.py
│       └── tests/
│           └── test_my_compute_framework.py
└── extenders/
    ├── manifest.py               # Entry-point manifest: EXTENDERS list
    └── my_plugin/
        ├── __init__.py
        ├── my_extender.py
        └── tests/
            └── test_my_extender.py
```

Each plugin kind ships an example test next to its implementation, put yours in the same
place.

### Plugin discovery

mloda auto-discovers installed plugins via `PluginLoader.all()`, no manual import needed. Each
`manifest.py` lists its concrete classes (`FEATURE_GROUPS`, `COMPUTE_FRAMEWORKS`, `EXTENDERS`) and
`pyproject.toml` wires them up under `[project.entry-points."mloda.*"]`. Add a plugin by appending
it to the relevant list.

If a manifest imports an optional backend (pandas, pyarrow, ...), guard the import: an uncaught
`ModuleNotFoundError` either silently drops the whole entry point or aborts discovery. Import
resiliently and append only the classes whose backend is present.

### Key files

- `placeholder/` - Root namespace (rename to your organization's name)
- `pyproject.toml` - Package config (edit directly, not auto-generated)
- `.github/workflows/test.yml` - CI workflow running pytest

### Setup Your Plugin

#### 1. Run the customization script

```bash
./bin/customize.sh <your-package-name> \
  --author "Your Name" \
  --email you@example.com \
  --description "Your plugin description" \
  --repository-url https://github.com/<your-org>/<your-repo>
```

This renames `placeholder/` to `<your-package-name>/`, updates `pyproject.toml` (`name`, `authors`, `description`, `packages.find.include`, `pytest.testpaths`), updates `.releaserc.yaml` (`message`, `repositoryUrl`), rewrites the `[project.entry-points."mloda.*"]` manifest paths, and rewrites `from placeholder.` imports across the package.

The package name must be a valid Python identifier (lowercase letters, digits, underscores; must start with a letter). The names `mloda` and `mloda_plugins` are reserved: the core `mloda` package is a shared PEP 420 namespace, so a plugin that shipped `mloda/__init__.py` would make mloda unimportable for everyone who installs it. Both `bin/customize.sh` and a `tox`/CI check reject these names. All option flags are optional; if you omit them you can edit the corresponding fields by hand later.

#### 2. Verify setup

```bash
uv venv && source .venv/bin/activate && uv sync --all-extras && tox
```

After `tox` passes, confirm `pyproject.toml` no longer contains the template's placeholder strings:

```bash
tox -e placeholders
```

This is also enforced in CI: the `test.yml` workflow fails on scaffolded plugins until the template's placeholder strings are removed from `pyproject.toml`. The check covers every field listed in step 1 above: `name`, `authors` (name and email), `description`, `tool.setuptools.packages.find.include`, and `tool.pytest.ini_options.testpaths`. It is skipped on the `mloda-ai/mloda-plugin-template` repository itself, where the placeholders are intentional.

#### 3. Remove template-only files

After `tox` passes, remove the files that only exist to support the template itself:

```bash
rm CONTRIBUTING.md bin/customize.sh tests/test_customize_script.py
```

`CONTRIBUTING.md` describes how to contribute to the template repo; `bin/customize.sh` is a one-shot scaffold script that has nothing left to do. `tests/test_customize_script.py` tests that script and copies it into a scratch scaffold, so it must go with it — leaving it behind fails `tox` with a `FileNotFoundError` on every subsequent run. The other test files (`test_entry_points.py`, `test_mloda_imports.py`, `test_reserved_namespace.py`) are rename-safe and should stay.

Also delete the `## First-time setup` section from `CLAUDE.md` and `AGENTS.md`. Those instructions only apply to fresh-template repos.

The remaining baseline files apply to your plugin out of the box and can be edited to match your conventions:

- `AGENTS.md` and `CLAUDE.md`: toolchain and project practices for the same `tox`/ruff/mypy/bandit pipeline you inherit. Tune the bullets if you change the toolchain.
- `CODE_OF_CONDUCT.md`: short, plain-English baseline. Update the contact (`conduct@mloda.ai` → your address) if you want enforcement to come to you.
- `.github/ISSUE_TEMPLATE/issue.yml`: unified issue form. `bin/customize.sh` already repoints its example file paths at your renamed package; edit the field wording if you want examples drawn from your own plugin.

You may also want to replace this `README.md` with one that describes your plugin.

### Where to next

- **[mloda-registry/docs/guides/](https://github.com/mloda-ai/mloda-registry/tree/main/docs/guides/)**: full plugin development walkthrough (FeatureGroups, ComputeFrameworks, Extenders, packaging, publishing).
- **[mloda](https://github.com/mloda-ai/mloda)**: core framework reference.
- **[Claude Code skills](https://github.com/mloda-ai/mloda-registry/tree/main/.claude/skills/)**: pattern guidance and best practices for AI-assisted plugin development.
- **[docs/github-workflows.md](docs/github-workflows.md)**: CI/CD setup and required secrets for the included workflows.
- **[docs/github-repository-settings.md](docs/github-repository-settings.md)**: repository-side settings (secrets, branch protection, required checks, dependabot reviewer) you should configure after scaffolding.

## Contribute to this template

This section is for people improving the scaffold itself (CI workflows, dev tooling, docs, examples). See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide. Quick pointers:

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [AGENTS.md](AGENTS.md): agent guidance, project practices, issue creation
- [Issue template](.github/ISSUE_TEMPLATE/issue.yml)
