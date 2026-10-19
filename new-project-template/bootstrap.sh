#!/usr/bin/env bash
# Seed a project from this template.
#
# Usage: bootstrap.sh /path/to/fresh/project [author] [--with-examples]
#
# The target must already have a .specify/ directory (created by
# `specify init` with any integration). This script installs:
#   - the requirements extension tooling under extensions/requirements/
#   - the enforcement hooks (declared in the extension manifest,
#     registered into .specify/extensions.yml at install time)
#   - the workflow review gates
#   - the spec and tasks templates (provided by the requirements
#     extension at install time, through its provides.templates manifest)
#   - the two-part constitution (replacing the one seeded by specify init)
#   - the mirror tests (tests/test_style.py,
#     tests/test_requirement_traceability.py,
#     tests/test_enforcement_chain.py, tests/test_workshop_actions.py,
#     tests/test_bootstrap_manifest.py)
#   - the AGENTS.md and CONTRIBUTING.md skeletons and the mechanics stub
#   - .github/copilot-instructions.md (where Copilot discovers it)
#   - the mirror dependencies (requirements.txt) and a seed .gitignore
#   - the Workshop development environment (.workshop/<name>.yaml,
#     named for the project, and the dev-tools SDK hooks), plus
#     scripts/workshop.sh, the host-side helper
#   - agent command shims (dot-form, registered by `specify extension add`)
# It then installs the extension and prints the fill-in checklist.
#
# Idempotent: re-running the script never overwrites customized skeleton
# content. The extension tree, tests, Makefile, requirements.txt, workflow
# overlay, helper scripts, and generated skills are machinery and refresh.
# Skeleton files (AGENTS.md, CONTRIBUTING.md, agent-instructions.md,
# .github/copilot-instructions.md, docs/implementation-mechanics.md, the
# constitution) are only copied when absent, when still byte-identical to
# this template's skeleton (a pristine copy, refreshed), or when still the
# stock file a bare `specify init` seeds (the previous content is kept in
# a .bootstrap-backup beside it); a customized file is never overwritten.
# The extension tree, tests, and skills are always regenerated (they are
# machinery, not user content). The project's requirement-phrases.txt and
# domain-terms.txt are seeded only when absent and are never touched by the
# extension re-copy (they live outside the extension tree); the manifest's
# author and repository attribution lines are user content and are preserved.
# Example files installed with --with-examples are only reinstalled over
# absent or pristine destinations; a customized file is kept.
#
# --with-examples copies the worked sample (requirements, roadmap, spec,
# requirement phrases) from examples/ into the target so the tooling can
# be verified green before writing your own content.
set -euo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:?usage: bootstrap.sh /path/to/project [author] [--with-examples]}
AUTHOR=${2:-}
# A flag in the author position, or no author at all, falls back to the
# target directory's name.
case "$AUTHOR" in
  ""|--*) AUTHOR=$(basename "$TARGET") ;;
esac
WITH_EXAMPLES=no
for arg in "$@"; do
  case "$arg" in
    --with-examples) WITH_EXAMPLES=yes ;;
  esac
done

[ -d "$TARGET/.specify" ] || {
  echo "error: $TARGET has no .specify/ directory; run 'specify init' there first" >&2
  exit 1
}

copy() {
  echo "  + ${2#$TARGET/}"
  cp "$1" "$2"
}

# Copy a skeleton file only when absent, when the existing copy is still
# byte-identical to this template's skeleton (a pristine copy, refreshed),
# or when it is still the stock file a bare `specify init` seeds (third
# argument: a line unique to that stock seed; the previous content is
# kept in a .bootstrap-backup beside it). Any other content - partially
# filled in or hand-edited - is user work and is never overwritten;
# delete the file and re-run to reset it.
copy_skeleton() {
  local src="$1" dst="$2" stock="${3:-}"
  if [ ! -f "$dst" ]; then
    copy "$src" "$dst"
    return
  fi
  if cmp -s "$src" "$dst"; then
    copy "$src" "$dst"
    return
  fi
  if [ -z "$stock" ] || ! grep -qF "$stock" "$dst"; then
    echo "  = ${dst#$TARGET/} kept, already customized (delete it to reset)"
    return
  fi
  cp "$dst" "$dst.bootstrap-backup"
  copy "$src" "$dst"
  echo "  ~ previous ${dst#$TARGET/} saved as ${dst#$TARGET/}.bootstrap-backup"
}

# Copy a worked example over a destination that is absent, still a
# pristine seed (third argument), or still a prior copy of the same
# example; a file that matches none of those was customized by the
# user and is never overwritten.
copy_example() {
  local src="$1" dst="$2" pristine="${3:-}"
  if [ -f "$dst" ] && ! cmp -s "$src" "$dst" \
    && { [ -z "$pristine" ] || ! cmp -s "$pristine" "$dst"; }; then
    echo "  = ${dst#$TARGET/} kept, already customized"
    return
  fi
  copy "$src" "$dst"
}

