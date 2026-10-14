"""Workshop-action mirror: the named actions track the Makefile's targets.

The Workshop definition (``.workshop/<name>.yaml`` - the file's name is
the workshop name, which keys the tool's image cache, so it is
per-project) exposes the project's entry points as named actions
(``workshop run -- <action>``): one stanza per public Makefile target,
the agent passthroughs, and a generic ``make`` passthrough. The mapping
is hand-maintained, so this mirror fails on drift in either direction:

- forward: an action naming a Makefile target that does not exist
  (broken by a rename or deletion);
- reverse: a public Makefile target with no named action and no
  recorded reason (invisible to the workshop surface until someone
  remembers the stanza).

Targets deliberately not exposed - aggregate sub-targets, build
artifacts - are recorded in ALLOWLIST with a reason per entry; a new
public target must either gain a matching action or a line there.
Adoption-gated: a project without a Workshop definition skips.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

WORKSHOP_DIR = REPO_ROOT / ".workshop"
MAKEFILE = REPO_ROOT / "Makefile"

# Public Makefile targets deliberately not exposed as named actions.
# Every entry states its reason. A new public target gains either a
# matching .workshop definition action or a line here with its reason.
ALLOWLIST: dict[str, str] = {
    "test-style": "sub-target of test",
    "test-traceability": "sub-target of test",
    "test-enforcement": "sub-target of test",
    "test-workshop-actions": "sub-target of test",
    "test-bootstrap-manifest": "sub-target of test",
}

# make <target> in an action script. The generic passthrough
# (make "$@") carries no literal target and does not match.
MAKE_CALL = re.compile(r"(?<![\w$-])make\s+([A-Za-z][A-Za-z0-9_-]*)")

# Target-definition lines. Leading-dot file rules (".venv/bin/activate:")
# and variables ("$(CHARM_FILE):") are not public targets; "_guard-*"
# helpers are internal and excluded by the leading-underscore convention.
TARGET_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):")


def _definitions() -> list[Path]:
    return sorted(WORKSHOP_DIR.glob("*.yaml"))


def _skip_unless_workshop_served():
    if not _definitions():
        pytest.skip(
            "no .workshop/*.yaml definition: not a Workshop-served project"
        )


def _makefile_targets() -> set[str]:
    targets: set[str] = set()
    for line in MAKEFILE.read_text(encoding="utf-8").splitlines():
        match = TARGET_LINE.match(line)
        if match:
            targets.add(match.group(1))
    return targets


def _actions() -> dict[str, str]:
    actions: dict[str, str] = {}
    for path in _definitions():
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, script in (definition.get("actions") or {}).items():
            if isinstance(script, str):
                actions[name] = script
    return actions


def test_actions_name_real_makefile_targets():
    """Forward: every named action's make target exists in the Makefile,
    and an action named after a Makefile target invokes that target:
    an action `test` calling `make test-charm` would pass an
    existence-only check while `workshop run -- test` runs the wrong
    suite."""
    _skip_unless_workshop_served()
    targets = _makefile_targets()
    offenders: list[str] = []
    for name, script in sorted(_actions().items()):
        called = [match.group(1) for match in MAKE_CALL.finditer(script)]
        for target in called:
            if target not in targets:
                offenders.append(f"action {name}: make {target}")
        if name in targets and name not in called:
            offenders.append(f"action {name}: does not invoke make {name}")
    assert not offenders, (
        "workshop actions name missing Makefile targets or fail to "
        "invoke their own target (rename or delete drift):\n  "
        + "\n  ".join(offenders)
    )


def test_public_makefile_targets_are_exposed_or_allowed():
    """Reverse: every public target has a same-named action, or is
    allowlisted with a reason.

    A call-site check would pass while an action is renamed: an action
    `run-tests` calling `make test` still exercises the target, but the
    advertised entry point `workshop run -- test` is gone. The action's
    name is the advertised interface, so each public target must be
    covered by an action of the same name. The generic `make`
    passthrough names no specific target and never counts. An
    allowlist entry whose Makefile target no longer exists is a stale
    exemption documenting nothing: deleting or renaming a target must
    retire its entry, not leave it as dead documentation."""
    _skip_unless_workshop_served()
    stale_allowlist = sorted(set(ALLOWLIST) - _makefile_targets())
    assert not stale_allowlist, (
        "ALLOWLIST names missing Makefile targets (stale exemptions "
        "documenting nothing - retire the entry when the target goes):"
        "\n  " + "\n  ".join(stale_allowlist)
    )
    for target, reason in ALLOWLIST.items():
        assert reason.strip(), (
            f"ALLOWLIST entry {target} states no reason; every entry "
            f"records why its target needs no same-name action - a "
            f"blank reason lets a public target vanish from the "
            f"advertised actions with no explanation"
        )
    action_names = set(_actions())
    offenders: list[str] = []
    for target in sorted(_makefile_targets()):
        if target in action_names or target in ALLOWLIST:
            continue
        offenders.append(f"{target}: no same-name action, no ALLOWLIST entry")
    assert not offenders, (
        "public Makefile targets without a same-name workshop action; "
        "add a .workshop definition action named for the target or an "
        "ALLOWLIST entry with a reason:"
        "\n  " + "\n  ".join(offenders)
    )