#!/usr/bin/env bash
# Rename the placeholder scaffold to your plugin's package name.
# Run once on a fresh clone of the template, then delete this script.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bin/customize.sh <package-name> [options]

Renames the placeholder/ package to <package-name> and updates all
references in pyproject.toml, .releaserc.yaml, and Python imports.

Arguments:
  <package-name>              Lowercase Python identifier (e.g. acme, my_org)

Options:
  --author "Your Name"        Set authors[].name in pyproject.toml
  --email you@example.com     Set authors[].email in pyproject.toml
  --description "..."         Set project.description in pyproject.toml
                              (must not contain the '|' character)
  --repository-url URL        Set repositoryUrl in .releaserc.yaml
  -h, --help                  Show this message

After running, verify with:
  uv venv && source .venv/bin/activate && uv sync --all-extras && tox
EOF
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

PACKAGE=""
AUTHOR=""
EMAIL=""
DESCRIPTION=""
REPOSITORY_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --author) AUTHOR="${2:-}"; shift 2 ;;
    --email) EMAIL="${2:-}"; shift 2 ;;
    --description) DESCRIPTION="${2:-}"; shift 2 ;;
    --repository-url) REPOSITORY_URL="${2:-}"; shift 2 ;;
    --*) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [[ -z "$PACKAGE" ]]; then
        PACKAGE="$1"
        shift
      else
        echo "Error: unexpected positional argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$PACKAGE" ]]; then
  echo "Error: <package-name> is required." >&2
  usage >&2
  exit 2
fi

if [[ "$PACKAGE" == "placeholder" ]]; then
  echo "Error: package name cannot be 'placeholder'." >&2
  exit 2
fi

if [[ "$PACKAGE" == "mloda" || "$PACKAGE" == "mloda_plugins" ]]; then
  echo "Error: package name '$PACKAGE' is reserved by the mloda namespace." >&2
  echo "The core mloda package is a shared PEP 420 namespace; a plugin that ships" >&2
  echo "mloda/__init__.py would make mloda unimportable for everyone who installs it." >&2
  echo "Choose a name unique to your organization (e.g. acme, my_org)." >&2
  exit 2
fi

if ! [[ "$PACKAGE" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "Error: package name must be lowercase letters/digits/underscores, starting with a letter." >&2
  echo "Got: $PACKAGE" >&2
  exit 2
fi

if [[ "$DESCRIPTION" == *"|"* ]]; then
  echo "Error: --description must not contain the '|' character." >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -d placeholder ]]; then
  echo "Error: placeholder/ directory not found at $REPO_ROOT." >&2
  echo "This template appears to be already customized (or you ran the script from the wrong directory)." >&2
  exit 1
fi

# Portable in-place sed: works on both GNU and BSD sed.
sed_inplace() {
  local pattern="$1"
  local file="$2"
  sed -i.bak "$pattern" "$file"
  rm -f "${file}.bak"
}

echo "==> Renaming placeholder/ to ${PACKAGE}/"
mv placeholder "$PACKAGE"

echo "==> Updating pyproject.toml"
sed_inplace "s/^name = \"placeholder-my-plugin\"\$/name = \"${PACKAGE}-my-plugin\"/" pyproject.toml
sed_inplace "s/^include = \[\"placeholder\\*\"\]\$/include = [\"${PACKAGE}*\"]/" pyproject.toml
sed_inplace "s/^testpaths = \[\"placeholder\", \"tests\"\]\$/testpaths = [\"${PACKAGE}\", \"tests\"]/" pyproject.toml
# Entry-point tables: rewrite both the label and the dotted manifest path
# (e.g. 'placeholder = "placeholder.feature_groups.manifest:...' -> '${PACKAGE} = "${PACKAGE}.feature_groups.manifest:...').
sed_inplace "s|^placeholder = \"placeholder\\.|${PACKAGE} = \"${PACKAGE}.|" pyproject.toml

if [[ -n "$AUTHOR" || -n "$EMAIL" ]]; then
  AUTHOR_NAME="${AUTHOR:-Your Name placeholder}"
  AUTHOR_EMAIL="${EMAIL:-placeholder@placeholder.com}"
  sed_inplace "s|^authors = .*|authors = [{ name = \"${AUTHOR_NAME}\", email = \"${AUTHOR_EMAIL}\" }]|" pyproject.toml
fi

if [[ -n "$DESCRIPTION" ]]; then
  sed_inplace "s|^description = .*|description = \"${DESCRIPTION}\"|" pyproject.toml
fi

echo "==> Updating .releaserc.yaml"
sed_inplace "s|chore(release mloda-plugin-template):|chore(release ${PACKAGE}-my-plugin):|" .releaserc.yaml
if [[ -n "$REPOSITORY_URL" ]]; then
  sed_inplace "s|^repositoryUrl: .*|repositoryUrl: \"${REPOSITORY_URL}\"|" .releaserc.yaml
fi

echo "==> Updating Python imports under ${PACKAGE}/"
find "$PACKAGE" -type f -name '*.py' -print0 | while IFS= read -r -d '' f; do
  sed_inplace "s/from placeholder\\./from ${PACKAGE}./g; s/import placeholder\\./import ${PACKAGE}./g" "$f"
done

echo "==> Checking for stale 'placeholder' references"
STALE="$(grep -rn 'placeholder' "$PACKAGE" pyproject.toml .releaserc.yaml || true)"
if [[ -n "$STALE" ]]; then
  echo "Error: stale 'placeholder' references found in customized files:" >&2
  printf '%s\n' "$STALE" >&2
  exit 1
fi

cat <<EOF

Customization complete.

Next steps:
  1. Verify the build:
       uv venv && source .venv/bin/activate && uv sync --all-extras && tox
  2. Remove template-only files:
       rm CONTRIBUTING.md bin/customize.sh
  3. Delete the '## First-time setup' section from CLAUDE.md and AGENTS.md.
EOF
