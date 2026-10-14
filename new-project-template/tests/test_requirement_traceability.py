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
    skills_dir = ROOT / ".github" / "skills"
    if not all(
        (skills_dir / skill / "SKILL.md").is_file()
        for skill in _SKILL_COMMAND_PAIRS
    ):
        pytest.skip("requirements skills not fully vendored; nothing to compare")
    for skill_name, command_file in sorted(_SKILL_COMMAND_PAIRS.items()):
        skill = (skills_dir / skill_name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        command = (
            EXTENSION_SOURCE / "commands" / command_file
        ).read_text(encoding="utf-8")
        assert _prose_after_frontmatter(skill) == _prose_after_frontmatter(command), (
            f"{skill_name}/SKILL.md prose diverges from {command_file}; "
            f"regenerate the skill from the extension command"
        )


def test_skill_generator_output_hermetic(tmp_path):
    """generate-skills.sh run against a synthetic project produces the
    skills the mirrors guard: quoted frontmatter that parses even for
    descriptions carrying a colon-and-space, the command body verbatim,
    the manifest author in the metadata (never the target's basename),
    and pruning of a generator-owned skill directory whose command no
    longer exists, while vendored core skills are never touched.

    The committed-skill mirrors (prose sync, frontmatter parse) guard
    drift between regeneration runs; this test guards the generator
    itself, so a quoting or pruning regression fails at the generator's
    real invocation path instead of surfacing as churn on the next
    regeneration."""
    import yaml

    if not SEEDED:
        pytest.skip("extension not installed yet; run bootstrap.sh first")
    generator = EXTENSION_SOURCE / "scripts" / "bash" / "generate-skills.sh"
    manifest = (EXTENSION_SOURCE / "extension.yml").read_text(encoding="utf-8")
    author_match = re.search(r'^\s+author:\s*"?([^"\n]+)"?\s*$', manifest, re.M)
    if author_match is None:
        pytest.fail(
            "extension.yml has no author field; the generator's "
            "manifest-author default has nothing to read"
        )
    expected_author = author_match.group(1).strip()

    stale = tmp_path / ".github" / "skills" / "speckit-requirements-olddiscipline"
    stale.mkdir(parents=True)
    (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
    vendored = tmp_path / ".github" / "skills" / "speckit-plan"
    vendored.mkdir(parents=True)
    (vendored / "SKILL.md").write_text("vendored\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(generator), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    colon_skill = (
        tmp_path / ".github" / "skills" / "speckit-requirements-plan-checklist"
        / "SKILL.md"
    )
    assert colon_skill.is_file(), (
        "generator did not write the plan-checklist skill whose "
        "description carries a colon-and-space"
    )
    text = colon_skill.read_text(encoding="utf-8")
    lines = text.splitlines()
    end = lines.index("---", 1)
    parsed = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(parsed, dict), "generated frontmatter is not a mapping"
    assert parsed["name"] == "speckit-requirements-plan-checklist"
    assert ": " in parsed["description"], (
        "fixture lost its colon-carrying description; the quoting check "
        "no longer tests anything"
    )
    assert parsed["metadata"]["author"] == expected_author, (
        "generator did not take the manifest author; a bare "
        "`generate-skills.sh .` would churn every skill's author"
    )
    command_text = (
        EXTENSION_SOURCE / "commands" / "speckit.requirements.plan-checklist.md"
    ).read_text(encoding="utf-8")
    command_lines = command_text.splitlines()
    command_body = "\n".join(command_lines[command_lines.index("---", 1) + 1:]).strip()
    assert _prose_after_frontmatter(text) == command_body.strip(), (
        "generated skill body diverges from the command body"
    )
    assert not stale.exists(), "stale generator-owned skill directory survived"
    assert vendored.is_dir() and (vendored / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "vendored\n", "vendored core skill was touched"


def test_generated_skill_frontmatter_parses():
    """Every generated SKILL.md frontmatter parses as YAML.

    The generator writes the command's description into the frontmatter
    raw; a description carrying a colon-and-space would break the
    scalar and skill discovery with it. The check is part of the mirror
    pair: frontmatter may differ in plumbing, but it may never be
    invalid. Skips when the requirements skills are not vendored (the
    same convention the enforcement-chain tests use)."""
    import yaml

    skills_dir = ROOT / ".github" / "skills"
    if not (
        skills_dir.is_dir()
        and any(skills_dir.glob("speckit-requirements-*/SKILL.md"))
    ):
        pytest.skip("no vendored requirements skills; nothing to parse")
    for skill in sorted(skills_dir.glob("speckit-requirements-*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert lines[0].strip() == "---", f"{skill.name}: missing frontmatter"
        try:
            end = lines.index("---", 1)
        except ValueError:
            assert False, f"{skill.name}: frontmatter never closes"
        parsed = yaml.safe_load("\n".join(lines[1:end]))
        assert isinstance(parsed, dict), f"{skill.name}: frontmatter is not a mapping"
        assert isinstance(parsed.get("description"), str) and parsed["description"], (
            f"{skill.name}: description is not a non-empty string - "
            f"regenerate with the current generator"
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
