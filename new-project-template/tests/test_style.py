"""Project style rule: no em dashes (U+2014) in project-produced artifacts.

Em dashes are banned in the artifacts this project produces: code, docs,
specs, plans, tasks, the extension (including the templates it provides),
the constitution, and hook and gate definitions. Use a hyphen instead.
Upstream Spec Kit content - the stock shared scripts and base templates,
the bundled workflow, the vendored skill tree, and the dot-form command
scaffolds - may contain em dashes and is excluded, as is local install
state and runtime output (``artifacts/``). The vendored skill tree is
excluded because the project-created skills in it are kept identical to
the scanned extension commands by the prose-sync test.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {
    ".md", ".py", ".yaml", ".yml", ".sh", ".json", ".rst", ".tf", ".toml", ".txt",
}

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".terraform",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
    "node_modules",
    "_build",
    "_dev",
}

EXCLUDED_FILES = {
    "LICENSE",
    "uv.lock",
    # Terraform-generated provider lock file: same class as uv.lock,
    # generated upstream content rather than a project artifact.
    ".terraform.lock.hcl",
    # Workshop runtime lock file: written by the Workshop CLI, not a
    # project artifact.
    ".workshop.lock",
}

# Upstream Spec Kit surfaces and local install state. Everything else under
# .specify/ (the constitution, extensions.yml, the workflow overlays) and
# everything under specs/ and extensions/ is project-produced and scanned;
# the extension-provided templates live in the tracked extension source and
# are scanned with it. The integration-installed skill trees
# (.github/skills, .claude/skills) are excluded because the project-created
# skills in them are kept identical to the scanned extension commands by the
# prose-sync test, while the upstream core skills may contain em dashes;
# each integration installs to its own tool directory (.opencode/commands,
# .claude/skills, .github/skills), so exclude the directory per tool.
EXCLUDED_PREFIXES = (
    ".specify/scripts/",
    ".specify/templates/",
    ".specify/workflows/speckit/",
    ".specify/workflows/workflow-registry.json",
    ".specify/integrations/",
    ".specify/extensions/",
    ".specify/feature.json",
    ".specify/init-options.json",
    ".specify/integration.json",
    ".github/skills/",
    ".claude/skills/",
    ".opencode/commands/speckit.",
)

# Installer-owned files: written by the Specify CLI, whose upstream content
# may contain em dashes. Excluded per-file (not per-directory) so the rest
# of the containing tree stays scanned.
EXCLUDED_INSTALLER_FILES = {
    ".specify/.gitignore",
}

# Project-produced files without a listed text suffix that the suffix filter
# would otherwise skip. The seed's own extensionless artifacts are listed so
# the gate scans them too (the shell hooks are explicitly meant to be edited);
# @FILL-IN@ add your project's own extensionless entry points (for example a
# `bin/` script with no extension).
ALWAYS_SCAN: set[str] = {
    ".gitignore",
    ".opencode/.gitignore",
    "Makefile",
    ".workshop/dev-tools/hooks/setup-base",
    ".workshop/dev-tools/hooks/setup-project",
    "gitignore",
    "phrases.txt.example",
}

EM_DASH = "\u2014"  # kept as an escape so this file passes its own rule


def _iter_project_files():
    for root, dirs, files in os.walk(REPO_ROOT, topdown=True):
        # ``*.egg-info`` directories are generated install state
        # (editable installs recreate them; .gitignore treats them the
        # same way) - the gates scan project-authored files, not
        # install output.
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")
        )
        for filename in sorted(files):
            path = Path(root) / filename
            rel = path.relative_to(REPO_ROOT)
            if rel.name in EXCLUDED_FILES:
                continue
            if str(rel) in EXCLUDED_INSTALLER_FILES:
                continue
            if any(str(rel).startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and str(rel) not in ALWAYS_SCAN:
                continue
            yield rel, path


def test_no_em_dashes_in_project_files():
    offenders: list[str] = []
    for rel, path in _iter_project_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if EM_DASH in line:
                offenders.append(f"{rel}:{lineno}: {line.strip()[:80]}")
    assert not offenders, (
        "em dash (U+2014) found in project files; use a hyphen instead:\n"
        + "\n".join(offenders)
    )


def test_no_unfilled_fill_in_markers():
    """In an adopting project, the @FILL-IN@ markers must all be resolved.

    A marker left unfilled ships placeholder text in a load-bearing
    place: a Verification section that says "@FILL-IN@ The commands that
    define done", or a constitution whose binding mechanics are stubs.
    The check fails while any tracked artifact still carries a marker,
    so the fill-in obligation is enforced by the gate, not by memory.

    Two-tier, like the enforcement-chain mirror tests: the seed template tree
    itself is the non-adopting state (no extensions/requirements), and
    there the markers are the product - the check skips. A project that
    has adopted the extension must have filled every marker; an
    unfilled one fails loudly with the offending file and line.
    """
    if not (REPO_ROOT / "extensions" / "requirements").is_dir():
        pytest.skip("seed template tree: markers are the product here")
    offenders: list[str] = []
    for rel, path in _iter_project_files():
        if rel.parts[0] == "tests" and rel.name == "test_style.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "@FILL-IN@" in line:
                offenders.append(f"{rel}:{lineno}: {line.strip()[:80]}")
    assert not offenders, (
        "unresolved @FILL-IN@ marker in project files; fill it in or "
        "remove the section:\n"
        + "\n".join(offenders)
    )
