"""Bootstrap-manifest mirror: the seed's copy manifest covers tests/ and scripts/.

``bootstrap.sh`` seeds a new project from a hand-maintained manifest of
``copy`` lines rather than copying ``tests/`` and ``scripts/`` wholesale,
so the sets that ship are curated. The manifest can drift from the tree in
two directions, and only one of them is loud:

- a line naming a file that no longer exists - ``copy`` is a bare ``cp``
  under ``set -e``, so bootstrap aborts at the stale line;
- a Python test file or a project helper script with no line - every
  future seed silently omits it while the trees' own suites stay green.

This mirror fails on both, so the manifest is checked rather than
accidentally loud. It includes itself: a new mirror test ships only
with its copy line. Tree-gated: the check fires in the seed template
tree and skips in a seeded project (which carries no bootstrap.sh).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

BOOTSTRAP = REPO_ROOT / "bootstrap.sh"
TESTS_DIR = REPO_ROOT / "tests"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# copy "$HERE/<dir>/<file>" "$TARGET/<dir>/<file>" - a manifest line for a
# tests/ or scripts/ file (source and target paths identical).
COPY_LINE = re.compile(
    r'^\s*copy "\$HERE/((?:tests|scripts)/[A-Za-z0-9_./-]+)" "\$TARGET/\1"$'
)


def _skip_unless_seed_template():
    if not BOOTSTRAP.is_file():
        pytest.skip("no bootstrap.sh: not the seed template tree")


def _manifest() -> set[str]:
    manifest: set[str] = set()
    for line in BOOTSTRAP.read_text(encoding="utf-8").splitlines():
        match = COPY_LINE.match(line)
        if match:
            manifest.add(match.group(1))
    return manifest


def _tests_tree() -> set[str]:
    return {f"tests/{path.name}" for path in TESTS_DIR.glob("*.py")}


def _scripts_tree() -> set[str]:
    return {f"scripts/{path.name}" for path in SCRIPTS_DIR.glob("*") if path.is_file()}


def test_manifest_covers_tests_tree():
    """Reverse: every Python file under tests/ ships in the manifest."""
    _skip_unless_seed_template()
    missing = sorted(_tests_tree() - _manifest())
    assert not missing, (
        "tests/ files absent from bootstrap.sh's copy manifest "
        "(every Python file under tests/ ships in the seed):\n  "
        + "\n  ".join(missing)
    )


def test_manifest_covers_scripts_tree():
    """Reverse: every project helper under scripts/ ships in the manifest."""
    _skip_unless_seed_template()
    missing = sorted(_scripts_tree() - _manifest())
    assert not missing, (
        "scripts/ files absent from bootstrap.sh's copy manifest "
        "(every project helper under scripts/ ships in the seed):\n  "
        + "\n  ".join(missing)
    )


def test_manifest_names_real_files():
    """Forward: every manifested tests/ or scripts/ path exists."""
    _skip_unless_seed_template()
    offenders = [
        rel for rel in sorted(_manifest()) if not (REPO_ROOT / rel).is_file()
    ]
    assert not offenders, (
        "bootstrap.sh manifest lines name files that do not exist "
        "(rename or delete drift):\n  " + "\n  ".join(offenders)
    )
