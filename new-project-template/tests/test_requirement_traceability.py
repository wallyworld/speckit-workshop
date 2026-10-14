"""Requirement traceability enforcement (speckit): mirror test.

Runs the `requirements` extension's deterministic Bash verifier
(`verify-traceability.sh`) as the mirror test of the agent-facing
`/speckit-requirements-verify` command. Keeping one source of truth: the Bash
suite under `extensions/requirements/tests/run-bash-tests.sh` owns the
behavioral assertions, and this module simply drives it under `make test`,
plus a live-spec check that every committed feature spec verifies clean and
a sync check that the installed extension copy matches the tracked source.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "extensions" / "requirements" / "tests" / "run-bash-tests.sh"
VERIFY = ROOT / "extensions" / "requirements" / "scripts" / "bash" / "verify-traceability.sh"
EXTENSION_SOURCE = ROOT / "extensions" / "requirements"
EXTENSION_INSTALLED = ROOT / ".specify" / "extensions" / "requirements"
REINSTALL = "specify extension add --dev --force extensions/requirements"

# In the seed template this module rides along before bootstrap: the
# extension source ships as `extension/` and is renamed by the installer,
# so the post-seed paths do not exist yet. Every test that needs the
# seeded surfaces skips with a stated reason until then.
SEEDED = EXTENSION_SOURCE.is_dir()


def test_requirements_extension_bash_suite():
    """The extension's fixture-driven Bash suite passes (traceable OK, drifted
    claims detected with a non-zero exit, no-Completes spec fails closed)."""
    if not SEEDED:
        pytest.skip("extension not installed yet; run bootstrap.sh first")
    result = subprocess.run([str(RUNNER)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_live_feature_specs_verify_clean():
    """Every committed feature spec must verify clean (DRIFT absent) against
    the traceability checker. Running the verifier with no arguments makes it
    check every spec.md under specs/, so every committed feature's Completes
    claims are live-enforced by make test. A project with no feature specs
    yet (a freshly seeded repository) skips: the check activates with the
    first committed spec. Also guards against a vacuous verifier: a checker
    that never flags anything would not assert an OK result for known-good
    specs either."""
    if not any((ROOT / "specs").glob("*/spec.md")):
        pytest.skip("no committed feature specs yet; the check activates with the first spec")
    result = subprocess.run([str(VERIFY)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK -" in result.stdout, result.stdout
    assert "DRIFT" not in result.stdout, result.stdout


def _tracked_extension_files():
    """Every tracked file of the extension source, excluding the dev adapter
    directory that the installer generates with substituted paths."""
    return sorted(
        path.relative_to(EXTENSION_SOURCE)
        for path in EXTENSION_SOURCE.rglob("*")
        if path.is_file() and ".specify-dev" not in path.relative_to(EXTENSION_SOURCE).parts
    )


def test_installed_extension_matches_source():
    """The installed extension copy must match the tracked source byte for
    byte. The agent-facing commands and hooks execute the installed copy
    under .specify/extensions/ while make test executes the tracked source,
    so the two must remain identical. Skips on a fresh clone before the
    documented install step."""
    if not EXTENSION_INSTALLED.is_dir():
        pytest.skip(f"requirements extension not installed; run: {REINSTALL}")
    tracked = _tracked_extension_files()
    assert tracked, "no tracked extension files found under extensions/requirements"
    for rel in tracked:
        source_bytes = (EXTENSION_SOURCE / rel).read_bytes()
        installed_path = EXTENSION_INSTALLED / rel
        assert installed_path.is_file(), (
            f"installed extension is missing {rel}; reinstall: {REINSTALL}"
        )
        assert installed_path.read_bytes() == source_bytes, (
            f"installed extension diverges from tracked source at {rel}; "
            f"reinstall: {REINSTALL}"
        )

_SKILL_COMMAND_PAIRS = {
    "speckit-requirements-prepare": "speckit.requirements.prepare.md",
    "speckit-requirements-verify": "speckit.requirements.verify.md",
    "speckit-requirements-plan-checklist": "speckit.requirements.plan-checklist.md",
    "speckit-requirements-tasks-checklist": "speckit.requirements.tasks-checklist.md",
    "speckit-requirements-remediation-loop": "speckit.requirements.remediation-loop.md",
}
_PLUMBING_TOKENS = ("assemble-brief.sh", "verify-traceability.sh", "{SCRIPT}")


def _prose_after_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            lines = lines[lines.index("---", 1) + 1:]
        except ValueError:
            # Malformed frontmatter: an opening --- with no closing
            # delimiter. Keep the whole file as body so the caller's
            # equality assertion fails with a readable diff instead of
            # an unhandled ValueError.
            pass
    return "\n".join(
        line for line in lines if not any(token in line for token in _PLUMBING_TOKENS)
    ).strip()


def test_extension_skills_match_source_commands():
    """Each skill under .github/skills mirrors its extension command doc's
    prose: the skills are the agent-facing copies of the extension commands.
    Frontmatter and script-path plumbing lines may differ between the two
    surfaces; the rule text may not."""
    if not SEEDED:
        pytest.skip("extension not installed yet; run bootstrap.sh first")
    for skill_name, command_file in sorted(_SKILL_COMMAND_PAIRS.items()):
        skill = (ROOT / ".github" / "skills" / skill_name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        command = (
            EXTENSION_SOURCE / "commands" / command_file
        ).read_text(encoding="utf-8")
        assert _prose_after_frontmatter(skill) == _prose_after_frontmatter(command), (
            f"{skill_name}/SKILL.md prose diverges from {command_file}; "
            f"regenerate the skill from the extension command"
        )


ROADMAP = ROOT / "ROADMAP.md"
ASSEMBLE = ROOT / "extensions" / "requirements" / "scripts" / "bash" / "assemble-brief.sh"


def _roadmap_rows():
    """Parse ROADMAP.md into {rid: {"completes": [...], "depends": [...],
    "status": str}} for each data row."""
    rows = {}
    for line in ROADMAP.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 9 or not cells[1].startswith("R") or not cells[1][1:].isdigit():
            continue
        rid = cells[1]
        completes_cell = cells[7]
        completes = [] if completes_cell in ("", "-", "\u2014") else [
            tok.strip() for tok in completes_cell.split(",") if tok.strip()
        ]
        depends_cell = cells[5]
        depends = [] if depends_cell in ("", "-", "\u2014") else [
            tok.strip() for tok in depends_cell.split(",") if tok.strip()
        ]
        rows[rid] = {"completes": completes, "depends": depends, "status": cells[6]}
    return rows


def _brief_completes(brief):
    for line in brief.splitlines():
        if line.startswith("Completes: "):
            cell = line[len("Completes: "):].strip()
            if cell == "(none)":
                return set()
            return {tok.strip() for tok in cell.split(",") if tok.strip()}
    raise AssertionError("Completes line not found in brief")


def test_assemble_brief_real_roadmap_emits_all_completes():
    """Every roadmap row the assembler accepts must emit the full set of
    Completes RQ IDs cited in that row, including letter-suffixed IDs (e.g.
    TEL-2a, SCEN-5a, PLATFORM-9a), with empty stderr. A brief that drops cited
    IDs would seed an under-covering spec. Rows whose dependencies are not yet
    'done' are dep-gated by the assembler and skipped here. Skips when the
    extension is not installed or no ROADMAP.md exists yet (a fresh seed
    before the roadmap is authored)."""
    if not SEEDED:
        pytest.skip("extension not installed yet; run bootstrap.sh first")
    if not ROADMAP.is_file():
        pytest.skip("no ROADMAP.md yet; the check activates with the roadmap")
    rows = _roadmap_rows()
    assert rows, "no roadmap rows parsed from ROADMAP.md"
    done = {rid for rid, r in rows.items() if r["status"] == "done"}
    for rid, row in sorted(rows.items()):
        result = subprocess.run(["bash", str(ASSEMBLE), rid], capture_output=True, text=True)
        if not all(dep in done for dep in row["depends"]):
            assert result.returncode != 0, f"{rid}: expected dep-gate refusal, got success"
            assert "must be 'done'" in result.stderr, f"{rid}: {result.stderr}"
            continue
        assert result.returncode == 0, f"{rid}: {result.stderr}"
        assert result.stderr == "", f"{rid}: {result.stderr}"
        assert _brief_completes(result.stdout) == set(row["completes"]), (
            f"{rid}: brief Completes != roadmap cell"
        )


_SPEC_COVERAGE_RE = re.compile(r"^roadmap entry:\s*`?ROADMAP\.md`?\s*->\s*\*\*(R\d+)\*\*", re.I | re.M)


def _spec_completes_set(text: str) -> set[str]:
    """The Completes set from a spec's Requirements Coverage section.

    The bullet may wrap across indented continuation lines, so this walks
    the bullet: the first line carries the marker, following indented lines
    that are not themselves bullets continue it, and the next bullet or
    blank line ends it."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^(?:[-*]\s*)?\*\*Completes\*\*:", line, re.I):
            cell = re.sub(r"^(?:[-*]\s*)?\*\*Completes\*\*:\s*", "", line, flags=re.I)
            j = i + 1
            while (
                j < len(lines)
                and lines[j][:1] in (" ", "\t")
                and lines[j].strip()
                and not lines[j].lstrip().startswith(("-", "*"))
            ):
                cell += " " + lines[j].strip()
                j += 1
            cell = cell.strip()
            if cell.lower() in ("(none)", "none", "-", ""):
                return set()
            return {token.strip() for token in cell.split(",") if token.strip()}
    raise AssertionError("no '**Completes**:' line found")


