[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/mloda-ai/mloda-plugin-template/blob/main/LICENSE)
[![mloda](https://img.shields.io/badge/built%20with-mloda-blue.svg)](https://github.com/mloda-ai/mloda)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

# mloda-plugin-template

> **A GitHub template for creating standalone mloda plugins.** Part of the [mloda](https://github.com/mloda-ai/mloda) ecosystem for open data access. Visit [mloda.ai](https://mloda.ai) for an overview and business context, the [GitHub repository](https://github.com/mloda-ai/mloda) for technical context, or the [documentation](https://mloda-ai.github.io/mloda/) for detailed guides.

Create your own FeatureGroups, ComputeFrameworks, and Extenders as standalone packages.

## Related Repositories

- **[mloda](https://github.com/mloda-ai/mloda)**: The core library for open data access. Declaratively define what data you need, not how to get it. mloda handles feature resolution, dependency management, and compute framework abstraction automatically.

- **[mloda-registry](https://github.com/mloda-ai/mloda-registry)**: The central hub for discovering and sharing mloda plugins. Browse community-contributed FeatureGroups, find integration guides, and publish your own plugins for others to use.

## Use this template

Click *Use this template* on GitHub to scaffold a new plugin repository. See [docs/getting-started.md](docs/getting-started.md) for the GitHub template-creation walkthrough; once your repository is in place, follow the steps below to customize the scaffold for your organization.

### Structure

```
placeholder/
├── feature_groups/
│   └── my_plugin/
│       ├── __init__.py           # Package exports
│       ├── my_feature_group.py   # Example FeatureGroup implementation
│       └── tests/
│           └── test_my_feature_group.py
├── compute_frameworks/
│   └── my_framework/
│       ├── __init__.py
│       └── my_compute_framework.py
└── extenders/
    └── my_extender/
        ├── __init__.py
        └── my_extender.py
```

### Key files

- `placeholder/` - Root namespace (rename to your organization's name)
- `pyproject.toml` - Package config (edit directly, not auto-generated)
- `.github/workflows/test.yml` - CI workflow running pytest

### Setup Your Plugin

#### 1. Rename the directory

```bash
mv placeholder acme
```

#### 2. Update pyproject.toml

Edit the following fields in `pyproject.toml`:

- `name`: change `"placeholder-my-plugin"` to `"acme-my-plugin"`
- `authors`: update name and email
- `description`: update to describe your plugin
- `tool.setuptools.packages.find.include`: change `["placeholder*"]` to `["acme*"]`
- `tool.pytest.ini_options.testpaths`: change `["placeholder", "tests"]` to `["acme", "tests"]`

#### 3. Update .releaserc.yaml

Edit the following fields in `.releaserc.yaml`:

- `message`: change `mloda-plugin-template` to your package name (e.g., `"chore(release acme-my-plugin): ${nextRelease.version}"`)
- `repositoryUrl`: change to your repository URL

#### 4. Update Python imports

Update imports in these files (change `from placeholder.` to `from acme.`):

- `acme/feature_groups/my_plugin/__init__.py`
- `acme/feature_groups/my_plugin/tests/test_my_feature_group.py`
- `acme/compute_frameworks/my_plugin/__init__.py`
- `acme/compute_frameworks/my_plugin/tests/test_my_compute_framework.py`
- `acme/extenders/my_plugin/__init__.py`
- `acme/extenders/my_plugin/tests/test_my_extender.py`

#### 5. Verify setup

```bash
uv venv && source .venv/bin/activate && uv sync --all-extras && tox
```

#### 6. Remove template-only files

These files belong to the template repo and don't apply to your scaffolded plugin. Remove them after `tox` passes:

```bash
rm CODE_OF_CONDUCT.md AGENTS.md CLAUDE.md CONTRIBUTING.md
rm -rf .github/ISSUE_TEMPLATE/
```

You may also want to replace this `README.md` with one that describes your plugin. Add your own Code of Conduct, contributor guide, and issue templates later if you want them.

### Where to next

- **[mloda-registry/docs/guides/](https://github.com/mloda-ai/mloda-registry/tree/main/docs/guides/)** — full plugin development walkthrough (FeatureGroups, ComputeFrameworks, Extenders, packaging, publishing).
- **[mloda](https://github.com/mloda-ai/mloda)** — core framework reference.
- **[Claude Code skills](https://github.com/mloda-ai/mloda-registry/tree/main/.claude/skills/)** — pattern guidance and best practices for AI-assisted plugin development.
- **[docs/github-workflows.md](docs/github-workflows.md)** — CI/CD setup and required secrets for the included workflows.