# Make a whole line safe to splice into a '|' delimited sed replacement
# field: backslash, '&', and the delimiter are escaped. Used for both the
# preserved and the fresh attribution values, so an author or repository
# string such as "ACME/R&D Labs" cannot abort or corrupt the manifest.
escape_sed() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

# Portable in-place sed (GNU and BSD): edit with a backup suffix, then drop
# the backup. Called as: sed_inplace FILE SCRIPT
sed_inplace() {
  sed -i.bak "$2" "$1" && rm -f "$1.bak"
}

echo "Installing extension tooling"
# The extension tree is regenerated machinery; the manifest's author and
# repository attribution lines are user content and survive the re-copy.
# Requirement phrases live at the project root, outside the extension
# tree. A legacy extension-tree phrases file (projects seeded before the
# move) is migrated before the tree is replaced.
PHRASES_DST="$TARGET/requirement-phrases.txt"
LEGACY_PHRASES="$TARGET/extensions/requirements/data/phrases.txt"
has_phrases_entries() {
  [ -f "$1" ] && grep -qvE '^[[:space:]]*(#|$)' "$1"
}
if { [ ! -f "$PHRASES_DST" ] || ! has_phrases_entries "$PHRASES_DST"; } \
  && has_phrases_entries "$LEGACY_PHRASES"; then
  cp "$LEGACY_PHRASES" "$PHRASES_DST"
  echo "  ~ migrated extensions/requirements/data/phrases.txt to requirement-phrases.txt"
fi
saved_author=""
saved_repository=""
if [ -f "$TARGET/extensions/requirements/extension.yml" ]; then
  saved_author=$(grep "^  author: " "$TARGET/extensions/requirements/extension.yml" || true)
  saved_repository=$(grep "^  repository: " "$TARGET/extensions/requirements/extension.yml" || true)
fi
mkdir -p "$TARGET/extensions"
rm -rf "$TARGET/extensions/requirements"
cp -R "$HERE/extension" "$TARGET/extensions/requirements"
if [ ! -f "$PHRASES_DST" ]; then
  copy "$HERE/requirement-phrases.txt.example" "$PHRASES_DST"
else
  echo "  = requirement-phrases.txt kept"
fi

DOMAIN_TERMS_DST="$TARGET/domain-terms.txt"
if [ ! -f "$DOMAIN_TERMS_DST" ]; then
  copy "$HERE/domain-terms.txt.example" "$DOMAIN_TERMS_DST"
else
  echo "  = domain-terms.txt kept"
fi
YML="$TARGET/extensions/requirements/extension.yml"
if [ -n "$saved_author" ]; then
  sed_inplace "$YML" "s|^  author: .*|$(escape_sed "$saved_author")|"
else
  sed_inplace "$YML" "s|^  author: .*|  author: $(escape_sed "$AUTHOR")|"
fi
if [ -n "$saved_repository" ]; then
  sed_inplace "$YML" "s|^  repository: .*|$(escape_sed "$saved_repository")|"
else
  sed_inplace "$YML" "s|^  repository: .*|  repository: TODO-your-repo-url|"
fi

if [ "$WITH_EXAMPLES" = "yes" ]; then
  echo "Installing the worked examples"
  copy_example "$HERE/examples/REQUIREMENTS.md" "$TARGET/REQUIREMENTS.md"
  copy_example "$HERE/examples/ROADMAP.md" "$TARGET/ROADMAP.md"
  copy_example "$HERE/examples/requirement-phrases.txt" \
    "$TARGET/requirement-phrases.txt" \
    "$HERE/requirement-phrases.txt.example"
  mkdir -p "$TARGET/specs"
  if [ ! -d "$TARGET/specs/001-greeting" ]; then
    cp -R "$HERE/examples/specs/001-greeting" "$TARGET/specs/"
    echo "  + specs/001-greeting/"
  else
    echo "  = specs/001-greeting/ kept"
  fi
fi

echo "Installing hooks, gates, constitution"
mkdir -p "$TARGET/.specify/workflows/overlays/speckit" "$TARGET/.specify/memory"
copy "$HERE/review-gates.yml" "$TARGET/.specify/workflows/overlays/speckit/review-gates.yml"
copy_skeleton "$HERE/constitution.md" "$TARGET/.specify/memory/constitution.md" \
  "# [PROJECT_NAME] Constitution"

echo "Installing mirror tests"
mkdir -p "$TARGET/tests"
copy "$HERE/tests/test_style.py" "$TARGET/tests/test_style.py"
copy "$HERE/tests/test_requirement_traceability.py" "$TARGET/tests/test_requirement_traceability.py"
copy "$HERE/tests/test_enforcement_chain.py" "$TARGET/tests/test_enforcement_chain.py"
copy "$HERE/tests/test_workshop_actions.py" "$TARGET/tests/test_workshop_actions.py"
copy "$HERE/tests/test_bootstrap_manifest.py" "$TARGET/tests/test_bootstrap_manifest.py"
copy "$HERE/Makefile" "$TARGET/Makefile"
copy "$HERE/requirements.txt" "$TARGET/requirements.txt"
if [ -f "$TARGET/.gitignore" ]; then
  echo "  = .gitignore kept, already present"