def test_spec_completes_align_with_roadmap():
    """Each spec's Requirements Coverage Completes set equals its feature's
    ROADMAP row, and no RQ ID is Completed by more than one feature.

    The phrase checker proves that claimed requirements are materially
    present in the spec; nothing else asserts the claim set itself to the
    roadmap: two specs could claim the same RQ, or a roadmap row could gain
    or lose Completes IDs without the spec following. The legend's "each RQ
    is completed by exactly one feature" and the coverage table's
    relationship rule both demand this alignment. Skips when no roadmap or
    no committed specs exist (a fresh seed)."""
    if not ROADMAP.is_file():
        pytest.skip("no ROADMAP.md yet; the check activates with the roadmap")
    specs = sorted((ROOT / "specs").glob("*/spec.md"))
    if not specs:
        pytest.skip("no committed feature specs yet")
    rows = _roadmap_rows()
    owners: dict[str, str] = {}
    for spec_path in specs:
        text = spec_path.read_text(encoding="utf-8")
        match = _SPEC_COVERAGE_RE.search(text)
        assert match, (
            f"{spec_path.parent.name}: spec has no 'Roadmap entry: "
            f"ROADMAP.md -> **R###**' line in Requirements Coverage"
        )
        rid = match.group(1)
        assert rid in rows, (
            f"{spec_path.parent.name}: cites roadmap {rid} which no roadmap row defines"
        )
        try:
            spec_completes = _spec_completes_set(text)
        except AssertionError as exc:
            raise AssertionError(
                f"{spec_path.parent.name}: {exc}"
            ) from None
        row = rows[rid]
        assert spec_completes == set(row["completes"]), (
            f"{spec_path.parent.name}: spec Completes {sorted(spec_completes)} "
            f"!= roadmap {rid} Completes {sorted(row['completes'])}"
        )
        for rq in spec_completes:
            previous = owners.get(rq)
            assert previous is None, (
                f"{rq} is Completed by both {previous} and "
                f"{spec_path.parent.name}; each RQ is completed by exactly "
                f"one feature"
            )
            owners[rq] = spec_path.parent.name
