# GitHub Repository Settings

This is the GitHub-side companion to [github-workflows.md](github-workflows.md). The workflow doc explains what each workflow does and how to mint the tokens it needs; this doc explains what to configure on the repository itself so the inherited workflows behave correctly and `main` does not run with unsafe defaults.

Apply these settings once, after creating your plugin repository from the template.

## Required secrets

The release workflow is the only one that needs secrets. Both live under **Settings > Secrets and variables > Actions > Repository secrets**.

| Secret | Used by | Purpose |
| --- | --- | --- |
| `SEMANTIC_RELEASE_TOKEN` | `release.yaml` (`github_release` job) | A Personal Access Token with `repo` write so semantic-release can tag the release and push the version-bump commit back to `main`. The default `GITHUB_TOKEN` cannot push to a protected branch, which is why a PAT is required. |
| `PYPI_API_TOKEN` | `release.yaml` (`publish` job) | PyPI API token used by `twine upload`. Scope it to the project once the package is published for the first time. |

See [github-workflows.md](github-workflows.md#setting-up-secrets) for the step-by-step on creating each token. The test and scaffold workflows (`test.yml`, `scaffold-test.yml`) run on the default `GITHUB_TOKEN` and need no secrets.

### PyPI Trusted Publisher (modern alternative)

Instead of a long-lived `PYPI_API_TOKEN`, PyPI supports OIDC Trusted Publishers, which exchange a short-lived token at publish time and remove the secret from your repository entirely. See the [PyPI documentation](https://docs.pypi.org/trusted-publishers/) for setup. Adopting it means reworking the `publish` job in `release.yaml` (typically switching to `pypa/gh-action-pypi-publish` and granting `id-token: write` permission), not just removing the token reference.

## Branch protection on `main`

Configure these under **Settings > Branches > Add branch ruleset** (or the older **Branch protection rules** UI).

Recommended rules:

- **Require status checks to pass before merging**, and select the matrix jobs listed in the next section.
- **Require branches to be up to date before merging** (optional, but matches what the test workflow already runs against).
- **Require linear history** (optional, keeps `main` readable).
- **Restrict force pushes** and **restrict deletions**.

### Do not "Require a pull request before merging" without an exception

The release workflow uses `@semantic-release/git` to push the version-bump commit (updates to `pyproject.toml` and `uv.lock`) directly to `main`. If you enable "Require a pull request before merging" on `main` and do not allow bypasses, `release.yaml` will fail at the push step.

You have three options:

1. Skip "Require a pull request before merging" and rely on required status checks + restricted force-pushes to gate `main`. This is the simplest path.
2. Enable it, then add a bypass for the account whose PAT is stored in `SEMANTIC_RELEASE_TOKEN` (or for a GitHub App acting as the release identity). On rulesets, this is the **Bypass list** field; on the classic UI it is **Allow specified actors to bypass required pull requests**.
3. Remove the `@semantic-release/git` plugin from `.releaserc.yaml`. The version bump will no longer be committed back to the repo, only tagged in the release. Only do this if you understand the trade-off (your `pyproject.toml` version stays at whatever value the template ships with).

## Required status checks

The test workflow (`test.yml`) declares a job called `test` with a matrix over Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`. GitHub presents the matrix-expanded check names in the branch-protection dropdown, not the workflow name. Add all five:

- `test (3.10)`
- `test (3.11)`
- `test (3.12)`
- `test (3.13)`
- `test (3.14)`

If you drop a Python version from the matrix in `test.yml`, also drop it from the required checks; otherwise PRs will block forever waiting for a check that never runs. The placeholder check rides on the `3.10` leg via an `if:` guard in `test.yml`; if you change which Python version runs that step, update the guard to match.

The scaffold-rename workflow (`scaffold-test.yml`) also runs on every PR to `main` and emits a `scaffold` check. Add it too if you want the customize-step validation to gate merges:

- `scaffold`

## Dependabot reviewer

`.github/dependabot.yml` does not name anyone out of the box, so dependabot PRs land without an assignee or review request. Add an `assignees:` entry so the PR appears in someone's "Assigned" feed:

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    assignees:
      - "your-github-username"
    groups:
      all-dependencies:
        patterns:
          - "*"
```

Assignees must have write access to the repository. See the [GitHub documentation](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#assignees) for details.

If you also want to *require* review (not just assign), add a `CODEOWNERS` file under `.github/` listing the same user or team, and enable **Require review from Code Owners** in the branch ruleset. CODEOWNERS covers human PRs too, so it is the broader option.

## Checklist

- [ ] `SEMANTIC_RELEASE_TOKEN` and `PYPI_API_TOKEN` added under repository secrets
- [ ] Branch protection on `main` with required status checks listed above
- [ ] Bypass configured for the release identity, or "Require pull request" left off
- [ ] `assignees:` set in `.github/dependabot.yml` (and optionally `CODEOWNERS`)
- [ ] Trusted Publisher considered (optional)