else
  copy "$HERE/gitignore" "$TARGET/.gitignore"
fi

echo "Installing skeletons"
copy_skeleton "$HERE/AGENTS.md" "$TARGET/AGENTS.md"
copy_skeleton "$HERE/CONTRIBUTING.md" "$TARGET/CONTRIBUTING.md"
copy_skeleton "$HERE/agent-instructions.md" "$TARGET/agent-instructions.md"
mkdir -p "$TARGET/.github"
copy_skeleton "$HERE/copilot-instructions.md" "$TARGET/.github/copilot-instructions.md"
mkdir -p "$TARGET/.workshop/dev-tools/hooks"
# The workshop definition is named for the project: the tool keys its
# image cache by workshop name, so no two projects on one machine
# should share a name. A fresh copy is named and its name field
# rewritten; an existing definition (however named) is always kept.
if compgen -G "$TARGET/.workshop/*.yaml" > /dev/null; then
  echo "  = .workshop definition kept, already present"
else
  SEED_WS_NAME=$(basename "$TARGET")
  SEED_WS_ESC=${SEED_WS_NAME//\\/\\\\}
  SEED_WS_ESC=${SEED_WS_ESC//&/\\&}
  copy_skeleton "$HERE/.workshop/workshop.yaml" "$TARGET/.workshop/${SEED_WS_NAME}.yaml"
  if grep -q "^name: workshop$" "$TARGET/.workshop/${SEED_WS_NAME}.yaml"; then
    sed --in-place "s/^name: workshop$/name: ${SEED_WS_ESC}/" "$TARGET/.workshop/${SEED_WS_NAME}.yaml"
  fi
fi
copy_skeleton "$HERE/.workshop/dev-tools/sdk.yaml" "$TARGET/.workshop/dev-tools/sdk.yaml"
copy_skeleton "$HERE/.workshop/dev-tools/hooks/setup-base" "$TARGET/.workshop/dev-tools/hooks/setup-base"
copy_skeleton "$HERE/.workshop/dev-tools/hooks/setup-project" "$TARGET/.workshop/dev-tools/hooks/setup-project"
mkdir -p "$TARGET/scripts"
copy "$HERE/scripts/workshop.sh" "$TARGET/scripts/workshop.sh"
mkdir -p "$TARGET/.opencode"
copy "$HERE/.opencode/opencode.json" "$TARGET/.opencode/opencode.json"
mkdir -p "$TARGET/docs"
copy_skeleton "$HERE/implementation-mechanics.md" "$TARGET/docs/implementation-mechanics.md"

echo "Generating agent skills from the extension commands"
"$TARGET/extensions/requirements/scripts/bash/generate-skills.sh" "$TARGET" "$AUTHOR"

if command -v specify >/dev/null 2>&1; then
  echo "Installing the requirements extension"
  (cd "$TARGET" && specify extension add --dev --force extensions/requirements)
else
  echo "  specify CLI not found; run: specify extension add --dev --force extensions/requirements"
fi

cat <<'CHECKLIST'

Seeded. Run `make install` to create the project virtual environment
and install the mirror-test dependencies. Then fill in the @FILL-IN@ markers,
in this order:

  1. REQUIREMENTS.md: your product scope with stable, section-scoped
     requirement IDs (see the README's conventions section).
  2. ROADMAP.md: the 9-column feature table mapping each ID to the feature
     that Completes it.
  3. requirement-phrases.txt: one line per requirement ID with verbatim
     phrases from your REQUIREMENTS.md (the bash suite validates and
     enforces coverage). It is a project artifact beside REQUIREMENTS.md,
     outside the extension tree, so editing it needs no extension reinstall.
  4. AGENTS.md and CONTRIBUTING.md skeletons (Project, Verification,
     tooling sections), then AGENTS.md's Project checklist
     instances.
  5. agent-instructions.md: your definition-of-done commands.
  6. docs/implementation-mechanics.md: the binding mechanics for your
     systems.
  7. .specify/memory/constitution.md: Part 2 (your domain principles).
  8. extensions/requirements/extension.yml: the repository URL.
  9. domain-terms.txt: extend the deny list with your domain's terms.
     Keep the shipped acme-storefront placeholder and append your own,
     one per line. The file is a project artifact; the scan guards your
     vocabulary once your terms are in, and a bootstrap re-run keeps it.

The no-unfilled-markers test in tests/test_style.py fails until every
@FILL-IN@ marker is resolved; run `make test` to see the remaining ones.

The full guide is in the template repository's README.md (the seed
checkout you ran this from).
CHECKLIST
